import pygame
import pygame.freetype as freetype
import math
import random
from utils import WHITE, BLACK, RED, BLUE, GREEN, YELLOW, CYAN, distance
from entities import Entity, Resource, Unit, Square, Dot, Triangle, Building, CommandCenter, UnitBuilding, Turret
import behaviors

# Import the specialized controllers
from ui_renderer import UIRenderer
from world_renderer import WorldRenderer
from input_handler import InputHandler
from entity_manager import EntityManager
from ai_controller import AIController

class Game:
    """Main game class that manages the game state."""
    
    instance = None
    
    def __init__(self, screen_width=1200, screen_height=800):
        """Initialize the game state."""
        Game.instance = self
        
        # Game window dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera offset
        self.camera_offset = [0, 0]
        
        # Delta time for animations
        self.dt = 0
        
        # World dimensions (larger than screen)
        self.world_width = 4000
        self.world_height = 3000
        
        # Game state
        self.paused = False
        self.enemy_ai_paused = False
        self.show_debug = False
        self.game_over = False
        self.winner = None
        
        # Resources [player, enemy]
        self.resources = [200, 200]
        
        # Selection state
        self.selected_entities = []
        self.is_selecting = False
        self.selection_start = None
        self.selection_end = None
        
        # Command state
        self.build_mode = False
        self.build_type = None
        self.attack_move_mode = False
        self.patrol_mode = False
        
        # Visual indicators for command modes
        self.show_patrol_line = False
        self.patrol_start = None
        self.patrol_end = None
        self.patrol_line_timer = 0
        
        # UI panel height
        self.ui_panel_height = 150
        
        # Fonts
        self.font_small = freetype.SysFont(None, 20)
        self.font_medium = freetype.SysFont(None, 30)
        self.font_large = freetype.SysFont(None, 72)
        
        # Pause enemy button (at top-right)
        self.pause_enemy_button = pygame.Rect(
            self.screen_width - 120, 10, 110, 30
        )
        
        # Initialize controllers
        self.renderer = None  # Set by main.py
        self.entity_manager = EntityManager(self)
        self.ui_renderer = UIRenderer(self)
        self.world_renderer = WorldRenderer(self)
        self.input_handler = InputHandler(self)
        self.ai_controller = AIController(self)
        
        # Initialize the game world
        self.entity_manager.init_map()
    
    @property
    def entities(self):
        """Get the list of entities from the entity manager."""
        return self.entity_manager.entities
    
    def update(self, dt):
        """Update the game state."""
        # Store dt for use in rendering animations
        self.dt = dt
        
        if self.game_over:
            return
            
        if not self.paused:
            # Update entities
            self.entity_manager.update(dt)
            
            # Update enemy AI if not paused
            if not self.enemy_ai_paused:
                self.ai_controller.update(dt)
    
    def render(self, screen, renderer):
        """Render the game state."""
        # Store renderer reference
        if self.renderer is None:
            self.renderer = renderer
        
        # Clear the screen
        screen.fill((0, 0, 0))
        
        # Set camera offset in renderer
        renderer.set_camera_offset(self.camera_offset)
        
        # Render world (entities, effects, etc.)
        self.world_renderer.render(screen, renderer, self.dt)
        
        # Render UI elements (minimap, buttons, etc.)
        self.ui_renderer.render(screen, renderer)
    
    def handle_event(self, event):
        """Handle an input event."""
        return self.input_handler.handle_event(event)
    
    def add_entity(self, entity):
        """Add an entity to the game."""
        self.entity_manager.add_entity(entity)
    
    def remove_entity(self, entity):
        """Remove an entity from the game."""
        self.entity_manager.remove_entity(entity)
    
    def print_debug_info(self, message):
        """Print debug info if debug is enabled."""
        if self.show_debug:
            print(message)
    
    def _deselect_all(self):
        """Deselect all selected entities."""
        for entity in self.selected_entities:
            entity.deselect()
        self.selected_entities = []
    
    def _screen_to_world(self, pos):
        """Convert screen coordinates to world coordinates."""
        return (pos[0] + self.camera_offset[0], pos[1] + self.camera_offset[1])
    
    def _world_to_screen(self, pos):
        """Convert world coordinates to screen coordinates."""
        return (pos[0] - self.camera_offset[0], pos[1] - self.camera_offset[1])
    
    def _get_entity_at_position(self, pos):
        """Get entity at the given world position."""
        for entity in reversed(self.entities):  # Reverse order to select top entities first
            if hasattr(entity, 'rect') and entity.rect.collidepoint(pos):
                return entity
        return None 