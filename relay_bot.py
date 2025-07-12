# relay.py (run this on Railway)

import socket
import threading
import time

SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001

USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

start_time = time.time()

def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    return f"{base + (t % 100000)}.263"

def build_mod_hash(eid):
    return (
        f"theOrder=true;unlocked=true;encryptID={eid};serversideConnectionID=423bca98;"
        f"FantomsPreview=2.3.0;Multiplayer={VERSION};Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;TheOrder-MultiplayerIntegration"
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

def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            print(f"[{label}] {data}")
            dst.sendall(data)
    except Exception as e:
        print(f"[X] Forwarding error ({label}): {e}")
    finally:
        print(f"[~] Closed {label}")
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

def wait_for_proxy(server_sock):
    while True:
        print(f"[~] Listening for proxy on port {RELAY_PORT}...")
        client_sock, addr = server_sock.accept()
        print(f"[✓] Proxy connected from {addr}")
        threading.Thread(target=forward, args=(client_sock, balatro_sock, "Proxy → Server")).start()
        threading.Thread(target=forward, args=(balatro_sock, client_sock, "Server → Proxy")).start()

def main():
    global balatro_sock

    print("[boot] Relay bot starting...")
    try:
        print(f"[*] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        balatro_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        balatro_sock.connect((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        eid = generate_encrypt_id()
        mod_hash = build_mod_hash(eid)

        print(f"[i] encryptID = {eid}")
        print("[→] Sending handshake...")
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        balatro_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[✓] Handshake sent.")

        threading.Thread(target=send_keep_alive_loop, args=(balatro_sock,), daemon=True).start()

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("0.0.0.0", RELAY_PORT))
        server_sock.listen(5)

        wait_for_proxy(server_sock)

    except Exception as e:
        print(f"[X] Relay bot error: {e}")

    finally:
        uptime = time.time() - start_time
        print(f"[!] Relay ran for {uptime:.2f} seconds")

if __name__ == "__main__":
    main()
