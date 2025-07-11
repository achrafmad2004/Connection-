import socket
import threading
import time

# === CONFIG ===
BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788
LISTEN_PORT = 18958

# === GLOBAL STATE ===
client_conn = None
client_lock = threading.Lock()

def set_keepalive(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:
        sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))  # Windows only
    except AttributeError:
        pass

def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                print(f"[!] {label} disconnected.")
                break
            dst.sendall(data)
    except Exception as e:
        print(f"[X] Forwarding error ({label}): {e}")
    finally:
        try: src.shutdown(socket.SHUT_RDWR); src.close()
        except: pass
        try: dst.shutdown(socket.SHUT_RDWR); dst.close()
        except: pass
        with client_lock:
            global client_conn
            client_conn = None

def wait_for_client(listener_sock):
    global client_conn
    while True:
        conn, addr = listener_sock.accept()
        with client_lock:
            if client_conn:
                print(f"[!] Replacing old client connection from {addr}")
                try: client_conn.shutdown(socket.SHUT_RDWR); client_conn.close()
                except: pass
            client_conn = conn
        print(f"[+] Proxy client connected from {addr}")
        # Start forwarding as soon as a new client connects
        threading.Thread(target=forward, args=(client_conn, balatro_sock, "client→server"), daemon=True).start()
        threading.Thread(target=forward, args=(balatro_sock, client_conn, "server→client"), daemon=True).start()

def start_relay():
    global balatro_sock

    # === Step 1: Connect to Balatro server and keep it open
    while True:
        try:
            print(f"[~] Connecting to Balatro server at {BALATRO_HOST}:{BALATRO_PORT}...")
            balatro_sock = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
            set_keepalive(balatro_sock)
            print("[✓] Connected to Balatro server.")
            break
        except Exception as e:
            print(f"[X] Balatro connection failed: {e}, retrying in 5s...")
            time.sleep(5)

    # === Step 2: Start listener for local proxy
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", LISTEN_PORT))
    listener.listen(1)
    print(f"[✓] Relay ready. Listening on port {LISTEN_PORT} for proxy client...")

    # === Step 3: Accept client and forward
    wait_for_client(listener)

if __name__ == "__main__":
    start_relay()
