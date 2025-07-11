import socket
import threading

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788
LISTEN_PORT = 18958

def set_keepalive(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

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
        print(f"[~] {label} forward thread exited.")

def handle_client(conn, addr):
    print(f"[+] Proxy client connected from {addr}")
    try:
        print(f"[~] Connecting to Balatro server for this client...")
        balatro_sock = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
        set_keepalive(balatro_sock)
        print("[✓] Connected to Balatro server.")

        t1 = threading.Thread(target=forward, args=(conn, balatro_sock, "client→server"))
        t2 = threading.Thread(target=forward, args=(balatro_sock, conn, "server→client"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"[X] Failed to connect to Balatro: {e}")
        conn.close()

def wait_for_clients():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", LISTEN_PORT))
    listener.listen(1)
    print(f"[✓] Relay ready. Listening for proxy on port {LISTEN_PORT}...")
    while True:
        conn, addr = listener.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    wait_for_clients()
