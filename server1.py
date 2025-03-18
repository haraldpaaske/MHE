import socket
import time
import numpy as np
import tenseal as ts

HOST = "127.0.0.1"
PORT = 65431

server1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server1.bind((HOST, PORT))
server1.listen(1)
print("Server 1 waiting...")

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
    conn, addr = server1.accept()
    server_proc_start = time.perf_counter()

    id = receive_large_data(conn).decode()
    ctx_bytes = receive_large_data(conn)
    context = ts.context_from(ctx_bytes)
    enc_p1 = ts.ckks_vector_from(context, receive_large_data(conn))

    receive_time = time.perf_counter()

    t1 = np.load(f"server1_database/{id}/{id}d0.npy")
    Enc_t1 = ts.ckks_vector(context, t1.tolist())
    diff = (Enc_t1 - enc_p1).serialize()

    calculation_time = time.perf_counter()

    send_large_data(conn, diff)
    server_proc_end = time.perf_counter()
    print(f"[Server1] ID={id}")
    print(f"receiving time : {receive_time - server_proc_start:.6f}s")
    print(f"calculation time : {calculation_time - receive_time:.6f}s")
    print(f"send time : {server_proc_end - calculation_time:.6f}s")

    print(f"total processing time : {server_proc_end - server_proc_start:.6f}s")
finally:
    conn.close()
    server1.close()