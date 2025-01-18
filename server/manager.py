from enum import Enum
import threading
import time

from socket_server import SocketInterface
from serial_interface import SerialInterface

player_ids = ["player1", "player2", "player3", "player4"]

MAX_VELOCITY = 10
MIN_VELOCITY = -10

class Mobility(Enum):
    STATIC = 1
    DYNAMIC = 2

class EntityType(Enum):
    PLAYER = 1
    BOUNDARY = 2
    OBSTACLE = 3
    REGION = 4

default_response = [
    {
        "id": "boundary",
        "pos": (0, 0, 0, 0 ,0, 0),
        "type": EntityType.BOUNDARY,
        "tag": [],
        "mobility": Mobility.STATIC,
        "other": {
            "boundary_points": [(0, 0), (0, 0), (0, 0), (0, 0)],
        },
    },
    {
        "id": "player1",
        "pos": (0, 0, 0, 0 ,0, 0),
        "type": EntityType.PLAYER,
        "tag": [],
        "mobility": Mobility.DYNAMIC,
        "other": {}
    },
    {
        "id": "ball",
        "pos": (5, 5, 0, 0 ,0, 0),
        "type": EntityType.OBSTACLE,
        "tag": [],
        "mobility": Mobility.DYNAMIC,
        "other": {}
    },
    {
        "id": "blue_goal",
        "pos": (0, 0, 0, 0 ,0, 0),
        "type": EntityType.REGION,
        "tag": [],
        "mobility": Mobility.STATIC,
        "other": {
            "polygon": [(20, 20), (0, 0)]
        }
    },
    {
        "id": "red_goal",
        "pos": (0, 0, 0, 0 ,0, 0),
        "type": EntityType.REGION,
        "tag": [],
        "mobility": Mobility.STATIC,
        "other": {
            "polygon": [(-20, -20), (0, 0)]
        }
    }
]


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
            Team("red", "blue_goal", [self.player_datas["player1"], self.player_datas["player2"]]),
            Team("blue", "red_goal", [self.player_datas["player3"], self.player_datas["player4"]])
        ]

        self.socket_interface = SocketInterface(self)
        self.serial_interface = SerialInterface(self)

    def validate_response(self, response: dict):
        player_id = response.get("player_id")
        velocity = response.get("velocity", (0, 0))
        boost = response.get("actions", {}).get("boost", False)

        if not player_id or player_id not in player_ids:
            print(f"Invalid player ID: {player_id}")
            return None
        
        player = self.player_datas[player_id]
        boost = boost and player.boost_available
        if boost:
            player.boost_available = False

        v, w = velocity
        v = max(min(v * 10, MAX_VELOCITY), MIN_VELOCITY)
        w = max(min(w * 10, MAX_VELOCITY), MIN_VELOCITY)

        v = v * 1.5 if boost else v
        return {"player_id": player_id, "v": int(v), "w": int(w)}

    def process_player_data(self, data):
        # player_id = data.get("player_id")
        # print(f"Player {player_id} sent data: {data}")

        serial_data = self.validate_response(data)
        if serial_data:
            self.serial_interface.send_data(serial_data)

    def process_serial_data(self, data):
        print(f"Serial dude sent: {data}")
        player_id = data.get("id")
        ldr_value = data.get('ldr', 0)

        player = self.player_datas.get(player_id)
        if ldr_value > 500:
            player.boost_available = True

    def opencv_detection(self):
        while self.running:
            response = default_response
            time.sleep(0.1)
            self.game_loop(response)

    def game_loop(self, response):
        ball_pos = (0, 0, 0, 0, 0, 0)
        goal_pos = {
            "red_goal": [(0, 0), (0, 0)],
            "blue_goal": [(0, 0), (0, 0)]
        }

        for obj in response:
            if obj["type"] == EntityType.PLAYER:
                player = self.player_datas.get(obj["id"])
                player.pos = obj["pos"]

            elif obj["id"] == "ball":
                ball_pos = obj["pos"]

            elif obj["type"] == EntityType.REGION and 'goal' in obj["id"]:
                goal_pos[obj["id"]] = obj["other"]["polygon"]

        # Send data to clients
        for player in self.player_datas.values():
            team_goal_pos = goal_pos[player.team.goal_tag]
            self.socket_interface.send_to_client(player.id, {
                "player": player.get_json(),
                "target_pos": ball_pos,
                "goal_pos": team_goal_pos
            })

    def run(self):
        detection_thread = threading.Thread(target=self.opencv_detection)
        detection_thread.start()

        socket_thread = threading.Thread(target=self.socket_interface.run_server)
        socket_thread.start()

        serial_thread = threading.Thread(target=self.serial_interface.start)
        serial_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Got Keyboard Interrupt")
            self.running = False
            detection_thread.join()
            socket_thread.join()
            serial_thread.join()

    
if __name__ == "__main__":
    manager = Manager()
    manager.run()