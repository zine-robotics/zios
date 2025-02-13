import cv2
import numpy as np
import json
from collections import deque
from camera.color_ranges import COLOR_RANGES
from camera.arena_entity import *
from camera.utils import *
import traceback
from enum import Enum


class ComputerVisionManager:
    def __init__(self, manager, config_path, width=700, height=470):
        # Initialize parameters
        self.width = width
        self.height = height
        self.src_history = deque(maxlen=20)  # Fixed-size queue for smoothing boundary points
        self.response_model = {}  # Public response model to store results

        # Load entities from JSON configuration
        self.created_entities = create_entities_from_json(config_path)
        self.aruco_entities = [
            entity for entity in self.created_entities if entity.aruco_id is not None
        ]
        self.color_entities = [
            entity for entity in self.created_entities if entity.color is not None
        ]

        # Camera object
        self.cam = None
        self.manager = manager

    def init_camera(self):
        """Initialize the camera settings."""
        self.cam = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def process_frame(self, image):
        """Process a single frame and update the response model."""
        # Detect features
        shape_color_points = detect_shapes_and_colors(image)
        aruco_marker_points = detect_aruco_markers(image)

        # Get positions of entities
        entity_pos = []
        entity_pos.extend(assign_positions_to_color_entities(self.color_entities, shape_color_points))
        entity_pos.extend(assign_positions_to_aruco_entities(self.aruco_entities, aruco_marker_points))

        # Categorize entities
        entity_data = categorize_entity(entity_pos)

        # Check if we have enough boundary points
        if len(entity_data[EntityType.BOUNDARY]) >= 4:
            # Extract and order boundary points
            boundary_points = np.float32(entity_data[EntityType.BOUNDARY])
            src_pts = order_points(boundary_points)
        else:
            # Fallback to default boundary points
            src_pts = order_points(np.float32([[0, 0], [self.width, 0], [self.width, self.height], [0, self.height]]))

        # Smoothing with a fixed-size queue
        self.src_history.append(src_pts)
        smoothed_src_pts = np.mean(self.src_history, axis=0)

        # Define destination points
        dst_pts = order_points(np.float32([[0, 0], [self.width, 0], [self.width, self.height], [0, self.height]]))

        # Calculate the perspective transform matrix
        M = cv2.getPerspectiveTransform(smoothed_src_pts, dst_pts)

        # Update the response model
        transformed_data = process_entity_data(entity_data, M)
        self.response_model = map_to_response(transformed_data)

        return M

    def run(self):
        """Run the vision pipeline in a loop."""
        if not self.cam:
            self.init_camera()
            print("Camera initialized.")

        while self.manager.running:
            # print("Processing frame...")
            ret, frame = self.cam.read()
            if not ret:
                break
            # frame = cv2.imread("server/camera/test_images/rlAgent.png")

            try:
                # Process the frame and get the transformation matrix
                current_M = self.process_frame(frame)
             
                
                #Apply the transformation and display the result
                if current_M is not None:
                    warped_img = cv2.warpPerspective(frame, current_M, (self.width, self.height))
                    warped_img = draw_circles(warped_img, self.response_model)
                    
                    self.manager.process_frame(self.response_model, warped_img)
                    cv2.imshow("Wrapped Frame", warped_img)
                else:
                    cv2.imshow("Wrapped Frame", frame)

            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()  # Prints the full tracebac
                

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) == ord("q"):
                break

        self.cam.release()
        cv2.destroyAllWindows()

    def get_response_model(self):
        """Get the latest response model."""
        return self.response_model


# Example usage
if __name__ == "__main__":
    config_path = "./config/config2.json"  # Path to your JSON file
    cv_manager = ComputerVisionManager(manager=None, config_path=config_path)
    cv_manager.run()
