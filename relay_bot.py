import socket
import threading
import time

SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001

USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

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

def send_keep_alive_loop(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

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
            src.close()
            dst.close()

    threading.Thread(target=forward, args=(client_sock, server_sock, "Client → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Client")).start()

def main():
    print("[boot] Relay bot starting up...")
    try:
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

        threading.Thread(target=send_keep_alive_loop, args=(s,), daemon=True).start()

        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay_sock.bind(("0.0.0.0", RELAY_PORT))  # CRUCIAL for Railway
        relay_sock.listen(1)

        print(f"[~] Waiting for Balatro to connect on port {RELAY_PORT}...")
        client_sock, addr = relay_sock.accept()
        print(f"[+] Proxy connected from {addr}")
        print("[✓] Relay is running and keeping session alive.")
        relay_handler(client_sock, s)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
