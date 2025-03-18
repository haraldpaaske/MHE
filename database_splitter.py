from pathlib import Path
import numpy as np

# Define paths using pathlib
input_folder = Path("IrisFingerprintDatabases/IrisDatabase")
server1_folder = Path("server1_iris_database")
server2_folder = Path("server2_iris_database")

# Ensure output folders exist
server1_folder.mkdir(parents=True, exist_ok=True)
server2_folder.mkdir(parents=True, exist_ok=True)

def split_into_shares(secret_vector):
    """ Splits a fingerprint template into two secret shares. """
    s2 = np.random.rand(*secret_vector.shape)  # Generate random float values
    s1 = secret_vector - s2  # Ensure sum of shares reconstructs original
    return s1, s2

# Iterate through user ID folders in the input database
for user_id_folder in input_folder.iterdir():
    if not user_id_folder.is_dir():  # Skip non-folder entries
        continue

    # Create corresponding folders in server1 and server2 databases
    server1_user_folder = server1_folder / user_id_folder.name
    server2_user_folder = server2_folder / user_id_folder.name

    server1_user_folder.mkdir(parents=True, exist_ok=True)
    server2_user_folder.mkdir(parents=True, exist_ok=True)

    # Process each .npy file in the user folder
    for file_path in user_id_folder.glob("*.npy"):
        # Load biometric template
        template = np.load(file_path)

        # Compute secret shares
        t1, t2 = split_into_shares(template)

        # Define save paths
        t1_path = server1_user_folder / file_path.name
        t2_path = server2_user_folder / file_path.name

        # Save secret shares in respective folders (ensure float64 for precision)
        np.save(t1_path, t1.astype(np.float64))
        np.save(t2_path, t2.astype(np.float64))

        # ✅ Load back & verify correctness
        t1_loaded = np.load(t1_path)
        t2_loaded = np.load(t2_path)
        reconstructed_template = t1_loaded + t2_loaded
        diff = np.sum(reconstructed_template - template)

        if not np.allclose(reconstructed_template, template, atol=1e-8):
            print(f"⚠️ WARNING: Mismatch detected for {file_path.name} (Sum difference: {diff})")

print("✅ Secret sharing complete. Data stored in 'server1_database' and 'server2_database'.")