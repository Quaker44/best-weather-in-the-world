import math

def calculate_sample_size(confidence_level, margin_of_error, population_size, sigma=0.25):
    """
    Calculates the required sample size given confidence level, margin of error, and population size.
    
    Parameters:
    confidence_level (float): The confidence level (e.g., 0.90 for 90%, 0.95 for 95%, 0.99 for 99%)
    margin_of_error (float): The acceptable margin of error (e.g., 0.05 for 5%)
    population_size (int or float): The total population size
    sigma (float, optional): The estimated standard deviation (default is 0.25 for worst-case scenario)
    
    Returns:
    int: The required sample size
    """
    # Z-scores for common confidence levels
    Z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576, 0.99999: 4.417}
    
    # Get the corresponding Z-score
    Z = Z_scores.get(confidence_level, None)
    if Z is None:
        raise ValueError("Unsupported confidence level. Choose from 0.90, 0.95, or 0.99.")
    
    # Compute initial sample size
    n = (Z * sigma / margin_of_error) ** 2
    
    # Apply finite population correction
    n_adj = n / (1 + (n - 1) / population_size)
    
    return math.ceil(n_adj)  # Round up to the nearest whole number

# Example usage
if __name__ == "__main__":
    confidence_levels = [0.99999, 
                        0.95,
                        0.99
                        ]
    margins_of_error = [0.20, 
                        0.10, 
                        0.15
                        ]
    population_size = 30  # Example population size
    
    for confidence in confidence_levels:
        for margin in margins_of_error:
            sample_size = calculate_sample_size(confidence, margin, population_size)
            print(f"Confidence: {confidence*100}%, Margin of Error: {margin*100}% -> Sample Size: {sample_size}")
