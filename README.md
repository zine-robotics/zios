# Player and Server Project

## Overview

This project consists of a player client and a server that communicate to simulate a game environment. The player client can be controlled via keyboard inputs or automated logic, and the server manages the game state and communication between multiple players.

## Project Structure

The project is organized into two main components:

### Player

The player client is implemented in the `player` directory. The main components are:

- `player.py`: Contains the `Player` class, `PlayerDataClient` class for server communication, and `KeyListener` class for handling keyboard inputs.
- `player_logic.py`: Contains the `player_logic` function that processes game state and updates the player's actions and velocity.

#### Running the Player

1. Ensure the server is running.
2. Run the player client:
    ```sh
    python player/player.py
    ```

### Server

The server is implemented in the `server` directory. The main components are:

- `manager.py`: Contains the `Manager` class that handles the game state and communication with players.
- `serial_interface.py`: Contains the `SerialInterface` class for handling serial communication.
- `socket_server.py`: Contains the `SocketInterface` and `SocketClient` classes for handling socket communication with players.

#### Running the Server

1. Run the server:
    ```sh
    python server/manager.py
    ```

## Communication

The player client communicates with the server using socket communication. The server processes the player's data and sends back the game state.

## Dependencies

- Python 3.x
- `pynput` for keyboard handling (install using `pip install pynput`)
- `pyserial` for serial communication (install using `pip install pyserial`)

