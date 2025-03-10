import pygame
import pygame.freetype as freetype
from utils import WHITE, rotate_polygon

class VectorRenderer:
    """Handles vector-based rendering of game entities."""
    
    def __init__(self, screen):
        """Initialize the renderer with the screen to draw on."""
        self.screen = screen
        self.camera_offset = [0, 0]
        self.font = freetype.SysFont(None, 20)  # Default font
    
    def set_camera_offset(self, offset):
        """Set the camera offset for rendering."""
        self.camera_offset = offset
    
    def apply_camera_offset(self, position):
        """Apply camera offset to translate world coordinates to screen coordinates."""
        if position is None:
            return None
        return (position[0] - self.camera_offset[0], position[1] - self.camera_offset[1])
    
    def draw_circle(self, center, radius, color=WHITE, width=1, filled=False):
        """Draw a circle at the given center position."""
        screen_pos = self.apply_camera_offset(center)
        if filled:
            pygame.draw.circle(self.screen, color, screen_pos, radius)
        else:
            pygame.draw.circle(self.screen, color, screen_pos, radius, width)
    
    def draw_polygon(self, points, color=WHITE, width=1, filled=False):
        """Draw a polygon defined by points."""
        # Apply camera offset to all points
        screen_points = [self.apply_camera_offset(point) for point in points]
        
        # Handle colors with alpha (opacity)
        surface = None
        if len(color) > 3 and filled:
            # Create a surface with per-pixel alpha
            surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(surface, color, screen_points)
            self.screen.blit(surface, (0, 0))
        else:
            if filled:
                pygame.draw.polygon(self.screen, color, screen_points)
            else:
                pygame.draw.polygon(self.screen, color, screen_points, width)
    
    def draw_line(self, start, end, color=WHITE, width=1):
        """Draw a line from start to end position."""
        screen_start = self.apply_camera_offset(start)
        screen_end = self.apply_camera_offset(end)
        pygame.draw.line(self.screen, color, screen_start, screen_end, width)
    
    def draw_rect(self, rect, color=WHITE, width=1, filled=False):
        """Draw a rectangle."""
        # Apply camera offset
        screen_rect = pygame.Rect(
            rect.x - self.camera_offset[0],
            rect.y - self.camera_offset[1],
            rect.width,
            rect.height
        )
        
        if filled:
            pygame.draw.rect(self.screen, color, screen_rect)
        else:
            pygame.draw.rect(self.screen, color, screen_rect, width)
    
    def draw_square(self, center, size, color=WHITE, width=1, filled=False, angle=0):
        """Draw a square with center and size."""
        half_size = size / 2
        x, y = center
        
        points = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x + half_size, y + half_size),
            (x - half_size, y + half_size)
        ]
        
        # Rotate if necessary
        if angle != 0:
            points = rotate_polygon(points, center, angle)
        
        self.draw_polygon(points, color, width, filled)
    
    def draw_triangle(self, center, size, color=WHITE, width=1, filled=False, angle=0):
        """Draw an equilateral triangle."""
        import math
        x, y = center
        height = size * math.sqrt(3) / 2  # Height of equilateral triangle
        
        # Create triangle pointing right by default
        points = [
            (x + size/2, y),
            (x - size/2, y - height/2),
            (x - size/2, y + height/2)
        ]
        
        # Rotate if necessary
        if angle != 0:
            points = rotate_polygon(points, center, angle)
        
        self.draw_polygon(points, color, width, filled)
    
    def draw_text(self, text, position, color=WHITE, font_size=20, centered=True):
        """Draw text at the given position."""
        screen_pos = self.apply_camera_offset(position)
        
        if font_size != 20:  # Use a different font size if requested
            font = freetype.SysFont(None, font_size)
        else:
            font = self.font
            
        # Create text surface using freetype
        text_rect = font.get_rect(text)
        
        if centered:
            text_rect.center = screen_pos
        else:
            text_rect.topleft = screen_pos
        
        font.render_to(self.screen, text_rect, text, color)
    
    def draw_selection_box(self, start, end, color=WHITE):
        """Draw a selection box from start to end positions.
        
        Args:
            start: The start position in screen coordinates
            end: The end position in screen coordinates
            color: The color to draw the box
        """
        # Calculate the box dimensions
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        width = abs(end[0] - start[0])
        height = abs(end[1] - start[1])
        
        # Draw the selection box
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, color, rect, 1) 