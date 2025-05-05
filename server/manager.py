from enum import Enum
import threading
import random
import math
import cv2
import time
import numpy as np
import asyncio
import os

from socket_server import SocketInterface
from serial_interface import SerialInterface
from camera.computer_vision import ComputerVisionManager
from ml_agent.agent_interface import AgentInterface
from websocket_server import WebSocketServer

player_ids = ["3",3,1,"1",2,"2"]
single_model_path= "server/ml_agent/models/PushBlock.onnx"
collab_model_path = "server/ml_agent/models/WallNigga.onnx"

MAX_VELOCITY = 10
MIN_VELOCITY = -10

class Mobility(Enum):
    STATIC = 1
    DYNAMIC = 2

class EntityType(Enum):
    BOUNDARY = "boundary"
    PLAYER = "player"
    OBJECT = "object"
    REGION = "region"

# default_response = [
#     {
#         "id": "boundary",
#         "pos": (0, 0, 0, 0 ,0, 0),
#         "type": EntityType.BOUNDARY,
#         "tag": [],
#         "mobility": Mobility.STATIC,
#         "other": {
#             "boundary_points": [(0, 0), (0, 0), (0, 0), (0, 0)],
#         },
#     },
#     {
#         "id": "player1",
#         "pos": (0, 0, 0, 0 ,0, 0),
#         "type": EntityType.PLAYER,
#         "tag": [],
#         "mobility": Mobility.DYNAMIC,
#         "other": {}
#     },
#     {
#         "id": "ball",
#         "pos": (5, 5, 0, 0 ,0, 0),
#         "type": EntityType.OBSTACLE,
#         "tag": [],
#         "mobility": Mobility.DYNAMIC,
#         "other": {}
#     },
#     {
#         "id": "blue_goal",
#         "pos": (0, 0, 0, 0 ,0, 0),
#         "type": EntityType.REGION,
#         "tag": [],
#         "mobility": Mobility.STATIC,
#         "other": {
#             "polygon": [(20, 20), (0, 0)]
#         }
#     },
#     {
#         "id": "red_goal",
#         "pos": (0, 0, 0, 0 ,0, 0),
#         "type": EntityType.REGION,
#         "tag": [],
#         "mobility": Mobility.STATIC,
#         "other": {
#             "polygon": [(-20, -20), (0, 0)]
#         }
#     }
# ]

# Revised Sample Data (Bot faces east toward the goal)
default_frame_data = {
    'goal_coords': [(-10, 0), (-10, 0), (0, 0), (0, -10)],  # Goal in front of the bot
    'wall_coords': [(-10, -10), (-10, 110), (110, 110), (110, -10)],  # Boundary around the world
    'ball_coords': (45, 20),  # Ball to the right of the bot
    'bot_pos': (40, 20),
    'bot_dir': 0  # Facing east (toward the goal)
}

class Player:
    def __init__(self, id: str):
        self.id = id
        self.pos = (0, 0, 0, 0, 0, 0)
        self.boost_available = False
        self.team: Team = None

    def get_json(self):
        return {
            "id": self.id,
            "pos": self.pos,
            "boost_available": self.boost_available
        }

class Team:
    def __init__(self, team_id, goal_tag, players: list[Player]):
        self.team_id = team_id
        self.players = players
        self.goal_tag = goal_tag

        for player in players:
            player.team = self


class Manager:
    def __init__(self):
        self.running = True
        self.player_datas = {pid: Player(pid) for pid in player_ids}
        self.teams = [
            Team("red", "green_goal", [self.player_datas[3]]),
        ]

        camera_config = os.path.join(os.path.dirname(__file__), "camera/config/config3.json")

        self.socket_interface = SocketInterface(self)
        self.serial_interface = SerialInterface(self)
        self.camera_interface = ComputerVisionManager(self, camera_config,width=700,height=470)
        self.aget_interface =  AgentInterface(self,collab_model_path)
        self.webscoket_interface = WebSocketServer(self)
        self.frame_const = 3
        self.frame_rate = 1

    def validate_response(self, response: dict):
        player_id = response.get("player_id")
        velocity = response.get("velocity", (0, 0))
        boost = response.get("actions", {}).get("boost", False)

        if not player_id or player_id not in player_ids:
            print(f"Invalid player ID: {player_id}")
            return None
        
        player = self.player_datas[player_id]
        boost = boost #and player.boost_available
        if boost:
            player.boost_available = False

        v, w = velocity
        v = max(min(-v * 10, MAX_VELOCITY), MIN_VELOCITY)
        w = max(min(-w * 10, MAX_VELOCITY), MIN_VELOCITY)

        v = v * 1.5 if boost else v
        return {"player_id": player_id, "v": int(v), "w": int(w)}

    def process_player_data(self, data):
        player_id = data.get("player_id")
       
        if "error" in data:
            return print(f"Error received from player: {data['error']}")

        serial_data = self.validate_response(data)
        if serial_data:
            self.serial_interface.send_data(serial_data)
        print(f"Player {player_id} sent data: {data}")

    def process_serial_data(self, data):
        print(f"Serial dude sent: {data}")
        player_id = data.get("id")
        ldr_value = data.get('ldr', 0)

        player = self.player_datas.get(player_id)
        if ldr_value > 500:
            player.boost_available = True

    # def opencv_detection(self):
    #     while self.running:
    #         # response = default_response
    #         self.camera_interface.r
    #         time.sleep(0.1)
    #         # self.game_loop(response)

    

    def process_frame(self, response, image):
        # return
        self.frame_rate -= 1
        
        if self.frame_rate > 0:
            return

        self.frame_rate = self.frame_const
        self.webscoket_interface.send_frame(image, "cvframe1")

        # Initialize storage with default empty values
        data = {
            "box1": [],
            "box2": [],
            "goals": [],
            "wall_coords": [],
            "agents": [],
            # "obstacles": []
        }
        # print(response)
        # Single-pass extraction of required data
        for obj in response:
            tag, obj_id, pose = obj.get("tag"), obj.get("id"), obj.get("pose", [])

            if tag == "target1":
                data["box1"].append(pose[:2])
            elif tag == "target2":
                data["box2"].append(pose[:2])
            elif tag == "goal":
                # print("goal")
                data["goals"].append(obj.get("options", {}).get("boundary_points", []))
            elif tag == "obstacle":
                data["obstacles"].append(obj.get("options", {}).get("boundary_points", []))
            elif obj_id == "boundary":
                data["wall_coords"] = obj.get("options", {}).get("boundary_points", [])
            elif "bot" in tag:
                data["agents"].append({
                    "bot_pos": pose[:2],
                    "bot_dir": math.degrees(pose[-1]),
                    "bot_id": obj_id
                })

        # Check for missing required fields and print only if empty
         # Check for missing required fields and print only if empty
        empty_fields = {
            key: value for key, value in data.items()
            if isinstance(value, list) and not value  # Handle lists safely
            or isinstance(value, np.ndarray) and value.size == 0  # Handle NumPy arrays safely
        }
        
        if empty_fields:
            print("Missing fields with empty data:")
            for key, value in empty_fields.items():
                print(f"{key}: {value}")
            # return

        # Process each bot with the filtered agent list
        for bot in data["agents"]:
            cv_frame_data = {
                "bot_pos": bot["bot_pos"],
                "bot_dir": bot["bot_dir"],
                "bot_id": bot["bot_id"],
                "ball_coords": {"box1": data["box1"], "box2": data["box2"]},
                "agent_coords": [a for a in data["agents"] if a["bot_id"] != bot["bot_id"]],
                "goals": data["goals"],
                "wall_coords": data["wall_coords"],
            }
            # print(cv_frame_data)

            # Send data for further processing
            self.aget_interface.step(cv_frame_data, image)
            
    def run(self):
        detection_thread = threading.Thread(target=self.camera_interface.run)
        detection_thread.start()

        # socket_thread = threading.Thread(target=self.socket_interface.run_server)
        # socket_thread.start()

        websocket_thread = threading.Thread(target=self.webscoket_interface.run)
        websocket_thread.start()

        serial_thread = threading.Thread(target=self.serial_interface.start)
        serial_thread.start()

        # asyncio.run(self.webscoket_interface.start())

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Got Keyboard Interrupt")
        finally:
            self.running = False
            self.webscoket_interface.stop()
            detection_thread.join(1)
            websocket_thread.join(1)
            serial_thread.join(1)
            # websocket_thread.stop

    
if __name__ == "__main__":
    manager = Manager()
    manager.run()