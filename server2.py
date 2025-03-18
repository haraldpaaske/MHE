import socket
import time
import numpy as np
import tenseal as ts

HOST = "127.0.0.1"
PORT = 65432

server2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server2.bind((HOST, PORT))
server2.listen(1)
print("Server 2 waiting...")

def send_large_data(sock, data_bytes):
    size = len(data_bytes)
    sock.sendall(size.to_bytes(4, 'big'))
    sock.sendall(data_bytes)

def receive_large_data(sock):
    size = int.from_bytes(sock.recv(4), 'big')
    data = b""
    while len(data) < size:
        chunk = sock.recv(min(131072, size - len(data)))
        if not chunk:
            raise ConnectionError("Closed prematurely")
        data += chunk
    return data

try:
    conn, addr = server2.accept()
    server_proc_start = time.perf_counter()

    id = receive_large_data(conn).decode()
    ctx_bytes = receive_large_data(conn)
    context = ts.context_from(ctx_bytes)
    enc_p2 = ts.ckks_vector_from(context, receive_large_data(conn))

    t2 = np.load(f"server2_database/{id}/{id}d0.npy")
    Enc_t2 = ts.ckks_vector(context, t2.tolist())
    diff = (Enc_t2 - enc_p2).serialize()

    send_large_data(conn, diff)
    server_proc_end = time.perf_counter()
    print(f"[Server2] ID={id}, processed in {server_proc_end - server_proc_start:.6f}s")
finally:
    conn.close()
    server2.close()