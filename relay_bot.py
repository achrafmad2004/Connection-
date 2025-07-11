import socket
import threading
import time

# === CONFIGURATION ===
SERVER_HOST = "161.35.252.15"  # Balatro server IP
SERVER_PORT = 8788
RELAY_PORT = 20001

USERNAME = "Achraf~1"
VERSION = "0.2.10-MULTIPLAYER"

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
    try:
        while True:
            msg = "action:keepAliveAck\n"
            sock.sendall(msg.encode())
            print(f"[KA] Sent keepAliveAck")
            time.sleep(4)
    except (BrokenPipeError, OSError) as e:
        print(f"[X] Keep-alive loop terminated: {e}")

def relay_handler(client_sock, server_sock):
    def forward(src, dst, tag):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    print(f"[{tag}] Connection closed.")
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

    threading.Thread(target=forward, args=(client_sock, server_sock, "Client → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Client")).start()

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

        # Handshake
        s.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        s.sendall(f"action:version,version:{VERSION}\n".encode())
        s.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent handshake.")
        print("[✓] Auth sent.")

        # Start keep-alive thread BEFORE accepting any client
        threading.Thread(target=send_keep_alive_loop, args=(s,), daemon=True).start()

        # Accept a connection from the proxy (Balatro)
        print(f"[~] Waiting for Balatro to connect on port {RELAY_PORT}...")
        relay = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay.bind(("0.0.0.0", RELAY_PORT))  # Accept external connections if cloud hosted
        relay.listen(1)
        client_sock, addr = relay.accept()
        print(f"[+] Proxy connected from {addr}")
        print("[✓] Relay is running and keeping session alive.")

        relay_handler(client_sock, s)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
