import asyncio
import websockets
import base64
import json
import cv2

class WebSocketServer:
    def __init__(self, manager, host="0.0.0.0", port=8081):
        self.host = host
        self.port = port
        self.clients = {}
        self.manager = manager
        self.loop = asyncio.new_event_loop()
        self.running = False  # To track server status

    async def handle_client(self, websocket):
        """Handles incoming WebSocket connections."""
        try:
            async for message in websocket:
                data = json.loads(message)
                player_id = data.get("player_id")

                if player_id and player_id not in self.clients:
                    self.clients[player_id] = websocket  # Store player_id and websocket mapping
                    print(f"Player {player_id} connected.")

                self.manager.process_player_data(data)

        except websockets.exceptions.ConnectionClosed:
            print("WebSocket client disconnected.")
        finally:
            # Remove disconnected player
            for pid, ws in list(self.clients.items()):
                if ws == websocket:
                    del self.clients[pid]
                    print(f"Player {pid} removed from client list.")
                    break

    async def send_to_player(self, player_id, data):
        """Sends data to a specific player."""
        websocket = self.clients.get(player_id)
        if websocket:
            message = json.dumps(data)
            await websocket.send(message)

    async def broadcast(self, data):
        """Sends data to all WebSocket clients."""
        if self.clients:
           # print("Sent frame")
            message = json.dumps(data)
            await asyncio.gather(*(ws.send(message) for ws in self.clients.values()))
        return True



    def send_frame(self, image_data, frame_type):
        """Receives image data and broadcasts it asynchronously."""
        # compressed_data = compress_image(image_data, quality=50)  # Compress image
        ret, jpg_buffer = cv2.imencode('.jpg', image_data)
        encoded_image = base64.b64encode(jpg_buffer).decode("utf-8")
        
        #print(f"Encoded Image Length: {len(encoded_image)}")
        image_message = json.dumps({"type": frame_type, "data": encoded_image})

        # Ensure the coroutine runs in the existing event loop
        if self.running:
            asyncio.run_coroutine_threadsafe(self.broadcast(image_message), self.loop)

    async def start(self):
        """Starts the WebSocket server."""
        self.running = True
        async with websockets.serve(self.handle_client, self.host, self.port,max_size=50**7):
            print(f"WebSocket Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Keeps the server running indefinitely

    def run(self):
        """Runs the WebSocket server inside a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start())

    def stop(self):
        """Stops the WebSocket server."""
        self.running = False
        for ws in self.clients.values():
            asyncio.run_coroutine_threadsafe(ws.close(), self.loop)
        self.loop.stop()
        print("WebSocket Server stopped.")
