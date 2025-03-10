# Vector RTS

A real-time strategy game with vector-based graphics inspired by classic games like Asteroids and StarCraft 2.

## Game Features

- Vector-based graphics for all game elements
- Resource gathering with worker units (squares)
- Base building and unit production
- Multiple unit types with different abilities:
  - Workers (squares): Gather resources and build structures
  - Fast units (dots/circles): Quick melee attackers
  - Heavy units (triangles): Slower ranged attackers with higher damage
- Building types:
  - Command Center: Main building, collects resources, produces workers
  - Unit Buildings: Produces combat units (dots and triangles)
- Physics-based movement with unit-specific properties
- Standardized, physics-based movement across all behaviors
- Collision detection and realistic unit interactions
- Formation movement for unit groups
- Enemy AI with resource gathering and combat behavior
- Debug visualization features

## Getting Started

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the game:
   ```
   python main.py
   ```

## Controls

- Left-click to select units or buildings
- Right-click to:
  - Move selected units to a location
  - Gather resources (when clicking on a mineral patch with workers)
  - Attack enemy units or buildings (when clicking on enemies with combat units)
  - Set rally points (when clicking with a building selected)
- Drag with left mouse button to select multiple units
- B: Enter build mode to construct a Unit Building (requires 150 resources)
- A: Toggle attack-move mode (units will attack enemies encountered on their way)
- P: Toggle patrol mode for combat units (units will patrol between current position and clicked location)
- H: Order selected units to hold position (will attack enemies in range without moving)
- S: Stop all selected units (change to idle behavior)
- D: Toggle debug visualization (shows slots, paths, and collision info)
- Escape: Cancel current build/attack mode

## Recent Updates

### Standardized Movement System (May 2024)
- Implemented unified movement logic across all unit behaviors
- Added physics-based movement with momentum, inertia, and deceleration
- Created unit-specific physics properties for distinctive movement styles
- Fixed oscillation and jittering issues at movement destinations
- Optimized resource gathering with improved collision handling
- Enhanced patrol mode with dedicated 'P' key and visual indicator

### REFACTOR1 Branch (March 2024)
- Fixed the patrol feature to work properly with combat units
- Improved selection box rendering for better unit selection
- Updated renderer to handle delta time for animations
- Fixed issues with coordinate systems in the UI
- Enhanced combat behavior to properly detect and attack enemies during patrol

## Gameplay

The goal is to build an army and destroy the enemy command center. Start by gathering minerals using "square" worker units, then build a unit production facility to create combat units (dots and triangles). Use these combat units to attack and destroy the enemy base.

## Code Architecture

The game is structured using the following main components:

### Main Components

- `main.py`: Entry point that initializes the game and runs the main loop
- `game.py`: Main game class that manages game state, entities, and user input
- `entities.py`: Entity classes for units, buildings, and resources
- `behaviors.py`: Behavior classes that implement unit AI (movement, gathering, attacking)
- `renderer.py`: Handles rendering game elements
- `utils.py`: Utility functions and constants
- `config.py`: Centralized configuration for all game parameters

### Entity Hierarchy

- `Entity`: Base class for all game objects
  - `Unit`: Base class for all movable units
    - `Square`: Worker unit (gathers resources)
    - `Dot`: Fast melee combat unit
    - `Triangle`: Slower ranged combat unit
  - `Building`: Base class for structures
    - `CommandCenter`: Main building, produces workers
    - `UnitBuilding`: Produces combat units
  - `Resource`: Mineral patches for gathering

### Behavior System

Units use a behavior-based AI system where each unit can have one active behavior:
- `Behavior`: Base class with standardized movement method used by all behaviors
- `IdleBehavior`: Default when not doing anything
- `MoveBehavior`: Moving to a position with physics-based momentum
- `GatherBehavior`: Gathering resources (moving, harvesting, returning, depositing)
- `AttackBehavior`: Attacking a target
- `HoldPositionBehavior`: Staying in place but attacking enemies in range
- `AttackMoveBehavior`: Moving to a position while attacking enemies encountered
- `PatrolBehavior`: Patrolling between two points and attacking enemies in range

### Movement System

The game uses a physics-based movement system:
- `_standardized_move_toward`: Common movement method in the base Behavior class
- Each unit type has custom physics properties:
  - Mass: Controls momentum and collision response
  - Friction: Affects how quickly units slow down
  - Restitution: Controls bouncing during collisions
  - Steering Force: Influences turning ability and acceleration

## Performance Considerations

- The game uses simple vector graphics for efficient rendering
- Collision detection uses rectangles and spatial partitioning
- Formation movement with steering behaviors for smooth unit movement
- Error handling for robustness during extended gameplay
- Physics optimizations with delta time clamping and velocity cutoff

## Development Notes

### Key Physics Parameters
- **Unit Mass**: Controls momentum and collision impact
  - Square (Worker): 1.3x size
  - Dot (Melee): 1.4x size
  - Triangle (Ranged): 3.0x size

- **Friction**: Higher values stop faster
  - Square: 0.96
  - Dot: 0.95
  - Triangle: 0.97

- **Target Reached Thresholds**: Distance at which to consider target reached
  - Square: 25.0
  - Dot: 35.0
  - Triangle: 45.0

### Movement Behavior
- `_standardized_move_toward`: The core movement method that all behaviors use
- Inside an arrival threshold, units will gradually slow down
- Deceleration is smooth and proportional to distance from target

### Known Issues
- If window loses focus, physics may behave erratically (added dt clamping to mitigate)
- Large groups of units may slow down the game due to collision calculations
- Very large maps might require spatial partitioning optimization

## Future Development Plans

Potential features for future development:
- Additional unit types with unique abilities
- Technology upgrades and research system
- Multiple resource types
- Larger maps with terrain features
- Improved pathfinding using A* algorithm
- Fog of war system
- Multiplayer support
- Map editor

## Contributing

Contributions are welcome! Here are some guidelines:
1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Ensure all game features still work
5. Submit a pull request
