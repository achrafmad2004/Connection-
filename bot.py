import socket
import time

# --- SETTINGS ---
HOST = "balatro.virtualized.dev"
PORT = 8788

USERNAME = "Achraf~1"
VERSION = "0.2.10-MULTIPLAYER"

# Full modHash captured from your logs
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

# --- BOT START ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect((HOST, PORT))
print("[+] Connected to server")

# Send handshake: username (initial empty hash)
s.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
time.sleep(0.1)

# Send version
s.sendall(f"action:version,version:{VERSION}\n".encode())
time.sleep(0.1)

# Send full identity again
s.sendall(f"action:username,username:{USERNAME},modHash:{MOD_HASH}\n".encode())
time.sleep(0.1)

# Start sending keepAlives
print("[+] Starting keepAlive loop")
try:
    while True:
        s.sendall(b"action:keepAlive\n")
        print("-> keepAlive sent")
        time.sleep(1)
except KeyboardInterrupt:
    print("[-] Bot stopped.")
    s.close()
