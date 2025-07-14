import socket
import threading
import time

# === CONFIG ===
SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# === Auth helpers ===
def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    simulated_id = base + (t % 100000)
    return f"{simulated_id}.263"

def build_mod_hash(encrypt_id):
    return (
        f"theOrder=true;"
        f"unlocked=true;"
        f"encryptID={encrypt_id};"
        f"serversideConnectionID=423bca98;"
        f"FantomsPreview=2.3.0;"
        f"Multiplayer={VERSION};"
        f"Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;"
        f"TheOrder-MultiplayerIntegration"
    )

# === Keep-alive ===
def keep_alive(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

# === Proxy handler ===
def handle_proxy_connection(client_sock, server_sock):
    def forward(src, dst, label):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                print(f"[{label}] {data!r}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Forwarding error ({label}): {e}")
        finally:
            print(f"[~] Closing {label} direction")

    threading.Thread(target=forward, args=(client_sock, server_sock, "Proxy → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Proxy")).start()

# === Main ===
def main():
    print("[BOOT] Relay starting...")

    # === Step 1: Connect to Balatro server ===
    try:
        print(f"[CONNECT] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        # === Authenticate ===
        server_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        server_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        server_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent authentication handshake.")

        threading.Thread(target=keep_alive, args=(server_sock,), daemon=True).start()

    except Exception as e:
        print(f"[X] Failed to connect to Balatro server: {e}")
        return

    # === Step 2: Accept incoming proxy connections ===
    try:
        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay_sock.bind(("0.0.0.0", RELAY_PORT))
        relay_sock.listen(5)
        print(f"[LISTENING] Relay is ready on port {RELAY_PORT}. Waiting for proxy...")

        while True:
            client_sock, addr = relay_sock.accept()
            print(f"[+] Proxy connected from {addr}")
            threading.Thread(target=handle_proxy_connection, args=(client_sock, server_sock), daemon=True).start()

    except Exception as e:
        print(f"[X] Relay error: {e}")

if __name__ == "__main__":
    main()
