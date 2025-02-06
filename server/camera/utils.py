import numpy as np
import cv2
from enum import Enum
from shapely.geometry import MultiPoint, Polygon
from camera.color_ranges import COLOR_RANGES
from camera.arena_entity import *


def detect_shapes_and_colors(image):

    detected_shapes = []
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    for color_name, ranges in COLOR_RANGES.items():
        # Create a combined mask for the color
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv_image, lower, upper))

        # Find contours for the color
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter small contours
                # Approximate the contour to detect shapes
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                shape = "unknown"

                # Identify shape based on the number of vertices
                num_vertices = len(approx)
                if num_vertices > 7:
                    shape = "circle"
                elif num_vertices == 3:
                    shape = "triangle"
                elif num_vertices == 4:
                     shape = "rectangle"
                elif num_vertices == 2:
                    shape = "line"

                # Get points for the detected shape
                points = [tuple(point[0]) for point in approx]
                detected_shapes.append(((shape, color_name), points))

    return detected_shapes




def detect_aruco_markers(image):

    markerDictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
    detectorParam = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(markerDictionary, detectorParam)
    corners, ids, rejected = detector.detectMarkers(image)
  

    list_of_aruco = []
    if ids is not None :
        for i in range(len(ids)):
            list_of_aruco.append((ids[i][0],corners[i][0]))

    return list_of_aruco

from collections import defaultdict




def assign_positions_to_color_entities(entities, shape_color_points):

    # Grouping entities by shape and color
    grouped_entities = defaultdict(list)
    for entity in entities:
        grouped_entities[(entity.shape, entity.color)].append(entity)

    # Dictionary to store available positions by shape and color
    positions_dict = defaultdict(list)
    for (shape, color), points in shape_color_points:
        positions_dict[(shape, color)].append(points)
    # print([len(x) for x in positions_dict.values()])

    # Prepare result list
    result = []

    # For each shape/color group, assign points to each entity in the group
    for shape_color, entities_group in grouped_entities.items():
        shape, color = shape_color
        
        if len(grouped_entities[(shape, color)]) <= len(positions_dict[(shape, color)]):
            for i in range(len(grouped_entities[(shape, color)])):
                positions = positions_dict[(shape, color)].pop()
                entity = grouped_entities[(shape, color)].pop()
                result.append((entity,positions))
            
    return result


def assign_positions_to_aruco_entities(entities, list_of_aruco):

    # Grouping entities by shape and color
    grouped_entities = defaultdict(list)
    for entity in entities:
        grouped_entities[entity.aruco_id].append(entity)

    # Dictionary to store available positions by shape and color
    positions_dict = defaultdict(list)
    for id, points in list_of_aruco:
        positions_dict[id].append(points)
    # print([len(x) for x in positions_dict.values()])

    # Prepare result list
    result = []

    # For each shape/color group, assign points to each entity in the group
    for id, entities_group in grouped_entities.items():
        if len(grouped_entities[id]) <= len(positions_dict[id]):
            for i in range(len(grouped_entities[id])):
                positions = positions_dict[id].pop()
                entity = grouped_entities[id].pop()
                result.append((entity,positions))
            
    return result


def categorize_entity(entity_pos):

    # Initialize categorized entity lists
    entity_categories = {
        EntityType.BOUNDARY: [],
        EntityType.PLAYER: [],
        EntityType.OBJECT: [],
        EntityType.REGION: [],
    }

    # Categorize entities
    for (entity,pos) in entity_pos:
        if entity.entity_type in entity_categories:
            entity_categories[entity.entity_type].append((entity,np.array(pos)))
        else:
            print(f"Unknown entity type: {entity.entity_type}")

    entity_categories[EntityType.BOUNDARY] = process_boundary_and_region_data(entity_categories[EntityType.BOUNDARY])
    # entity_categories[EntityType.OBJECT] = process_boundary_and_region_data(entity_categories[EntityType.OBJECT])
    return entity_categories


def transform_points(points, M):
    if len(points)>0:
        points_homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])
        transformed_points_homogeneous = np.dot(points_homogeneous, M.T)
        transformed_points = transformed_points_homogeneous[:, :2] / transformed_points_homogeneous[:, 2][:, np.newaxis]
    else:
        transformed_points = []
    return np.array(transformed_points,dtype=np.int32)


def get_6dof_pos(points, is_aruco=False):

    if is_aruco:
        x = (points[0][0] + points[2][0]) / 2
        y = (points[0][1] + points[2][1]) / 2
        yaw = np.arctan2(points[2][1] - points[0][1], points[2][0] - points[0][0])
        return np.array((x, y, 0, 0, 0, yaw),dtype=np.float32)
    
    
    else:
        point = np.mean(points,axis=0)
        return np.array((point[0], point[1], 0, 0, 0, 0),dtype=np.float32)
    

def order_points(pts):

    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]  # top-left: smallest sum of x + y
    rect[2] = pts[np.argmax(s)]  # bottom-right: largest sum of x + y
    rect[1] = pts[np.argmin(diff)]  # top-right: smallest difference of x - y
    rect[3] = pts[np.argmax(diff)]  # bottom-left: largest difference of x - y

    return rect

 # Compute the concave hull
def compute_concave_hull(points, alpha=0.1):
    if len(points) < 4:
        return points  # Not enough points for a hull
    points = MultiPoint(points)
    polygon = points.convex_hull
    return polygon



def process_entity_data(entity_data, M):

    for entity_type in entity_data:
        if entity_type  == EntityType.BOUNDARY:
            tf_pose = transform_points(np.array(entity_data[EntityType.BOUNDARY]),M)
            entity_data[EntityType.BOUNDARY] = tf_pose
        else:
            process_entity_pos = []
            entity_pos = entity_data[entity_type]
            for entity,pos in entity_pos:
                if len(pos) > 0:
                    tf_pose = transform_points(pos,M)
                    if entity_type in [EntityType.OBJECT,EntityType.PLAYER] :
                        tf_pose = get_6dof_pos(tf_pose,entity.aruco_id!=None)
                    process_entity_pos.append((entity,tf_pose))

                entity_data[entity_type] = process_entity_pos

    return entity_data


def process_boundary_and_region_data(list_of_entity_pos):

    all_points = []

    for entity, points in list_of_entity_pos:
        # Calculate the center point of the boundary entity
        center = np.mean(points, axis=0)
        all_points.append(center)

    if len(all_points) == 0:
        # print("No center points found for boundary entities.")
        return []

    # Compute convex hull of the center points
    all_points = np.array(all_points)
    if len(all_points) > 4:
        points = MultiPoint(points)
        polygon = points.convex_hull
        hull_points = np.array(list(polygon.exterior.coords), dtype=np.int32)[:-1]
    else:
        hull_points = all_points

    return hull_points

def map_to_response(data_entity):
    response = []
    for entity_type in data_entity:
        resp_dict = {}
        if entity_type in [EntityType.OBJECT,EntityType.PLAYER] :
            for entity, pos in data_entity[entity_type]:
                resp_dict['id'] = entity.id
                resp_dict['pose'] = pos
                resp_dict['object_type'] = entity_type
                resp_dict['tag'] = entity.tag
                resp_dict['mobility'] = entity.mobility
                resp_dict['options'] = {}
                response.append(resp_dict)
        elif entity_type in [EntityType.REGION] :
            for entity, pos in data_entity[entity_type]:
                resp_dict['id'] = entity.id
                resp_dict['pose'] = np.zeros(6)
                resp_dict['object_type'] = entity_type
                resp_dict['tag'] = entity.tag
                resp_dict['mobility'] = entity.mobility
                resp_dict['options'] = {"boundary_points" : pos}
                response.append(resp_dict)
        else:
            pos = data_entity[entity_type]
            resp_dict['id'] = 'boundary'
            resp_dict['pose'] = np.zeros(6)
            resp_dict['object_type'] = entity_type
            resp_dict['tag'] = 'boundary_polygon'
            resp_dict['mobility'] = 'fixed'
            resp_dict['options'] = {"boundary_points" : pos}
            response.append(resp_dict)
    
    return response


def draw_circles(image, response, color=(0, 255, 0), radius=5, thickness=-1):

    points = []
    for r in response:
        if r['object_type'] in [EntityType.REGION,EntityType.BOUNDARY]:
            boundary_points = r['options']['boundary_points']
            cv2.polylines(image, [boundary_points], isClosed=True, color=(0, 255, 255), thickness=1)
        pose = r['pose']
        points.append((pose[0],pose[1]))
    
    points = np.array(points, dtype=np.int32)
    
    for point in points:
        cv2.circle(image, tuple(point), radius, color, thickness)
    
    return image

