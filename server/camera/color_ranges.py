import numpy as np
import cv2
from enum import Enum
from shapely.geometry import MultiPoint, Polygon

# Define color ranges (HSV format)
COLOR_RANGES = {
    "red": [
        (np.array([0, 50, 50]), np.array([10, 255, 255])),  # Lower red range
        (np.array([170, 50, 50]), np.array([180, 255, 255]))  # Upper red range
    ],
    "blue": [
        (np.array([100, 50, 50]), np.array([130, 255, 255])),
    ],
    "green": [
        (np.array([40, 50, 50]), np.array([80, 255, 255]))
    ],
    "yellow": [
        (np.array([20, 100, 100]), np.array([30, 255, 255]))
    ],
    "cyan": [
        (np.array([80, 100, 100]), np.array([90, 255, 255]))
    ],
    "magenta": [
        (np.array([140, 50, 50]), np.array([160, 255, 255]))
    ],
    "orange": [
        (np.array([10, 100, 100]), np.array([20, 255, 255]))
    ],
    "purple": [
        (np.array([125, 50, 50]), np.array([140, 255, 255]))
    ],
    "black": [
        (np.array([0, 0, 0]), np.array([180, 255, 30]))
    ],
    "white": [
        (np.array([0, 0, 200]), np.array([180, 30, 255]))
    ]
}
