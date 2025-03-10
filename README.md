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
- Collision detection and physics
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
- `IdleBehavior`: Default when not doing anything
- `MoveBehavior`: Moving to a position
- `GatherBehavior`: Gathering resources
- `AttackBehavior`: Attacking a target
- `HoldPositionBehavior`: Staying in place but attacking enemies in range
- `AttackMoveBehavior`: Moving to a position while attacking enemies encountered

## Performance Considerations

- The game uses simple vector graphics for efficient rendering
- Collision detection uses rectangles and spatial partitioning
- Formation movement with steering behaviors for smooth unit movement
- Error handling for robustness during extended gameplay

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
