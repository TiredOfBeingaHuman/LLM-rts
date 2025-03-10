import pygame
import pygame.freetype as freetype
import sys
import random
import math
from utils import WHITE, BLACK, RED, BLUE, GREEN, YELLOW, CYAN, distance
from entities import Entity, Resource, Unit, Square, Dot, Triangle, Building, CommandCenter, UnitBuilding, Turret
import behaviors

class Game:
    """Main game class that manages the game state."""
    
    instance = None
    
    def __init__(self, screen_width=1200, screen_height=800):
        """Initialize the game state."""
        Game.instance = self
        
        # Game window dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Game state
        self.entities = []
        self.selected_entities = []
        self.resources = [200, 200]  # Player and enemy resources
        self.unit_building_cost = 150  # Cost to build a unit building
        
        # Selection state
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        
        # Special command states
        self.build_mode = False      # Track if we're in build mode
        self.build_type = None       # What we're building
        self.attack_move_mode = False # Track if we're in attack-move mode
        self.patrol_mode = False      # Track if we're in patrol mode
        
        # UI state
        self.show_debug = False
        self.paused = False
        self.enemy_ai_paused = False  # Flag to pause just the enemy AI
        self.game_over = False
        self.winner = None
        
        # Fonts
        self.font_small = freetype.SysFont(None, 18)
        self.font_medium = freetype.SysFont(None, 30)
        self.font_large = freetype.SysFont(None, 72)
        
        # UI Elements
        self.ui_panel_height = 150  # Height of the bottom UI panel
        self.minimap_size = 200     # Size of the minimap
        self.command_card_size = 250  # Size of the command card
        
        # Command buttons (initialized in _create_command_buttons)
        self.command_buttons = []
        self._create_command_buttons()
        
        # Pause enemy button
        self.pause_enemy_button = pygame.Rect(
            self.screen_width - 120, 10, 110, 30
        )
        
        # Initialize the map
        self._init_map()
    
    def _create_command_buttons(self):
        """Create command buttons for different unit/building types."""
        self.command_buttons = []
        
        # Dimensions and layout
        button_size = 40
        button_margin = 5
        card_start_x = self.screen_width - self.command_card_size + button_margin
        card_start_y = self.screen_height - self.ui_panel_height + button_margin
        
        # Define all possible buttons
        self.all_buttons = {
            # Worker buttons
            "move": {
                "type": "move",
                "position": (card_start_x, card_start_y),
                "tooltip": "Move (Right-click)",
                "key": None,
                "text": "M",
                "color": BLUE
            },
            "gather": {
                "type": "gather",
                "position": (card_start_x + button_size + button_margin, card_start_y),
                "tooltip": "Gather Resources (Right-click)",
                "key": None,
                "text": "G",
                "color": CYAN
            },
            "build": {
                "type": "build",
                "position": (card_start_x + (button_size + button_margin) * 2, card_start_y),
                "tooltip": "Build Unit Building (B)",
                "key": pygame.K_b,
                "text": "B",
                "color": YELLOW
            },
            
            # Combat unit commands
            "attack": {
                "type": "attack",
                "position": (card_start_x, card_start_y),
                "tooltip": "Attack (A)",
                "key": pygame.K_a,
                "text": "A",
                "color": RED
            },
            "hold": {
                "type": "hold",
                "position": (card_start_x + button_size + button_margin, card_start_y),
                "tooltip": "Hold Position (H)",
                "key": pygame.K_h,
                "text": "H",
                "color": GREEN
            },
            "patrol": {
                "type": "patrol",
                "position": (card_start_x + (button_size + button_margin) * 2, card_start_y),
                "tooltip": "Patrol (P)",
                "key": pygame.K_p,
                "text": "P",
                "color": BLUE
            },
            
            # Command Center buttons
            "square": {
                "type": "square",
                "position": (card_start_x, card_start_y),
                "tooltip": "Build Worker (S) - 50",
                "key": pygame.K_s,
                "text": "S",
                "color": BLUE
            },
            
            # Unit Building buttons
            "dot": {
                "type": "dot",
                "position": (card_start_x, card_start_y),
                "tooltip": "Build Dot (D) - 75",
                "key": pygame.K_d,
                "text": "D",
                "color": GREEN
            },
            "triangle": {
                "type": "triangle",
                "position": (card_start_x + button_size + button_margin, card_start_y),
                "tooltip": "Build Triangle (T) - 100",
                "key": pygame.K_t,
                "text": "T",
                "color": YELLOW
            }
        }
    
    def _init_map(self):
        """Initialize the game map with resources and starting buildings."""
        # Add player command center
        player_cc_pos = (self.screen_width * 0.2, self.screen_height * 0.5)
        player_cc = CommandCenter(player_cc_pos, player_id=0)
        self.add_entity(player_cc)
        
        # Add enemy command center
        enemy_cc_pos = (self.screen_width * 0.8, self.screen_height * 0.5)
        enemy_cc = CommandCenter(enemy_cc_pos, player_id=1)
        self.add_entity(enemy_cc)
        
        # Add unit building for player
        unit_building_pos = (player_cc_pos[0] + 150, player_cc_pos[1])
        player_unit_building = UnitBuilding(unit_building_pos, player_id=0)
        self.add_entity(player_unit_building)
        
        # Add 5 Dot units for player
        for i in range(5):
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)
            pos = (unit_building_pos[0] + 80 + offset_x, unit_building_pos[1] + offset_y)
            self.add_entity(Dot(pos, player_id=0))
        
        # Add initial worker units for player
        for i in range(4):
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            pos = (player_cc_pos[0] + offset_x, player_cc_pos[1] + offset_y)
            self.add_entity(Square(pos, player_id=0))
        
        # Add initial worker units for enemy
        for i in range(4):
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            pos = (enemy_cc_pos[0] + offset_x, enemy_cc_pos[1] + offset_y)
            self.add_entity(Square(pos, player_id=1))
        
        # Add mineral resources near player base
        for i in range(5):
            offset_x = random.randint(-200, -100)
            offset_y = random.randint(-100, 100)
            pos = (player_cc_pos[0] + offset_x, player_cc_pos[1] + offset_y)
            self.add_entity(Resource(pos))
        
        # Add mineral resources near enemy base
        for i in range(5):
            offset_x = random.randint(100, 200)
            offset_y = random.randint(-100, 100)
            pos = (enemy_cc_pos[0] + offset_x, enemy_cc_pos[1] + offset_y)
            self.add_entity(Resource(pos))
    
    def add_entity(self, entity):
        """Add an entity to the game."""
        self.entities.append(entity)
        return entity
    
    def remove_entity(self, entity):
        """Remove an entity from the game."""
        if entity in self.entities:
            self.entities.remove(entity)
            if entity in self.selected_entities:
                self.selected_entities.remove(entity)
    
    def update(self, dt):
        """Update the game state for one frame."""
        if self.paused or self.game_over:
            return
        
        try:
            # Update all entities
            entities_to_remove = []
            for entity in list(self.entities):  # Create a copy to avoid modification during iteration
                try:
                    entity.update(dt)
                    
                    # Check if entity is destroyed
                    if hasattr(entity, 'health') and entity.health <= 0:
                        entities_to_remove.append(entity)
                        
                except Exception as e:
                    print(f"Error updating entity {entity}: {e}")
                    # If an entity has an error during update, remove it safely
                    entities_to_remove.append(entity)
            
            # Remove destroyed entities
            for entity in entities_to_remove:
                try:
                    self.remove_entity(entity)
                except Exception as e:
                    print(f"Error removing entity: {e}")
                    # If it fails to remove, force remove from lists
                    if entity in self.entities:
                        self.entities.remove(entity)
                    if entity in self.selected_entities:
                        self.selected_entities.remove(entity)
            
            # Check win/lose conditions
            self._check_game_over()
            
            # Simple AI for enemy
            try:
                self._update_enemy_ai(dt)
            except Exception as e:
                print(f"Error in enemy AI: {e}")
                # Prevent the AI error from crashing the game
                pass
                
        except Exception as e:
            print(f"Critical error in game update: {e}")
            # Continue the game loop even if there's an error
    
    def _check_game_over(self):
        """Check if the game is over."""
        # Check if player has any command centers
        player_cc = [e for e in self.entities 
                    if isinstance(e, CommandCenter) and e.player_id == 0]
        
        # Check if enemy has any command centers
        enemy_cc = [e for e in self.entities 
                    if isinstance(e, CommandCenter) and e.player_id == 1]
        
        if not player_cc:
            self.game_over = True
            self.winner = 1  # Enemy wins
        elif not enemy_cc:
            self.game_over = True
            self.winner = 0  # Player wins
    
    def _update_enemy_ai(self, dt):
        """Simple AI for enemy player."""
        # Skip updating if enemy AI is paused
        if self.enemy_ai_paused:
            return
            
        try:
            # Get all enemy units and buildings
            enemy_units = [e for e in self.entities 
                          if hasattr(e, 'player_id') and e.player_id == 1]
            
            enemy_command_centers = [e for e in enemy_units if isinstance(e, CommandCenter)]
            enemy_workers = [e for e in enemy_units if isinstance(e, Square)]
            enemy_unit_buildings = [e for e in enemy_units if isinstance(e, UnitBuilding)]
            enemy_combat_units = [e for e in enemy_units 
                                 if isinstance(e, (Dot, Triangle))]
            
            # Find resources
            resources = [e for e in self.entities if isinstance(e, Resource)]
            
            # Find player buildings (targets)
            player_buildings = [e for e in self.entities 
                               if isinstance(e, Building) and e.player_id == 0]
            
            # Phase 1: Gather resources with workers
            for worker in enemy_workers:
                try:
                    # Check if the worker is idle (using the new behavior system)
                    if isinstance(worker.current_behavior, behaviors.IdleBehavior):
                        # Find nearest resource with remaining amount
                        valid_resources = [r for r in resources if r.amount > 0]
                        if valid_resources:
                            nearest = min(valid_resources, 
                                         key=lambda r: (worker.position[0] - r.position[0])**2 + 
                                                     (worker.position[1] - r.position[1])**2)
                            worker.gather(nearest)
                except Exception as e:
                    print(f"Error in enemy worker AI: {e}")
            
            # Phase 2: Build unit building if enough resources
            if not enemy_unit_buildings and self.resources[1] >= self.unit_building_cost:
                try:
                    # Find a good position near command center
                    if enemy_command_centers:
                        cc = enemy_command_centers[0]
                        offset_x = random.randint(-100, 100)
                        offset_y = random.randint(-100, 100)
                        pos = (cc.position[0] + offset_x, cc.position[1] + offset_y)
                        
                        # Build unit building
                        self.resources[1] -= self.unit_building_cost
                        self.add_entity(UnitBuilding(pos, player_id=1))
                except Exception as e:
                    print(f"Error in enemy building construction: {e}")
        
            # Phase 3: Produce units if possible
            for building in enemy_unit_buildings:
                try:
                    if not building.production_queue and self.resources[1] >= 50:
                        unit_type = random.choice([Dot, Triangle])
                        building.produce(unit_type)
                        self.resources[1] -= 50
                except Exception as e:
                    print(f"Error in enemy unit production: {e}")
            
            # Phase 4: Attack with combat units
            idle_combat_units = [unit for unit in enemy_combat_units 
                                if isinstance(unit.current_behavior, behaviors.IdleBehavior)]
                                
            if idle_combat_units and random.random() < 0.01:  # 1% chance per update to start attack
                try:
                    # Find player targets
                    player_units = [e for e in self.entities 
                                  if hasattr(e, 'player_id') and e.player_id == 0]
                                  
                    if player_units:
                        # Choose a random target
                        target = random.choice(player_units)
                        
                        # Order all idle combat units to attack
                        for unit in idle_combat_units:
                            unit.attack(target)
                except Exception as e:
                    print(f"Error in enemy combat unit AI: {e}")
                    
        except Exception as e:
            print(f"Error in enemy AI: {e}")
    
    def render(self, screen, renderer):
        """Render the game state."""
        # Clear screen
        screen.fill(BLACK)
        
        # Render all entities
        for entity in self.entities:
            entity.render(renderer)
        
        # Render selection box if selecting
        if self.is_selecting and self.selection_start and self.selection_end:
            renderer.draw_selection_box(self.selection_start, self.selection_end)
        
        # Render building preview if in build mode
        if self.build_mode and pygame.mouse.get_pos()[1] < self.screen_height - self.ui_panel_height:
            self._render_building_preview(screen, renderer, pygame.mouse.get_pos())
        
        # Render attack-move cursor if in attack-move mode
        if self.attack_move_mode and pygame.mouse.get_pos()[1] < self.screen_height - self.ui_panel_height:
            self._render_attack_move_cursor(screen, renderer, pygame.mouse.get_pos())
        
        # Render UI
        self._render_ui(screen, renderer)
        
        # Render pause enemy button at the top right
        button_color = RED if self.enemy_ai_paused else GREEN
        pygame.draw.rect(screen, button_color, self.pause_enemy_button)
        button_text = "ENEMY PAUSED" if self.enemy_ai_paused else "PAUSE ENEMY"
        self.font_small.render_to(screen, 
                                 (self.pause_enemy_button.x + 10, self.pause_enemy_button.y + 8), 
                                 button_text, WHITE)
        
        # Render debug info
        if self.show_debug:
            self._render_debug(screen, renderer)
        
        # Render game over screen
        if self.game_over:
            self._render_game_over(screen, renderer)
    
    def _render_building_preview(self, screen, renderer, pos):
        """Render a preview of the building at the mouse position."""
        if self.build_type == "unit_building":
            # Draw a semi-transparent preview
            pygame.draw.polygon(screen, (*YELLOW, 128),  # RGBA with 50% alpha
                               [(pos[0] - 30, pos[1] - 30), 
                                (pos[0] + 30, pos[1] - 30),
                                (pos[0] + 30, pos[1] + 30),
                                (pos[0] - 30, pos[1] + 30)])
        elif self.build_type == "turret":
            # Draw a semi-transparent hexagon for turret
            points = []
            size = 20
            for i in range(6):
                angle = math.pi/3 * i
                x = pos[0] + math.cos(angle) * size
                y = pos[1] + math.sin(angle) * size
                points.append((int(x), int(y)))
            
            # Draw the hexagon with semi-transparency
            pygame.draw.polygon(screen, (*GREEN, 128), points)
            
            # Draw a line for the turret barrel
            pygame.draw.line(screen, (255, 255, 255, 128), 
                            pos, 
                            (pos[0] + size, pos[1]), 
                            3)
            
            # Draw attack range indicator
            pygame.draw.circle(screen, (255, 255, 255, 30), pos, 150, 1)
    
    def _render_attack_move_cursor(self, screen, renderer, pos):
        """Render a custom cursor for attack-move mode."""
        # Draw a red targeting reticle
        pygame.draw.circle(screen, RED, pos, 15, 2)
        pygame.draw.line(screen, RED, (pos[0] - 20, pos[1]), (pos[0] + 20, pos[1]), 2)
        pygame.draw.line(screen, RED, (pos[0], pos[1] - 20), (pos[0], pos[1] + 20), 2)
    
    def _render_ui(self, screen, renderer):
        """Render the game UI."""
        # Draw the bottom UI panel
        pygame.draw.rect(screen, (50, 50, 50), 
                         (0, self.screen_height - self.ui_panel_height, 
                          self.screen_width, self.ui_panel_height))
        
        # Draw minimap on the left
        pygame.draw.rect(screen, (0, 0, 0), 
                         (10, self.screen_height - self.ui_panel_height + 10, 
                          self.minimap_size, self.minimap_size - 20))
        
        # Draw command card on the right
        pygame.draw.rect(screen, (30, 30, 30), 
                         (self.screen_width - self.command_card_size, 
                          self.screen_height - self.ui_panel_height, 
                          self.command_card_size, self.ui_panel_height))
        
        # Resource display
        resource_text = f"Resources: {self.resources[0]}"
        self.font_medium.render_to(screen, (self.screen_width / 2 - 100, self.screen_height - self.ui_panel_height + 10), 
                                 resource_text, WHITE)
        
        # Render command buttons based on selection
        self._render_command_buttons(screen)
        
        # Render minimap
        self._render_minimap(screen)
    
    def _render_command_buttons(self, screen):
        """Render command buttons based on current selection."""
        # Determine which buttons to show based on selection
        selected_types = set()
        for entity in self.selected_entities:
            if isinstance(entity, Square) and entity.player_id == 0:
                selected_types.add("worker")
            elif isinstance(entity, (Dot, Triangle)) and entity.player_id == 0:
                selected_types.add("combat")
            elif isinstance(entity, CommandCenter) and entity.player_id == 0:
                selected_types.add("command_center")
            elif isinstance(entity, UnitBuilding) and entity.player_id == 0:
                selected_types.add("unit_building")
        
        # Position variables
        button_size = 40
        button_margin = 5
        card_start_x = self.screen_width - self.command_card_size + button_margin
        card_start_y = self.screen_height - self.ui_panel_height + button_margin
        
        # Create visible command buttons based on selection
        self.command_buttons = []
        
        # If worker is selected
        if "worker" in selected_types:
            self._add_command_button("move", 0, 0)
            self._add_command_button("gather", 1, 0)
            self._add_command_button("build", 2, 0)
        
        # If combat unit is selected
        elif "combat" in selected_types:
            self._add_command_button("attack", 0, 0)
            self._add_command_button("hold", 1, 0)
            self._add_command_button("patrol", 2, 0)
        
        # If command center is selected
        elif "command_center" in selected_types:
            self._add_command_button("square", 0, 0)
        
        # If unit building is selected
        elif "unit_building" in selected_types:
            self._add_command_button("dot", 0, 0)
            self._add_command_button("triangle", 1, 0)
        
        # Render all visible buttons
        for button in self.command_buttons:
            # Draw button background
            pygame.draw.rect(screen, button["color"], button["rect"])
            
            # Draw button text
            self.font_small.render_to(
                screen,
                (button["rect"].x + 15, button["rect"].y + 12),
                button["text"],
                WHITE
            )
            
            # Draw tooltip if mouse is over button
            mouse_pos = pygame.mouse.get_pos()
            if button["rect"].collidepoint(mouse_pos):
                tooltip_bg = pygame.Rect(
                    mouse_pos[0] + 10,
                    mouse_pos[1] - 30,
                    len(button["tooltip"]) * 7,
                    25
                )
                pygame.draw.rect(screen, (50, 50, 50), tooltip_bg)
                self.font_small.render_to(
                    screen,
                    (mouse_pos[0] + 15, mouse_pos[1] - 25),
                    button["tooltip"],
                    WHITE
                )
    
    def _add_command_button(self, button_id, col, row):
        """Add a command button to the visible list."""
        button_size = 40
        button_margin = 5
        card_start_x = self.screen_width - self.command_card_size + button_margin
        card_start_y = self.screen_height - self.ui_panel_height + button_margin
        
        # Get button data
        button_data = self.all_buttons[button_id].copy()
        
        # Calculate position based on col/row
        x = card_start_x + (button_size + button_margin) * col
        y = card_start_y + (button_size + button_margin) * row
        
        # Create rectangle for the button
        button_data["rect"] = pygame.Rect(x, y, button_size, button_size)
        
        # Add to visible buttons
        self.command_buttons.append(button_data)
    
    def _render_minimap(self, screen):
        """Render a minimap showing entities."""
        minimap_rect = pygame.Rect(10, self.screen_height - self.ui_panel_height + 10, 
                                  self.minimap_size, self.minimap_size - 20)
        pygame.draw.rect(screen, (0, 0, 0), minimap_rect)
        pygame.draw.rect(screen, (100, 100, 100), minimap_rect, 1)
        
        # Calculate scale factors for the entire world map
        scale_x = minimap_rect.width / self.world_width
        scale_y = minimap_rect.height / self.world_height
        
        # Draw entities on minimap
        for entity in self.entities:
            # Skip entities with no position
            if not hasattr(entity, 'position'):
                continue
                
            # Calculate minimap position
            mini_x = minimap_rect.x + entity.position[0] * scale_x
            mini_y = minimap_rect.y + entity.position[1] * scale_y
            
            # Determine color and size based on entity type
            color = WHITE
            size = 1
            
            if isinstance(entity, Resource):
                color = CYAN
                size = 1
            elif isinstance(entity, Building):
                if entity.player_id == 0:
                    color = BLUE
                else:
                    color = RED
                size = 3
            elif isinstance(entity, Unit):
                if entity.player_id == 0:
                    color = GREEN
                else:
                    color = RED
                size = 1
            
            # Draw the entity on the minimap
            if 0 <= mini_x <= minimap_rect.right and 0 <= mini_y <= minimap_rect.bottom:
                pygame.draw.circle(screen, color, (int(mini_x), int(mini_y)), size)
        
        # Draw the current viewport as a rectangle
        viewport_rect = pygame.Rect(
            minimap_rect.x + self.camera_offset[0] * scale_x,
            minimap_rect.y + self.camera_offset[1] * scale_y,
            self.screen_width * scale_x,
            (self.screen_height - self.ui_panel_height) * scale_y
        )
        pygame.draw.rect(screen, (255, 255, 255), viewport_rect, 1)
        
        # Handle minimap clicks to move the camera
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        
        if mouse_buttons[0] and minimap_rect.collidepoint(mouse_pos):
            # Calculate world position from minimap click
            world_x = (mouse_pos[0] - minimap_rect.x) / scale_x
            world_y = (mouse_pos[1] - minimap_rect.y) / scale_y
            
            # Center the camera on the clicked position
            self.camera_offset[0] = max(0, min(world_x - self.screen_width/2, self.world_width - self.screen_width))
            self.camera_offset[1] = max(0, min(world_y - self.screen_height/2, self.world_height - self.screen_height))
    
    def _render_debug(self, screen, renderer):
        """Render debug information."""
        # Entity count
        entity_count = len(self.entities)
        text = f"Entities: {entity_count}"
        self.font_small.render_to(screen, (10, 40), text, WHITE)
        
        # FPS (calculate outside)
        fps_text = f"FPS: {pygame.time.Clock().get_fps():.1f}"
        self.font_small.render_to(screen, (10, 60), fps_text, WHITE)
        
        # Selected entities info
        if self.selected_entities:
            y_offset = 80
            for i, entity in enumerate(self.selected_entities[:5]):  # Show max 5
                entity_class = entity.__class__.__name__
                entity_pos = f"({entity.position[0]:.0f}, {entity.position[1]:.0f})"
                
                if hasattr(entity, 'health'):
                    health_text = f" HP: {entity.health:.0f}/{entity.max_health:.0f}"
                else:
                    health_text = ""
                
                info_text = f"[{i}] {entity_class}{health_text} at {entity_pos}"
                self.font_small.render_to(screen, (10, y_offset), info_text, WHITE)
                y_offset += 20
    
    def _render_game_over(self, screen, renderer):
        """Render game over screen."""
        # Transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = "GAME OVER"
        game_over_rect = self.font_large.get_rect(game_over_text)
        game_over_rect.center = (self.screen_width/2, self.screen_height/2 - 40)
        
        if self.winner == 0:
            result_text = "Player Wins!"
            result_color = GREEN
        else:
            result_text = "Enemy Wins!"
            result_color = RED
            
        result_rect = self.font_large.get_rect(result_text)
        result_rect.center = (self.screen_width/2, self.screen_height/2 + 20)
        
        restart_text = "Press R to restart or ESC to quit"
        restart_rect = self.font_medium.get_rect(restart_text)
        restart_rect.center = (self.screen_width/2, self.screen_height/2 + 80)
        
        self.font_large.render_to(screen, game_over_rect, game_over_text, WHITE)
        self.font_large.render_to(screen, result_rect, result_text, result_color)
        self.font_medium.render_to(screen, restart_rect, restart_text, WHITE)
    
    def handle_event(self, event):
        """Handle an input event."""
        if event.type == pygame.QUIT:
            return False
        
        # Handle keyboard events
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # If in a special mode, cancel it
                if self.build_mode or self.attack_move_mode:
                    self.build_mode = False
                    self.build_type = None
                    self.attack_move_mode = False
                    self.print_debug_info("Command canceled")
                # Otherwise deselect everything
                else:
                    self._deselect_all()
                    self.print_debug_info("All units deselected")
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_p:  # Add keyboard shortcut for pausing enemy
                self.enemy_ai_paused = not self.enemy_ai_paused
                self.print_debug_info(f"Enemy AI {'paused' if self.enemy_ai_paused else 'resumed'}")
            elif event.key == pygame.K_F3:
                self.show_debug = not self.show_debug
            elif event.key == pygame.K_r and self.game_over:
                self._restart_game()
            elif event.key == pygame.K_q:  # Add Q as quit
                return False
            else:
                self._handle_key_command(event.key)
        
        # Handle mouse events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on pause enemy button
                if self.pause_enemy_button.collidepoint(event.pos):
                    self.enemy_ai_paused = not self.enemy_ai_paused
                    self.print_debug_info(f"Enemy AI {'paused' if self.enemy_ai_paused else 'resumed'}")
                    return True
                
                self._handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left release
                self._handle_left_release(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_selecting:
                self.selection_end = event.pos
        
        return True
    
    def _handle_key_command(self, key):
        """Handle keyboard command inputs."""
        # Look for buttons with this key
        for button_id, button in self.all_buttons.items():
            if button["key"] == key:
                self._execute_command(button_id)
                return
        
        # If no button found, check additional global commands
        if key == pygame.K_b:
            self._execute_command("build")
        elif key == pygame.K_u:
            # If in build selection mode, select unit building
            if self.build_mode and self.build_type == "select":
                self._execute_command("build_unit_building")
        elif key == pygame.K_t:
            # If in build selection mode, select turret
            if self.build_mode and self.build_type == "select":
                self._execute_command("build_turret")
    
    def _execute_command(self, command_type):
        """Execute a command based on its type."""
        # Worker commands
        if command_type == "build":
            workers_selected = any(isinstance(e, Square) and e.player_id == 0 for e in self.selected_entities)
            if workers_selected and self.resources[0] >= self.unit_building_cost:
                self.build_mode = True
                self.build_type = "select"
                self.print_debug_info("Entered build mode - select building type (U: Unit Building, T: Turret)")
        
        elif command_type == "build_unit_building":
            workers_selected = any(isinstance(e, Square) and e.player_id == 0 for e in self.selected_entities)
            if workers_selected and self.resources[0] >= self.unit_building_cost:
                self.build_mode = True
                self.build_type = "unit_building"
                self.print_debug_info("Building Unit Building - click to place")
                
        elif command_type == "build_turret":
            workers_selected = any(isinstance(e, Square) and e.player_id == 0 for e in self.selected_entities)
            if workers_selected and self.resources[0] >= 100:  # Turret cost
                self.build_mode = True
                self.build_type = "turret"
                self.print_debug_info("Building Turret - click to place")
        
        # Combat unit commands
        elif command_type == "attack":
            combat_units = [e for e in self.selected_entities 
                           if isinstance(e, (Dot, Triangle)) and e.player_id == 0]
            if combat_units:
                self.attack_move_mode = True
                # Change cursor to attack cursor
                pygame.mouse.set_visible(False)  # Hide default cursor
                self.print_debug_info("Attack-move mode - click target location with left or right button")
        
        elif command_type == "patrol":
            combat_units = [e for e in self.selected_entities 
                          if isinstance(e, (Dot, Triangle)) and e.player_id == 0]
            if combat_units:
                self.patrol_mode = True
                self.print_debug_info("Patrol mode - click target location")
        
        elif command_type == "hold":
            combat_units = [e for e in self.selected_entities 
                          if isinstance(e, Unit) and e.player_id == 0]
            for unit in combat_units:
                # Create and assign a hold position behavior
                hold_behavior = behaviors.HoldPositionBehavior(unit)
                unit.current_behavior = hold_behavior
                self.print_debug_info(f"Unit holding position at {unit.position}")
        
        # Building production commands
        elif command_type == "square":
            selected_buildings = [e for e in self.selected_entities if isinstance(e, CommandCenter)]
            if selected_buildings:
                selected_buildings[0].produce("square")
                self.print_debug_info("Producing a Square worker")
        
        elif command_type == "dot":
            selected_buildings = [e for e in self.selected_entities if isinstance(e, UnitBuilding)]
            if selected_buildings:
                selected_buildings[0].produce("dot")
                self.print_debug_info("Producing a Dot unit")
        
        elif command_type == "triangle":
            selected_buildings = [e for e in self.selected_entities if isinstance(e, UnitBuilding)]
            if selected_buildings:
                selected_buildings[0].produce("triangle")
                self.print_debug_info("Producing a Triangle unit")
    
    def _handle_left_click(self, pos):
        """Handle left mouse button click."""
        if self.game_over:
            return
        
        # Check if clicking on pause enemy button
        if self.pause_enemy_button.collidepoint(pos):
            self.enemy_ai_paused = not self.enemy_ai_paused
            self.print_debug_info(f"Enemy AI {'paused' if self.enemy_ai_paused else 'resumed'}")
            return True
        
        # Check if clicking in UI area
        if pos[1] > self.screen_height - self.ui_panel_height:
            if self._handle_ui_click(pos):
                return
            return
        
        # If in build mode, try to place the building
        if self.build_mode:
            if self.build_type == "unit_building":
                if self._try_build_unit_building(pos):
                    self.build_mode = False
                    self.build_type = None
                return
            elif self.build_type == "turret":
                if self._try_build_turret(pos):
                    self.build_mode = False
                    self.build_type = None
                return
        
        # If in attack-move mode, set attack-move target
        if self.attack_move_mode:
            self._execute_attack_move(pos)
            return
        
        # If in patrol mode, set patrol target
        if self.patrol_mode:
            self._execute_patrol(pos)
            return
        
        # Otherwise handle normal selection
        self.selection_start = pos
        self.selection_end = pos
        self.is_selecting = True
    
    def _handle_left_release(self, pos):
        """Handle left mouse button release."""
        if self.game_over:
            return
        
        self.is_selecting = False
        
        # If it's a click (start == end approximately)
        if (abs(self.selection_start[0] - pos[0]) < 5 and 
            abs(self.selection_start[1] - pos[1]) < 5):
            self._handle_selection_click(pos)
        else:
            # It's a selection box
            self._handle_selection_box(self.selection_start, pos)
    
    def _handle_selection_click(self, pos):
        """Handle selecting a single entity with a click."""
        # Deselect all if no shift key
        if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
            for entity in self.selected_entities:
                entity.deselect()
            self.selected_entities = []
        
        # Check for entity at click position (prioritize units and buildings over resources)
        clicked_entities = []
        
        # First pass: check buildings and units
        for entity in self.entities:
            if (hasattr(entity, 'player_id') and entity.player_id == 0 and 
                entity.contains_point(pos)):
                clicked_entities.append(entity)
        
        # Second pass: if no buildings or units, check resources
        if not clicked_entities:
            for entity in self.entities:
                if isinstance(entity, Resource) and entity.contains_point(pos):
                    clicked_entities.append(entity)
        
        # Select the first (top) entity
        if clicked_entities:
            entity = clicked_entities[0]
            entity.select()
            self.selected_entities.append(entity)
    
    def _handle_selection_box(self, start, end):
        """Handle selecting multiple entities with a selection box."""
        # Create a rect for the selection box
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        width = abs(start[0] - end[0])
        height = abs(start[1] - end[1])
        selection_rect = pygame.Rect(x, y, width, height)
        
        # Deselect all if no shift key
        if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
            for entity in self.selected_entities:
                entity.deselect()
            self.selected_entities = []
        
        # Select all player units and buildings in the box
        for entity in self.entities:
            if (hasattr(entity, 'player_id') and entity.player_id == 0 and 
                selection_rect.colliderect(entity.rect)):
                if entity not in self.selected_entities:
                    entity.select()
                    self.selected_entities.append(entity)
    
    def _handle_right_click(self, pos):
        """Handle right mouse button click."""
        if self.game_over or not self.selected_entities:
            return
        
        # Check if clicking in UI area
        if pos[1] > self.screen_height - self.ui_panel_height:
            return
        
        # If in attack-move mode, set attack-move target
        if self.attack_move_mode:
            self._execute_attack_move(pos)
            return
        
        # Check if clicked on an entity
        target_entity = None
        for entity in self.entities:
            if hasattr(entity, 'contains_point') and entity.contains_point(pos):
                target_entity = entity
                break
        
        # If we have a target entity
        if target_entity:
            # If target is a resource, gather resources
            if isinstance(target_entity, Resource):
                found_workers = False
                for entity in self.selected_entities:
                    if isinstance(entity, Square) and entity.player_id == 0:
                        self.print_debug_info(f"Ordering worker to gather from resource with {target_entity.amount} remaining")
                        entity.gather(target_entity)
                        found_workers = True
                
                if not found_workers:
                    self.print_debug_info("No workers selected to gather resources")
            
            # If target is an enemy unit or building, attack it
            elif hasattr(target_entity, 'player_id') and target_entity.player_id == 1:
                found_attackers = False
                for entity in self.selected_entities:
                    if (isinstance(entity, (Dot, Triangle)) and entity.player_id == 0 and 
                        hasattr(entity, 'attack_damage') and entity.attack_damage > 0):
                        self.print_debug_info(f"Ordering attack on enemy {type(target_entity).__name__}")
                        entity.attack(target_entity)
                        found_attackers = True
                
                if not found_attackers:
                    self.print_debug_info("No combat units selected to attack")
            
            # If target is a friendly building, just select it
            elif hasattr(target_entity, 'player_id') and target_entity.player_id == 0:
                self._handle_selection_click(pos)
        
        # No target entity, move units
        else:
            # Move selected units with formation spreading
            selected_units = [e for e in self.selected_entities if isinstance(e, Unit) and e.player_id == 0]
            
            if len(selected_units) > 1:
                try:
                    # Calculate formation radius based on number of units
                    # More units = bigger formation, but less dramatic spacing
                    num_units = len(selected_units)
                    formation_radius = max(20, 10 * (num_units ** 0.5))
                    
                    # Calculate positions in a rough circle/grid formation around the target
                    for i, entity in enumerate(selected_units):
                        # Safety check to prevent division by zero
                        if num_units <= 0:
                            entity.move_to(pos)
                            continue
                            
                        # Calculate angle for circular formation
                        angle = (i / num_units) * 2 * 3.14159
                        
                        # Calculate offset from center
                        offset_x = formation_radius * math.cos(angle)
                        offset_y = formation_radius * math.sin(angle)
                        
                        # Calculate final position with slight random variation
                        # Random variation helps prevent units from getting symmetrically stuck
                        random_offset = 5.0  # Small random offset to prevent exact symmetrical formations
                        final_pos = (
                            pos[0] + offset_x + random.uniform(-random_offset, random_offset),
                            pos[1] + offset_y + random.uniform(-random_offset, random_offset)
                        )
                        
                        # Ensure positions are valid numbers
                        if (isinstance(final_pos[0], (int, float)) and 
                            isinstance(final_pos[1], (int, float)) and
                            not math.isnan(final_pos[0]) and 
                            not math.isnan(final_pos[1])):
                            # Order unit to move
                            entity.move_to(final_pos)
                        else:
                            # Use original position as fallback
                            entity.move_to(pos)
                except Exception as e:
                    # If formation calculation fails, fall back to simple movement
                    print(f"Formation calculation error: {e}")
                    for entity in selected_units:
                        entity.move_to(pos)
            else:
                # For single unit, just move to the exact position
                for entity in selected_units:
                    entity.move_to(pos)
            
            # Set rally points for selected buildings
            for entity in self.selected_entities:
                if isinstance(entity, Building) and entity.player_id == 0:
                    entity.set_rally_point(pos)
    
    def _handle_ui_click(self, pos):
        """Handle clicking on UI elements."""
        # Check if click is on a command button
        for button in self.command_buttons:
            if button["rect"].collidepoint(pos):
                self._execute_command(button["type"])
                return True
        
        return False
    
    def _try_build_unit_building(self, pos=None):
        """Try to build a unit building at the given position."""
        # Check if we have enough resources
        if self.resources[0] < self.unit_building_cost:
            self.print_debug_info("Not enough resources to build a unit building")
            return False
        
        # Find selected or nearby workers
        workers = [e for e in self.selected_entities if isinstance(e, Square) and e.player_id == 0]
        
        if not workers:
            self.print_debug_info("No workers selected to build")
            return False
        
        # If position is provided, find the closest worker to that position
        if pos:
            closest_worker = min(workers, key=lambda w: distance(w.position, pos))
            
            # Check if worker is close enough to build
            if distance(closest_worker.position, pos) > 150:  # Maximum build distance
                self.print_debug_info("Worker too far from build location")
                return False
                
            # Use this worker to build
            worker = closest_worker
        else:
            # Just use the first selected worker
            worker = workers[0]
            # Generate a position near the worker
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            pos = (worker.position[0] + offset_x, worker.position[1] + offset_y)
        
        # Build unit building and consume the worker (Zerg-style)
        self.resources[0] -= self.unit_building_cost
        
        # Create the building at the worker's position rather than the clicked position
        build_position = worker.position
        
        # Remove the worker
        self.print_debug_info(f"Worker {worker} morphing into building at {build_position}")
        self.remove_entity(worker)
        
        # Create the new building
        new_building = UnitBuilding(build_position, player_id=0)
        self.add_entity(new_building)
        
        # Select the new building
        self._select_single_entity(new_building)
        
        self.print_debug_info("Building created successfully")
        return True
        
    def _select_single_entity(self, entity):
        """Select a single entity, deselecting all others."""
        # Deselect all current selections
        for e in self.selected_entities:
            e.deselect()
        self.selected_entities = []
        
        # Select the new entity
        entity.select()
        self.selected_entities.append(entity)
    
    def _try_build_turret(self, pos=None):
        """Try to build a defensive turret at the given position."""
        # Define turret cost
        turret_cost = 100
        
        # Check if we have enough resources
        if self.resources[0] < turret_cost:
            self.print_debug_info("Not enough resources to build a turret")
            return False
        
        # Find selected or nearby workers
        workers = [e for e in self.selected_entities if isinstance(e, Square) and e.player_id == 0]
        
        if not workers:
            self.print_debug_info("No workers selected to build")
            return False
        
        # If position is provided, find the closest worker to that position
        if pos:
            closest_worker = min(workers, key=lambda w: distance(w.position, pos))
            
            # Check if worker is close enough to build
            if distance(closest_worker.position, pos) > 150:  # Maximum build distance
                self.print_debug_info("Worker too far from build location")
                return False
                
            # Use this worker to build
            worker = closest_worker
        else:
            # Just use the first selected worker
            worker = workers[0]
            # Generate a position near the worker
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            pos = (worker.position[0] + offset_x, worker.position[1] + offset_y)
        
        # Build turret and consume the worker
        self.resources[0] -= turret_cost
        
        # Create the building at the specified position
        build_position = pos
        
        # Remove the worker
        self.print_debug_info(f"Worker {worker} building turret at {build_position}")
        self.remove_entity(worker)
        
        # Create the new turret
        new_turret = Turret(build_position, player_id=0)
        self.add_entity(new_turret)
        return True
    
    def _restart_game(self):
        """Restart the game."""
        self.entities = []
        self.selected_entities = []
        self.resources = [200, 200]
        self.game_over = False
        self.winner = None
        self.build_mode = False
        self.build_type = None
        self.attack_move_mode = False
        self.patrol_mode = False
        self._init_map()

    def print_debug_info(self, message):
        """Print debug info if debug is enabled."""
        if self.show_debug:
            print(message)

    def _deselect_all(self):
        """Deselect all selected entities."""
        for entity in self.selected_entities:
            entity.deselect()
        self.selected_entities = []
    
    def _execute_attack_move(self, pos):
        """Execute attack-move command to the target position."""
        combat_units = [e for e in self.selected_entities 
                      if isinstance(e, (Dot, Triangle)) and e.player_id == 0]
        
        for unit in combat_units:
            unit.current_behavior = behaviors.AttackMoveBehavior(unit, pos)
        
        self.attack_move_mode = False
        pygame.mouse.set_visible(True)  # Show default cursor again
        self.print_debug_info(f"Units attacking-moving to {pos}")
    
    def _execute_patrol(self, pos):
        """Set patrol target for selected units."""
        # Convert screen position to world position
        world_pos = self._screen_to_world(pos)
        
        # Get selected combat units
        combat_units = [e for e in self.selected_entities 
                       if isinstance(e, (Dot, Triangle)) and e.player_id == 0]
        
        # Set patrol behavior for each unit
        for unit in combat_units:
            # Store current position as the start of patrol route
            start_position = unit.position.copy()
            # Create patrol behavior
            unit.current_behavior = PatrolBehavior(unit, start_position, world_pos)
        
        # Exit patrol mode
        self.patrol_mode = False
        
        # Show visual feedback
        if combat_units:
            self.print_debug_info(f"Units patrolling to {world_pos[0]:.0f}, {world_pos[1]:.0f}") 