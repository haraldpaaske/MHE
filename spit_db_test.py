import numpy as np


def split_into_shares(secret_vector):
    """ Splits a fingerprint template into two secret shares. """
    s2 = np.random.rand(*secret_vector.shape)  # Use random float values
    s1 = secret_vector - s2  # Ensure sum of shares reconstructs original
    return s1, s2


probe = np.load("IrisFingerprintDatabases/FingerprintDatabase/3567/3567d11.npy")

p1, p2 = split_into_shares(probe)

t1 = np.load("server1_database/3567/3567d1.npy")
t2 = np.load("server2_database/3567/3567d1.npy")
f = np.sum(t1 + t2)

s1_diff = t1 - p1
s2_diff = t2 - p2

# Reconstruct the actual difference
reconstructed_diff = s1_diff + s2_diff

# Compute the squared Euclidean distance using secret shares
squared_distance = np.sum(reconstructed_diff ** 2)

#Euclidean distance
euclidean_distance = np.sqrt(squared_distance)
# Print the match result

print(f"Euclidean Distance (Secret Shared Computation): {euclidean_distance}")




