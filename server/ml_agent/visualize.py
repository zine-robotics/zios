import numpy as np
import cv2

def visualize_frame(cv_frame_data, processed_frame, rays, image, agent_action):
    img = image.copy()  # Work on the provided image

    # Draw walls (polygon)
    if 'wall_coords' in cv_frame_data and cv_frame_data['wall_coords'].size > 0:
        walls = np.array(cv_frame_data['wall_coords'], np.int32)
        cv2.polylines(img, [walls], isClosed=True, color=(255, 0, 0), thickness=2)

    # Draw goal area (filled polygon)
    if 'goal_coords' in cv_frame_data and cv_frame_data['goal_coords'].size > 0:
        goal = np.array(cv_frame_data['goal_coords'], np.int32)
        cv2.fillPoly(img, [goal], color=(0, 255, 0))  # Green

    # Draw ball (circle)
    if 'ball_coords' in cv_frame_data and len(cv_frame_data['ball_coords']) == 2:
        bx, by = cv_frame_data['ball_coords']
        cv2.circle(img, (int(bx), int(by)), 5, (0, 0, 255), -1)  # Red

    # Draw bot (rotated triangle)
    if 'bot_pos' in cv_frame_data and 'bot_dir' in cv_frame_data:
        bot_x, bot_y = cv_frame_data['bot_pos']
        bot_dir = np.radians(cv_frame_data['bot_dir'])
        size = 15  # Bot size

        # Calculate triangle vertices
        front = (bot_x + size * np.cos(bot_dir), bot_y + size * np.sin(bot_dir))
        left = (bot_x + size / 2 * np.cos(bot_dir + np.pi / 2), bot_y + size / 2 * np.sin(bot_dir + np.pi / 2))
        right = (bot_x + size / 2 * np.cos(bot_dir - np.pi / 2), bot_y + size / 2 * np.sin(bot_dir - np.pi / 2))

        triangle = np.array([(int(front[0]), int(front[1])),
                             (int(left[0]), int(left[1])),
                             (int(right[0]), int(right[1]))], np.int32)
        cv2.fillPoly(img, [triangle], color=(0, 255, 0))  # Green bot

        # Draw action arrow
        arrow_length = 30
        arrow_thickness = 2
        arrow_color = (0, 165, 255)  # Orange

        # Action movement dictionary
        action_labels = {
            1: "Move Forward",
            2: "Move Backward",
            3: "Rotate Right",
            4: "Rotate Left",
            5: "Dir Left",
            6: "Dir Right"
        }
        
        action_text = action_labels.get(agent_action, "No Movement")  # Default if unknown action

        if agent_action == 1:  # Move forward
            arrow_end = (bot_x + arrow_length * np.cos(bot_dir), bot_y + arrow_length * np.sin(bot_dir))
        elif agent_action == 2:  # Move backward
            arrow_end = (bot_x - arrow_length * np.cos(bot_dir), bot_y - arrow_length * np.sin(bot_dir))
        elif agent_action == 3:  # Rotate left
            arrow_color = (255, 255, 0)  # Yellow
            arrow_end = (bot_x + arrow_length * np.cos(bot_dir + np.pi / 4), bot_y + arrow_length * np.sin(bot_dir + np.pi / 4))
        elif agent_action == 4:  # Rotate right
            arrow_color = (255, 255, 0)  # Yellow
            arrow_end = (bot_x + arrow_length * np.cos(bot_dir - np.pi / 4), bot_y + arrow_length * np.sin(bot_dir - np.pi / 4))
        elif agent_action == 5:  # Strafe left
            arrow_color = (255, 0, 255)  # Purple
            arrow_end = (bot_x - arrow_length * np.cos(bot_dir + np.pi / 2), bot_y - arrow_length * np.sin(bot_dir + np.pi / 2))
        elif agent_action == 6:  # Strafe right
            arrow_color = (255, 0, 255)  # Purple
            arrow_end = (bot_x + arrow_length * np.cos(bot_dir - np.pi / 2), bot_y + arrow_length * np.sin(bot_dir - np.pi / 2))
        else:
            arrow_end = (bot_x, bot_y)  # No movement

        cv2.arrowedLine(img, (int(bot_x), int(bot_y)), (int(arrow_end[0]), int(arrow_end[1])), arrow_color, arrow_thickness, tipLength=0.3)

        # Draw action text in the top-right corner
        text_position = (img.shape[1] - 200, 30)  # Top-right corner
        cv2.putText(img, f"Action: {action_text}", text_position, cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, (0, 0, 200), 2, cv2.LINE_AA)  # White text with black outline

        # Draw Rays
        for idx, ray in enumerate(rays):
            start = ray.coords[0]
            end = ray.coords[1]
            hit_info = processed_frame[idx]
            hit_tags = hit_info[:3]
            hit_fraction = hit_info[3]

            tag_hit = np.argmax(hit_tags)
            colors = [
                (0, 0, 255),  # Ball (red)
                (0, 255, 0),  # Goal (green)
                (255, 0, 0)   # Wall (blue)
            ]

            # Compute hit point
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            hit_x = start[0] + dx * hit_fraction
            hit_y = start[1] + dy * hit_fraction

            # Draw the ray up to the hit point
            cv2.line(img, (int(start[0]), int(start[1])), (int(hit_x), int(hit_y)), (0, 255, 0), 1)

            # Draw cross at hit point
            if not hit_info[4]:  # If an object was hit
                cv2.drawMarker(img, (int(hit_x), int(hit_y)), colors[tag_hit], markerType=cv2.MARKER_CROSS, thickness=2)

    # Show the image
    cv2.imshow('Observation Frame', img)
    cv2.waitKey(1)
    return img
