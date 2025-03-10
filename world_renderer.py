import pygame
from entities import Building, Unit
from utils import WHITE
import math

class WorldRenderer:
    """Handles rendering of world entities and effects."""
    
    def __init__(self, game):
        """Initialize the world renderer.
        
        Args:
            game: Reference to the main Game instance
        """
        self.game = game
    
    def render(self, screen, renderer, dt=None):
        """Render the game world.
        
        Args:
            screen: The pygame screen to render to
            renderer: The vector renderer instance
            dt: Delta time for animations, if None defaults to 0
        """
        # If dt is not provided, default to 0
        if dt is None:
            dt = 0
            
        # Set clipping rect to exclude UI area
        screen.set_clip(0, 0, self.game.screen_width, self.game.screen_height - self.game.ui_panel_height)
        
        # Clear screen
        screen.fill((20, 20, 20))  # Very dark gray background
        
        # Draw grid
        self._render_world_grid(screen, renderer)
        
        # Render all entities (sorted by type to control rendering order)
        all_entities = self.game.entities
        
        # Render resources first (bottom layer)
        for entity in [e for e in all_entities if hasattr(e, 'render') and not isinstance(e, Building) and not isinstance(e, Unit)]:
            entity.render(renderer)
        
        # Render buildings next (middle layer)
        for entity in [e for e in all_entities if hasattr(e, 'render') and isinstance(e, Building)]:
            entity.render(renderer)
            
        # Render units last (top layer)
        for entity in [e for e in all_entities if hasattr(e, 'render') and isinstance(e, Unit)]:
            entity.render(renderer)
        
        # Draw selection box if selecting
        if self.game.is_selecting and self.game.selection_start and self.game.selection_end:
            renderer.draw_selection_box(self.game.selection_start, self.game.selection_end, (255, 255, 255))
        
        # Render building placement preview if in build mode
        if self.game.build_mode and self.game.build_type:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[1] < self.game.screen_height - self.game.ui_panel_height:
                self._render_building_preview(screen, renderer, mouse_pos)
        
        # Render attack-move cursor if in attack-move mode
        if self.game.attack_move_mode:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[1] < self.game.screen_height - self.game.ui_panel_height:
                self._render_attack_move_cursor(screen, renderer, mouse_pos)
                
        # Render patrol line if active
        if self.game.show_patrol_line and self.game.patrol_start and self.game.patrol_end:
            self._render_patrol_line(screen, renderer)
            # Decrease timer
            self.game.patrol_line_timer -= dt
            if self.game.patrol_line_timer <= 0:
                self.game.show_patrol_line = False
        
        # Reset clipping
        screen.set_clip(None)
    
    def _render_world_grid(self, screen, renderer):
        """Render a grid to help visualize the world.
        
        Args:
            screen: The pygame screen to render to
            renderer: The vector renderer instance
        """
        # Grid settings
        grid_size = 200  # Size of grid cells
        grid_color = (30, 30, 30)  # Very dark gray
        
        # Calculate visible grid range
        start_x = (self.game.camera_offset[0] // grid_size) * grid_size
        end_x = start_x + self.game.screen_width + grid_size
        
        start_y = (self.game.camera_offset[1] // grid_size) * grid_size
        end_y = start_y + self.game.screen_height + grid_size
        
        # Draw vertical grid lines
        for x in range(int(start_x), int(end_x), grid_size):
            start_pos = self.game._world_to_screen([x, start_y])
            end_pos = self.game._world_to_screen([x, end_y])
            pygame.draw.line(screen, grid_color, start_pos, end_pos, 1)
        
        # Draw horizontal grid lines
        for y in range(int(start_y), int(end_y), grid_size):
            start_pos = self.game._world_to_screen([start_x, y])
            end_pos = self.game._world_to_screen([end_x, y])
            pygame.draw.line(screen, grid_color, start_pos, end_pos, 1)
    
    def _render_building_preview(self, screen, renderer, pos):
        """Render a preview of the building that's about to be placed.
        
        Args:
            screen: The pygame screen to render to
            renderer: The vector renderer instance
            pos: Mouse position on screen
        """
        # Apply camera offset to get world position
        world_pos = self.game._screen_to_world(pos)
        
        # Check for valid placement
        valid_placement = True
        for entity in self.game.entities:
            if hasattr(entity, 'position') and hasattr(entity, 'position'):
                if self._distance(world_pos, entity.position) < 70:
                    valid_placement = False
                    break
        
        # Determine building size and type
        size = 0
        if self.game.build_type == "unit_building":
            size = 60  # UnitBuilding size
            # Create preview surface
            preview_surface = pygame.Surface((self.game.screen_width, self.game.screen_height), pygame.SRCALPHA)
            
            # Draw a pentagon for unit building
            points = []
            for i in range(5):
                angle = 2*math.pi/5 * i - math.pi/2  # Start from top
                x = pos[0] + math.cos(angle) * size/2
                y = pos[1] + math.sin(angle) * size/2
                points.append((x, y))
                
            color = (100, 100, 255) if valid_placement else (255, 100, 100)
            
            # Draw the pentagon body
            pygame.draw.polygon(preview_surface, (*color, 128), points)
            
            # Draw the outline
            pygame.draw.polygon(preview_surface, (255, 255, 255, 200), points, 2)
            
            # Blit the entire preview
            screen.blit(preview_surface, (0, 0))
            
        elif self.game.build_type == "turret":
            size = 40  # Turret size
            # Create preview surface
            preview_surface = pygame.Surface((self.game.screen_width, self.game.screen_height), pygame.SRCALPHA)
            
            # Draw a hexagon for turret
            points = []
            for i in range(6):
                angle = math.pi/3 * i
                x = pos[0] + math.cos(angle) * size/2
                y = pos[1] + math.sin(angle) * size/2
                points.append((x, y))
                
            color = (100, 100, 255) if valid_placement else (255, 100, 100)
            
            # Draw the hexagon body
            pygame.draw.polygon(preview_surface, (*color, 128), points)
            
            # Draw a line for the turret
            barrel_length = size * 0.7
            pygame.draw.line(preview_surface, (255, 255, 255, 180), pos, (pos[0] + barrel_length, pos[1]), 3)
            
            # Draw range circle
            pygame.draw.circle(preview_surface, (255, 255, 255, 30), pos, 150)  # Turret range
            pygame.draw.circle(preview_surface, (255, 255, 255, 60), pos, 150, 1)
            
            # Draw the outline
            pygame.draw.polygon(preview_surface, (255, 255, 255, 200), points, 2)
            
            # Blit the entire preview
            screen.blit(preview_surface, (0, 0))
        
        # Draw placement status text
        status_text = "Valid Location" if valid_placement else "Cannot Build Here"
        status_color = (0, 255, 0) if valid_placement else (255, 0, 0)
        
        # Create a background for the text
        text_rect = self.game.font_small.get_rect(status_text)
        text_rect.center = (pos[0], pos[1] - size - 20)
        
        bg_rect = pygame.Rect(text_rect)
        bg_rect.inflate_ip(10, 5)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)
        
        # Draw the text
        self.game.font_small.render_to(screen, text_rect, status_text, status_color)
    
    def _render_attack_move_cursor(self, screen, renderer, pos):
        """Render a custom cursor for attack-move mode.
        
        Args:
            screen: The pygame screen to render to
            renderer: The vector renderer instance
            pos: Mouse position on screen
        """
        # Draw a red targeting reticle
        pygame.draw.circle(screen, (255, 0, 0), pos, 15, 2)
        pygame.draw.line(screen, (255, 0, 0), (pos[0] - 20, pos[1]), (pos[0] + 20, pos[1]), 2)
        pygame.draw.line(screen, (255, 0, 0), (pos[0], pos[1] - 20), (pos[0], pos[1] + 20), 2)
    
    def _render_patrol_line(self, screen, renderer):
        """Render a line indicating the patrol route.
        
        Args:
            screen: The pygame screen to render to
            renderer: The vector renderer instance
            pos: Mouse position
        """
        if not self.game.patrol_start or not self.game.patrol_end:
            return
            
        # Convert world positions to screen positions
        start_screen = self.game._world_to_screen(self.game.patrol_start)
        end_screen = self.game._world_to_screen(self.game.patrol_end)
        
        # Draw a dashed line between the points
        dash_length = 10
        gap_length = 5
        dash_color = (0, 255, 0)  # Green
        
        # Calculate the total distance and angle
        dx = end_screen[0] - start_screen[0]
        dy = end_screen[1] - start_screen[1]
        dist = self._distance(start_screen, end_screen)
        
        if dist == 0:
            return
            
        # Normalize direction vector
        dx /= dist
        dy /= dist
        
        # Draw dashes
        pos = start_screen
        current_length = 0
        drawing = True
        
        while current_length < dist:
            if drawing:
                dash_end = (
                    pos[0] + dx * min(dash_length, dist - current_length),
                    pos[1] + dy * min(dash_length, dist - current_length)
                )
                pygame.draw.line(screen, dash_color, pos, dash_end, 2)
                pos = dash_end
                current_length += dash_length
                drawing = False
            else:
                pos = (
                    pos[0] + dx * min(gap_length, dist - current_length),
                    pos[1] + dy * min(gap_length, dist - current_length)
                )
                current_length += gap_length
                drawing = True
        
        # Draw arrow at end to indicate direction
        arrow_length = 15
        arrow_width = 8
        angle = math.atan2(dy, dx)
        
        # Arrow points
        p1 = (
            end_screen[0] - arrow_length * math.cos(angle),
            end_screen[1] - arrow_length * math.sin(angle)
        )
        p2 = (
            p1[0] - arrow_width * math.cos(angle + math.pi/2),
            p1[1] - arrow_width * math.sin(angle + math.pi/2)
        )
        p3 = (
            p1[0] - arrow_width * math.cos(angle - math.pi/2),
            p1[1] - arrow_width * math.sin(angle - math.pi/2)
        )
        
        # Draw arrow
        pygame.draw.polygon(screen, dash_color, [end_screen, p2, p3])
    
    def _distance(self, pos1, pos2):
        """Calculate distance between two points.
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            float: Euclidean distance
        """
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5 