import onnxruntime as ort
import numpy as np
from ml_agent.agent_observation import Observation
from ml_agent.visualize import visualize_frame


class AgentInterface:
    def __init__(self,manager, model_path):
        """
        Initialize the UnityAgent with an ONNX model.

        :param model_path: Path to the ONNX model file.
        """
        self.model_path = model_path
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        print("Model input shape:", self.session.get_inputs()[1].shape)
        self.manager = manager
        self.agent_observation = Observation()

    def preprocess_observation(self, ray_data):
        """
        Preprocess ray perception data to prepare it for model inference.

        :param ray_data: A numpy array of shape (3, 7, 5) for ray perception sensor.
        :return: Flattened and normalized observation for inference.
        """
        # Validate the input shape
        if ray_data.shape != (3, 7, 5):
            raise ValueError("Input ray data must have the shape (3, 7, 5).")

        # Flatten the data and normalize if required (example normalization applied here)
        flat_data = ray_data.flatten()
        

        return flat_data

    def infer_action(self, observation):
        """
        Run inference using the ONNX model to get the agent's action.
        """
        action_masks = np.ones((1, 7), dtype=np.float32)

        # Ensure correct observation format
        observation = np.array(observation, dtype=np.float32)
        observation = np.expand_dims(observation, axis=0)

        inputs = {'obs_0': observation, 'action_masks': action_masks}

        # Run inference
        result = self.session.run(None, inputs)
        
        # Extract discrete action (using index 2)
        discrete_action = int(result[2][0][0])  # Extract value from array

        # print("Discrete Action:", discrete_action)  # Debugging

        return discrete_action  # Return as integer


       
    def action_to_vel(self,action):
        """
        Maps the discrete action from Unity to real-world velocities (v, w).
        
        :param action: Discrete action (0-6)
        :return: Tuple (v, w) where v is linear velocity and w is angular velocity
        """
        v, w = 0, 0  # Default stop
        scale = 10

        if action == 1:  # Move forward
            v = 1
        elif action == 2:  # Move backward
            v = -1
        elif action == 3:  # Rotate right
            w = -1
        elif action == 4:  # Rotate left
            w = 1
        elif action == 5:  # Strafe left (approximate with slight left rotation)
            w = 0.5
        elif action == 6:  # Strafe right (approximate with slight right rotation)
            w = -0.5

        
        return v*scale, w*scale 

    def step(self, cv_frame_data,image):
        """
        Execute one step of the agent's decision-making process.

        :param frame_data: Dictionary containing keys 'goal_coords', 'wall_coords', 'ball_coords', 'bot_pos', and 'bot_dir'.
        :return: Action to be performed by the agent.
        """
        # Create an observation object

        #print(cv_frame_data)
        processed_frame_data,rays = self.agent_observation.addObservation(cv_frame_data)
        # print("added observation")
       
        # print("ray Data",ray_data)
        # print(ray_data)

        # Preprocess the ray data
        # print(self.agent_observation.data)
        observation = self.preprocess_observation(self.agent_observation.data)
        # # print("Processed observation shape:", observation.shape)
        # # Infer the action
        # print(observation)
        action = self.infer_action(observation)
        # print(action)
        target_velocity= self.action_to_vel(action)

        agent_response_data= {
            "player_id": cv_frame_data["bot_id"],
            "velocity": target_velocity,
            "actions":{}
        }
        self.manager.process_player_data(agent_response_data)
       
        print("actions",action,target_velocity)

        processed_frame_img= visualize_frame(cv_frame_data,processed_frame_data,rays,image,action)
        self.manager.webscoket_interface.send_frame(processed_frame_img,"cvframe2")
        #return action

# Example usage:
# agent = UnityAgent("path_to_model.onnx")
# tag_data = {
#     'goal_coords': [(1, 2), (2, 3)],
#     'wall_coords': [(0, 0), (1, 0), (1, 1), (0, 1)],
#     'ball_coords': (2, 2),
#     'bot_pos': (0, 0),
#     'bot_dir': 0  # Facing right
# }
# action = agent.step(tag_data)
# print("Predicted Action:", action)
