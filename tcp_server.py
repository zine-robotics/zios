import socket
import threading

# Server setup
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)

print("✅ Server is listening for ESP32 connections...")

# Handle client connection
def handle_client(client, addr):
    print(f"✅ ESP32 Connected from {addr}")
    try:
        while True:
            data = client.recv(1024)
            if not data:
                print(f"❌ ESP32 {addr} Disconnected")
                # break
            print(f"📩 Received from {addr}: {data.decode('utf-8')}")
            client.sendall(b"ACK")  # Optional acknowledgment
    except Exception as e:
        print(f"❌ Connection Error with {addr}: {e}")
    finally:
        client.close()  # Close connection properly
        print(f"🔌 Connection closed for {addr}")

while True:
    client, addr = server.accept()
    client_thread = threading.Thread(target=handle_client, args=(client, addr))
    client_thread.start()
