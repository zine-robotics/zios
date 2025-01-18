import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

def player_logic(player: 'Player', game_data: dict):
    """
    Processes the game state and updates the player's actions and velocity.
    :param player: The Player object
    :param game_data: The game data received from the server
    """
    if "player" not in game_data:
        return
    
    player_pos = game_data["player"]["pos"][:2]  # Extract (x, y) position of the player
    ball_pos = game_data["target_pos"][:2]  # Extract (x, y) position of the ball
    goal_pos = game_data["goal_pos"]  # List of bounding points for the goal area

    # Calculate the center of the goal area
    goal_center = (
        sum(point[0] for point in goal_pos) / len(goal_pos),
        sum(point[1] for point in goal_pos) / len(goal_pos),
    )

    # Compute direction to the ball
    direction_to_ball = (ball_pos[0] - player_pos[0], ball_pos[1] - player_pos[1])

    # Compute direction to the center of the goal from the ball
    direction_to_goal = (goal_center[0] - ball_pos[0], goal_center[1] - ball_pos[1])

    # Normalize velocities to get unit vectors
    def normalize(vector):
        magnitude = (vector[0]**2 + vector[1]**2)**0.5
        return (vector[0] / magnitude, vector[1] / magnitude) if magnitude > 0 else (0, 0)

    normalized_velocity = normalize(direction_to_ball)
    angular_velocity = (direction_to_goal[0] - direction_to_ball[0],
                        direction_to_goal[1] - direction_to_ball[1])

    # Calculate left and right velocities (vl, vr)
    linear_velocity = normalized_velocity[0]  # Forward velocity
    angular_velocity = angular_velocity[0]  # Rotational velocity (simplified to the x-component)

    vl = linear_velocity - angular_velocity
    vr = linear_velocity + angular_velocity

    # Decide whether to boost: Boost if the ball is far from the goal center
    boost = abs(direction_to_goal[0]) + abs(direction_to_goal[1]) > 15

    # Update player's state
    player.velocity = (vl, vr)
    player.actions["boost"] = boost