import socket
import threading
import time

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788
LISTEN_PORT = 18958

client_conn = None
client_lock = threading.Lock()
balatro_sock = None
balatro_lock = threading.Lock()

def set_keepalive(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

def connect_to_balatro():
    while True:
        try:
            print(f"[~] Connecting to Balatro server at {BALATRO_HOST}:{BALATRO_PORT}...")
            s = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
            set_keepalive(s)
            print("[✓] Connected to Balatro server.")
            return s
        except Exception as e:
            print(f"[X] Balatro connection failed: {e}")
            time.sleep(5)

def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                print(f"[!] {label} closed.")
                break
            dst.sendall(data)
    except Exception as e:
        print(f"[X] {label} error: {e}")
    finally:
        try: src.shutdown(socket.SHUT_RDWR); src.close()
        except: pass
        try: dst.shutdown(socket.SHUT_RDWR); dst.close()
        except: pass
        with client_lock:
            global client_conn
            client_conn = None
        print(f"[~] {label} forward thread exited.")

def handle_client(conn, addr):
    global client_conn, balatro_sock

    print(f"[+] Proxy client connected from {addr}")
    with client_lock:
        if client_conn:
            try: client_conn.shutdown(socket.SHUT_RDWR); client_conn.close()
            except: pass
        client_conn = conn

    with balatro_lock:
        # Reconnect if the Balatro socket is closed
        if balatro_sock is None:
            balatro_sock = connect_to_balatro()

    try:
        # Test if it's alive
        balatro_sock.send(b"\x00")
    except Exception as e:
        print("[!] Balatro socket broken. Reconnecting...")
        with balatro_lock:
            try: balatro_sock.shutdown(socket.SHUT_RDWR); balatro_sock.close()
            except: pass
            balatro_sock = connect_to_balatro()

    # Start fresh forward threads
    t1 = threading.Thread(target=forward, args=(conn, balatro_sock, "client→server"))
    t2 = threading.Thread(target=forward, args=(balatro_sock, conn, "server→client"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def wait_for_clients():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", LISTEN_PORT))
    listener.listen(1)
    print(f"[✓] Relay ready. Listening for proxy on port {LISTEN_PORT}...")
    while True:
        conn, addr = listener.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def start_relay():
    global balatro_sock
    balatro_sock = connect_to_balatro()
    wait_for_clients()

if __name__ == "__main__":
    start_relay()
