import numpy as np
import shapely.geometry as geom
import shapely.ops as ops
import math
import cv2

class Observation:
    def __init__(self):
        self.data = np.zeros((3, 7, 5), dtype=float)  
        self.ray_length = 400.0  
        self.num_rays = 7

        self.new_frame = np.tile([0, 0, 0, 1, 1], (7, 1)).astype(float)
        self.rays = []
        self.tag_index_map = {
            "ball": 0,
            "goal": 1,
            "wall": 2
        }
        self.frame_fps = 30
        self.hit_threshold = 50

    def generate_rays(self, origin, angle):
        """Generate rays from the given origin with a spread of angles."""
        rays = []
        angles = np.linspace(angle-90, angle , self.num_rays)

        for theta in angles:
            theta_rad = np.radians(theta)
            end_x = origin[0] + self.ray_length * np.cos(theta_rad)
            end_y = origin[1] + self.ray_length * np.sin(theta_rad)

            ray = geom.LineString([origin, (end_x, end_y)])
            rays.append(ray)

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
            if self.new_frame[ray_index, 3] > hitFraction:  # Update only if closer hit
                self.new_frame[ray_index, :3] = 0  # Reset all tag indices to 0
                self.new_frame[ray_index, tag_index] = 1
                self.new_frame[ray_index, 3] = hitFraction  # Store closest hit fraction
                self.new_frame[ray_index, 4] = 0  # Unused, can be extended

    def object_hit(self, target, tag_index, origin):
        """Check if any ray hits a target point and update the frame."""
        target_point = geom.Point(target)
        origin_point = geom.Point(origin)

        for idx, ray in enumerate(self.rays):
            if ray.distance(target_point) <= self.hit_threshold:
                intersection = ray.interpolate(ray.project(target_point))
                hit_distance = origin_point.distance(intersection)
                hitFraction = hit_distance / self.ray_length
                self.update_new_frame(idx, True, tag_index, hitFraction)

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
        self.new_frame = np.tile([0, 0, 0, 1, 1], (7, 1)).astype(float)

        bot_pos = frame_data['bot_pos']
        bot_dir = frame_data['bot_dir']
        goal_coords = frame_data['goal_coords']
        ball_pos = frame_data['ball_coords']

        self.rays = self.generate_rays(bot_pos, bot_dir)
        self.object_hit(ball_pos, self.tag_index_map['ball'], bot_pos)
        self.polygon_hit(goal_coords, self.tag_index_map['goal'], bot_pos)
        self.wall_hit(frame_width, frame_height, bot_pos)

       
        self.data = np.roll(self.data, -1, axis=0)
        self.data[-1] = self.new_frame

        return self.new_frame, self.rays
