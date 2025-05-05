import numpy as np
import shapely.geometry as geom
import shapely.ops as ops
import math
import cv2

class MultiAgentObservation:
    def __init__(self):
        self.num_rays = 37
        self.stacked_rays=3
        self.tags_num = 6
        self.obs_shape = (self.stacked_rays, self.num_rays, self.tags_num+2)
        self.data = np.zeros(self.obs_shape, dtype=float)  
        self.ray_length = 480.0  
       

        self.new_frame = np.tile([0, 0, 0,0,0, 1, 1], (9, 1)).astype(float)
        self.rays = []
        self.tag_index_map = {
            "wall": 0,
            "agent": 1,
            "goal": 2,
            "box1":3,
            "box2":4,
            "obstacle":6,
        }
        self.frame_fps = 30
        self.hit_threshold = 50

    def generate_rays(self, origin, angle):
        """Generate rays in an alternating order around the central angle."""
        
        delta_angles = np.linspace(0,360, self.num_rays, endpoint=False)  # Define full 360-degree spread

        # Generate alternating order (0, -1, +1, -2, +2, ..., -n, +n)
        mid_idx = len(delta_angles) // 2
        sorted_indices = np.argsort(np.abs(np.arange(len(delta_angles)) - mid_idx))
        alt_angles = delta_angles[sorted_indices]  # Reorder angles
        # print(angle,alt_angles-angle)
        # Convert to radians and apply to base angle
        angles = np.radians(angle + alt_angles)
        # print(angles)
        # Vectorized endpoint computation
        end_x = origin[0] + self.ray_length * np.cos(angles)
        end_y = origin[1] + self.ray_length * np.sin(angles)

        # Create LineString rays
        rays = [geom.LineString([origin, (ex, ey)]) for ex, ey in zip(end_x, end_y)]
        
        return rays

    def wall_hit(self, frame_width, frame_height, origin):
        """Check if any rays hit the walls and update hit distances."""
        frame_boundary = geom.Polygon([
            (0, 0), (frame_width, 0), 
            (frame_width, frame_height), (0, frame_height)
        ])
        origin_point = geom.Point(origin)

        for idx, ray in enumerate(self.rays):
            if not frame_boundary.contains(ray.boundary.geoms[-1]):  # If end of ray is outside frame
                intersection = frame_boundary.boundary.intersection(ray)

                if isinstance(intersection, geom.Point):
                    hit_point = intersection
                elif isinstance(intersection, geom.MultiPoint):
                    hit_point = min(intersection.geoms, key=lambda p: origin_point.distance(p))
                else:
                    continue  # No valid intersection

                hit_distance = origin_point.distance(hit_point)
                hit_fraction = hit_distance / self.ray_length
                self.update_new_frame(idx, True, self.tag_index_map['wall'], hit_fraction)

    def update_new_frame(self, ray_index, hitFlag, tag_index, hitFraction):
        """Update the observation frame with hit data."""
        if hitFlag:
            if self.new_frame[ray_index, -2] > hitFraction:  # Update only if closer hit
                self.new_frame[ray_index, :-2] = 0  # Reset all tag indices to 0
                self.new_frame[ray_index, tag_index] = 1
                self.new_frame[ray_index, -2] = hitFraction  # Store closest hit fraction
                self.new_frame[ray_index, -1] = 0  # Unused, can be extended

    def object_hit(self, targets, tag_index, origin):
        """Check if rays hit multiple target points (e.g., box1, box2)."""
        origin_point = geom.Point(origin)

        for target in targets:
            target_point = geom.Point(target)
            for idx, ray in enumerate(self.rays):
                if ray.distance(target_point) <= self.hit_threshold:
                    intersection = ray.interpolate(ray.project(target_point))
                    hit_fraction = origin_point.distance(intersection) / self.ray_length
                    self.update_new_frame(idx, True, tag_index, hit_fraction)

    def polygon_hit(self, polygon_coords, tag_index, origin):
        """Check if any rays intersect a polygon boundary and update hit distances."""
        polygon = geom.Polygon(polygon_coords)
        boundary = polygon.boundary
        origin_point = geom.Point(origin)

        for idx, ray in enumerate(self.rays):
            if boundary.intersects(ray):
                intersection = boundary.intersection(ray)

                points = []
                if isinstance(intersection, geom.Point):
                    points = [intersection]
                elif isinstance(intersection, geom.MultiPoint):
                    points = list(intersection.geoms)
                elif isinstance(intersection, geom.LineString):
                    points = [geom.Point(intersection.coords[0]), geom.Point(intersection.coords[-1])]

                valid_points = [p for p in points if ray.distance(p) < 1e-6]
                if valid_points:
                    closest_point = min(valid_points, key=lambda p: origin_point.distance(p))
                    hit_distance = origin_point.distance(closest_point)
                    hit_fraction = hit_distance / self.ray_length
                    self.update_new_frame(idx, True, tag_index, hit_fraction)

    def addObservation(self, frame_data, frame_width=700, frame_height=470):
        """Update the observation model with new frame data."""
        self.new_frame = np.tile([0]*self.tags_num+[1,1], (self.num_rays, 1)).astype(float)

        bot_pos = frame_data['bot_pos']
        bot_dir = frame_data['bot_dir']
    
        goals = frame_data['goals']
        box_coords = frame_data['ball_coords']
        agent_coords = frame_data['agent_coords']
        agent_coords = [agent["bot_pos"] for agent in agent_coords]

        self.rays = self.generate_rays(bot_pos, bot_dir)

         # Check for object hits (ball, boxes)
        self.object_hit(box_coords['box1'], self.tag_index_map['box1'], bot_pos)
        self.object_hit(box_coords['box2'], self.tag_index_map['box2'], bot_pos)
        self.object_hit(agent_coords, self.tag_index_map['agent'], bot_pos)
        for goal in goals:
            # print("goal",len(goals))
            self.polygon_hit(goal, self.tag_index_map['goal'], bot_pos)
           
        

        self.wall_hit(frame_width, frame_height, bot_pos)

       
        self.data = np.roll(self.data, -1, axis=0)
        self.data[-1] = self.new_frame

        return self.new_frame, self.rays
