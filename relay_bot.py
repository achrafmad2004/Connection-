import socket
import threading
import time

# === CONFIGURATION ===
SERVER_HOST = "161.35.252.15"  # Balatro server IP
SERVER_PORT = 8788
RELAY_PORT = 20001
TIMEOUT_SECONDS = 600  # 10 minutes

USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

def generate_encrypt_id():
    base = 41317000000
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
        f"TheOrder-MultiplayerIntegration"
    )

def send_keep_alive_loop(sock):
    while True:
        try:
            msg = "action:keepAliveAck\n"
            sock.sendall(msg.encode())
            print(f"[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

def proxy_handler(client_sock, server_sock):
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
            try: src.shutdown(socket.SHUT_RD)
            except: pass
            try: dst.shutdown(socket.SHUT_WR)
            except: pass

    threading.Thread(target=forward, args=(client_sock, server_sock, "Client → Server"), daemon=True).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Client"), daemon=True).start()


def main():
    print("[boot] Relay bot starting up...")
    try:
        # Connect to Balatro server
        print(f"[*] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)
        print(f"[i] encryptID = {encrypt_id}")
        print("[~] Sending authentication handshake...")

        s.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        s.sendall(f"action:version,version:{VERSION}\n".encode())
        s.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent handshake.")
        print("[✓] Auth sent.")

        threading.Thread(target=send_keep_alive_loop, args=(s,), daemon=True).start()

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("0.0.0.0", RELAY_PORT))
        listener.listen(1)

        print(f"[~] Waiting for Balatro to connect to relay on port {RELAY_PORT}...")

        while True:
            listener.settimeout(TIMEOUT_SECONDS)
            try:
                client_sock, addr = listener.accept()
                print(f"[+] Proxy connected from {addr}")
                proxy_handler(client_sock, s)
            except socket.timeout:
                print("[!] No proxy connected for 10 minutes. Shutting down relay.")
                break

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
