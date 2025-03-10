import math
from utils import distance, normalize, angle_between
import random
from config import ResourceConfig

class Behavior:
    """Base class for all behaviors."""
    
    def __init__(self, unit):
        self.unit = unit
    
    def update(self, dt):
        """Update behavior state."""
        raise NotImplementedError("Subclasses must implement update()")
    
    def enter(self):
        """Called when behavior becomes active."""
        pass
    
    def exit(self):
        """Called when behavior is no longer active."""
        pass
    
    def is_finished(self):
        """Check if behavior is complete."""
        return False
        
    def _standardized_move_toward(self, target_position, dt, force_scale=None):
        """Standardized movement logic used by all behaviors.
        
        Args:
            target_position: The position to move toward
            dt: Delta time
            force_scale: Optional force scaling factor (defaults to unit's steering_force)
        """
        if force_scale is None:
            force_scale = self.unit.steering_force
            
        # Calculate distance and direction to target
        dx = target_position[0] - self.unit.position[0]
        dy = target_position[1] - self.unit.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Normalize direction
            dir_x = dx / dist
            dir_y = dy / dist
            
            # Calculate if we're in deceleration range
            arrival_threshold = self.unit.target_reached_threshold
            deceleration_radius = 150.0
            
            # Calculate deceleration factor if close to target
            decel_factor = 1.0
            if dist < deceleration_radius:
                # Linearly scale from 1.0 at deceleration_radius to 0.3 at arrival_threshold
                decel_factor = 0.3 + 0.7 * (dist - arrival_threshold) / (deceleration_radius - arrival_threshold)
                decel_factor = max(0.3, min(1.0, decel_factor))
            
            # Calculate force to apply
            force_intensity = force_scale * decel_factor
                
            # Apply steering force toward target
            self.unit.apply_force(dir_x * force_intensity, dir_y * force_intensity)
            
            # Update unit angle to face movement direction if moving
            if abs(self.unit.velocity[0]) > 1 or abs(self.unit.velocity[1]) > 1:
                self.unit.angle = angle_between((0, 0), (self.unit.velocity[0], self.unit.velocity[1]))
            else:
                # If almost stopped, face the target
                self.unit.angle = angle_between((0, 0), (dx, dy))
                
        return dist <= arrival_threshold

class IdleBehavior(Behavior):
    """Behavior for a unit that's idle."""
    
    def update(self, dt):
        # Actively stop movement for units in idle state
        if hasattr(self.unit, 'velocity'):
            # Apply stronger damping to velocities when idle to prevent unwanted movement
            self.unit.velocity[0] *= 0.8
            self.unit.velocity[1] *= 0.8
            
            # If velocity is very small, zero it out completely 
            if abs(self.unit.velocity[0]) < 0.5 and abs(self.unit.velocity[1]) < 0.5:
                self.unit.velocity[0] = 0
                self.unit.velocity[1] = 0
        
        return False

class MoveBehavior(Behavior):
    """Behavior for moving to a target position using physics-based movement."""
    
    def __init__(self, unit, target_position, callback=None):
        super().__init__(unit)
        self.target_position = target_position
        self.callback = callback  # Optional callback when movement is complete
        self.arrival_threshold = self.unit.target_reached_threshold  # Use unit's threshold
    
    def update(self, dt):
        """Update behavior state."""
        if not self.target_position:
            return True
        
        # Use the standard movement logic
        arrived = self._standardized_move_toward(self.target_position, dt)
        
        # If we've arrived, complete the behavior
        if arrived:
            if self.callback:
                self.callback()
            return True
            
        return False
    
    def is_finished(self):
        """Check if we've reached the target."""
        if not self.target_position:
            return True
        
        # Consider finished if very close and nearly stopped
        dist = distance(self.unit.position, self.target_position)
        low_velocity = abs(self.unit.velocity[0]) < 2 and abs(self.unit.velocity[1]) < 2
        
        return dist < self.arrival_threshold * 0.5 and low_velocity

class GatherBehavior(Behavior):
    """Behavior for gathering resources using physics-based movement."""
    
    def __init__(self, unit, resource, command_center=None):
        super().__init__(unit)
        self.resource = resource
        self.command_center = command_center
        self.state = "MOVING_TO_RESOURCE"  # Initial state
        self.force_scale = unit.steering_force * 0.8  # Slightly reduced force for gathering
        self.arrival_threshold = unit.target_reached_threshold
        self.gather_time = 0
        self.gather_duration = ResourceConfig.HARVEST_TIME
        self.deposit_time = 0
        self.deposit_duration = ResourceConfig.DEPOSIT_TIME
        self.slot_index = -1  # Will be assigned when getting to resource
    
    def update(self, dt):
        """Update the gather behavior state machine."""
        try:
            # Check if resource still exists
            if not self.resource or (hasattr(self.resource, 'amount') and self.resource.amount <= 0):
                # Try to find a new resource
                new_resource = self._find_new_resource()
                if new_resource:
                    self.resource = new_resource
                    self.state = "MOVING_TO_RESOURCE"
                    self.slot_index = -1
                else:
                    # No resources left, return to idle
                    return True
            
            # State machine
            if self.state == "MOVING_TO_RESOURCE":
                return self._update_moving_to_resource(dt)
            elif self.state == "GATHERING":
                return self._update_gathering(dt)
            elif self.state == "RETURNING":
                return self._update_returning(dt)
            elif self.state == "DEPOSITING":
                return self._update_depositing(dt)
            
            return False
        except Exception as e:
            print(f"Error in GatherBehavior update: {e}")
            return True
    
    def _update_moving_to_resource(self, dt):
        """Handle movement to the resource."""
        # Try to get a harvest slot if we don't have one
        if self.slot_index == -1:
            self.slot_index = self.resource.get_available_slot()
            
            # If no slot is available, wait near the resource
            if self.slot_index is None:
                # Move to the resource and wait
                self._move_toward_target(self.resource.position, dt)
                return False
            
            # If we got a slot, register with the resource
            self.resource.assign_worker_to_slot(self.unit, self.slot_index)
        
        # Calculate target position (slot position)
        target_position = self.resource.get_slot_position(self.slot_index)
        
        # Move toward the slot position
        dist = distance(self.unit.position, target_position)
        
        if dist < self.arrival_threshold:
            # We've arrived, slow down
            self.unit.velocity[0] *= 0.7
            self.unit.velocity[1] *= 0.7
            
            # If nearly stopped, start gathering
            if abs(self.unit.velocity[0]) < 5 and abs(self.unit.velocity[1]) < 5:
                self.state = "GATHERING"
                self.gather_time = 0
        else:
            # Keep moving toward slot
            self._move_toward_target(target_position, dt)
            
            # Face the resource
            dx = self.resource.position[0] - self.unit.position[0]
            dy = self.resource.position[1] - self.unit.position[1]
            self.unit.angle = angle_between((0, 0), (dx, dy))
        
        return False
    
    def _update_gathering(self, dt):
        """Handle resource gathering."""
        # Increment gather time
        self.gather_time += dt
        
        # Keep facing the resource
        dx = self.resource.position[0] - self.unit.position[0]
        dy = self.resource.position[1] - self.unit.position[1]
        self.unit.angle = angle_between((0, 0), (dx, dy))
        
        # Show gathering effect
        if random.random() < 0.1:  # Occasionally show effect
            self.unit.show_gather_effect = True
            self.unit.effect_timer = 0
        
        # Check if we're done gathering
        if self.gather_time >= self.gather_duration:
            # Extract resources
            gathered_amount = min(
                self.unit.max_carry_capacity - self.unit.carrying_resources,
                ResourceConfig.RESOURCE_GATHER_RATE
            )
            
            # Extract from resource if possible and resource has amount
            if hasattr(self.resource, 'extract') and hasattr(self.resource, 'amount') and self.resource.amount > 0:
                print(f"Extracting {gathered_amount} resources from {self.resource.amount} available")
                gathered_amount = self.resource.extract(gathered_amount)
                print(f"Extracted {gathered_amount}, now carrying {self.unit.carrying_resources + gathered_amount}")
            else:
                gathered_amount = 0
                print("Resource not available for extraction")
            
            # Add to carried amount
            self.unit.carrying_resources += gathered_amount
            
            # If we're full or resource is depleted, return to base
            if (self.unit.carrying_resources >= self.unit.max_carry_capacity or
                (hasattr(self.resource, 'amount') and self.resource.amount <= 0)):
                # Release our slot
                if self.slot_index != -1:
                    self.resource.release_worker_from_slot(self.unit)
                    self.slot_index = -1
                
                # Find a command center to return to
                if not self.command_center:
                    self.command_center = self._find_nearest_command_center()
                
                if self.command_center:
                    print(f"Returning to command center with {self.unit.carrying_resources} resources")
                    self.state = "RETURNING"
                else:
                    # No command center, keep gathering
                    self.gather_time = 0
            else:
                # Continue gathering
                self.gather_time = 0
        
        return False
    
    def _update_returning(self, dt):
        """Handle returning to command center."""
        # Check if command center still exists
        if not self.command_center or (hasattr(self.command_center, 'health') and self.command_center.health <= 0):
            # Find a new command center
            self.command_center = self._find_nearest_command_center()
            if not self.command_center:
                # No command center to return to - go back to gathering
                self.state = "MOVING_TO_RESOURCE"
                return False
        
        # Move toward command center
        dist = distance(self.unit.position, self.command_center.position)
        
        # Use a larger threshold for command centers since they're bigger
        command_center_threshold = self.arrival_threshold + self.command_center.size / 2
        
        if dist < command_center_threshold:
            # We've arrived, slow down
            self.unit.velocity[0] *= 0.7
            self.unit.velocity[1] *= 0.7
            
            # If nearly stopped or close enough, start depositing
            if abs(self.unit.velocity[0]) < 5 and abs(self.unit.velocity[1]) < 5 or dist < command_center_threshold * 0.7:
                print(f"Starting deposit at distance {dist} from command center")
                self.state = "DEPOSITING"
                self.deposit_time = 0
        else:
            # Keep moving toward command center
            self._move_toward_target(self.command_center.position, dt)
            
            # Face the command center
            dx = self.command_center.position[0] - self.unit.position[0]
            dy = self.command_center.position[1] - self.unit.position[1]
            self.unit.angle = angle_between((0, 0), (dx, dy))
        
        return False
    
    def _update_depositing(self, dt):
        """Handle depositing resources at command center."""
        # Increment deposit time
        self.deposit_time += dt
        
        # Keep facing the command center
        dx = self.command_center.position[0] - self.unit.position[0]
        dy = self.command_center.position[1] - self.unit.position[1]
        self.unit.angle = angle_between((0, 0), (dx, dy))
        
        # Check if we're done depositing
        if self.deposit_time >= self.deposit_duration:
            # Deposit resources
            amount_to_deposit = self.unit.carrying_resources
            if hasattr(self.command_center, 'add_resources') and amount_to_deposit > 0:
                print(f"Depositing {amount_to_deposit} resources at command center")
                self.command_center.add_resources(amount_to_deposit)
                
                # Get game instance to verify resources were added
                from game import Game
                if Game.instance:
                    player_id = self.unit.player_id
                    print(f"Player {player_id} now has {Game.instance.resources[player_id]} resources")
            
            # Reset carrying amount
            self.unit.carrying_resources = 0
            
            # Return to resource
            self.state = "MOVING_TO_RESOURCE"
        
        return False
    
    def _find_nearest_command_center(self):
        """Find the nearest command center belonging to the same player."""
        from entities import CommandCenter
        from game import Game
        
        # Find all command centers for this player
        command_centers = [e for e in Game.instance.entities 
                         if isinstance(e, CommandCenter) and e.player_id == self.unit.player_id]
        
        if command_centers:
            # Return closest one
            return min(command_centers, 
                     key=lambda cc: distance(self.unit.position, cc.position))
        return None
    
    def _find_new_resource(self):
        """Find a new resource to gather from."""
        from entities import Resource
        from game import Game
        
        # Find all resources that aren't depleted
        resources = [e for e in Game.instance.entities 
                   if isinstance(e, Resource) and hasattr(e, 'amount') and e.amount > 0]
        
        if resources:
            # Return closest one
            return min(resources, 
                     key=lambda r: distance(self.unit.position, r.position))
        return None
    
    def _move_toward_target(self, target_position, dt):
        """Apply force to move toward target position."""
        return self._standardized_move_toward(target_position, dt, force_scale=self.force_scale)
    
    def exit(self):
        """Clean up when this behavior ends."""
        # Release slot if we have one
        if self.resource and self.slot_index != -1:
            self.resource.release_worker_from_slot(self.unit)

class AttackBehavior(Behavior):
    """Behavior for attacking a target with physics-based movement."""
    
    def __init__(self, unit, target):
        super().__init__(unit)
        self.target = target
        self.in_range = False
        self.chase_range = unit.aggro_range  # Use the unit's aggro range for chasing
        self.force_scale = unit.steering_force * 0.8  # Slightly reduced force for better control
        self.approach_complete = False  # Flag for when we've approached the target
        
        # Determine attack type based on unit
        from entities import Dot
        self.is_melee = isinstance(unit, Dot)  # Dots are melee units
    
    def update(self, dt):
        try:
            # Check if target is still valid
            from entities import Building
            
            if not self.target:
                return True
                
            # Check if target is still alive
            if not hasattr(self.target, 'health') or self.target.health <= 0:
                return True
            
            # Update attack cooldown
            if self.unit.attack_cooldown > 0:
                self.unit.attack_cooldown -= dt
            
            # Calculate distance to target
            dist = distance(self.unit.position, self.target.position)
            
            # If target moved out of chase range, stop attacking
            if dist > self.chase_range:
                return True
            
            # Handle movement based on attack type
            if self.is_melee:
                # Melee units need to get close to the target
                # When in range, they'll deal damage through collision in _handle_collisions
                if dist > self.unit.size:  # Need to be touching target
                    # Apply force toward target
                    self._move_toward_target(dt)
                    self.in_range = False
                else:
                    # We're in melee range, slow down
                    self.unit.velocity[0] *= 0.8
                    self.unit.velocity[1] *= 0.8
                    self.in_range = True
            else:
                # Ranged units should maintain distance
                if dist > self.unit.attack_range:
                    # Move toward target
                    self._move_toward_target(dt)
                    self.in_range = False
                else:
                    # In range, apply a smaller force to maintain position
                    self._maintain_attack_position(dt)
                    self.in_range = True
                    
                    # Fire if cooldown is ready
                    if self.unit.attack_cooldown <= 0:
                        self._fire_ranged_attack()
            
            # Update angle to face target
            if self.target:
                dx = self.target.position[0] - self.unit.position[0]
                dy = self.target.position[1] - self.unit.position[1]
                self.unit.angle = angle_between((0, 0), (dx, dy))
            
            return False
            
        except Exception as e:
            print(f"Error in AttackBehavior: {e}")
            return True
    
    def _move_toward_target(self, dt):
        """Move toward the attack target."""
        if not self.target:
            return
            
        return self._standardized_move_toward(self.target.position, dt)
    
    def _maintain_attack_position(self, dt):
        """Apply forces to maintain optimal attack position."""
        if not self.target:
            return
            
        # Calculate direction vector to target
        dx = self.target.position[0] - self.unit.position[0]
        dy = self.target.position[1] - self.unit.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Calculate optimal attack distance (75% of attack range)
            optimal_dist = self.unit.attack_range * 0.75
            
            # Determine if we need to move closer or further
            distance_factor = (dist - optimal_dist) / optimal_dist
            
            # Apply a weak force to maintain distance
            if abs(distance_factor) > 0.1:  # Only adjust if needed
                # Normalize direction
                dir_x = dx / dist
                dir_y = dy / dist
                
                # Scale force based on how far we are from optimal position
                force_scale = min(self.force_scale * 0.5, self.force_scale * abs(distance_factor))
                
                # Move toward or away from target
                if distance_factor < 0:  # Too close
                    self.unit.apply_force(-dir_x * force_scale, -dir_y * force_scale)
                else:  # Too far
                    self.unit.apply_force(dir_x * force_scale, dir_y * force_scale)
            
            # Apply a small damping to velocity to avoid orbiting
            self.unit.velocity[0] *= 0.95
            self.unit.velocity[1] *= 0.95
    
    def _fire_ranged_attack(self):
        """Fire a ranged attack at the target."""
        if not self.target or not hasattr(self.target, 'take_damage'):
            return
            
        # Apply damage to target
        damage = self.unit.attack_damage
        self.target.take_damage(damage)
        
        # Reset attack cooldown
        self.unit.attack_cooldown = self.unit.attack_cooldown_max
        
        # Show attack effect
        self.unit.show_attack_effect = True
        self.unit.effect_timer = 0
    
    def is_finished(self):
        return not self.target or not hasattr(self.target, 'health') or self.target.health <= 0
        
    def exit(self):
        """Clean up when this behavior ends."""
        pass

class HoldPositionBehavior(Behavior):
    """Behavior for holding position and attacking enemies in range."""
    
    def __init__(self, unit):
        super().__init__(unit)
        # Store the position to hold
        self.hold_position = list(unit.position)
        self.check_enemies_timer = 0
        self.check_enemies_interval = 0.3  # How often to check for enemies
        self.attacking_target = None
        self.position_threshold = 20.0  # How far unit can drift from hold position
    
    def update(self, dt):
        # First apply a damping force to slow down
        self.unit.velocity[0] *= 0.9
        self.unit.velocity[1] *= 0.9
        
        # Check if we've drifted too far from hold position
        dist_from_hold = distance(self.unit.position, self.hold_position)
        if dist_from_hold > self.position_threshold:
            # Apply force to move back to hold position
            self._return_to_position(dt)
        
        # Check for enemies to attack
        self.check_enemies_timer += dt
        if self.check_enemies_timer >= self.check_enemies_interval:
            self.check_enemies_timer = 0
            
            # If we have a target, check if it's still valid
            if self.attacking_target:
                if (not hasattr(self.attacking_target, 'health') or 
                    self.attacking_target.health <= 0 or
                    distance(self.unit.position, self.attacking_target.position) > self.unit.aggro_range):
                    self.attacking_target = None
            
            # If no target, look for a new one
            if not self.attacking_target:
                self.attacking_target = self._find_nearest_enemy()
        
        # Attack the target if we have one
        if self.attacking_target:
            # Update attack cooldown
            if self.unit.attack_cooldown > 0:
                self.unit.attack_cooldown -= dt
            
            # Calculate distance to target
            target_dist = distance(self.unit.position, self.attacking_target.position)
            
            # Determine if we're in attack range
            from entities import Dot
            is_melee = isinstance(self.unit, Dot)
            
            if is_melee:
                # Melee units need to be close to target
                if target_dist <= self.unit.size:
                    # In melee range, deliver damage
                    if self.unit.attack_cooldown <= 0:
                        self._apply_melee_damage(self.attacking_target)
                else:
                    # Only move slightly from hold position if needed
                    max_move_dist = min(self.position_threshold * 0.8, target_dist * 0.5)
                    if target_dist < self.unit.aggro_range * 0.5:  # Only chase if fairly close
                        self._move_slightly_toward(self.attacking_target.position, max_move_dist, dt)
            else:
                # Ranged units attack from distance
                if target_dist <= self.unit.attack_range:
                    # In range, attack
                    if self.unit.attack_cooldown <= 0:
                        self._fire_ranged_attack(self.attacking_target)
            
            # Face the target
            dx = self.attacking_target.position[0] - self.unit.position[0]
            dy = self.attacking_target.position[1] - self.unit.position[1]
            if dx != 0 or dy != 0:
                self.unit.angle = angle_between((0, 0), (dx, dy))
        
        return False
    
    def _return_to_position(self, dt):
        """Return to original hold position if pushed away."""
        if distance(self.unit.position, self.hold_position) > self.position_threshold:
            # Use standardized movement to return to position
            self._standardized_move_toward(self.hold_position, dt, force_scale=self.unit.steering_force * 0.3)
    
    def _move_slightly_toward(self, target_position, max_dist, dt):
        """Move slightly toward a target without going too far from hold position."""
        # Calculate vector to target
        dx = target_position[0] - self.unit.position[0]
        dy = target_position[1] - self.unit.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Only move if in range
        if dist > 0 and dist < max_dist:
            # Calculate limited movement target - don't go too far from hold position
            limit_dist = min(dist, max_dist * 0.5)
            limited_target = [
                self.unit.position[0] + (dx / dist) * limit_dist,
                self.unit.position[1] + (dy / dist) * limit_dist
            ]
            
            # Use standardized movement with reduced force
            self._standardized_move_toward(limited_target, dt, force_scale=self.unit.steering_force * 0.2)
    
    def _find_nearest_enemy(self):
        """Find the nearest enemy within aggro range."""
        if self.unit.attack_damage <= 0:
            return None
            
        # Import here to avoid circular imports
        from game import Game
        
        # Look for enemies in aggro range
        enemies = []
        for entity in Game.instance.entities:
            if (hasattr(entity, 'player_id') and entity.player_id != self.unit.player_id and
                hasattr(entity, 'health') and entity.health > 0):
                
                dist = distance(self.unit.position, entity.position)
                if dist <= self.unit.aggro_range:
                    enemies.append((entity, dist))
        
        # Sort by distance
        if enemies:
            enemies.sort(key=lambda x: x[1])
            return enemies[0][0]
        
        return None
    
    def _apply_melee_damage(self, target):
        """Apply melee damage to target."""
        if hasattr(target, 'take_damage') and self.unit.attack_cooldown <= 0:
            damage = self.unit.attack_damage
            target.take_damage(damage)
            self.unit.attack_cooldown = self.unit.attack_cooldown_max
            self.unit.show_attack_effect = True
            self.unit.effect_timer = 0
    
    def _fire_ranged_attack(self, target):
        """Fire a ranged attack at the target."""
        if hasattr(target, 'take_damage'):
            damage = self.unit.attack_damage
            target.take_damage(damage)
            self.unit.attack_cooldown = self.unit.attack_cooldown_max
            self.unit.show_attack_effect = True
            self.unit.effect_timer = 0
    
    def is_finished(self):
        # Hold position behavior only ends when explicitly changed
        return False

class AttackMoveBehavior(Behavior):
    """Behavior for moving to a position while attacking any enemies encountered."""
    
    def __init__(self, unit, target_position):
        super().__init__(unit)
        self.target_position = target_position
        self.force_scale = unit.steering_force * 0.8  # Slightly reduced force for attack-move
        self.arrival_threshold = unit.target_reached_threshold
        self.check_enemies_timer = 0
        self.check_enemies_interval = 0.4  # How often to check for enemies
        self.attacking_target = None
        
        # Determine attack type based on unit
        from entities import Dot
        self.is_melee = isinstance(unit, Dot)  # Dots are melee units
    
    def update(self, dt):
        # Check if we've arrived at the destination
        if distance(self.unit.position, self.target_position) < self.arrival_threshold:
            # Slow down as we approach
            self.unit.velocity[0] *= 0.8
            self.unit.velocity[1] *= 0.8
            
            # If nearly stopped, consider arrived
            if abs(self.unit.velocity[0]) < 5 and abs(self.unit.velocity[1]) < 5:
                return True
        
        # Check for enemies
        self.check_enemies_timer += dt
        if self.check_enemies_timer >= self.check_enemies_interval:
            self.check_enemies_timer = 0
            
            # Check if current target is still valid
            if self.attacking_target:
                if (not hasattr(self.attacking_target, 'health') or 
                    self.attacking_target.health <= 0 or
                    distance(self.unit.position, self.attacking_target.position) > self.unit.aggro_range):
                    self.attacking_target = None
            
            # If no target, check for new enemies
            if not self.attacking_target:
                self.attacking_target = self._find_nearest_enemy()
        
        # Handle attack or movement
        if self.attacking_target:
            # Update attack cooldown
            if self.unit.attack_cooldown > 0:
                self.unit.attack_cooldown -= dt
            
            target_dist = distance(self.unit.position, self.attacking_target.position)
            
            if self.is_melee:
                # For melee units, move toward target
                if target_dist > self.unit.size:
                    self._move_toward_target(self.attacking_target.position, dt)
                else:
                    # In melee range, slow down
                    self.unit.velocity[0] *= 0.8
                    self.unit.velocity[1] *= 0.8
                    
                    # Deal damage if cooldown ready
                    if self.unit.attack_cooldown <= 0:
                        self._apply_melee_damage(self.attacking_target)
            else:
                # For ranged units
                if target_dist <= self.unit.attack_range:
                    # In range for attack, slow down
                    self.unit.velocity[0] *= 0.9
                    self.unit.velocity[1] *= 0.9
                    
                    # Attack if cooldown ready
                    if self.unit.attack_cooldown <= 0:
                        self._fire_ranged_attack(self.attacking_target)
                else:
                    # Need to move closer
                    self._move_toward_target(self.attacking_target.position, dt)
            
            # Face the target
            dx = self.attacking_target.position[0] - self.unit.position[0]
            dy = self.attacking_target.position[1] - self.unit.position[1]
            if dx != 0 or dy != 0:
                self.unit.angle = angle_between((0, 0), (dx, dy))
        else:
            # No enemies, continue moving toward destination
            self._move_toward_target(self.target_position, dt)
        
        return False
    
    def _move_toward_target(self, target_position, dt):
        """Apply force to move toward target position."""
        return self._standardized_move_toward(target_position, dt, force_scale=self.force_scale)
    
    def _find_nearest_enemy(self):
        """Find the nearest enemy within aggro range."""
        if self.unit.attack_damage <= 0:
            return None
            
        # Import here to avoid circular imports
        from game import Game
        
        # Look for enemies in aggro range
        enemies = []
        for entity in Game.instance.entities:
            if (hasattr(entity, 'player_id') and entity.player_id != self.unit.player_id and
                hasattr(entity, 'health') and entity.health > 0):
                
                dist = distance(self.unit.position, entity.position)
                if dist <= self.unit.aggro_range:
                    enemies.append((entity, dist))
        
        # Sort by distance
        if enemies:
            enemies.sort(key=lambda x: x[1])
            return enemies[0][0]
        
        return None
    
    def _apply_melee_damage(self, target):
        """Apply melee damage to target."""
        if hasattr(target, 'take_damage'):
            damage = self.unit.attack_damage
            target.take_damage(damage)
            self.unit.attack_cooldown = self.unit.attack_cooldown_max
            self.unit.show_attack_effect = True
            self.unit.effect_timer = 0
    
    def _fire_ranged_attack(self, target):
        """Fire a ranged attack at the target."""
        if hasattr(target, 'take_damage'):
            damage = self.unit.attack_damage
            target.take_damage(damage)
            self.unit.attack_cooldown = self.unit.attack_cooldown_max
            self.unit.show_attack_effect = True
            self.unit.effect_timer = 0
    
    def is_finished(self):
        """Check if we've arrived at destination with no enemies."""
        # If we've reached the target position and aren't attacking anything
        if distance(self.unit.position, self.target_position) < self.arrival_threshold and not self.attacking_target:
            return True
        return False

class PatrolBehavior(Behavior):
    """Behavior for patrolling between two points with physics-based movement."""
    
    def __init__(self, unit, start_position, end_position):
        super().__init__(unit)
        self.start_position = list(start_position)  # Make a copy
        self.end_position = list(end_position)     # Make a copy
        self.current_target = list(end_position)   # Start by moving to end position
        self.moving_to_end = True                  # Direction flag
        self.force_scale = unit.steering_force * 0.9  # Slightly reduced force for patrol
        self.arrival_threshold = unit.target_reached_threshold * 1.5  # Larger threshold for patrol points
        
        # Attack properties
        self.chase_range = unit.aggro_range
        self.check_enemies_timer = 0
        self.check_enemies_interval = 0.5  # How often to check for enemies
        self.attacking_target = None
    
    def update(self, dt):
        # First, check for and handle enemies
        self.check_enemies_timer += dt
        if self.check_enemies_timer >= self.check_enemies_interval:
            self.check_enemies_timer = 0
            enemy = self._check_for_enemies()
            if enemy:
                # If we found an enemy, attack it
                self.attacking_target = enemy
                
                # We'll keep track of the patrol state, but switch to attack mode
                from entities import Dot
                if isinstance(self.unit, Dot):
                    # For melee units, we need to get close
                    self._move_toward_target(self.attacking_target.position, dt)
                    
                    # Deal damage if close enough
                    if distance(self.unit.position, self.attacking_target.position) <= self.unit.size and self.unit.attack_cooldown <= 0:
                        self._apply_melee_damage(self.attacking_target)
                else:
                    # For ranged units
                    if distance(self.unit.position, self.attacking_target.position) <= self.unit.attack_range:
                        # In range, slow down and attack
                        self.unit.velocity[0] *= 0.9
                        self.unit.velocity[1] *= 0.9
                        
                        if self.unit.attack_cooldown <= 0:
                            self._fire_ranged_attack(self.attacking_target)
                    else:
                        # Move towards enemy
                        self._move_toward_target(self.attacking_target.position, dt)
                
                # Update attack cooldown
                if self.unit.attack_cooldown > 0:
                    self.unit.attack_cooldown -= dt
                
                # Update angle to face target
                dx = self.attacking_target.position[0] - self.unit.position[0]
                dy = self.attacking_target.position[1] - self.unit.position[1]
                self.unit.angle = angle_between((0, 0), (dx, dy))
                
                # Check if target is dead or out of range
                if (not hasattr(self.attacking_target, 'health') or 
                    self.attacking_target.health <= 0 or
                    distance(self.unit.position, self.attacking_target.position) > self.chase_range):
                    # Go back to patrolling
                    self.attacking_target = None
                
                # Skip normal patrol behavior when attacking
                if self.attacking_target:
                    return False
        
        # If no enemies, continue patrolling
        # Calculate distance to current target
        dist = distance(self.unit.position, self.current_target)
        
        # If reached current target, switch direction
        if dist < self.arrival_threshold:
            # Slow down as we reach the patrol point
            self.unit.velocity[0] *= 0.7
            self.unit.velocity[1] *= 0.7
            
            # If nearly stopped, switch target
            if abs(self.unit.velocity[0]) < 10 and abs(self.unit.velocity[1]) < 10:
                self.moving_to_end = not self.moving_to_end
                self.current_target = self.end_position if self.moving_to_end else self.start_position
        
        # Move toward current target
        self._move_toward_target(self.current_target, dt)
        
        return False
    
    def _move_toward_target(self, target_position, dt):
        """Apply force to move toward target."""
        return self._standardized_move_toward(target_position, dt)
    
    def _check_for_enemies(self):
        """Check for enemies in aggro range."""
        if self.unit.attack_damage <= 0 or self.unit.attack_range <= 0:
            return None
            
        # Import here to avoid circular imports
        from game import Game
        
        # Look for enemies in aggro range
        enemies = [e for e in Game.instance.entities 
                   if hasattr(e, 'player_id') and e.player_id != self.unit.player_id
                   and hasattr(e, 'health') and e.health > 0]
        
        # Find closest enemy in aggro range
        enemies_in_range = []
        for enemy in enemies:
            if distance(self.unit.position, enemy.position) <= self.unit.aggro_range:
                enemies_in_range.append(enemy)
        
        if enemies_in_range:
            # Target closest enemy
            return min(enemies_in_range, 
                     key=lambda e: distance(self.unit.position, e.position))
        
        return None
    
    def _apply_melee_damage(self, target):
        """Apply melee damage to target on collision."""
        if hasattr(target, 'take_damage') and self.unit.attack_cooldown <= 0:
            damage = self.unit.attack_damage
            target.take_damage(damage)
            self.unit.attack_cooldown = self.unit.attack_cooldown_max
            self.unit.show_attack_effect = True
            self.unit.effect_timer = 0
    
    def _fire_ranged_attack(self, target):
        """Fire a ranged attack at the target."""
        if not target or not hasattr(target, 'take_damage'):
            return
            
        # Apply damage to target
        damage = self.unit.attack_damage
        target.take_damage(damage)
        
        # Reset attack cooldown
        self.unit.attack_cooldown = self.unit.attack_cooldown_max
        
        # Show attack effect
        self.unit.show_attack_effect = True
        self.unit.effect_timer = 0
    
    def is_finished(self):
        """Patrol behavior only ends when explicitly changed."""
        return False 