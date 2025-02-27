import numpy as np
import matplotlib.pyplot as plt

# Parameters
start_weight = 1.0
end_weight = 0.0
steps = 31

# Generate linearly decaying weights
weights = np.linspace(start_weight, end_weight, steps)

print(weights)

1.         0.96666667 0.93333333 0.9        0.86666667 0.83333333
 0.8        0.76666667 0.73333333 0.7        0.66666667 0.63333333
 0.6        0.56666667 0.53333333 0.5        0.46666667 0.43333333
 0.4        0.36666667 0.33333333 0.3        0.26666667 0.23333333
 0.2        0.16666667 0.13333333 0.1        0.06666667 0.03333333
 0.   
