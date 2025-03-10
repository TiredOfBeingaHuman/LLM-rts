"""
Configuration settings for the Vector RTS game.
This file centralizes game parameters to make balancing and configuration easier.
"""

# Display settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
UI_PANEL_HEIGHT = 150
MINIMAP_SIZE = 200
FPS = 60
DEBUG_MODE = False  # Set to True to show debug info by default

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)

# Game settings
STARTING_RESOURCES = 200

# Unit settings
class UnitConfig:
    # Worker (Square)
    WORKER_SIZE = 15
    WORKER_HEALTH = 50
    WORKER_SPEED = 100
    WORKER_CARRY_CAPACITY = 10
    WORKER_COST = 50
    WORKER_BUILD_TIME = 5.0
    
    # Fast Unit (Dot)
    DOT_SIZE = 15
    DOT_HEALTH = 30
    DOT_SPEED = 150
    DOT_ATTACK_DAMAGE = 10
    DOT_ATTACK_RANGE = 50
    DOT_ATTACK_COOLDOWN = 0.5
    DOT_AGGRO_RANGE = 150
    DOT_COST = 75
    DOT_BUILD_TIME = 6.0
    
    # Heavy Unit (Triangle)
    TRIANGLE_SIZE = 20
    TRIANGLE_HEALTH = 70
    TRIANGLE_SPEED = 80
    TRIANGLE_ATTACK_DAMAGE = 15
    TRIANGLE_ATTACK_RANGE = 150
    TRIANGLE_ATTACK_COOLDOWN = 1.0
    TRIANGLE_AGGRO_RANGE = 200
    TRIANGLE_COST = 100
    TRIANGLE_BUILD_TIME = 7.0

# Building settings
class BuildingConfig:
    # Command Center
    COMMAND_CENTER_SIZE = 60
    COMMAND_CENTER_HEALTH = 1000
    
    # Unit Building
    UNIT_BUILDING_SIZE = 50
    UNIT_BUILDING_HEALTH = 500
    UNIT_BUILDING_COST = 150

# Resource settings
class ResourceConfig:
    RESOURCE_SIZE = 30
    RESOURCE_AMOUNT = 500
    RESOURCE_GATHER_RATE = 2
    HARVEST_TIME = 1.5
    DEPOSIT_TIME = 0.5
    NUM_SLOTS = 4  # Number of harvest slots per resource

# AI settings
class AIConfig:
    ATTACK_PROBABILITY = 0.01  # Chance per update to start an attack
    MAX_ARMY_SIZE = 10         # Size at which AI will attack

# Movement and collision settings
class MovementConfig:
    # Physics parameters
    FRICTION = 0.95            # Base friction coefficient 
    RESTITUTION = 0.5          # Bounciness factor for collisions
    
    # Unit steering parameters
    STEERING_BASE_FORCE = 1000  # Base force for steering
    MAX_SPEED_MULTIPLIER = 1.2  # Maximum speed as a multiplier of unit.speed
    
    # Group movement parameters
    FORMATION_BASE_RADIUS = 20
    FORMATION_SCALE_FACTOR = 10
    SEPARATION_WEIGHT = 0.4     # Weight for separation steering
    SEPARATION_RADIUS = 30      # Radius for separation behavior
    COHESION_WEIGHT = 0.1       # Weight for cohesion steering (stay with group)
    COHESION_RADIUS = 80        # Radius for cohesion behavior
    
    # Arrival behavior
    ARRIVAL_THRESHOLD = 20.0    # Distance at which target is considered reached
    SLOWDOWN_RADIUS = 50.0      # Start slowing down when this close to target
    
    # Collision parameters
    COLLISION_PUSH_FORCE = 300  # Force applied when colliding with static objects
    MELEE_ATTACK_DISTANCE = 5.0 # Distance for melee damage to be applied 