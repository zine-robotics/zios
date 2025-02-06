import numpy as np
import shapely.geometry as geom
import shapely.ops as ops
import math
import cv2

class Observation:
    def __init__(self):
        self.data = np.zeros((3, 7, 5),dtype=float)  
        self.ray_length = 250.0  
        self.num_rays = 7

        self.new_frame = np.tile([0, 0, 0, 1, 1], (7, 1)).astype(float)
        self.rays = []
        self.tag_index_map = {
            "ball": 0,
            "goal": 1,
            "wall": 2
        }
        self.frame_fps = 30
        self.hit_threshold=50

    # Ray Casting Functions
    def generate_rays(self, origin, angle):
        """Generate rays from origin in a 90-degree spread centered around angle."""
        rays = []
        angles = np.linspace(angle - 45, angle + 45, self.num_rays)  
        for theta in angles:
            theta_rad = np.radians(theta)
            end_x = origin[0] + self.ray_length * np.cos(theta_rad)
            end_y = origin[1] + self.ray_length * np.sin(theta_rad)
            rays.append(geom.LineString([origin, (end_x, end_y)]))
        # print(len(rays))
        return rays

    def update_new_frame(self, ray_index, hitFlag, tag_index, hitFraction):
        #print(hitFraction)
        if hitFlag:
            if self.new_frame[ray_index, 3] > hitFraction:  # Update only if closer hit
                self.new_frame[ray_index, :3] = 0  # Reset all tag indices to 0
                self.new_frame[ray_index, tag_index] = 1
                self.new_frame[ray_index, 3] = hitFraction  # Store closest hit fraction
                self.new_frame[ray_index, 4] = 0  # Unused, can be extended
                #print("intersected object tag, at ray: ", tag_index,  ray_index )

    def object_hit(self, target, tag_index, origin):
        """Check if any ray hits the target within a given distance threshold and update frame."""
        target_point = geom.Point(target)
        origin_point = geom.Point(origin)
        rays_list = list(self.rays)
        for idx, ray in enumerate(rays_list):

            #print("try object hit: idx, raydist",len(rays_list),idx, ray.distance(target_point))
            if ray.distance(target_point) <= self.hit_threshold:
               
               
                # Compute closest intersection point on the ray
                intersection = ray.interpolate(ray.project(target_point))
                hit_distance = origin_point.distance(intersection)
                hitFraction = hit_distance / self.ray_length*1.0
               
                self.update_new_frame(idx, True, tag_index, hitFraction)
                

    def polygon_hit(self, polygon_coords, tag_index, origin):
        """Find rays that intersect with a polygon's boundary and update hit distances."""
        polygon = geom.Polygon(polygon_coords)
        boundary = polygon.boundary  # Get the polygon's boundary as a LinearRing
        origin_point = geom.Point(origin)

        for idx, ray in enumerate(self.rays):
            if boundary.intersects(ray):
                intersection = boundary.intersection(ray)
                # print(intersection,idx)
                
                # Extract all intersection points
                points = []
                if intersection.is_empty:
                    continue
                elif isinstance(intersection, geom.Point):
                    points = [intersection]
                elif isinstance(intersection, geom.MultiPoint):
                    points = list(intersection.geoms)
                elif isinstance(intersection, geom.LineString):
                    # For line intersections, use start/end points
                    points = [geom.Point(intersection.coords[0]), 
                            geom.Point(intersection.coords[-1])]
                
                # Find the closest valid intersection point
                valid_points = [
                    p for p in points 
                    if ray.distance(p) < 1e-6  # Ensure point lies on the ray
                ]
                if valid_points:
                    closest_point = min(
                        valid_points, 
                        key=lambda p: origin_point.distance(p)
                    )
                    hit_distance = origin_point.distance(closest_point)
                    hit_fraction = hit_distance / self.ray_length
                    self.update_new_frame(idx, True, tag_index, hit_fraction)

    def addObservation(self, frame_data):
        self.new_frame = np.tile([0, 0, 0, 1, 1], (7, 1)).astype(float)
        bot_pos = frame_data['bot_pos']
        bot_dir = frame_data['bot_dir']
        goal_coords = frame_data['goal_coords']
        ball_pos = frame_data['ball_coords']

       

        self.rays = self.generate_rays(bot_pos, bot_dir)
        self.object_hit(ball_pos, self.tag_index_map['ball'], bot_pos)
        self.polygon_hit(goal_coords, self.tag_index_map['goal'], bot_pos)

        self.frame_fps -=1
        self.data = np.roll(self.data, -1, axis=0)
        self.data[-1] = self.new_frame
        return self.new_frame,self.rays

        