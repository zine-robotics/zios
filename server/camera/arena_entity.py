import json
from enum import Enum

# Define EntityType Enum
class EntityType(Enum):
    BOUNDARY = "boundary"
    PLAYER = "player"
    OBJECT = "object"
    REGION = "region"

# Define ArenaEntity class
class ArenaEntity:
    def __init__(self, color, shape, tag, aruco_id, entity_id, entity_type, mobility):
        self.color = color
        self.shape = shape
        self.tag = tag
        self.aruco_id = aruco_id
        self.id = entity_id
        self.entity_type = entity_type  # Entity type using Enum (BOUNDARY, PLAYER, OBJECT, REGION)
        self.mobility = mobility  # Parameter indicating movement capability

    def __repr__(self):
        return (f"ArenaEntity(id={self.id}, aruco_id={self.aruco_id}, entity_type={self.entity_type.name}, "
                f"color={self.color}, shape={self.shape}, tag={self.tag}, mobility={self.mobility})")

# Function to parse the JSON configuration and return a list of ArenaEntity objects
def create_entities_from_json(json_file_path):

    json_config = read_json_from_file(json_file_path)

    entities = []
    entity_id_counter = 1  # Start the entity IDs from 1

    # Mapping of entity_type names to the EntityType enum
    entity_type_mapping = {
        "boundary": EntityType.BOUNDARY,
        "player": EntityType.PLAYER,
        "object": EntityType.OBJECT,
        "region": EntityType.REGION
    }

    # Loop through each entity_type in the JSON config
    for entity_type_key, objects in json_config.items():
        entity_type = entity_type_mapping.get(entity_type_key)  # Convert to EntityType Enum

        # Iterate through the list of objects for the current entity_type
        for obj in objects:
            count = obj.get("count", 1)  # Default count to 1 if not provided
            for _ in range(count):
                # Create an ArenaEntity object for each entity and give it a unique id
                entity = ArenaEntity(
                    entity_id = obj.get("id"),
                    color=obj.get("color"),
                    shape=obj.get("shape"),
                    tag=obj.get("tags"),
                    aruco_id=obj.get("aruco_id"),  # Assuming aruco_id isn't provided in the JSON, can add logic if needed
                    entity_type=entity_type,
                    mobility=obj.get("mobility")
                )
                entities.append(entity)
                entity_id_counter += 1  # Increment the entity ID for each entity

    return entities

# Function to read JSON from file
def read_json_from_file(file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)
    return json_data
