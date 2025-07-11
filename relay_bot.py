import socket
import threading
import time

# === CONFIGURATION ===
SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001

USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

def generate_encrypt_id():
    base = 45385000000
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
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except (BrokenPipeError, ConnectionResetError):
            print("[X] Keep-alive error: Broken pipe. Server likely disconnected.")
            break
        except Exception as e:
            print(f"[X] Unexpected keep-alive error: {e}")
            break

def relay_handler(client_sock, server_sock):
    def forward(src, dst, tag):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    print(f"[~] {tag} closed connection.")
                    break
                print(f"[{tag}] {data}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Relay error ({tag}): {e}")
        finally:
            try: src.shutdown(socket.SHUT_RD)
            except: pass
            try: dst.shutdown(socket.SHUT_WR)
            except: pass
            src.close()
            dst.close()

    threading.Thread(target=forward, args=(client_sock, server_sock, "Client → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Client")).start()

def wait_for_client(server_sock):
    while True:
        print(f"[~] Waiting for proxy client on port {RELAY_PORT}...")
        try:
            client_sock, addr = server_sock.accept()
            print(f"[+] Proxy connected from {addr}")
            relay_handler(client_sock, server_socket)
        except Exception as e:
            print(f"[X] Error accepting client: {e}")

def main():
    global server_socket
    print("[boot] Relay bot starting up...")
    try:
        print(f"[*] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        server_socket = socket.create_connection((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)
        print(f"[i] encryptID = {encrypt_id}")
        print("[~] Sending authentication handshake...")

        server_socket.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        server_socket.sendall(f"action:version,version:{VERSION}\n".encode())
        server_socket.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent handshake.")
        print("[✓] Auth sent.")

        threading.Thread(target=send_keep_alive_loop, args=(server_socket,), daemon=True).start()

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("0.0.0.0", RELAY_PORT))
        listener.listen(5)
        wait_for_client(listener)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
