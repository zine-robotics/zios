import socket
import threading
import json

default_socket_response = {
    "player_id": "player1",
    "velocity": (0, 0),
    "actions": {
        "shoot": False,
    }
}

player_socket_map = {}

class SocketClient:
    """Handles communication with a specific client."""
    def __init__(self, manager, client_socket, client_address):
        self.manager = manager
        self.client_socket = client_socket
        self.client_address = client_address
        self.active = True
        self.player_id = ""
        self.cv_frame = None
        
        threading.Thread(target=self.handle_client).start()

    def handle_client(self):
        """Handles communication with the client."""
        try:
            while self.active:
                data = self.client_socket.recv(1024)
                if data:
                    try:
                        json_data = json.loads(data.decode())
                        if not self.player_id:
                            self.player_id = json_data.get("player_id", "")

                            player_socket_map[self.player_id] = self
                            print(f"Client {self.client_address} identified as {self.player_id}")
                        
                        self.manager.process_player_data(json_data)
                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON from {self.client_address}: {data.decode()}")
                        self.send_data({"error": "Invalid JSON format"})
                else:
                    break
        finally:
            self.close_connection()

    def send_data(self, data):
        """Sends data to the client."""
        if self.active:
            json_data = json.dumps(data)
            self.client_socket.sendall(json_data.encode('utf-8'))
    
    def close_connection(self):
        """Closes the connection with the client."""
        self.active = False
        self.client_socket.close()
        print(f"Connection to {self.client_address} closed.")


class SocketInterface:
    """Handles the server socket interface."""
    def __init__(self, manager, host='127.0.0.1', port=65432):
        self.manager = manager
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = []

    def send_to_client(self, client_name, data):
        """Sends data to a specific client."""
        client = player_socket_map.get(client_name)
        if client:
            client.send_data(data)
        else:
            # print(f"Client {client_name} not found.")
            pass

    def broadcast_to_clients(self, data):
        """Sends data to all connected clients."""
        for client in self.clients:
            client.send_data(data)

    def run_server(self):
        """Accepts incoming client connections."""
        print(f"Server started. Listening on {self.host}:{self.port}...")
        try:
            while self.manager.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection from {client_address} established!")

                client_handler = SocketClient(self.manager, client_socket, client_address)
                self.clients.append(client_handler)
        except KeyboardInterrupt:
            print("Server shutting down...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            for client in self.clients:
                client.close_connection()

            self.server_socket.close()
            print("Socket Server closed.")
