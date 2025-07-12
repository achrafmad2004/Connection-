import socket
import threading
import time

# === CONFIG ===
SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# === ID + Hash ===
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

# === Keep Balatro connection alive ===
def send_keep_alive_loop(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

# === Bi-directional forwarding ===
def relay_handler(client_sock, server_sock):
    def forward(src, dst, tag):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                print(f"[{tag}] {data}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Relay error ({tag}): {e}")
        finally:
            try: src.close()
            except: pass
            try: dst.close()
            except: pass
            print(f"[~] Closed {tag}")

    threading.Thread(target=forward, args=(client_sock, server_sock, "Proxy → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Proxy")).start()

# === Main Relay ===
def main():
    print("[boot] Relay bot starting...")
    try:
        print(f"[*] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        print(f"[i] encryptID = {encrypt_id}")
        print("[→] Sending handshake...")
        server_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        server_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        server_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[✓] Handshake sent.")

        threading.Thread(target=send_keep_alive_loop, args=(server_sock,), daemon=True).start()

        # === Start listening for proxy connections ===
        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        relay_sock.bind(("0.0.0.0", RELAY_PORT))
        relay_sock.listen(5)

        print(f"[~] Waiting for proxies on port {RELAY_PORT}...")

        while True:
            try:
                client_sock, addr = relay_sock.accept()
                print(f"[+] Proxy connected from {addr}")
                relay_handler(client_sock, server_sock)
            except Exception as e:
                print(f"[X] Accept error: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
