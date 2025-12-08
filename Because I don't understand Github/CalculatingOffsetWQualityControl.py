#!/usr/bin/env python3
"""
Station offset estimation using overlapping TMAX >= 300 days.

Adds:
- Robust parsing of TMAX_ATTRIBUTES (quality flags)
- Logging of how many TMAX values are invalidated by QC flags and by numeric/format issues
"""

import os, math, time
from itertools import combinations
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

# ------------------ USER SETTINGS ------------------
input_dir = r"C:\Projects\best-weather-in-the-world\New Dataset\US\USStations"
output_csv = r"C:\Projects\best-weather-in-the-world\New Dataset\US\US_Offsets.csv"
hot_threshold = 300   # TMAX >= this defines "hot day"
date_column = "DATE"
tmax_column = "TMAX"
meta_cols = ["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME"]
min_overlap_for_edge = 5  # Fixed minimum number of overlapping days
# ---------------------------------------------------

start_time = time.time()

# ----------------- helpers -----------------
def is_valid_tmax(x):
    """Original sanity check."""
    if pd.isna(x):
        return False
    s = str(x).strip()
    return s not in {"", "999", "9999"}

def parse_date_multiformat(s):
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%b-%Y", "%d/%m/%Y"]
    for fmt in fmts:
        try:
            return pd.to_datetime(s, format=fmt, errors="raise")
        except Exception:
            pass
    try:
        return pd.to_datetime(s, infer_datetime_format=True, errors="coerce")
    except Exception:
        return pd.NaT

def parse_tmax_attributes(attr):
    """
    Robustly extract the 'middle' QC code.
    If attr has at least 2 comma-separated fields:
        - middle field is index 1
        - if stripped middle field is nonempty => qc_fail
    Otherwise:
        - no QC fail
    """
    if pd.isna(attr):
        return False

    s = str(attr).strip()
    if s == "":
        return False

    parts = [p.strip() for p in s.split(",")]

    # Need a middle field
    if len(parts) >= 2:
        return parts[1] != ""
    return False


def read_station_file(filepath):
    df = pd.read_csv(filepath, low_memory=False)
    if date_column not in df.columns or tmax_column not in df.columns:
        raise RuntimeError(f"{os.path.basename(filepath)} missing '{date_column}' or '{tmax_column}'")

    # Convert dates
    df[date_column] = df[date_column].apply(parse_date_multiformat)
    df = df.dropna(subset=[date_column]).copy()
    df[date_column] = pd.to_datetime(df[date_column])

    # --- CLEAN TMAX ---
    # Initial numeric coercion
    before_clean_count = df[tmax_column].notna().sum()
    df[tmax_column] = pd.to_numeric(df[tmax_column], errors="coerce")

    # Mark known invalid sentinels
    sentinel_invalid = df[tmax_column].isin([999, 9999])
    df.loc[sentinel_invalid, tmax_column] = np.nan

    # Remove other invalid based on string-format rules
    invalid_format = ~df[tmax_column].apply(is_valid_tmax)
    df.loc[invalid_format, tmax_column] = np.nan

    # TMAX_ATTRIBUTES quality flags
    qc_invalid = pd.Series(False, index=df.index)
    if "TMAX_ATTRIBUTES" in df.columns:
        qc_invalid = df["TMAX_ATTRIBUTES"].apply(parse_tmax_attributes)
        df.loc[qc_invalid, tmax_column] = np.nan

    after_clean_count = df[tmax_column].notna().sum()
    removed_numeric = sentinel_invalid.sum() + invalid_format.sum()
    removed_qc = qc_invalid.sum()

    print(f"  [{os.path.basename(filepath)}] TMAX invalidated: "
          f"{removed_numeric} from invalid numeric/format, "
          f"{removed_qc} from QC attributes.")

    # Make final series
    series = df.set_index(date_column)[tmax_column].sort_index()

    # Extract meta fields
    meta = {}
    for m in meta_cols:
        val = df.get(m)
        if val is not None:
            first = val.dropna().astype(str).str.strip()
            meta[m] = first.iloc[0] if len(first) > 0 else ""
        else:
            meta[m] = ""

    return meta, series


# ----------------- Read all stations -----------------
print("Scanning station files...")
filenames = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".csv",".txt"))])
station_meta = {}
station_series = {}
station_total_hot_days = {}

print(f"Reading {len(filenames)} station files and extracting hot days >= {hot_threshold}...")
all_hot_days = set()

for fname in tqdm(filenames, desc="Reading stations"):
    path = os.path.join(input_dir, fname)
    try:
        meta, series = read_station_file(path)
    except Exception as e:
        print(f"Skipping {fname} due to read error: {e}")
        continue

    hot_dates = series[series >= hot_threshold].index
    all_hot_days.update(hot_dates)
    station_meta[fname] = meta
    station_series[fname] = series
    station_total_hot_days[fname] = int(len(hot_dates))

all_hot_days = pd.to_datetime(sorted(all_hot_days))
if len(all_hot_days) == 0:
    raise RuntimeError(f"No hot days (TMAX >= {hot_threshold}) found in any station.")

print(f"Total unique hot days across all stations: {len(all_hot_days)}")

# Filter to hot days only
for s in station_series:
    s_series = station_series[s]
    station_series[s] = s_series[s_series.index.isin(all_hot_days)].copy()

stations = list(station_series.keys())

# ----------------- Pairwise differences -----------------
pairwise_mean = {}
pairwise_count = {}
connectivity = defaultdict(int)

print("\nComputing pairwise overlaps on hot days...")
pairs = list(combinations(stations, 2))
for A,B in tqdm(pairs, desc="Pairwise"):
    sa = station_series[A]
    sb = station_series[B]
    common_idx = sa.index.intersection(sb.index)
    va = sa.loc[common_idx].values
    vb = sb.loc[common_idx].values
    valid_mask = (~np.isnan(va)) & (~np.isnan(vb))
    n_overlap = int(valid_mask.sum())
    if n_overlap < 1:
        continue

    diffs = (va[valid_mask] - vb[valid_mask]).astype(float)
    mean_diff = float(np.nanmean(diffs))
    pairwise_mean[(A,B)] = mean_diff
    pairwise_mean[(B,A)] = -mean_diff
    pairwise_count[(A,B)] = n_overlap
    pairwise_count[(B,A)] = n_overlap
    connectivity[A] += n_overlap
    connectivity[B] += n_overlap

if len(pairwise_count) == 0:
    raise RuntimeError("No overlapping hot days found between any station pairs.")

print(f"Using fixed min_overlap_for_edge = {min_overlap_for_edge}")

# ----------------- Anchor station -----------------
connectivity_series = pd.Series(connectivity).reindex(stations).fillna(0).astype(int)
anchor_station = connectivity_series.idxmax()
anchor_score = int(connectivity_series.max())
print(f"Anchor station: {anchor_station} (connectivity = {anchor_score})")

# ----------------- Least squares -----------------
var_stations = [s for s in stations if s != anchor_station]
var_index = {s: idx for idx,s in enumerate(var_stations)}

eq_rows = []
eq_rhs = []
seen_pairs = set()

for (A,B), count in tqdm(pairwise_count.items(), desc="Edges"):
    if (A,B) in seen_pairs or (B,A) in seen_pairs:
        continue
    seen_pairs.add((A,B)); seen_pairs.add((B,A))

    if count < min_overlap_for_edge:
        continue

    d_ab = pairwise_mean[(A,B)]
    sqrtw = math.sqrt(count)
    row = np.zeros(len(var_stations), dtype=float)

    if A != anchor_station:
        row[var_index[A]] = sqrtw
    if B != anchor_station:
        row[var_index[B]] -= sqrtw

    eq_rows.append(row)
    eq_rhs.append(sqrtw * d_ab)

X = np.vstack(eq_rows)
y = np.array(eq_rhs)
sol, residuals, rank, svals = np.linalg.lstsq(X, y, rcond=None)

offsets = {anchor_station: 0.0}
for sname, val in zip(var_stations, sol):
    offsets[sname] = float(val)

# Uncertainties
resids = X.dot(sol) - y
dof = max(1, X.shape[0] - X.shape[1])
sigma2 = float((resids**2).sum()/dof) if dof > 0 else float((resids**2).sum())

cov = None
try:
    XtX = X.T.dot(X)
    cov = sigma2 * np.linalg.inv(XtX)
except Exception:
    cov = None

uncertainties = {}
for s in stations:
    if s == anchor_station:
        uncertainties[s] = 0.0
    else:
        idx = var_index[s]
        if cov is not None:
            diag = cov[idx, idx]
            uncertainties[s] = float(math.sqrt(max(0.0, diag)))
        else:
            uncertainties[s] = float(math.sqrt(sigma2) /
                                     math.sqrt(max(1, connectivity.get(s,1))))

overlap_with_anchor = {s: pairwise_count.get((s,anchor_station), 0) for s in stations}
overlap_with_anchor[anchor_station] = connectivity.get(anchor_station, 0)

# ----------------- Output -----------------
rows = []
for s in stations:
    meta = station_meta.get(s, {})
    rows.append({
        "filename": s,
        "station_code": meta.get("STATION",""),
        "name": meta.get("NAME",""),
        "latitude": meta.get("LATITUDE",""),
        "longitude": meta.get("LONGITUDE",""),
        "elevation": meta.get("ELEVATION",""),
        "connectivity": int(connectivity.get(s, 0)),
        "overlap_with_anchor": int(overlap_with_anchor.get(s,0)),
        f"offset_to_{anchor_station}": offsets.get(s, float("nan")),
        "uncertainty": uncertainties.get(s, float("nan")),
        "total_hot_days": int(station_total_hot_days.get(s, 0))
    })

out_df = pd.DataFrame(rows).sort_values(
    by=f"offset_to_{anchor_station}", ascending=False
).reset_index(drop=True)

out_df.to_csv(output_csv, index=False)
print(f"\nSaved offsets + metadata to: {output_csv}")

elapsed = time.time() - start_time
print(f"Done. Total time: {elapsed:.2f} s")
