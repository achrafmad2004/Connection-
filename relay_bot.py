import socket
import threading
import time

LOCAL_PORT = 8788
RELAY_HOST = "trolley.proxy.rlwy.net"
RELAY_PORT = 18958

# This runs forever and never closes the relay socket
def forward_forever(src, dst, label):
    while True:
        try:
            data = src.recv(4096)
            if data:
                dst.sendall(data)
        except Exception:
            pass  # Ignore all errors silently

def start_proxy():
    try:
        print(f"[+] Connecting to relay at {RELAY_HOST}:{RELAY_PORT}...")
        relay_sock = socket.create_connection((RELAY_HOST, RELAY_PORT))
        print("[✓] Connected to relay. Waiting for Balatro...")

        while True:
            try:
                listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("127.0.0.1", LOCAL_PORT))
                listener.listen(1)

                client_sock, addr = listener.accept()
                print(f"[✓] Balatro connected from {addr}")

                threading.Thread(target=forward_forever, args=(client_sock, relay_sock, "Balatro→Relay"), daemon=True).start()
                threading.Thread(target=forward_forever, args=(relay_sock, client_sock, "Relay→Balatro"), daemon=True).start()

                # This part doesn't care about disconnections
                # Threads exit silently, and we wait for the next game launch
                time.sleep(1)
                listener.close()

            except Exception:
                time.sleep(1)

    except Exception as e:
        print(f"[X] Fatal: Couldn't connect to relay: {e}")
        time.sleep(3)
        start_proxy()  # retry endlessly

if __name__ == "__main__":
    print(f"[+] Starting Persistent Proxy on port {LOCAL_PORT}")
    start_proxy()
