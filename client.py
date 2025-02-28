import socket
import numpy as np
import tenseal as ts


# Initialize TenSEAL BFV context
PLAIN_MODULUS = 1032193  # Store plain modulus separately

context = ts.context(
    scheme=ts.SCHEME_TYPE.BFV,
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[40, 40, 40],  # BFV moduli
    plain_modulus=PLAIN_MODULUS  # Set manually
)
context.generate_galois_keys()
context.generate_relin_keys()

# Serialize context
context_bytes = context.serialize()

def split_into_shares(secret_vector):
    """ Splits a fingerprint template into two secret shares. """
    s2 = np.random.rand(*secret_vector.shape)  # Use random float values
    s1 = secret_vector - s2  # Ensure sum of shares reconstructs original
    return s1, s2



# Function to send large data
def send_large_data(sock, data_bytes):
    """Send large data with a size prefix."""
    data_size = len(data_bytes)
    sock.sendall(data_size.to_bytes(4, 'big'))
    sock.sendall(data_bytes)

# Function to receive large data
def receive_large_data(sock):
    """Receive large data in chunks based on the size prefix."""
    data_size = int.from_bytes(sock.recv(4), 'big')  # Read size first
    data_bytes = b""

    # Read the expected data size in chunks
    CHUNK_SIZE = 4096
    while len(data_bytes) < data_size:
        chunk = sock.recv(min(CHUNK_SIZE, data_size - len(data_bytes)))
        if not chunk:
            raise ConnectionError("Connection closed before receiving full data")
        data_bytes += chunk

    return data_bytes



# Define the biometric ID to send
#biometric_id = input("Enter Biometric ID: ")
biometric_id = "3567"

probe = np.load(f"IrisFingerprintDatabases/FingerprintDatabase/3567/3567d11.npy")


p_1, p_2 = split_into_shares(probe)

#scale probes
p_1 = p_1*1000
p_2 = p_2*1000


# Encrypt P1 and P2 using BFV
Enc_p1 = ts.bfv_vector(context, p_1.tolist())
Enc_p2 = ts.bfv_vector(context, p_2.tolist())


## 🔹 Send ID & Encrypted p_1 to Server 1 ##
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 65431))

    # Send the ID and wait for acknowledgment before proceeding
    client_socket.sendall(biometric_id.encode())

    # 2️⃣ Wait for the server's ACK response
    ack = client_socket.recv(1024)
    if ack != b"ACK":
        print("Error: Server 1 did not acknowledge ID.")
        client_socket.close()
        exit()

    # 3️⃣ Send the context only after receiving the ACK
    send_large_data(client_socket, context_bytes)

    # 4️⃣ Wait for another ACK before sending the probe share
    ack = client_socket.recv(1024)
    if ack != b"ACK":
        print("Error: Server 1 did not acknowledge context.")
        client_socket.close()
        exit()

    # 5️⃣ Send the encrypted probe share
    send_large_data(client_socket, Enc_p1.serialize())

    # 6️⃣ Receive encrypted squared distance result
    Enc_result1 = ts.bfv_vector_from(context, receive_large_data(client_socket))

finally:
    client_socket.close()


## 🔹 Send ID & Encrypted p_2 to Server 2 ##
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 65432))

    # Send the ID and wait for acknowledgment before proceeding
    client_socket.sendall(biometric_id.encode())

    # 2️⃣ Wait for the server's ACK response
    ack = client_socket.recv(1024)
    if ack != b"ACK":
        print("Error: Server 1 did not acknowledge ID.")
        client_socket.close()
        exit()

    # 3️⃣ Send the context only after receiving the ACK
    send_large_data(client_socket, context_bytes)

    # 4️⃣ Wait for another ACK before sending the probe share
    ack = client_socket.recv(1024)
    if ack != b"ACK":
        print("Error: Server 1 did not acknowledge context.")
        client_socket.close()
        exit()

    # 5️⃣ Send the encrypted probe share
    send_large_data(client_socket, Enc_p2.serialize())

    # 6️⃣ Receive encrypted squared distance result
    Enc_result2 = ts.bfv_vector_from(context, receive_large_data(client_socket))

finally:
    client_socket.close()


## 🔹 Compute Final Secure Distance ##
Enc_total_difference = Enc_result1 + Enc_result2

# Mahattan distance
Enc_manhattan_distance = Enc_total_difference.sum()
manhattan_distance = abs(Enc_manhattan_distance.decrypt()[0])

# Euclidean distance
Enc_squared_difference = Enc_total_difference * Enc_total_difference
Enc_squared_distance = Enc_squared_difference.sum()
#must decrypt before taking square root (but its safe)
decrypted_squared_distance = Enc_squared_distance.decrypt()[0] % PLAIN_MODULUS
euclidean_distance = np.sqrt(decrypted_squared_distance)

# Print match result
print(f"Euclidean Distance: {euclidean_distance}")
print(f"Manhattan Distance: {manhattan_distance}")


# Matching thresholds
threshold_1 = 20  # Identical templates expected to be below 20
threshold_2 = 500  # Same finger, different template
threshold_3 = 800 # Different finger

if euclidean_distance <= threshold_1:
    print("Identical fingerprints")
elif euclidean_distance <= threshold_2:
    print("Most definitely a match")
elif euclidean_distance <= threshold_3:
    print("Cannot determine, needs further investigation")
else:
    print("Not a match")