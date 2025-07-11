import socket
import threading
import time

# === CONFIGURATION ===
BALATRO_SERVER_HOST = "161.35.252.15"
BALATRO_SERVER_PORT = 8788
RELAY_LISTEN_PORT = 20001  # This stays 20001, Railway TCP proxy will point here

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

def forward(src, dst, tag):
    try:
        buffer = b""
        while True:
            data = src.recv(4096)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                print(f"[{tag}] {line}")
                dst.sendall(line + b"\n")
    except Exception as e:
        print(f"[X] Relay error ({tag}): {e}")
    finally:
        try:
            src.shutdown(socket.SHUT_RD)
        except:
            pass
        try:
            dst.shutdown(socket.SHUT_WR)
        except:
            pass

def handle_connection(balatro_sock, relay_sock):
    threading.Thread(target=forward, args=(relay_sock, balatro_sock, "Client → Server"), daemon=True).start()
    threading.Thread(target=forward, args=(balatro_sock, relay_sock, "Server → Client"), daemon=True).start()

def main():
    print("[boot] Cloud Relay Bot starting...")
    try:
        # Connect to the real Balatro server
        print(f"[*] Connecting to Balatro server at {BALATRO_SERVER_HOST}:{BALATRO_SERVER_PORT}...")
        balatro_sock = socket.create_connection((BALATRO_SERVER_HOST, BALATRO_SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        # Authentication handshake
        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        print("[~] Sending authentication handshake...")
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        balatro_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent handshake.")

        # Start keepAlive
        threading.Thread(target=send_keep_alive_loop, args=(balatro_sock,), daemon=True).start()

        # Listen for local proxy connection from Railway
        print(f"[~] Waiting for proxy client on port {RELAY_LISTEN_PORT}...")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("0.0.0.0", RELAY_LISTEN_PORT))  # Ensure public binding in Railway
        listener.listen(1)
        relay_sock, addr = listener.accept()
        print(f"[+] Proxy connected from {addr}")
        print("[✓] Relay session established and running.")

        handle_connection(balatro_sock, relay_sock)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

if __name__ == "__main__":
    main()
