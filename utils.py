import math
import pygame
import numpy as np

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Vector operations
def normalize(vector):
    """Normalize a vector to unit length."""
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2)
    if magnitude == 0:
        return (0, 0)
    return (vector[0] / magnitude, vector[1] / magnitude)

def distance(pos1, pos2):
    """Calculate Euclidean distance between two positions."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def angle_between(pos1, pos2):
    """Calculate angle in radians between two positions."""
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.atan2(dy, dx)

def rotate_point(point, center, angle):
    """Rotate a point around a center by angle (radians)."""
    x, y = point
    cx, cy = center
    
    # Translate point to origin
    translated_x = x - cx
    translated_y = y - cy
    
    # Rotate point
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rotated_x = translated_x * cos_a - translated_y * sin_a
    rotated_y = translated_x * sin_a + translated_y * cos_a
    
    # Translate back
    return (rotated_x + cx, rotated_y + cy)

def rotate_polygon(points, center, angle):
    """Rotate all points in a polygon around a center by angle (radians)."""
    return [rotate_point(point, center, angle) for point in points]

def create_square(center, size, angle=0):
    """Create a square centered at center with side length size, rotated by angle (radians)."""
    half_size = size / 2
    x, y = center
    points = [
        (x - half_size, y - half_size),
        (x + half_size, y - half_size),
        (x + half_size, y + half_size),
        (x - half_size, y + half_size)
    ]
    
    # Rotate if needed
    if angle != 0:
        points = rotate_polygon(points, center, angle)
    
    return points

def create_triangle(center, size, angle=0):
    """Create an equilateral triangle centered at center with side length size."""
    x, y = center
    height = size * math.sqrt(3) / 2  # Height of equilateral triangle
    
    # Create triangle pointing right
    points = [
        (x + size/2, y),
        (x - size/2, y - height/2),
        (x - size/2, y + height/2)
    ]
    
    # Rotate if needed
    if angle != 0:
        points = rotate_polygon(points, center, angle)
    
    return points

# Game utility functions
def is_point_in_rect(point, rect):
    """Check if a point is inside a pygame Rect."""
    return rect.collidepoint(point)

def is_rect_in_rect(rect1, rect2):
    """Check if rect1 is completely inside rect2."""
    return rect2.contains(rect1)

def is_rect_colliding_rect(rect1, rect2):
    """Check if rect1 is colliding with rect2."""
    return rect1.colliderect(rect2)

def draw_health_bar(surface, position, size, value, max_value, color=GREEN, bg_color=RED):
    """Draw a health bar at the specified position."""
    x, y = position
    width, height = size
    
    # Calculate fill width based on health percentage
    fill_width = (value / max_value) * width
    
    # Draw background
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    
    # Draw filled portion
    if value > 0:
        pygame.draw.rect(surface, color, (x, y, fill_width, height))
    
    # Draw border
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 1) 