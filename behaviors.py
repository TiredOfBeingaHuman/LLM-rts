import math
from utils import distance, normalize, angle_between

class Behavior:
    """Base class for all unit behaviors."""
    
    def __init__(self, unit):
        self.unit = unit
    
    def update(self, dt):
        """Update behavior state."""
        pass
    
    def enter(self):
        """Called when this behavior becomes active."""
        pass
    
    def exit(self):
        """Called when this behavior is no longer active."""
        pass
    
    def is_finished(self):
        """Return True if this behavior is complete."""
        return False

class IdleBehavior(Behavior):
    """Behavior for a unit that's idle."""
    
    def update(self, dt):
        # Do nothing while idle
        pass

class MoveBehavior(Behavior):
    """Behavior for moving to a target position."""
    
    def __init__(self, unit, target_position, callback=None):
        super().__init__(unit)
        self.target_position = target_position
        self.callback = callback  # Optional callback when movement is complete
        self.arrival_threshold = 5.0  # Distance to consider "arrived"
    
    def update(self, dt):
        if not self.target_position:
            return True
        
        # Calculate distance to target
        dist = distance(self.unit.position, self.target_position)
        
        # If we've arrived at the target
        if dist < self.arrival_threshold:
            if self.callback:
                self.callback()
            return True
        
        # Calculate direction vector
        dx = self.target_position[0] - self.unit.position[0]
        dy = self.target_position[1] - self.unit.position[1]
        
        # Calculate base movement direction
        direction = normalize((dx, dy))
        
        # Apply steering behaviors for better group movement
        from game import Game
        game_instance = Game.instance
        
        # Initialize steering vector
        steer_x, steer_y = 0, 0
        
        if game_instance:
            try:
                # Add separation behavior - steer away from nearby units
                separation_weight = 0.3
                separation_radius = 20.0
                
                # Get other units - don't rely on selection state which can change
                nearby_units = []
                for entity in game_instance.entities:
                    try:
                        # Check if entity is a unit of same type and not self
                        if (entity != self.unit and 
                            isinstance(entity, type(self.unit)) and 
                            hasattr(entity, 'position')):
                            
                            # Check if it's close enough to consider
                            d = distance(self.unit.position, entity.position)
                            if d < separation_radius:
                                nearby_units.append((entity, d))
                    except Exception:
                        # Skip any problematic entities
                        continue
                
                # Apply separation force from nearby units
                if nearby_units:
                    for entity, d in nearby_units:
                        if d <= 0:  # Skip if somehow at exact same position
                            continue
                            
                        # Get vector away from other unit
                        away_x = self.unit.position[0] - entity.position[0]
                        away_y = self.unit.position[1] - entity.position[1]
                        
                        # Normalize the away vector
                        away_length = math.sqrt(away_x**2 + away_y**2)
                        if away_length > 0:
                            away_x /= away_length
                            away_y /= away_length
                            
                            # Inverse square falloff - closer units push harder
                            strength = (separation_radius - d) / separation_radius
                            strength = strength * strength  # Square for stronger effect at close range
                                
                            # Apply weighted separation
                            steer_x += away_x * strength * separation_weight
                            steer_y += away_y * strength * separation_weight
            except Exception:
                # If any error occurs, just use basic movement
                pass
        
        # Adjust final movement direction with steering forces
        final_dx = direction[0] + steer_x
        final_dy = direction[1] + steer_y
        
        # Make sure we have a non-zero direction
        magnitude = math.sqrt(final_dx**2 + final_dy**2)
        if magnitude < 0.001:  # Very small, essentially zero
            final_dx = direction[0]  # Fall back to original direction
            final_dy = direction[1]
            magnitude = math.sqrt(final_dx**2 + final_dy**2)
            if magnitude < 0.001:  # If still zero, use a default direction
                final_dx = 1.0
                final_dy = 0.0
                magnitude = 1.0
        
        # Re-normalize the final direction
        final_dx /= magnitude
        final_dy /= magnitude
        
        # Calculate speed based on distance to target - slow down when approaching
        speed_factor = 1.0
        if dist < 50:  # Start slowing down when getting close
            speed_factor = max(0.5, dist / 50)  # Scale between 0.5 and 1.0
            
        # Move towards target with steering behaviors applied
        self.unit.position[0] += final_dx * self.unit.speed * speed_factor * dt
        self.unit.position[1] += final_dy * self.unit.speed * speed_factor * dt
        
        # Update angle to face movement direction
        self.unit.angle = angle_between((0, 0), (final_dx, final_dy))
        
        return False
    
    def is_finished(self):
        if not self.target_position:
            return True
        
        dist = distance(self.unit.position, self.target_position)
        return dist < self.arrival_threshold

class GatherBehavior(Behavior):
    """Behavior for gathering resources."""
    
    def __init__(self, unit, resource, command_center=None):
        super().__init__(unit)
        self.resource = resource
        self.command_center = command_center
        self.stage = "moving_to_resource"  # Stages: moving_to_resource, gathering, returning, depositing
        self.gather_timer = 0
        self.deposit_timer = 0
        self.assigned_slot = False  # Track if we've been assigned a mining slot
        
        # Find nearest command center if not provided
        if not self.command_center:
            self._find_nearest_command_center()
    
    def update(self, dt):
        from entities import Resource, CommandCenter  # Import here to avoid circular imports
        
        # Update any active timers
        if self.gather_timer > 0:
            self.gather_timer -= dt
        if self.deposit_timer > 0:
            self.deposit_timer -= dt
        
        # Validate targets - check if resource still exists or got removed
        if not self.resource or not hasattr(self.resource, 'amount'):
            print(f"Warning: Invalid resource for {self.unit}")
            if self.assigned_slot:
                # Try to release the slot before changing behavior
                try:
                    if hasattr(self.resource, 'release_worker_from_slot'):
                        self.resource.release_worker_from_slot(self.unit)
                except Exception:
                    pass
                self.assigned_slot = False
            
            # Find a new resource or go idle
            if not self._find_new_resource():
                self.unit.current_behavior = behaviors.IdleBehavior(self.unit)
            return True
        
        # If resource is depleted, try to find a new one
        if self.resource.amount <= 0:
            # Release slot
            if self.assigned_slot:
                try:
                    self.resource.release_worker_from_slot(self.unit)
                except Exception:
                    pass
                self.assigned_slot = False
                
            # Try to find a new resource
            if not self._find_new_resource():
                self.unit.current_behavior = behaviors.IdleBehavior(self.unit)
            return True
        
        if not self.command_center:
            self._find_nearest_command_center()
            if not self.command_center:
                print(f"Warning: No command center found for {self.unit}")
                return True
        
        # State machine for gathering behavior
        if self.stage == "moving_to_resource":
            self._update_moving_to_resource(dt)
        elif self.stage == "gathering":
            self._update_gathering(dt)
        elif self.stage == "returning":
            self._update_returning(dt)
        elif self.stage == "depositing":
            self._update_depositing(dt)
        
        return False
    
    def _update_moving_to_resource(self, dt):
        """Move to the target resource."""
        # Check if resource still exists and has resources
        if not hasattr(self.resource, 'amount') or self.resource.amount <= 0:
            self._find_new_resource()
            return
        
        # Calculate distance to resource
        dist = distance(self.unit.position, self.resource.position)
        
        # If close enough, start gathering
        if dist <= self.unit.size + self.resource.size/2:
            self.stage = "gathering"
            self.gather_timer = 0.5  # Set initial gather timer
            # We should already be in a slot from the Square.gather() method
            self.assigned_slot = True
            return
        
        # Get the target position - if we're assigned a slot, move to that specific position
        target_pos = self.resource.position
        if hasattr(self.resource, 'get_slot_position'):
            # Try to find which slot we're assigned to
            for i, worker in enumerate(self.resource.slots):
                if worker == self.unit:
                    # We found our slot, move directly to it
                    target_pos = self.resource.get_slot_position(i)
                    break
        
        # Move towards the target position
        dx = target_pos[0] - self.unit.position[0]
        dy = target_pos[1] - self.unit.position[1]
        
        # Calculate distance to target
        dist_to_target = (dx*dx + dy*dy) ** 0.5
        
        # If we're very close to the target, snap to it
        if dist_to_target < 5:
            self.unit.position[0] = target_pos[0]
            self.unit.position[1] = target_pos[1]
            return
        
        # Normalize and apply speed
        if dist_to_target > 0:  # Avoid division by zero
            dx /= dist_to_target
            dy /= dist_to_target
        
        # Move towards target with a small correction to prevent oscillation
        approach_factor = min(1.0, dist_to_target / (self.unit.speed * dt))
        
        self.unit.position[0] += dx * self.unit.speed * dt * approach_factor
        self.unit.position[1] += dy * self.unit.speed * dt * approach_factor
        
        # Update angle to face movement direction
        self.unit.angle = angle_between((0, 0), (dx, dy))
    
    def _update_gathering(self, dt):
        """Gather resources from target."""
        # Check if resource still exists and has resources
        if not hasattr(self.resource, 'amount') or self.resource.amount <= 0:
            # Release our slot before finding a new resource
            if self.assigned_slot:
                self.resource.release_worker_from_slot(self.unit)
                self.assigned_slot = False
            self._find_new_resource()
            return
        
        # If already full, return to base
        if self.unit.carrying_resources >= self.unit.max_carry_capacity:
            self.stage = "returning"
            return
        
        # If gather timer is done, collect resources
        if self.gather_timer <= 0:
            # Extract resources
            gathered = self.resource.extract(1)
            self.unit.carrying_resources += gathered
            
            # Set cooldown for next gather action
            self.gather_timer = 0.5  # Gather every 0.5 seconds
            
            # Visual indication of gathering
            self.unit.show_gather_effect = True
            
            # If resource is depleted or we're full, return to base
            if gathered == 0 or self.unit.carrying_resources >= self.unit.max_carry_capacity:
                self.stage = "returning"
    
    def _update_returning(self, dt):
        """Return gathered resources to command center."""
        # Calculate distance to command center
        dist = distance(self.unit.position, self.command_center.position)
        
        # If close enough, start depositing
        if dist <= self.unit.size + self.command_center.size/2:
            self.stage = "depositing"
            self.deposit_timer = 0.3  # Set initial deposit timer
            return
        
        # Move towards command center
        dx = self.command_center.position[0] - self.unit.position[0]
        dy = self.command_center.position[1] - self.unit.position[1]
        
        # Calculate distance to target
        dist_to_target = (dx*dx + dy*dy) ** 0.5
        
        # Normalize and apply speed
        if dist_to_target > 0:  # Avoid division by zero
            dx /= dist_to_target
            dy /= dist_to_target
        
        # Move towards target with a small correction to prevent oscillation
        approach_factor = min(1.0, dist_to_target / (self.unit.speed * dt))
        
        self.unit.position[0] += dx * self.unit.speed * dt * approach_factor
        self.unit.position[1] += dy * self.unit.speed * dt * approach_factor
        
        # Update angle to face movement direction
        self.unit.angle = angle_between((0, 0), (dx, dy))
    
    def _update_depositing(self, dt):
        """Deposit resources at the command center."""
        # If deposit timer is done, deposit resources
        if self.deposit_timer <= 0:
            # Deposit resources
            from game import Game  # Import here to avoid circular import
            
            # Debug message
            if Game.instance.show_debug:
                print(f"Worker depositing {self.unit.carrying_resources} resources at command center")
            
            self.command_center.add_resources(self.unit.carrying_resources)
            self.unit.carrying_resources = 0
            
            # Check if original resource still has minerals
            if hasattr(self.resource, 'amount') and self.resource.amount > 0:
                # Go back to the same resource
                self.stage = "moving_to_resource"
            else:
                # Release our slot before finding a new resource
                if self.assigned_slot:
                    self.resource.release_worker_from_slot(self.unit)
                    self.assigned_slot = False
                # Find a new resource
                self._find_new_resource()
    
    def _find_nearest_command_center(self):
        """Find the nearest command center belonging to this unit's player."""
        from game import Game  # Import here to avoid circular import
        from entities import CommandCenter
        
        command_centers = [e for e in Game.instance.entities 
                          if isinstance(e, CommandCenter) and e.player_id == self.unit.player_id]
        
        if command_centers:
            self.command_center = min(command_centers, 
                                     key=lambda cc: distance(self.unit.position, cc.position))
        else:
            self.command_center = None
    
    def _find_new_resource(self):
        """Find a new resource to gather from."""
        from game import Game  # Import here to avoid circular import
        from entities import Resource
        
        resources = [e for e in Game.instance.entities 
                    if isinstance(e, Resource) and e.amount > 0]
        
        if resources:
            self.resource = min(resources, key=lambda r: distance(self.unit.position, r.position))
            # Need to get assigned a new slot
            slot_position = self.resource.assign_harvest_slot(self.unit)
            if slot_position is not None:
                self.assigned_slot = True
                self.unit.position = list(slot_position)  # Snap to the slot position
            self.stage = "moving_to_resource"
        else:
            # No resources available, become idle
            self.resource = None
            self.stage = "idle"
            return True
            
    def exit(self):
        """Clean up when behavior is finished."""
        # Release our slot when we're done
        if self.assigned_slot and self.resource:
            self.resource.release_worker_from_slot(self.unit)
            self.assigned_slot = False

class AttackBehavior(Behavior):
    """Behavior for attacking a target."""
    
    def __init__(self, unit, target):
        super().__init__(unit)
        self.target = target
        self.in_range = False
        self.chase_range = unit.aggro_range  # Use the unit's aggro range for chasing
    
    def update(self, dt):
        try:
            # Check if target is still valid - different check for buildings vs units
            from entities import Building, Dot
            
            if not self.target:
                print("Target is None")
                return True
                
            # Buildings don't have the same properties as units, handle them differently
            is_building_target = isinstance(self.target, Building)
            
            # Adjust attack range for dot units attacking buildings
            original_attack_range = self.unit.attack_range
            if isinstance(self.unit, Dot) and is_building_target:
                # Double the attack range for dots attacking buildings (much bigger increase)
                print(f"Dot attacking building: Increasing range from {self.unit.attack_range} to {self.unit.attack_range * 2}")
                self.unit.attack_range = self.unit.attack_range * 2  # Double the range
                
                # Also make the log message clearer
                print(f"Dot with attack range {self.unit.attack_range} targeting building at distance {distance(self.unit.position, self.target.position)}")
            
            if is_building_target:
                # For buildings, just check if they have health
                if not hasattr(self.target, 'health') or self.target.health <= 0:
                    print(f"Building target invalid: health={self.target.health if hasattr(self.target, 'health') else 'no health'}")
                    # Restore original attack range
                    self.unit.attack_range = original_attack_range
                    return True
            else:
                # For other entities, check standard properties
                if not hasattr(self.target, 'health') or self.target.health <= 0:
                    print(f"Target invalid: health={self.target.health if hasattr(self.target, 'health') else 'no health'}")
                    # Restore original attack range
                    self.unit.attack_range = original_attack_range
                    return True
            
            # Update attack cooldown
            if self.unit.attack_cooldown > 0:
                self.unit.attack_cooldown -= dt
            
            # Calculate distance to target
            dist = distance(self.unit.position, self.target.position)
            
            # If target moved out of chase range, stop attacking
            if dist > self.chase_range:
                print(f"Target out of chase range: {dist} > {self.chase_range}")
                # Restore original attack range
                self.unit.attack_range = original_attack_range
                return True
            
            # If not in attack range, move towards target
            if dist > self.unit.attack_range:
                # Move towards target
                dx = self.target.position[0] - self.unit.position[0]
                dy = self.target.position[1] - self.unit.position[1]
                
                # Normalize and apply speed
                direction = normalize((dx, dy))
                
                # Move towards target
                self.unit.position[0] += direction[0] * self.unit.speed * dt
                self.unit.position[1] += direction[1] * self.unit.speed * dt
                
                # Update angle to face movement direction
                self.unit.angle = angle_between((0, 0), direction)
                
                self.in_range = False
            else:
                # In range, attack if cooldown is ready
                self.in_range = True
                print(f"In attack range: {dist} <= {self.unit.attack_range}, cooldown: {self.unit.attack_cooldown}")
                
                if self.unit.attack_cooldown <= 0:
                    try:
                        target_type = type(self.target).__name__
                        print(f"Attacking target: {target_type}, has_take_damage={hasattr(self.target, 'take_damage')}")
                        
                        # Attack target - check if target has take_damage method first
                        if hasattr(self.target, 'take_damage'):
                            # Apply damage and check if destroyed
                            damage = self.unit.attack_damage
                            print(f"Applying {damage} damage to {target_type} with {self.target.health} health")
                            
                            # Apply damage
                            target_destroyed = self.target.take_damage(damage)
                            print(f"After attack: target health = {self.target.health}, destroyed = {target_destroyed}")
                        else:
                            # Legacy fallback - directly modify health
                            self.target.health -= self.unit.attack_damage
                            target_destroyed = self.target.health <= 0
                        
                        # Reset attack cooldown
                        self.unit.attack_cooldown = self.unit.attack_cooldown_max
                        
                        # Show attack effect
                        self.unit.show_attack_effect = True
                        
                        # If target was destroyed
                        if target_destroyed or self.target.health <= 0:
                            print(f"Target destroyed")
                            # Restore original attack range
                            self.unit.attack_range = original_attack_range
                            return True
                    except Exception as e:
                        print(f"Error during attack: {e}")
                        import traceback
                        traceback.print_exc()
                        # If attack fails, consider behavior complete
                        # Restore original attack range
                        self.unit.attack_range = original_attack_range
                        return True
            
            # Restore original attack range at the end of the update
            self.unit.attack_range = original_attack_range
            return False
        except Exception as e:
            print(f"Error in AttackBehavior: {e}")
            # Make sure to restore the original attack range on error
            if hasattr(self, 'unit') and hasattr(self.unit, 'attack_range') and 'original_attack_range' in locals():
                self.unit.attack_range = original_attack_range
            return True
    
    def is_finished(self):
        return not self.target or not hasattr(self.target, 'health') or self.target.health <= 0
        
    def exit(self):
        """Clean up when this behavior ends."""
        pass

class HoldPositionBehavior(Behavior):
    """Behavior for holding position and only attacking when enemies approach attack range."""
    
    def __init__(self, unit):
        super().__init__(unit)
        self.original_position = tuple(unit.position)
        self.detection_range = unit.aggro_range  # Use aggro range to detect enemies
        self.target = None
        self.hold_strict = True  # Strict hold means don't move to chase enemies
    
    def update(self, dt):
        # Import here to avoid circular imports
        from game import Game
        
        # If we have an active target, attack it if in range
        if self.target:
            # Check if target is still valid
            if not hasattr(self.target, 'health') or self.target.health <= 0:
                self.target = None
            else:
                # Calculate distance to target
                target_dist = distance(self.unit.position, self.target.position)
                
                # If target moved out of detection range, stop tracking it
                if target_dist > self.detection_range:
                    self.target = None
                elif target_dist <= self.unit.attack_range:
                    # Target is in attack range, attack it
                    if self.unit.attack_cooldown > 0:
                        self.unit.attack_cooldown -= dt
                    
                    if self.unit.attack_cooldown <= 0:
                        # Attack
                        self.target.health -= self.unit.attack_damage
                        self.unit.attack_cooldown = self.unit.attack_cooldown_max
                        self.unit.show_attack_effect = True
                        
                        # If target was destroyed
                        if self.target.health <= 0:
                            self.target = None
                else:
                    # Target is detected but not in attack range
                    # In strict hold mode, unit doesn't move but keeps tracking the target
                    pass
        
        # No target, scan for enemies in detection range
        else:
            # Look for enemies in detection range
            enemies = [e for e in Game.instance.entities 
                      if hasattr(e, 'player_id') and e.player_id != self.unit.player_id
                      and hasattr(e, 'health') and e.health > 0]
            
            # Find closest enemy in detection range
            enemies_in_range = []
            for enemy in enemies:
                if distance(self.unit.position, enemy.position) <= self.detection_range:
                    enemies_in_range.append(enemy)
            
            if enemies_in_range:
                # Target closest enemy
                self.target = min(enemies_in_range, 
                                 key=lambda e: distance(self.unit.position, e.position))
        
        # Always ensure unit stays at original position in strict hold mode
        if self.hold_strict:
            # Only snap back if drifted significantly
            current_pos_dist = distance(self.unit.position, self.original_position)
            if current_pos_dist > 5:
                self.unit.position = list(self.original_position)
        
        return False
    
    def is_finished(self):
        # Hold position behavior only ends when explicitly changed
        return False

class AttackMoveBehavior(Behavior):
    """Behavior for moving to a position while attacking any enemies encountered."""
    
    def __init__(self, unit, target_position):
        super().__init__(unit)
        self.target_position = target_position
        self.move_behavior = MoveBehavior(unit, target_position)
        self.current_target = None
        self.detection_range = unit.aggro_range  # Use the unit's aggro range for detection
    
    def update(self, dt):
        from game import Game
        
        # If we have a target, attack it
        if self.current_target:
            # Check if target is still valid
            if not hasattr(self.current_target, 'health') or self.current_target.health <= 0:
                self.current_target = None
            else:
                # Calculate distance to target
                target_dist = distance(self.unit.position, self.current_target.position)
                
                # If target moved out of detection range, stop attacking and continue moving
                if target_dist > self.detection_range:
                    self.current_target = None
                # If target is in attack range, attack it
                elif target_dist <= self.unit.attack_range:
                    if self.unit.attack_cooldown > 0:
                        self.unit.attack_cooldown -= dt
                    
                    if self.unit.attack_cooldown <= 0:
                        # Attack
                        self.current_target.health -= self.unit.attack_damage
                        self.unit.attack_cooldown = self.unit.attack_cooldown_max
                        self.unit.show_attack_effect = True
                        
                        # If target was destroyed
                        if self.current_target.health <= 0:
                            self.current_target = None
                else:
                    # Move towards the target
                    dx = self.current_target.position[0] - self.unit.position[0]
                    dy = self.current_target.position[1] - self.unit.position[1]
                    
                    # Normalize and apply speed
                    direction = normalize((dx, dy))
                    
                    # Move towards target
                    self.unit.position[0] += direction[0] * self.unit.speed * dt
                    self.unit.position[1] += direction[1] * self.unit.speed * dt
                    
                    # Update angle to face movement direction
                    self.unit.angle = angle_between((0, 0), direction)
        
        # No target, continue moving and scan for enemies
        else:
            # Check if we've arrived at destination
            dist_to_target = distance(self.unit.position, self.target_position)
            if dist_to_target < 5:
                return True
            
            # Look for enemies in detection range
            enemies = [e for e in Game.instance.entities 
                      if hasattr(e, 'player_id') and e.player_id != self.unit.player_id
                      and hasattr(e, 'health') and e.health > 0]
            
            # Find closest enemy in detection range
            enemies_in_range = []
            for enemy in enemies:
                if distance(self.unit.position, enemy.position) <= self.detection_range:
                    enemies_in_range.append(enemy)
            
            if enemies_in_range:
                # Target closest enemy
                self.current_target = min(enemies_in_range, 
                                         key=lambda e: distance(self.unit.position, e.position))
            else:
                # No enemies, continue moving
                self.move_behavior.update(dt)
        
        return False
    
    def is_finished(self):
        # Check if we've arrived at destination with no enemies
        if not self.current_target:
            return self.move_behavior.is_finished()
        return False 