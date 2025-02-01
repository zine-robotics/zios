import numpy as np
import cv2

def visualize_frame(cv_frame_data, processed_frame, rays, image):
    img = image.copy()  # Work on the provided image

    # Draw walls (polygon)
    if 'wall_coords' in cv_frame_data and cv_frame_data['wall_coords'].size > 0:
        walls = np.array(cv_frame_data['wall_coords'], np.int32)
        cv2.polylines(img, [walls], isClosed=True, color=(0, 255, 0), thickness=2)

    # Draw goal area (filled polygon)
    if 'goal_coords' in cv_frame_data and cv_frame_data['goal_coords'].size > 0:
        goal = np.array(cv_frame_data['goal_coords'], np.int32)
        cv2.fillPoly(img, [goal], color=(255, 0, 0))  # Red

    # Draw ball (circle)
    if 'ball_coords' in cv_frame_data and len(cv_frame_data['ball_coords']) == 2:
        bx, by = cv_frame_data['ball_coords']
        cv2.circle(img, (int(bx), int(by)), 5, (0, 0, 255), -1)  # Blue

    # Draw bot (rotated triangle)
    if 'bot_pos' in cv_frame_data and 'bot_dir' in cv_frame_data:
        bot_x, bot_y = cv_frame_data['bot_pos']
        bot_dir = np.radians(cv_frame_data['bot_dir'])
        size = 15  # Bot size

        # Calculate triangle vertices
        front = (bot_x + size * np.cos(bot_dir), bot_y + size * np.sin(bot_dir))
        left = (bot_x + size/2 * np.cos(bot_dir + np.pi/2), bot_y + size/2 * np.sin(bot_dir + np.pi/2))
        right = (bot_x + size/2 * np.cos(bot_dir - np.pi/2), bot_y + size/2 * np.sin(bot_dir - np.pi/2))

        triangle = np.array([(int(front[0]), int(front[1])),
                             (int(left[0]), int(left[1])),
                             (int(right[0]), int(right[1]))], np.int32)
        cv2.fillPoly(img, [triangle], color=(0, 255, 0))  # Green

    
        
        for idx, ray in enumerate(rays):
            start = ray.coords[0]
            end = ray.coords[1]
           
            hit_info = processed_frame[idx]
            hit_tags = hit_info[:3]
            hit_fraction = hit_info[3]

            # Only draw if there's a hit
          
            tag_hit = np.argmax(hit_tags)
            colors = [
                (0, 0, 255),  # Ball (red)
                (255, 0, 0),  # Goal (blue)
                (0, 255, 0)   # Wall (green)
            ]
            

            # Compute hit point
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            hit_x = start[0] + dx * hit_fraction
            hit_y = start[1] + dy * hit_fraction

            # Draw the ray up to the hit point
            cv2.line(img, (int(start[0]), int(start[1])), (int(hit_x), int(hit_y)), (0, 255, 0) , 1)

            # Draw cross at hit point
            if(not hit_info[4]):
                print(hit_info)
                print(start,end, hit_x,hit_y)
              
                cv2.drawMarker(img, (int(hit_x), int(hit_y)), (0, 0, 255), markerType=cv2.MARKER_CROSS, thickness=2)

    # Show the image
    cv2.imshow('Observation Frame', img)
    cv2.waitKey(1)
