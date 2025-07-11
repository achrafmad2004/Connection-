import socket
import threading
import time

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788
RELAY_PORT = 18958  # Port to accept proxy connection

def forward_forever(src, dst, label):
    while True:
        try:
            data = src.recv(4096)
            if data:
                dst.sendall(data)
        except:
            pass  # Ignore all errors and keep going

def start_relay():
    print(f"[+] Connecting to Balatro at {BALATRO_HOST}:{BALATRO_PORT}...")
    try:
        balatro_sock = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
        print("[✓] Connected to Balatro server.")
    except Exception as e:
        print(f"[X] Failed to connect to Balatro: {e}")
        time.sleep(5)
        return

    # Now we open a server socket to accept the proxy
    print(f"[+] Relay waiting for proxy connection on port {RELAY_PORT}...")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", RELAY_PORT))
    listener.listen(1)

    proxy_sock = None

    while True:
        try:
            proxy_sock, addr = listener.accept()
            print(f"[✓] Proxy connected from {addr}")

            threading.Thread(target=forward_forever, args=(proxy_sock, balatro_sock, "Proxy→Balatro"), daemon=True).start()
            threading.Thread(target=forward_forever, args=(balatro_sock, proxy_sock, "Balatro→Proxy"), daemon=True).start()

            # Just wait for this session to die and re-accept next one
            while True:
                time.sleep(60)

        except Exception as e:
            print(f"[!] Error accepting proxy connection: {e}")
            time.sleep(2)

if __name__ == "__main__":
    start_relay()
