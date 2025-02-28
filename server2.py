import socket
import numpy as np
import tenseal as ts

# Server 2 setup
HOST = "127.0.0.1"
PORT = 65432

server2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server2_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ✅ Allow immediate port reuse
server2_socket.bind((HOST, PORT))
server2_socket.listen(1)

print("Server 2 is waiting for a connection...")

# Function to send large data
def send_large_data(sock, data_bytes):
    """Send large data with a size prefix."""
    data_size = len(data_bytes)
    sock.sendall(data_size.to_bytes(4, 'big'))
    sock.sendall(data_bytes)


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

try:
    conn, addr = server2_socket.accept()
    print(f"Connected to {addr}")

    # 1️⃣ Receive the biometric ID
    received_id = conn.recv(1024).decode()
    print(f"Server 2 received ID: {received_id}")

    # 2️⃣ Send ACK to the client confirming receipt of ID
    conn.sendall(b"ACK")

    # 3️⃣ Receive serialized TenSEAL context
    context_bytes = receive_large_data(conn)
    context = ts.context_from(context_bytes)

    # 4️⃣ Send another ACK to confirm context receipt
    conn.sendall(b"ACK")

    # 5️⃣ Receive encrypted probe share
    Enc_p2 = ts.bfv_vector_from(context, receive_large_data(conn))
    t_2 = np.load(f"server2_database/{received_id}/{received_id}d0.npy")
    t_2 = t_2 * 1000
    Enc_t2 = ts.bfv_vector(context, t_2.tolist())

    # 6️⃣ Compute difference
    Enc_diff = Enc_t2 - Enc_p2

    # 7️⃣ Send back the encrypted squared distance
    send_large_data(conn, Enc_diff.serialize())
    print("job done")

finally:
    conn.close()
    server2_socket.close()