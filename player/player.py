import socket
import json
import time
import threading
from pynput import keyboard  # Use pynput for keyboard handling
from player_logic import player_logic

current_player = "player1"
play_logic_flag = False

# Sample server response for testing
dummyserverResponse = {
    "player": {"id": current_player, "pos": (0, 0, 0, 0, 0, 0), "boost": True},
    "target_pos": (0, 0, 0, 0, 0, 0),
    "goal_pos": [(0, 0), (0, 0), (0, 0)],
}

class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.velocity = (0, 0)  # (linear_velocity, angular_velocity)
        self.actions = {"boost": False}
        self.linear_velocity = 0.0  # Forward/backward speed
        self.angular_velocity = 0.0  # Rotation speed

    def update_velocity_based_on_keys(self):
        self.velocity = (self.linear_velocity , self.angular_velocity)

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "velocity": self.velocity,
            "actions": self.actions
        }

    def __str__(self):
        return str(self.to_dict())

class PlayerDataClient:
    def __init__(self, server_host='127.0.0.1', server_port=65432):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_response_data = {   
            "player": {"id": "player1", "pos": (0, 0, 0, 0, 0, 0), "boost": False},
            "target_pos": (0, 0, 0, 0, 0, 0),
            "goal_pos": [(0, 0), (0, 0), (0, 0)]
        }

    def connect(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
        except ConnectionRefusedError:
            print(f"Failed to connect to server at {self.server_host}:{self.server_port}")

    def send_data(self, data):
        try:
            json_data = json.dumps(data)
            self.client_socket.sendall(json_data.encode('utf-8'))
        except Exception as e:
            print(f"Error sending data: {e}")

    def receive_data(self):
        try:
            while True:
                response = self.client_socket.recv(1024)
                if response:
                    try:
                        self.server_response_data = json.loads(response.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON: {e}")
                else:
                    break
        except Exception as e:
            print(f"Error receiving data: {e}")

    def close(self):
        self.client_socket.close()
        print("Connection closed.")


class KeyListener:
    def __init__(self, player,client):
        self.player = player
        self.client = client

    def on_press(self, key):
        """Handle key press events."""
        try:
            if key.char == "w":  # Stop the listener on ESC key
                self.player.linear_velocity = 1
            elif key.char == "s": 
                self.player.linear_velocity = -1
            elif key.char == "a":
                self.player.angular_velocity = 1
            elif key.char == "d": 
                self.player.angular_velocity = -1
            elif key.char == "b":
                self.player.actions["boost"] = not self.player.actions["boost"]

            self.player.update_velocity_based_on_keys()
            # Send updated player data to the server
            self.client.send_data(self.player.to_dict())  
            self.player.linear_velocity = 0
            self.player.angular_velocity = 0
        except AttributeError:
            pass
        except Exception as e:
            print(f"Error sending data to server: {e}")

    def start_listening(self):
        """Start the keyboard listener."""
        print("Listening for key presses (Use WASD)...")
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()  # Starts listening asynchronously

def playerInterface(player: Player, socket_client: PlayerDataClient):
  
    while True:
        game_data = socket_client.server_response_data  # Fetch game data from socket client
        
        # Call the game logic function to update player state
        player_logic(player, game_data)
        
        # Send updated player data to the server
        socket_client.send_data(player.to_dict())

        # Sleep to control the game loop frequency
        time.sleep(0.1)

def main():
    player = Player(player_id=current_player)
    client = PlayerDataClient()

    # Connect to server
    client.connect()
    client.send_data(player.to_dict())

    # Start listening for key events in a separate thread
   

    # Start receiving server data in a separate thread
    receive_thread = threading.Thread(target=client.receive_data)
    receive_thread.start()

    if(play_logic_flag):
        player_thread = threading.Thread(target=playerInterface, args=(player, client))
        player_thread.start()
    else:
        key_listener = KeyListener(player,client)
        key_thread = threading.Thread(target=key_listener.start_listening)
        key_thread.start()


    try:
        while True:
            time.sleep(0.5)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Shutting down client...")
    finally:
        receive_thread.join()
        if(not play_logic_flag):
            key_thread.join()
        else:
            player_thread.join()
        client.close()
       
       
if __name__ == "__main__":
    main()
