import onnxruntime as ort
import numpy as np
from ml_agent.agent_observation import Observation
from ml_agent.visualize import visualize_frame


class AgentInterface:
    def __init__(self, model_path):
        """
        Initialize the UnityAgent with an ONNX model.

        :param model_path: Path to the ONNX model file.
        """
        self.model_path = model_path
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        print("Model input shape:", self.session.get_inputs()[1].shape)
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

        :param observation: Processed input for the model.
        :return: The action predicted by the model.
        """
        # Create dummy action masks (adjust as needed based on your environment)
        action_masks = np.ones((1, 7), dtype=np.float32)  # Assuming  possible actions

        # Add batch dimension and ensure correct dtype for observation
        observation = np.expand_dims(observation, axis=0).astype(np.float32)
        observation1_np =  np.tile(np.tile(np.array([0,0, 0,1,1]),7),3).flatten()
        observation1 = np.expand_dims(observation1_np, axis=0).astype(np.float32)
        # Prepare inputs for the model
        inputs = {
            'obs_0': observation,  # Main observation data
            'obs_1': observation1,  # If the model requires a secondary observation input
            'action_masks': action_masks  # Mask to restrict invalid actions
        }
        
        # Perform inference
        result = self.session.run([self.output_name], inputs)
        return(result[0])
       

    def step(self, cv_frame_data,image):
        """
        Execute one step of the agent's decision-making process.

        :param frame_data: Dictionary containing keys 'goal_coords', 'wall_coords', 'ball_coords', 'bot_pos', and 'bot_dir'.
        :return: Action to be performed by the agent.
        """
        # Create an observation object

        print(cv_frame_data)
        processed_frame_data,rays = self.agent_observation.addObservation(cv_frame_data)
        # print("added observation")
        visualize_frame(cv_frame_data,processed_frame_data,rays,image)
        # print("ray Data",ray_data)
        # print(ray_data)

        # Preprocess the ray data
        # observation = self.preprocess_observation(self.agent_observation.data)
        # # print("Processed observation shape:", observation.shape)
        # # Infer the action
        # action = self.infer_action(observation)
        # print("actions",action)

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
