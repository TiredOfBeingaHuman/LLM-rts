# Vector RTS Project Structure

This document explains the organization of the Vector RTS codebase to help developers quickly understand the project architecture.

## Directory Structure

```
vector-rts/
├── main.py               # Entry point for the game
├── game.py               # Main game class and game loop
├── entities.py           # Entity classes (units, buildings, resources)
├── behaviors.py          # AI behavior system for units
├── renderer.py           # Graphics rendering utilities
├── utils.py              # Utility functions and helpers
├── config.py             # Game configuration and constants
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── PROJECT_STRUCTURE.md  # This document
├── .gitignore            # Git ignore file
└── tests/                # Unit tests
    ├── test_entities.py  # Tests for entity system
    └── ...               # Other test files
```

## Key Components and Architecture

### Entity System

The game uses a component-based architecture for entities:

- `Entity`: Base class for all game objects
  - Manages position, size, and selection state
  - Implements basic collision detection
  - Handles physics properties (friction, mass, restitution)

- `Unit`: Extends Entity for movable game objects
  - Implements health, movement, and behaviors
  - Handles collision resolution
  - Customizable physics properties per unit type

- `Building`: Extends Entity for structures
  - Manages production queues and rally points
  - Handles resource storage

- `Resource`: Extends Entity for mineral patches
  - Implements resource harvesting slot system
  - Manages resource depletion

### Movement System

The game uses a physics-based movement system with the following features:

- **Standardized Movement Logic**: All movement is handled through a common method in the base Behavior class
- **Velocity-Based Movement**: Units move using physics with forces, momentum, and friction
- **Inertia and Deceleration**: Smooth arrival with progressive deceleration when approaching targets
- **Unit-Specific Physics**: Each unit type has tailored physics properties:
  - Mass: Affects momentum and collision response
  - Friction: Controls how quickly units slow down
  - Restitution: Determines bounciness during collisions
  - Steering Force: Influences turning ability and acceleration

### Behavior System

Units use a behavior-based AI system where each unit has one active behavior object that determines what the unit does each frame:

- `Behavior`: Base abstract class for all behaviors
  - Provides the standardized movement method used by all behaviors
- `IdleBehavior`: Default waiting behavior
- `MoveBehavior`: Moving to a position with physics-based momentum
- `GatherBehavior`: Resource gathering state machine (moving, harvesting, returning, depositing)
- `AttackBehavior`: Attacking enemy units/buildings
- `HoldPositionBehavior`: Defensive stance
- `AttackMoveBehavior`: Moving while attacking enemies in path
- `PatrolBehavior`: Patrolling between two points and attacking enemies in range

### Game Manager

The `Game` class manages the overall game state:

- Maintains lists of all entities
- Processes player input
- Updates all entities each frame
- Manages the UI and rendering
- Implements the enemy AI
- Handles special visualizations for patrol and attack-move modes

### Configuration

Game parameters are centralized in `config.py` to facilitate:
- Easy game balancing
- Gameplay tweaking
- Enhanced maintainability
- Unit-specific configurations:
  - Size, health, speed
  - Attack properties (damage, range, cooldown)
  - Physics properties (adjusted in entity classes)

### Event System

The game uses pygame events for handling user input:
- Mouse clicks for unit selection and commands
- Keyboard shortcuts for game actions:
  - P: Patrol mode
  - A: Attack-move mode
  - H: Hold position
  - S: Stop/idle
  - B: Build mode
  - D: Debug visualization
- UI button interactions

## Recent Improvements

### Standardized Movement System (May 2024)
- Unified movement logic across all behavior types
- Physics-based movement with consistent deceleration
- Unit-specific physics properties
- Fixed oscillation and jittering issues

### Resource Gathering Optimization
- Fixed resource extraction and delivery
- Improved collision handling with command centers
- Streamlined deposit process

### Patrol Mode Enhancement
- Dedicated 'P' key for patrol mode
- Blue visualization for patrol cursor
- Fixed issues with patrol routing

## Development Workflow

1. For implementing new features:
   - Add necessary parameters to `config.py`
   - Implement new behavior classes if needed
   - Extend existing entity classes or create new ones
   - Update the game loop to handle the new feature
   - Write tests for the new functionality

2. For bug fixes:
   - Add a test that demonstrates the bug
   - Fix the underlying issue
   - Verify the test passes
   - Consider adding error handling to prevent similar issues

## Best Practices

1. **Type Hints**: Use Python type hints for all function parameters and return values
2. **Documentation**: Add docstrings to all classes and methods
3. **Error Handling**: Implement robust error handling for better stability
4. **Testing**: Write unit tests for new functionality
5. **Configuration**: Keep game parameters in the config file, not hardcoded
6. **Separation of Concerns**: Keep rendering, game logic, and input handling separate
7. **Physics Consistency**: When modifying physics parameters, test across all unit types and behaviors
8. **Movement Consistency**: Use the standardized movement method for all new behaviors 