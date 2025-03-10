import pygame
import math
import random
from utils import distance, angle_between, normalize, create_square, create_triangle
from utils import WHITE, RED, GREEN, BLUE, YELLOW, CYAN
from behaviors import IdleBehavior, MoveBehavior, GatherBehavior, AttackBehavior, HoldPositionBehavior, AttackMoveBehavior, PatrolBehavior
from typing import List, Tuple, Optional, Union, Dict, Any
from config import UnitConfig, BuildingConfig, ResourceConfig, MovementConfig

# Import the game instance for debug rendering
# We'll use a function to avoid circular imports
def get_game_instance():
    from game import Game
    return Game.instance

class Entity:
    """Base class for all game entities."""
    
    def __init__(self, position, size, color=WHITE):
        self.position = list(position)
        self.size = size
        self.color = color
        self.selected = False
        self.rect = pygame.Rect(position[0] - size/2, position[1] - size/2, size, size)
        self.angle = 0  # Orientation in radians
    
    def update(self, dt):
        """Update entity state. Called every frame."""
        # Update collision rect
        self.rect.x = self.position[0] - self.size/2
        self.rect.y = self.position[1] - self.size/2
    
    def render(self, renderer):
        """Render the entity using the vector renderer."""
        pass
    
    def select(self):
        """Select this entity."""
        self.selected = True
    
    def deselect(self):
        """Deselect this entity."""
        self.selected = False
    
    def contains_point(self, point):
        """Check if this entity contains the given point."""
        return distance(self.position, point) <= self.size/2


class Resource(Entity):
    """Resource entity (minerals)."""
    
    def __init__(self, position, amount=500):
        super().__init__(position, 30, CYAN)
        self.amount = amount
        self.max_amount = amount
        self.slots = [None, None, None, None]  # Up to 4 workers can mine at once
        self.slot_positions = self._calculate_slot_positions()
    
    def _calculate_slot_positions(self):
        """Calculate positions for up to 4 workers to mine this resource (aligned with sides)."""
        # Calculate positions aligned with the 4 sides of the square
        half_size = self.size / 2
        slot_offset = self.size * 0.75  # Position workers slightly outside the resource
        
        return [
            (self.position[0], self.position[1] - slot_offset),  # Top
            (self.position[0] + slot_offset, self.position[1]),  # Right
            (self.position[0], self.position[1] + slot_offset),  # Bottom
            (self.position[0] - slot_offset, self.position[1]),  # Left
        ]
    
    def get_available_slot(self):
        """Find an available harvesting slot or return None if all are occupied."""
        for i, worker in enumerate(self.slots):
            if worker is None:
                return i
        return None
    
    def assign_worker_to_slot(self, worker, slot_index):
        """Assign a worker to a specific slot."""
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index] = worker
    
    def release_worker_from_slot(self, worker):
        """Release a worker from its slot."""
        try:
            for i, w in enumerate(self.slots):
                if w == worker:
                    self.slots[i] = None
                    return True
            return False
        except Exception as e:
            print(f"Error in release_worker_from_slot: {e}")
            return False
    
    def get_slot_position(self, slot_index):
        """Get the position for a specific harvesting slot."""
        try:
            if 0 <= slot_index < len(self.slot_positions):
                return self.slot_positions[slot_index]
            return self.position  # Default to resource center if invalid
        except Exception as e:
            print(f"Error in get_slot_position: {e}")
            return self.position  # Return center position as fallback
    
    def assign_harvest_slot(self, worker):
        """Assign a worker to an available harvesting slot, snapping them to the resource face.
           Returns the slot position if successful, or None if no slot is available."""
        try:
            slot_index = self.get_available_slot()
            if slot_index is not None:
                self.assign_worker_to_slot(worker, slot_index)
                return self.get_slot_position(slot_index)
            return None
        except Exception as e:
            print(f"Error in assign_harvest_slot: {e}")
            return None
    
    def extract(self, amount):
        """Extract resources and return the amount extracted."""
        if self.amount <= 0:
            return 0
        
        actual_amount = min(amount, self.amount)
        self.amount -= actual_amount
        
        # Adjust size based on remaining amount
        scale_factor = self.amount / self.max_amount
        self.size = max(15, 30 * scale_factor)  # Minimum size of 15
        
        # Update the rect
        self.rect = pygame.Rect(
            self.position[0] - self.size/2,
            self.position[1] - self.size/2,
            self.size,
            self.size
        )
        
        return actual_amount
    
    def render(self, renderer):
        """Render the resource as a square."""
        # Skip if depleted
        if self.amount <= 0:
            return
        
        # Draw as a square
        points = [
            (self.position[0] - self.size/2, self.position[1] - self.size/2),
            (self.position[0] + self.size/2, self.position[1] - self.size/2),
            (self.position[0] + self.size/2, self.position[1] + self.size/2),
            (self.position[0] - self.size/2, self.position[1] + self.size/2)
        ]
        
        # Draw filled square with border
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 1, False)
        
        # Draw amount text if selected
        if self.selected:
            renderer.draw_text(f"{self.amount}", 
                              (self.position[0], self.position[1] - self.size - 10), 
                              WHITE)
        
        # Draw slot positions and connecting lines
        game_instance = get_game_instance()
        if game_instance and game_instance.show_debug:
            # Draw slots
            for i, slot_pos in enumerate(self.slot_positions):
                # Color based on slot status (green=available, red=occupied)
                color = GREEN if self.slots[i] is None else RED
                renderer.draw_circle(slot_pos, 5, color, 1, False)
                
                # Draw line connecting slot to resource
                renderer.draw_line(self.position, slot_pos, color, 1)


class Unit(Entity):
    """Base class for all units."""
    
    def __init__(self, position, size, color, max_health, speed, player_id=0):
        super().__init__(position, size, color)
        self.max_health = max_health
        self.health = max_health
        self.speed = speed
        self.target_position = None
        self.player_id = player_id  # 0 for player, 1 for enemy
        self.carrying_resources = 0
        self.max_carry_capacity = 10
        self.attack_cooldown = 0
        self.attack_range = 0          # Range where unit can attack
        self.aggro_range = 0           # Range where unit detects and engages enemies
        self.attack_cooldown_max = 0
        self.attack_damage = 0
        self.collision_radius = size/2  # Radius for collision detection
        
        # Visual effects
        self.show_gather_effect = False
        self.show_attack_effect = False
        self.effect_timer = 0
        
        # Behavior system
        self.current_behavior = IdleBehavior(self)
    
    def update(self, dt):
        """Update unit state."""
        # Call parent update
        super().update(dt)
        
        try:
            # Update visual effects
            if self.show_gather_effect or self.show_attack_effect:
                self.effect_timer += dt
                if self.effect_timer > 0.2:  # Show effect for 0.2 seconds
                    self.show_gather_effect = False
                    self.show_attack_effect = False
                    self.effect_timer = 0
            
            # Save original position for collision resolution
            original_position = list(self.position)
            
            # Update position based on velocity (for physics effects)
            if hasattr(self, 'velocity'):
                self.position[0] += self.velocity[0] * dt
                self.position[1] += self.velocity[1] * dt
                
                # Dampen velocity over time
                self.velocity[0] *= 0.9
                self.velocity[1] *= 0.9
                
                # If velocity is very small, zero it out to prevent jitter
                if abs(self.velocity[0]) < 0.1 and abs(self.velocity[1]) < 0.1:
                    self.velocity[0] = 0
                    self.velocity[1] = 0
            
            # Update attack cooldown
            if self.attack_cooldown > 0:
                self.attack_cooldown -= dt
            
            # Update behavior
            if self.current_behavior:
                try:
                    # Update behavior state
                    behavior_complete = self.current_behavior.update(dt)
                    
                    # If behavior is complete, switch to idle
                    if behavior_complete:
                        # Safely exit the current behavior
                        try:
                            if hasattr(self.current_behavior, 'exit'):
                                self.current_behavior.exit()
                        except Exception as e:
                            print(f"Error during behavior exit: {e}")
                        
                        # Switch to idle behavior
                        from behaviors import IdleBehavior
                        self.current_behavior = IdleBehavior(self)
                except Exception as e:
                    print(f"Error during behavior update: {e}")
                    # Fall back to idle on error
                    from behaviors import IdleBehavior
                    self.current_behavior = IdleBehavior(self)
            
            # Update collision rect
            self.rect.x = self.position[0] - self.size/2
            self.rect.y = self.position[1] - self.size/2
            
            # Resolve collisions with other entities
            self._resolve_unit_collisions()
            
            # Auto-engage enemies in aggro range if idle
            from behaviors import IdleBehavior
            if isinstance(self.current_behavior, IdleBehavior) and self.aggro_range > 0:
                try:
                    self._check_for_enemies_in_range()
                except Exception as e:
                    print(f"Error checking for enemies: {e}")
        except Exception as e:
            print(f"Error in unit update: {e}")
    
    def _resolve_unit_collisions(self):
        """Prevent units from overlapping with other entities.
           Units should never be able to traverse buildings or resources.
           Only the unit calling this method will be moved."""
        game_instance = get_game_instance()
        if not game_instance:
            return
        
        # If we're attacking, allow us to get closer to our target
        from behaviors import AttackBehavior
        attacking_target = None
        if isinstance(self.current_behavior, AttackBehavior) and hasattr(self.current_behavior, 'target'):
            attacking_target = self.current_behavior.target
        
        # Check collisions with all entities
        for other in game_instance.entities:
            if other is self or not hasattr(other, "rect"):
                continue
                
            # Skip collision resolution if we're attacking this specific entity
            if attacking_target is not None and other is attacking_target:
                # Allow dot units to get close enough to attack buildings
                if isinstance(attacking_target, Building) and isinstance(self, Dot):
                    # Skip collision completely to let melee units approach buildings
                    print(f"Dot attacking building: Skipping collision resolution")
                    continue
                    
                # Also add general case for any unit attacking
                print(f"Unit attacking target: Distance = {distance(self.position, other.position)}")
                # Reduce the collision avoidance for attacking units
                continue
            
            # Create slightly larger collision rect for buildings/resources to avoid getting too close
            other_rect = other.rect.copy()
            if not isinstance(other, Unit):
                # Add a small buffer around buildings and resources
                other_rect.inflate_ip(4, 4)
                
            # If we're colliding with another entity
            if self.rect.colliderect(other_rect):
                # Only the current unit (self) gets pushed, not buildings or resources
                overlap = self.rect.clip(other_rect)
                
                # Calculate push direction (away from the other entity)
                dx = self.position[0] - other.position[0]
                dy = self.position[1] - other.position[1]
                
                # Add a tiny random offset to avoid units getting stuck
                dx += random.uniform(-1.0, 1.0)
                dy += random.uniform(-1.0, 1.0)
                
                # Small threshold to prevent jitter when just touching
                push_threshold = 2.0
                
                # Push along the axis with smallest overlap, plus some extra to avoid re-collision
                if overlap.width <= overlap.height:
                    # Push horizontally
                    push_amount = overlap.width + push_threshold
                    if dx < 0:
                        self.position[0] -= push_amount
                    else:
                        self.position[0] += push_amount
                else:
                    # Push vertically
                    push_amount = overlap.height + push_threshold
                    if dy < 0:
                        self.position[1] -= push_amount
                    else:
                        self.position[1] += push_amount
                
                # Update collision rect after being pushed
                self.rect.x = self.position[0] - self.size/2
                self.rect.y = self.position[1] - self.size/2
                
                # Add a tiny velocity to help units separate
                if isinstance(other, Unit):
                    # Calculate unit direction vector
                    dist = ((dx * dx) + (dy * dy)) ** 0.5
                    if dist > 0:
                        normalized_dx = dx / dist
                        normalized_dy = dy / dist
                        
                        # Add a small separation force
                        separation_force = 5.0
                        self.position[0] += normalized_dx * separation_force
                        self.position[1] += normalized_dy * separation_force
                        
                        # Update rect once more
                        self.rect.x = self.position[0] - self.size/2
                        self.rect.y = self.position[1] - self.size/2
    
    def _check_for_enemies_in_range(self):
        """Check for enemies in aggro range and engage them if found."""
        # Only combat units with attack damage and range should auto-engage
        if self.attack_damage <= 0 or self.attack_range <= 0:
            return
            
        # Import here to avoid circular imports
        from game import Game
        
        # Look for enemies in aggro range
        enemies = [e for e in Game.instance.entities 
                   if hasattr(e, 'player_id') and e.player_id != self.player_id
                   and hasattr(e, 'health') and e.health > 0]
        
        # Find closest enemy in aggro range
        enemies_in_range = []
        for enemy in enemies:
            if distance(self.position, enemy.position) <= self.aggro_range:
                enemies_in_range.append(enemy)
        
        if enemies_in_range:
            # Target closest enemy
            closest_enemy = min(enemies_in_range, 
                               key=lambda e: distance(self.position, e.position))
            
            # Attack the enemy
            self.attack(closest_enemy)
    
    def move_to(self, position):
        """Order the unit to move to a position."""
        self.target_position = position
        self.current_behavior = MoveBehavior(self, position)
    
    def gather(self, resource):
        """Override gather so that harvesters snap to a designated resource slot."""
        # Try to get a harvesting slot
        slot_position = resource.assign_harvest_slot(self)
        
        # If no slot is available, just set behavior without moving
        if slot_position is None:
            self.current_behavior = GatherBehavior(self, resource)
            return
            
        # If we got a slot, move to it
        self.move_to(slot_position)
        self.current_behavior = GatherBehavior(self, resource)
    
    def attack(self, target):
        """Order the unit to attack a target."""
        self.current_behavior = AttackBehavior(self, target)
    
    def take_damage(self, amount):
        """Take damage and return True if destroyed."""
        print(f"Building {type(self).__name__} taking {amount} damage. Current health: {self.health}")
        old_health = self.health
        self.health -= amount
        print(f"Building health after damage: {self.health}, was destroyed: {self.health <= 0}")
        if old_health > 0 and self.health <= 0:
            print(f"Building {type(self).__name__} was destroyed!")
        return self.health <= 0
    
    def render(self, renderer):
        """Render the unit."""
        # Get game instance for debug mode
        game_instance = get_game_instance()
        
        # Draw selection circle if selected
        if self.selected:
            renderer.draw_circle(self.position, self.size*0.75, WHITE, 1)
            
            # Draw aggro range when selected and in debug mode
            if self.aggro_range > 0 and game_instance and game_instance.show_debug:
                renderer.draw_circle(self.position, self.aggro_range, (255, 100, 100), 1, False)
                
            # Draw attack range when selected and in debug mode
            if self.attack_range > 0 and game_instance and game_instance.show_debug:
                renderer.draw_circle(self.position, self.attack_range, (255, 50, 50), 1, False)
        
        # Draw health bar if damaged
        if self.health < self.max_health:
            health_pct = self.health / self.max_health
            bar_width = self.size * 1.2
            renderer.draw_rect(
                pygame.Rect(
                    self.position[0] - bar_width/2,
                    self.position[1] - self.size - 5,
                    bar_width,
                    3
                ),
                RED,
                0,
                True
            )
            renderer.draw_rect(
                pygame.Rect(
                    self.position[0] - bar_width/2,
                    self.position[1] - self.size - 5,
                    bar_width * health_pct,
                    3
                ),
                GREEN,
                0,
                True
            )
        
        # Draw resource indicator if carrying
        if self.carrying_resources > 0:
            renderer.draw_text(
                f"{self.carrying_resources}",
                (self.position[0], self.position[1] + self.size + 5),
                CYAN,
                16
            )
        
        # Draw visual effects
        if self.show_gather_effect:
            # Draw gathering effect (sparkles)
            renderer.draw_circle(
                (self.position[0] + random.uniform(-self.size/2, self.size/2),
                 self.position[1] + random.uniform(-self.size/2, self.size/2)),
                2, CYAN, 0, True
            )
        
        if self.show_attack_effect:
            # Draw attack effect
            renderer.draw_circle(
                (self.position[0] + random.uniform(-self.size/2, self.size/2),
                 self.position[1] + random.uniform(-self.size/2, self.size/2)),
                3, RED, 0, True
            )

    def attack_move(self, position):
        """Order the unit to move to a position while attacking enemies encountered."""
        self.current_behavior = AttackMoveBehavior(self, position)
    
    def hold_position(self):
        """Order the unit to hold its current position."""
        self.current_behavior = HoldPositionBehavior(self)
        
    def patrol(self, position):
        """Order the unit to patrol between its current position and the target position."""
        from behaviors import PatrolBehavior
        # Store current position as the start of patrol route
        start_position = self.position.copy()
        self.current_behavior = PatrolBehavior(self, start_position, position)


class Square(Unit):
    """Worker unit that gathers resources. Squares are used to gather resources and build structures."""
    
    def __init__(self, position: List[float], player_id: int = 0):
        """Initialize a Square worker unit.
        
        Args:
            position: [x, y] position coordinates
            player_id: 0 for player, 1 for enemy
        """
        color = BLUE if player_id == 0 else RED
        super().__init__(
            position, 
            UnitConfig.WORKER_SIZE,  # Size from config
            color, 
            UnitConfig.WORKER_HEALTH,  # Health from config
            UnitConfig.WORKER_SPEED,  # Speed from config
            player_id
        )
        self.max_carry_capacity = UnitConfig.WORKER_CARRY_CAPACITY  # Capacity from config
    
    def gather(self, resource: 'Resource') -> None:
        """Override gather so that harvesters snap to a designated resource slot.
        
        Args:
            resource: The resource to gather from
        """
        # Try to get a harvesting slot
        slot_position = resource.assign_harvest_slot(self)
        
        # If no slot is available, just set behavior without moving
        if slot_position is None:
            self.current_behavior = GatherBehavior(self, resource)
            return
            
        # If we got a slot, move to it
        self.move_to(slot_position)
        self.current_behavior = GatherBehavior(self, resource)
    
    def render(self, renderer):
        # Draw as a square
        points = create_square(self.position, self.size)
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 1, False)
        
        super().render(renderer)  # Draw health bar, selection, etc.


class Dot(Unit):
    """Fast melee unit that can attack buildings and other units."""
    
    def __init__(self, position, player_id=0):
        color = GREEN if player_id == 0 else RED
        super().__init__(
            position, 
            UnitConfig.DOT_SIZE,
            color, 
            UnitConfig.DOT_HEALTH, 
            UnitConfig.DOT_SPEED, 
            player_id
        )
        self.attack_range = UnitConfig.DOT_ATTACK_RANGE
        self.aggro_range = UnitConfig.DOT_AGGRO_RANGE
        self.attack_cooldown_max = UnitConfig.DOT_ATTACK_COOLDOWN
        self.attack_damage = UnitConfig.DOT_ATTACK_DAMAGE
        self.can_attack_buildings = True  # Flag to indicate this unit can attack buildings
    
    def attack(self, target):
        """Order this dot to attack a target, ensuring it can damage buildings."""
        # Use the parent attack method but first check if the target is a building
        from behaviors import AttackBehavior
        
        # Special case for buildings
        if isinstance(target, Building):
            print(f"Dot attacking building: {type(target).__name__} at {distance(self.position, target.position)}")
            
            # Store original attack range and damage
            original_damage = self.attack_damage
            
            # Temporarily increase damage against buildings
            self.attack_damage = self.attack_damage * 1.5
            
            # Create the attack behavior with boosted stats
            self.current_behavior = AttackBehavior(self, target)
            
            # Reset stats
            self.attack_damage = original_damage
        else:
            # Normal attack for non-buildings
            self.current_behavior = AttackBehavior(self, target)
    
    def render(self, renderer):
        # Draw as a circle
        renderer.draw_circle(self.position, self.size/2, self.color, 0, True)
        renderer.draw_circle(self.position, self.size/2, WHITE, 1, False)
        
        # Get game instance
        game_instance = get_game_instance()
        
        # Draw aggro range when selected and in debug mode
        if self.selected and game_instance and game_instance.show_debug:
            renderer.draw_circle(self.position, self.aggro_range, self.color, 1, False)
        
        super().render(renderer)  # Draw health bar, selection, etc.


class Triangle(Unit):
    """Ranged attack unit."""
    
    def __init__(self, position, player_id=0):
        color = YELLOW if player_id == 0 else RED
        super().__init__(position, 25, color, 40, 70, player_id)
        self.attack_range = 150         # Range where it can attack
        self.aggro_range = 250          # Range where it will detect and chase enemies
        self.attack_cooldown_max = 1.0
        self.attack_damage = 15
    
    def render(self, renderer):
        # Draw as a triangle
        points = create_triangle(self.position, self.size, self.angle)
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 1, False)
        
        # Get game instance for debug visualization
        game_instance = get_game_instance()
        
        # Draw ranges when selected and debug mode is on
        if self.selected and game_instance and game_instance.show_debug:
            # Draw attack range
            renderer.draw_circle(self.position, self.attack_range, (255, 50, 50), 1, False)
            # Draw aggro range
            renderer.draw_circle(self.position, self.aggro_range, (255, 100, 100), 1, False)
        
        super().render(renderer)  # Draw health bar, selection, etc.


class Building(Entity):
    """Base class for all buildings."""
    
    def __init__(self, position, size, color, max_health, player_id=0):
        super().__init__(position, size, color)
        self.max_health = max_health
        self.health = max_health
        self.player_id = player_id  # 0 for player, 1 for enemy
        self.production_queue = []
        self.build_progress = 0
        self.build_time = 0
        self.rally_point = None
    
    def update(self, dt):
        super().update(dt)
        
        # Process production queue
        if self.production_queue and self.build_progress < self.build_time:
            self.build_progress += dt
            if self.build_progress >= self.build_time:
                self._complete_production()
    
    def _complete_production(self):
        """Complete the current production item."""
        if not self.production_queue:
            return
        
        unit_type = self.production_queue.pop(0)
        
        # Create the unit near the building
        offset_x = random.randint(-40, 40)
        offset_y = random.randint(-40, 40)
        spawn_pos = [self.position[0] + offset_x, self.position[1] + offset_y]
        
        new_unit = None
        
        try:
            # Handle both string and class type
            if isinstance(unit_type, str):
                # String type reference
                if unit_type == "square":
                    new_unit = Square(spawn_pos, self.player_id)
                elif unit_type == "dot":
                    new_unit = Dot(spawn_pos, self.player_id)
                elif unit_type == "triangle":
                    new_unit = Triangle(spawn_pos, self.player_id)
            else:
                # Already a class reference
                new_unit = unit_type(spawn_pos, self.player_id)
            
            if new_unit:
                # Get the game instance
                game_instance = get_game_instance()
                if game_instance:
                    game_instance.add_entity(new_unit)
                    
                    # Send to rally point if set
                    if self.rally_point:
                        new_unit.move_to(self.rally_point)
        except Exception as e:
            print(f"Error completing production: {e}")
        
        self.build_progress = 0
        
        # Start next production if queue is not empty
        if self.production_queue:
            next_unit = self.production_queue[0]
            self.build_time = self._get_build_time(next_unit)
            # Safety check
            if self.build_time <= 0:
                self.build_time = 5.0
    
    def _get_build_time(self, unit_type):
        """Get build time for a unit type."""
        # Handle both string type names and class types
        unit_type_name = unit_type
        if not isinstance(unit_type, str):
            # If it's a class type, convert to string name
            unit_type_name = unit_type.__name__.lower()
            
        if unit_type_name == "square":
            return 5
        elif unit_type_name == "dot":
            return 6
        elif unit_type_name == "triangle":
            return 7
        return 5.0  # Default time if type not recognized
    
    def take_damage(self, amount):
        """Take damage and return True if destroyed."""
        print(f"Building {type(self).__name__} taking {amount} damage. Current health: {self.health}")
        old_health = self.health
        self.health -= amount
        print(f"Building health after damage: {self.health}, was destroyed: {self.health <= 0}")
        if old_health > 0 and self.health <= 0:
            print(f"Building {type(self).__name__} was destroyed!")
        return self.health <= 0
    
    def produce(self, unit_type):
        """Queue a unit for production."""
        # Get game instance
        game_instance = get_game_instance()
        if not game_instance:
            return False
        
        # Handle both string type names and class types
        unit_type_name = unit_type
        if not isinstance(unit_type, str):
            # If it's a class type, convert to string name
            unit_type_name = unit_type.__name__.lower()
        
        # Calculate cost
        cost = 0
        if unit_type_name == "square":
            cost = 50
        elif unit_type_name == "dot":
            cost = 75
        elif unit_type_name == "triangle":
            cost = 100
        
        if game_instance.resources[self.player_id] < cost:
            return False
        
        # Deduct resources
        game_instance.resources[self.player_id] -= cost
        
        # Add to queue
        self.production_queue.append(unit_type)
        
        # If this is the first item, start production
        if len(self.production_queue) == 1:
            self.build_time = self._get_build_time(unit_type_name)
            # Safety check to ensure build_time is valid
            if self.build_time <= 0:
                self.build_time = 5.0  # Default build time if lookup fails
            self.build_progress = 0.0  # Reset build progress
        
        return True
    
    def set_rally_point(self, position):
        """Set the rally point for produced units."""
        self.rally_point = position
    
    def render(self, renderer):
        # Get game instance
        game_instance = get_game_instance()
        
        # Draw selection
        if self.selected:
            renderer.draw_rect(
                pygame.Rect(
                    self.position[0] - self.size/2 - 5,
                    self.position[1] - self.size/2 - 5,
                    self.size + 10,
                    self.size + 10
                ),
                WHITE,
                1
            )
        
        # Draw rally point if set
        if self.selected and self.rally_point:
            renderer.draw_line(self.position, self.rally_point, WHITE, 1)
            renderer.draw_circle(self.rally_point, 5, WHITE, 1)
        
        # Draw health bar
        health_pct = self.health / self.max_health
        bar_width = self.size * 1.2
        renderer.draw_rect(
            pygame.Rect(
                self.position[0] - bar_width/2,
                self.position[1] - self.size/2 - 10,
                bar_width,
                5
            ),
            RED,
            0,
            True
        )
        renderer.draw_rect(
            pygame.Rect(
                self.position[0] - bar_width/2,
                self.position[1] - self.size/2 - 10,
                bar_width * health_pct,
                5
            ),
            GREEN,
            0,
            True
        )
        
        # Draw production progress if producing
        if self.production_queue and self.build_time > 0:
            progress = self.build_progress / self.build_time
            renderer.draw_rect(
                pygame.Rect(
                    self.position[0] - bar_width/2,
                    self.position[1] + self.size/2 + 5,
                    bar_width,
                    5
                ),
                WHITE,
                1
            )
            renderer.draw_rect(
                pygame.Rect(
                    self.position[0] - bar_width/2,
                    self.position[1] + self.size/2 + 5,
                    bar_width * progress,
                    5
                ),
                BLUE,
                0,
                True
            )
            
            # Draw queue info
            renderer.draw_text(
                f"Queue: {len(self.production_queue)}",
                (self.position[0], self.position[1] + self.size/2 + 20),
                WHITE,
                16
            )


class CommandCenter(Building):
    """Central building for resource collection and worker production."""
    
    def __init__(self, position, player_id=0):
        color = BLUE if player_id == 0 else RED
        super().__init__(position, 80, color, 500, player_id)
        self.resource_queue = []  # Queue of resources to be processed
    
    def add_resources(self, amount):
        """Add resources to the player's stockpile."""
        # Get game instance
        game_instance = get_game_instance()
        if game_instance:
            game_instance.resources[self.player_id] += amount
        
        # Visual feedback
        self.resource_queue.append({
            "amount": amount,
            "timer": 0.5  # Show for 0.5 seconds
        })
    
    def update(self, dt):
        super().update(dt)
        
        # Update resource queue
        for i in range(len(self.resource_queue) - 1, -1, -1):
            self.resource_queue[i]["timer"] -= dt
            if self.resource_queue[i]["timer"] <= 0:
                self.resource_queue.pop(i)
    
    def render(self, renderer):
        # Draw as a large hexagon
        points = []
        for i in range(6):
            angle = math.pi/3 * i
            x = self.position[0] + math.cos(angle) * self.size/2
            y = self.position[1] + math.sin(angle) * self.size/2
            points.append((x, y))
        
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 2, False)
        
        # Draw resource indicators
        for i, resource in enumerate(self.resource_queue):
            renderer.draw_text(
                f"+{resource['amount']}",
                (self.position[0], self.position[1] - self.size/2 - 20 - i*15),
                CYAN,
                16
            )
        
        super().render(renderer)  # Draw health bar, selection, etc.


class UnitBuilding(Building):
    """Building for producing combat units."""
    
    def __init__(self, position, player_id=0):
        color = YELLOW if player_id == 0 else RED
        super().__init__(position, 60, color, 300, player_id)
    
    def render(self, renderer):
        # Draw as a pentagon
        points = []
        for i in range(5):
            angle = 2*math.pi/5 * i - math.pi/2  # Start from top
            x = self.position[0] + math.cos(angle) * self.size/2
            y = self.position[1] + math.sin(angle) * self.size/2
            points.append((x, y))
        
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 2, False)
        
        super().render(renderer)  # Draw health bar, selection, etc.


class Turret(Building):
    """Defensive building that attacks nearby enemy units."""
    
    def __init__(self, position, player_id=0):
        color = GREEN if player_id == 0 else RED
        super().__init__(position, 40, color, 250, player_id)
        self.attack_range = 150  # Range in pixels
        self.attack_damage = 10  # Damage per hit
        self.attack_cooldown_max = 1.0  # Seconds between attacks
        self.attack_cooldown = 0
        self.target = None
        self.rotation = 0.0  # For turret rotation animation
        
    def update(self, dt):
        super().update(dt)
        
        # Get game instance
        game_instance = get_game_instance()
        if not game_instance:
            return
            
        # Decrease attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
            
        # If we have a target, check if it's still valid
        if self.target:
            if not hasattr(self.target, 'health') or self.target.health <= 0 or self.target not in game_instance.entities:
                self.target = None
            else:
                # Calculate distance to target
                target_dist = math.sqrt((self.position[0] - self.target.position[0])**2 + 
                                        (self.position[1] - self.target.position[1])**2)
                
                # If target moved out of range, stop tracking it
                if target_dist > self.attack_range:
                    self.target = None
                # Attack if cooldown is ready
                elif self.attack_cooldown <= 0:
                    self.attack_cooldown = self.attack_cooldown_max
                    self.target.take_damage(self.attack_damage)
                    
                    # Calculate angle for turret barrel rotation
                    dx = self.target.position[0] - self.position[0]
                    dy = self.target.position[1] - self.position[1]
                    self.rotation = math.atan2(dy, dx)
        
        # If no target, find closest enemy in range
        if not self.target:
            closest_dist = float('inf')
            closest_enemy = None
            
            for entity in game_instance.entities:
                # Check if entity is an enemy with health
                if (hasattr(entity, 'player_id') and entity.player_id != self.player_id and 
                    hasattr(entity, 'health') and entity.health > 0):
                    
                    dist = math.sqrt((self.position[0] - entity.position[0])**2 + 
                                     (self.position[1] - entity.position[1])**2)
                    
                    if dist <= self.attack_range and dist < closest_dist:
                        closest_dist = dist
                        closest_enemy = entity
            
            self.target = closest_enemy
            
            # If found a new target, calculate rotation
            if self.target:
                dx = self.target.position[0] - self.position[0]
                dy = self.target.position[1] - self.position[1]
                self.rotation = math.atan2(dy, dx)
    
    def render(self, renderer):
        # Draw turret base (hexagon)
        points = []
        for i in range(6):
            angle = math.pi/3 * i
            x = self.position[0] + math.cos(angle) * self.size/2
            y = self.position[1] + math.sin(angle) * self.size/2
            points.append((x, y))
        
        renderer.draw_polygon(points, self.color, 0, True)
        renderer.draw_polygon(points, WHITE, 2, False)
        
        # Draw turret barrel (line)
        barrel_length = self.size * 0.8
        barrel_end = (
            self.position[0] + math.cos(self.rotation) * barrel_length,
            self.position[1] + math.sin(self.rotation) * barrel_length
        )
        renderer.draw_line(self.position, barrel_end, WHITE, 3)
        
        # Draw attack range indicator when selected
        if self.selected:
            # Semi-transparent circle for range
            renderer.draw_circle(self.position, self.attack_range, (255, 255, 255, 70), 1)
        
        super().render(renderer)  # Draw health bar, selection, etc. 