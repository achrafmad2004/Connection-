import socket
import threading
import time

# === CONFIG ===
LOCAL_PORT = 8788
RELAY_HOST = "centerbeam.proxy.rlwy.net"
RELAY_PORT = 12082
RECONNECT_DELAY = 2  # Delay before retrying relay connection

# === Forward data ===
def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                print(f"[~] {label} closed connection.")
                break
            print(f"[{label}] {data!r}")
            dst.sendall(data)
    except Exception as e:
        print(f"[X] Forwarding error ({label}): {e}")
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

# === Handle Balatro connection ===
def handle_client(client_sock, addr):
    print(f"[+] Balatro connected from {addr}")

    while True:
        try:
            print(f"[~] Connecting to relay at {RELAY_HOST}:{RELAY_PORT}...")
            relay_sock = socket.create_connection((RELAY_HOST, RELAY_PORT))
            print("[✓] Connected to relay!")

            # Start bidirectional forwarding
            t1 = threading.Thread(target=forward, args=(client_sock, relay_sock, "Balatro → Relay"))
            t2 = threading.Thread(target=forward, args=(relay_sock, client_sock, "Relay → Balatro"))
            t1.start()
            t2.start()

            # Wait for either direction to close
            t1.join()
            t2.join()

            print("[~] Disconnected from relay. Retrying soon...")
            time.sleep(RECONNECT_DELAY)

        except Exception as e:
            print(f"[X] Failed to connect to relay: {e}")
            time.sleep(RECONNECT_DELAY)

# === Start local proxy server ===
def start_proxy():
    print(f"[=] Proxy listening on 127.0.0.1:{LOCAL_PORT}")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", LOCAL_PORT))
    listener.listen(5)

    while True:
        try:
            client_sock, addr = listener.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr)).start()
        except Exception as e:
            print(f"[X] Accept error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_proxy()
