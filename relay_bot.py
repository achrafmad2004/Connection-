import socket
import threading

LOCAL_PORT = 8788
RELAY_HOST = "trolley.proxy.rlwy.net"
RELAY_PORT = 18958

def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            print(f"[DATA from {label}] {data!r}")
            dst.sendall(data)
    except Exception as e:
        print(f"[X] Error forwarding {label} traffic: {e}")
    finally:
        src.close()
        dst.close()

def handle_client(client_sock, addr):
    print(f"[+] Proxy connected from {addr}")
    try:
        server_sock = socket.create_connection((RELAY_HOST, RELAY_PORT))
        threading.Thread(target=forward, args=(client_sock, server_sock, "client")).start()
        threading.Thread(target=forward, args=(server_sock, client_sock, "server")).start()
    except Exception as e:
        print(f"[X] Failed to connect to relay: {e}")
        client_sock.close()

def start_proxy():
    print(f"[+] Proxy listening on port {LOCAL_PORT}, forwarding to {RELAY_HOST}:{RELAY_PORT}...")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", LOCAL_PORT))
    listener.listen(5)

    while True:
        try:
            client, addr = listener.accept()
            threading.Thread(target=handle_client, args=(client, addr)).start()
        except Exception as e:
            print(f"[X] Error accepting connection: {e}")

if __name__ == "__main__":
    start_proxy()
