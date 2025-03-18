import socket
import time
import threading
import numpy as np
import tenseal as ts

PLAIN_MODULUS = 1032193

# Global counters for bandwidth
TOTAL_BYTES_SENT = 0
TOTAL_BYTES_RECEIVED = 0
BW_LOCK = threading.Lock()  # lock to protect counters

def create_ckks_context():
    context = ts.context(
        scheme=ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.global_scale = 2**40
    context.generate_galois_keys()
    return context

def split_into_shares(secret_vector):
    s2 = np.random.rand(*secret_vector.shape)
    s1 = secret_vector - s2
    return s1, s2

def send_large_data(sock, data_bytes):
    """Send data with size prefix, track total bytes sent."""
    global TOTAL_BYTES_SENT
    size = len(data_bytes)
    size_prefix = size.to_bytes(4, 'big')
    # increment counters
    with BW_LOCK:
        TOTAL_BYTES_SENT += len(size_prefix) + size
    # send
    sock.sendall(size_prefix)
    sock.sendall(data_bytes)

def receive_large_data(sock):
    """Receive data with size prefix, track total bytes read."""
    global TOTAL_BYTES_RECEIVED
    size_prefix = sock.recv(4)
    if len(size_prefix) < 4:
        raise ConnectionError("Connection closed prematurely")
    size = int.from_bytes(size_prefix, 'big')
    with BW_LOCK:
        TOTAL_BYTES_RECEIVED += 4 + size

    data = b""
    while len(data) < size:
        chunk = sock.recv(min(131072, size - len(data)))
        if not chunk:
            raise ConnectionError("Connection closed prematurely")
        data += chunk
    return data

def send_and_receive_server(
    host, port,
    biometric_id,
    ctx_bytes,
    enc_share_bytes,
    context,
    result_dict,
    result_key
):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    send_large_data(sock, biometric_id.encode())
    send_large_data(sock, ctx_bytes)
    send_large_data(sock, enc_share_bytes)

    partial_diff_bytes = receive_large_data(sock)
    sock.close()

    result_dict[result_key] = ts.ckks_vector_from(context, partial_diff_bytes)

# Main Client Code
overall_start = time.perf_counter()

context_creation_start = time.perf_counter()
context = create_ckks_context()
context_creation_end = time.perf_counter()

ctx_bytes = context.serialize()

probe = np.load("IrisFingerprintDatabases/FingerprintDatabase/3567/3567d11.npy")
p1, p2 = split_into_shares(probe)

encrypt_start = time.perf_counter()
Enc_p1 = ts.ckks_vector(context, p1.tolist())
Enc_p2 = ts.ckks_vector(context, p2.tolist())
encrypt_end = time.perf_counter()
encrypt_time = encrypt_end - encrypt_start

biometric_id = "3567"
ctx_size = len(ctx_bytes)
enc_p1_bytes = Enc_p1.serialize()
enc_p2_bytes = Enc_p2.serialize()
enc_p1_size = len(enc_p1_bytes)
enc_p2_size = len(enc_p2_bytes)

results = {}

parallel_start = time.perf_counter()

t1 = threading.Thread(
    target=send_and_receive_server,
    args=(
        "127.0.0.1", 65431,
        biometric_id, ctx_bytes, enc_p1_bytes,
        context, results, "res1"
    )
)
t2 = threading.Thread(
    target=send_and_receive_server,
    args=(
        "127.0.0.1", 65432,
        biometric_id, ctx_bytes, enc_p2_bytes,
        context, results, "res2"
    )
)

t1.start()
t2.start()
t1.join()
t2.join()

parallel_end = time.perf_counter()

enc_res1 = results["res1"]
enc_res2 = results["res2"]

combine_start = time.perf_counter()
enc_total_diff = enc_res1 + enc_res2
enc_sq_diff = enc_total_diff * enc_total_diff
enc_sq_dist = enc_sq_diff.sum()
dec_sq_dist = enc_sq_dist.decrypt()[0] % PLAIN_MODULUS
dist = np.sqrt(dec_sq_dist)
combine_end = time.perf_counter()
overall_end = time.perf_counter()

print(f"Euclidean Distance: {dist}")

print("\n==== BENCHMARK RESULTS ====")

print("\n-- Times --")
print(f"Context creation time:    {context_creation_end - context_creation_start:.6f} s")
print(f"Encryption time (p1,p2):  {encrypt_time:.6f} s")
print(f"Server round-trip time:   {(parallel_end - parallel_start):.6f} s")
print(f"Final combine & decrypt:  {(combine_end - combine_start):.6f} s")
print(f"Total client time:        {(overall_end - overall_start):.6f} s")

print("\n-- Data Sizes (bytes) --")
print(f"Context size:             {ctx_size}")
print(f"Encrypted share 1 size:   {enc_p1_size}")
print(f"Encrypted share 2 size:   {enc_p2_size}")

print("\n-- Bandwidth (Bytes) --")
print(f"Total bytes sent:         {TOTAL_BYTES_SENT}")
print(f"Total bytes received:     {TOTAL_BYTES_RECEIVED}")
print(f"Sum (sent+received):      {TOTAL_BYTES_SENT + TOTAL_BYTES_RECEIVED}")