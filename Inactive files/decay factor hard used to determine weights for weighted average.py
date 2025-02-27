import math

# Number of years (1994 to 2023 inclusive)
num_years = 30

# Calculate the decay factor to ensure the first year is worth 1% of the last year
def calculate_decay_factor():
    target_ratio = 0.1
    decay_factor = -math.log(target_ratio) / (num_years - 1)
    return decay_factor

# Function to calculate weights for each year based on the decay factor
def calculate_weights(decay_factor):
    weights = [math.exp(-decay_factor * (num_years - 1 - i)) for i in range(num_years)]
    return weights

# Calculate decay factor
decay_factor = calculate_decay_factor()
print(f"Calculated decay factor: {decay_factor:.4f}")

# Calculate weights using the decay factor
weights = calculate_weights(decay_factor)

# Print weights for each year from 1994 to 2023
for year, weight in zip(range(1994, 2024), weights):
    print(f"Year {year}: Weight {weight:.4f}")

