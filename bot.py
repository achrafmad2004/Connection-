import socket
import time
import threading

# === CONFIGURATION ===
HOST = "balatro.virtualized.dev"
PORT = 8788

USERNAME = "Achraf~1"
VERSION = "0.2.10-MULTIPLAYER"
MOD_HASH = (
    "theOrder=true;"
    "unlocked=true;"
    "encryptID=12395116800.263;"
    "serversideConnectionID=423bca98;"
    "FantomsPreview-2.3.0;"
    "Multiplayer-0.2.10;"
    "Saturn-0.2.2-E-ALPHA;"
    "TheOrder-MultiplayerIntegration"
)

# === LISTEN TO SERVER AND RESPOND ===
def listen_and_respond(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[!] Server closed the connection.")
                break

            lines = data.decode().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                print(f"[←] Server: {line.strip()}")

                if "action:keepAlive" in line:
                    sock.sendall(b"action:keepAliveAck\n")
                    print("[→] Sent: action:keepAliveAck")
    except Exception as e:
        print(f"[!] Listener error: {e}")

# === MAIN BOT ===
def run_bot():
    while True:
        try:
            print(f"[+] Connecting to {HOST}:{PORT}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((HOST, PORT))
            print("[✓] Connected")

            # Start listening thread
            threading.Thread(target=listen_and_respond, args=(s,), daemon=True).start()

            # Handshake
            s.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
            time.sleep(0.1)
            s.sendall(f"action:version,version:{VERSION}\n".encode())
            time.sleep(0.1)
            s.sendall(f"action:username,username:{USERNAME},modHash:{MOD_HASH}\n".encode())
            time.sleep(0.1)
            print("[✓] Handshake complete")

            # Optional: Still send your own keepAlive for safety
            while True:
                s.sendall(b"action:keepAlive\n")
                print("→ keepAlive sent")
                time.sleep(1)

        except Exception as e:
            print(f"[!] Connection error: {e}")
        finally:
            try:
                s.close()
            except:
                pass
            print("[*] Reconnecting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
