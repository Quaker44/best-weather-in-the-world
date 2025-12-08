#!/usr/bin/env python3
"""
Patched & instrumented version of your station offset calculation script.

This file includes:
- Full multiprocessing-safe pairwise computation (using Pool initializer)
- Restored detailed print statements and progress reporting
- Spatial-filter support preserved
- Checkpointing and debug prints to ensure the pairwise loop runs
- Safety/diagnostic exits when no pairs are available
"""

import os
import sys
import math
import time
import pickle
from itertools import combinations
from collections import defaultdict
from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd
from tqdm import tqdm

# ==================== USER SETTINGS ====================
input_dir = r"C:\Projects\best-weather-in-the-world\Data\GHCND"
metadata_file = r"C:\Projects\best-weather-in-the-world\Data\All Stations with TMAX.csv"
output_csv = r"C:\Projects\best-weather-in-the-world\New Dataset\US\US_Offsets.csv"

hot_threshold = 322   # TMAX >= this defines "hot day" (tenths of Celsius)

date_column = "DATE"
tmax_column = "TMAX"
meta_cols = ["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME"]

prefix_filter = ["US"]
state_filter = []
exclude_states = ["AK", "HI"]

use_spatial_filter = False
max_distance_km = 300

min_overlap_for_edge = 5
checkpoint_interval = 3600
checkpoint_file = r"C:\Projects\best-weather-in-the-world\New Dataset\US\checkpoint_pairwise.pkl"
use_multiprocessing = True
num_workers = None
# ========================================================

# ---------- Globals for worker processes ----------
WORKER_STATION_SERIES = None


def worker_init(series_dict):
    """Initializer for Pool workers: set a global reference to station_series (pickled once)."""
    global WORKER_STATION_SERIES
    WORKER_STATION_SERIES = series_dict


def compute_pair_overlap_worker(pair):
    """Worker-friendly overlap computation; pair is (A, B)."""
    A, B = pair
    sa = WORKER_STATION_SERIES.get(A)
    sb = WORKER_STATION_SERIES.get(B)
    if sa is None or sb is None:
        return None

    # efficient index intersection
    common_idx = sa.index.intersection(sb.index)
    if len(common_idx) == 0:
        return None

    va = sa.loc[common_idx].values
    vb = sb.loc[common_idx].values
    valid_mask = (~np.isnan(va)) & (~np.isnan(vb))
    n_overlap = int(valid_mask.sum())
    if n_overlap < 1:
        return None

    diffs = (va[valid_mask] - vb[valid_mask]).astype(float)
    mean_diff = float(np.nanmean(diffs))
    return (A, B, mean_diff, n_overlap)


# ---------- Utilities ----------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def read_station_file(filepath):
    """Read and clean a single station file with strict QC."""
    try:
        sample = pd.read_csv(filepath, nrows=0)
        has_qc = "TMAX_ATTRIBUTES" in sample.columns
    except Exception:
        has_qc = False

    if not has_qc:
        raise RuntimeError(f"{os.path.basename(filepath)} missing TMAX_ATTRIBUTES - file rejected")

    cols_to_read = [date_column, tmax_column, "TMAX_ATTRIBUTES"]
    try:
        df = pd.read_csv(filepath, usecols=cols_to_read, low_memory=False)
    except Exception:
        raise RuntimeError(f"{os.path.basename(filepath)} missing required columns")

    df[date_column] = pd.to_datetime(df[date_column], format='mixed', errors='coerce')
    df = df.dropna(subset=[date_column])

    df[tmax_column] = pd.to_numeric(df[tmax_column], errors='coerce')
    df.loc[df[tmax_column].isin([999, 9999]), tmax_column] = np.nan

    qc_col = df["TMAX_ATTRIBUTES"].fillna("")
    df.loc[qc_col == "", tmax_column] = np.nan

    has_comma = qc_col.str.contains(",", na=False)
    if has_comma.any():
        middle = qc_col.str.split(",", expand=True, n=2)
        if 1 in middle.columns:
            df.loc[middle[1].str.strip().ne(""), tmax_column] = np.nan

    return df.set_index(date_column)[tmax_column].sort_index()


# ---------- Main Workflow ----------
def main():
    start_time = time.time()

    print("=" * 70)
    print("OPTIMIZED STATION OFFSET CALCULATION – PATCHED FOR MULTIPROCESSING")
    print("=" * 70)

    # ----------------- Load Metadata -----------------
    print(f"\n1. Loading metadata from: {metadata_file}")
    metadata_df = pd.read_csv(metadata_file)
    print(f"   Total stations in metadata: {len(metadata_df)}")

    filtered_df = metadata_df.copy()

    if prefix_filter:
        filtered_df = filtered_df[filtered_df['STATION'].str[:2].isin(prefix_filter)]
        print(f"   After prefix filter {prefix_filter}: {len(filtered_df)} stations")

    if state_filter:
        filtered_df = filtered_df[filtered_df['STATE'].isin(state_filter)]
        print(f"   After state filter {state_filter}: {len(filtered_df)} stations")

    if exclude_states:
        before = len(filtered_df)
        filtered_df = filtered_df[~filtered_df['STATE'].isin(exclude_states)]
        print(f"   After excluding states {exclude_states}: {len(filtered_df)} stations (removed {before - len(filtered_df)})")

    if len(filtered_df) == 0:
        raise RuntimeError("No stations match the filter criteria!")

    station_lookup = {}
    for _, row in filtered_df.iterrows():
        station_code = str(row['STATION'])
        station_lookup[station_code] = {
            'latitude': float(row['LATITUDE']) if pd.notna(row['LATITUDE']) else None,
            'longitude': float(row['LONGITUDE']) if pd.notna(row['LONGITUDE']) else None,
            'elevation': row['ELEVATION'] if pd.notna(row['ELEVATION']) else None,
            'state': row['STATE'] if pd.notna(row['STATE']) else '',
            'name': row['NAME'] if pd.notna(row['NAME']) else ''
        }

    print(f"   Stations after filtering: {len(station_lookup)}")

    # ----------------- Read Station Files -----------------
    print(f"\n2. Reading station files from: {input_dir}")

    all_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.csv', '.txt'))]
    print(f"   Total files in directory: {len(all_files)}")

    station_files = {}
    for fname in all_files:
        station_code = os.path.splitext(fname)[0]
        if station_code in station_lookup:
            station_files[station_code] = fname

    print(f"   Files matching filtered stations: {len(station_files)}")

    if len(station_files) == 0:
        raise RuntimeError("No station files found matching the filter criteria!")

    station_meta = {}
    station_series = {}
    station_total_hot_days = {}
    all_hot_days = set()

    print(f"\n3. Loading data and extracting hot days >= {hot_threshold}...")

    for station_code, fname in tqdm(station_files.items(), desc="Reading stations"):
        path = os.path.join(input_dir, fname)
        try:
            series = read_station_file(path)

            hot_dates = series[series >= hot_threshold].index
            all_hot_days.update(hot_dates)

            station_meta[station_code] = station_lookup[station_code]
            station_series[station_code] = series
            station_total_hot_days[station_code] = len(hot_dates)

        except Exception as e:
            print(f"\nSkipping {fname}: {e}")
            continue

    all_hot_days = pd.to_datetime(sorted(all_hot_days))
    if len(all_hot_days) == 0:
        raise RuntimeError(f"No hot days (TMAX >= {hot_threshold}) found!")

    # Filter series to hot days only
    for station_code in list(station_series.keys()):
        series = station_series[station_code]
        station_series[station_code] = series[series.index.isin(all_hot_days)].copy()

    stations = list(station_series.keys())
    print(f"   Stations with data: {len(stations)}")
    print(f"   Total unique hot days: {len(all_hot_days)}")

    # ----------------- Build Spatial Index (Optional) -----------------
    spatial_pairs = None
    if use_spatial_filter:
        print(f"\n4. Building spatial index (max distance: {max_distance_km} km)...")
        coords = {}
        for station_code in stations:
            meta = station_meta[station_code]
            lat = meta.get('latitude')
            lon = meta.get('longitude')
            if lat is not None and lon is not None:
                coords[station_code] = (lat, lon)
        print(f"   Stations with coordinates: {len(coords)}")

        spatial_pairs = set()
        stations_with_coords = list(coords.keys())
        for i, A in enumerate(tqdm(stations_with_coords, desc="Spatial filtering")):
            lat1, lon1 = coords[A]
            for B in stations_with_coords[i+1:]:
                lat2, lon2 = coords[B]
                dist = haversine_distance(lat1, lon1, lat2, lon2)
                if dist <= max_distance_km:
                    spatial_pairs.add((A, B))
                    spatial_pairs.add((B, A))

        print(f"   Pairs within {max_distance_km}km: {len(spatial_pairs)//2:,}")
        print(f"   Reduction: {100*(1 - len(spatial_pairs)/(len(stations)*(len(stations)-1))):.1f}%")

    # ----------------- Pairwise Comparisons -----------------
    print(f"\n{ '4' if not use_spatial_filter else '5'}. Computing pairwise overlaps...")

    pairwise_mean = {}
    pairwise_count = {}
    connectivity = defaultdict(int)

    pairs = list(combinations(stations, 2))
    total_pairs = len(pairs)

    if use_spatial_filter and spatial_pairs is not None:
        pairs = [(A, B) for A, B in pairs if (A, B) in spatial_pairs]
        print(f"   Pairs to process (after spatial filter): {len(pairs):,} of {total_pairs:,}")
    else:
        print(f"   Pairs to process: {len(pairs):,}")

    if len(pairs) == 0:
        print("   ❗ No pairs to process — exiting")
        sys.exit(1)

    # Check for existing checkpoint
    start_idx = 0
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)

            pairwise_mean = checkpoint_data['pairwise_mean']
            pairwise_count = checkpoint_data['pairwise_count']
            connectivity = checkpoint_data['connectivity']
            start_idx = checkpoint_data['last_index']

            print(f"   📂 Resuming from checkpoint: {start_idx:,}/{len(pairs):,} pairs complete")
            print(f"      ({100*start_idx/len(pairs):.1f}% done)")
        except Exception as e:
            print(f"   ⚠️  Could not load checkpoint: {e}")
            print(f"   Starting from beginning...")
            start_idx = 0

    pairs_with_overlap = len(pairwise_count) // 2  # Each pair stored twice (A,B) and (B,A)

    # multiprocessing block
    if use_multiprocessing:
        if num_workers is None:
            workers = cpu_count()
        else:
            workers = num_workers

        print(f"   🚀 Using multiprocessing with {workers} workers")

        chunk_size = 100000
        last_checkpoint_time = time.time()

        # iterate through chunks
        for chunk_start in range(start_idx, len(pairs), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(pairs))
            chunk_pairs = pairs[chunk_start:chunk_end]

            print(f"   Processing pairs {chunk_start:,} to {chunk_end:,} (chunk size: {len(chunk_pairs):,})")

            # start pool with initializer (station_series pickled once)
            with Pool(workers, initializer=worker_init, initargs=(station_series,)) as pool:
                results = list(tqdm(
                    pool.imap_unordered(compute_pair_overlap_worker, chunk_pairs, chunksize=500),
                    total=len(chunk_pairs),
                    desc=f"Chunk {chunk_start//chunk_size + 1}",
                    position=0
                ))

            for result in results:
                if result is not None:
                    A, B, mean_diff, n_overlap = result
                    pairs_with_overlap += 1

                    pairwise_mean[(A, B)] = mean_diff
                    pairwise_mean[(B, A)] = -mean_diff
                    pairwise_count[(A, B)] = n_overlap
                    pairwise_count[(B, A)] = n_overlap
                    connectivity[A] += n_overlap
                    connectivity[B] += n_overlap

            # Checkpoint after each chunk if enough time elapsed
            if time.time() - last_checkpoint_time >= checkpoint_interval:
                checkpoint_data = {
                    'pairwise_mean': pairwise_mean,
                    'pairwise_count': pairwise_count,
                    'connectivity': connectivity,
                    'last_index': chunk_end,
                    'timestamp': time.time()
                }
                try:
                    with open(checkpoint_file, 'wb') as f:
                        pickle.dump(checkpoint_data, f)
                    print(f"\n   💾 Checkpoint saved at {chunk_end:,}/{len(pairs):,} pairs ({100*chunk_end/len(pairs):.1f}%)")
                except Exception as e:
                    print(f"\n   ⚠️  Could not save checkpoint: {e}")

                last_checkpoint_time = time.time()

    else:
        print(f"   ⚙️  Using single-threaded processing")
        last_checkpoint_time = time.time()

        for i, (A, B) in enumerate(tqdm(pairs[start_idx:], desc="Pairwise comparisons", initial=start_idx, total=len(pairs))):
            sa = station_series[A]
            sb = station_series[B]

            common_idx = sa.index.intersection(sb.index)
            if len(common_idx) == 0:
                continue

            va = sa.loc[common_idx].values
            vb = sb.loc[common_idx].values
            valid_mask = (~np.isnan(va)) & (~np.isnan(vb))
            n_overlap = int(valid_mask.sum())

            if n_overlap < 1:
                continue

            pairs_with_overlap += 1
            diffs = (va[valid_mask] - vb[valid_mask]).astype(float)
            mean_diff = float(np.nanmean(diffs))

            pairwise_mean[(A, B)] = mean_diff
            pairwise_mean[(B, A)] = -mean_diff
            pairwise_count[(A, B)] = n_overlap
            pairwise_count[(B, A)] = n_overlap
            connectivity[A] += n_overlap
            connectivity[B] += n_overlap

            # Checkpoint every hour
            if time.time() - last_checkpoint_time >= checkpoint_interval:
                checkpoint_data = {
                    'pairwise_mean': pairwise_mean,
                    'pairwise_count': pairwise_count,
                    'connectivity': connectivity,
                    'last_index': start_idx + i + 1,
                    'timestamp': time.time()
                }
                try:
                    with open(checkpoint_file, 'wb') as f:
                        pickle.dump(checkpoint_data, f)
                    print(f"\n   💾 Checkpoint saved at {start_idx + i + 1:,}/{len(pairs):,} pairs ({100*(start_idx + i + 1)/len(pairs):.1f}%)")
                except Exception as e:
                    print(f"\n   ⚠️  Could not save checkpoint: {e}")

                last_checkpoint_time = time.time()

    # Clean up checkpoint file after successful completion
    if os.path.exists(checkpoint_file):
        try:
            os.remove(checkpoint_file)
            print(f"   🗑️  Checkpoint file removed (processing complete)")
        except Exception:
            pass

    print(f"   Pairs with overlap >= 1 day: {pairs_with_overlap:,}")

    if len(pairwise_count) == 0:
        raise RuntimeError("No overlapping hot days found between any station pairs!")

    # ----------------- Anchor Selection -----------------
    print(f"\n{ '5' if not use_spatial_filter else '6'}. Selecting anchor station...")

    connectivity_series = pd.Series(connectivity).reindex(stations).fillna(0).astype(int)
    anchor_station = connectivity_series.idxmax()
    anchor_score = int(connectivity_series.max())

    print(f"   Anchor: {anchor_station}")
    print(f"   Connectivity: {anchor_score:,}")

    # ----------------- Least Squares Solution -----------------
    print(f"\n{ '6' if not use_spatial_filter else '7'}. Computing offsets via least squares...")

    var_stations = [s for s in stations if s != anchor_station]
    var_index = {s: idx for idx, s in enumerate(var_stations)}

    eq_rows = []
    eq_rhs = []
    seen_pairs = set()

    for (A, B), count in pairwise_count.items():
        if (A, B) in seen_pairs or (B, A) in seen_pairs:
            continue
        seen_pairs.add((A, B))
        seen_pairs.add((B, A))

        if count < min_overlap_for_edge:
            continue

        d_ab = pairwise_mean[(A, B)]
        sqrtw = math.sqrt(count)
        row = np.zeros(len(var_stations), dtype=float)

        if A != anchor_station:
            row[var_index[A]] = sqrtw
        if B != anchor_station:
            row[var_index[B]] -= sqrtw

        eq_rows.append(row)
        eq_rhs.append(sqrtw * d_ab)

    print(f"   Equations: {len(eq_rows)}")
    print(f"   Variables: {len(var_stations)}")

    X = np.vstack(eq_rows)
    y = np.array(eq_rhs)
    sol, residuals, rank, svals = np.linalg.lstsq(X, y, rcond=None)

    offsets = {anchor_station: 0.0}
    for sname, val in zip(var_stations, sol):
        offsets[sname] = float(val)

    # Compute uncertainties
    resids = X.dot(sol) - y
    dof = max(1, X.shape[0] - X.shape[1])
    sigma2 = float((resids**2).sum() / dof)

    cov = None
    try:
        XtX = X.T.dot(X)
        cov = sigma2 * np.linalg.inv(XtX)
    except Exception:
        pass

    uncertainties = {}
    for s in stations:
        if s == anchor_station:
            uncertainties[s] = 0.0
        else:
            idx = var_index[s]
            if cov is not None:
                uncertainties[s] = float(math.sqrt(max(0.0, cov[idx, idx])))
            else:
                uncertainties[s] = float(math.sqrt(sigma2) /
                                       math.sqrt(max(1, connectivity.get(s, 1))))

    overlap_with_anchor = {s: pairwise_count.get((s, anchor_station), 0) for s in stations}
    overlap_with_anchor[anchor_station] = connectivity.get(anchor_station, 0)

    # ----------------- Output -----------------
    print(f"\n{ '7' if not use_spatial_filter else '8'}. Preparing output...")

    rows = []
    for s in stations:
        meta = station_meta.get(s, {})
        rows.append({
            "station_code": s,
            "name": meta.get("name", ""),
            "latitude": meta.get("latitude", ""),
            "longitude": meta.get("longitude", ""),
            "elevation": meta.get("elevation", ""),
            "state": meta.get("state", ""),
            "connectivity": int(connectivity.get(s, 0)),
            "overlap_with_anchor": int(overlap_with_anchor.get(s, 0)),
            f"offset_to_{anchor_station}": offsets.get(s, float("nan")),
            "uncertainty": uncertainties.get(s, float("nan")),
            "total_hot_days": int(station_total_hot_days.get(s, 0))
        })

    out_df = pd.DataFrame(rows).sort_values(
        by=f"offset_to_{anchor_station}", ascending=False
    ).reset_index(drop=True)

    out_df.to_csv(output_csv, index=False)
    print(f"\n✅ Saved results to: {output_csv}")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes ({elapsed:.1f} seconds)")
    print("=" * 70)


if __name__ == '__main__':
    main()
