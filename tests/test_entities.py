import sys
import os
import pygame
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entities import Entity, Unit, Square, Resource
from config import UnitConfig, ResourceConfig


class TestEntity:
    """Tests for the base Entity class."""
    
    def test_entity_initialization(self):
        """Test that an entity initializes correctly."""
        position = [100, 200]
        size = 30
        color = (255, 0, 0)  # RED
        
        entity = Entity(position, size, color)
        
        assert entity.position == position
        assert entity.size == size
        assert entity.color == color
        assert entity.selected == False
        assert isinstance(entity.rect, pygame.Rect)
        assert entity.rect.x == position[0] - size/2
        assert entity.rect.y == position[1] - size/2
        assert entity.rect.width == size
        assert entity.rect.height == size
    
    def test_entity_selection(self):
        """Test that selection and deselection work."""
        entity = Entity([100, 100], 20)
        
        # Initially not selected
        assert entity.selected == False
        
        # Select
        entity.select()
        assert entity.selected == True
        
        # Deselect
        entity.deselect()
        assert entity.selected == False
        
    def test_contains_point(self):
        """Test that point containment checks work."""
        entity = Entity([100, 100], 20)
        
        # Points inside the entity
        assert entity.contains_point((100, 100))  # Center
        assert entity.contains_point((90, 90))    # Top-left quadrant
        assert entity.contains_point((110, 90))   # Top-right quadrant
        assert entity.contains_point((90, 110))   # Bottom-left quadrant
        assert entity.contains_point((110, 110))  # Bottom-right quadrant
        
        # Points outside the entity
        assert not entity.contains_point((80, 80))    # Too far top-left
        assert not entity.contains_point((120, 80))   # Too far top-right
        assert not entity.contains_point((80, 120))   # Too far bottom-left
        assert not entity.contains_point((120, 120))  # Too far bottom-right


class TestUnit:
    """Tests for the Unit class."""
    
    def test_unit_initialization(self):
        """Test that a unit initializes correctly."""
        position = [100, 200]
        size = 15
        color = (0, 0, 255)  # BLUE
        max_health = 50
        speed = 100
        player_id = 0
        
        unit = Unit(position, size, color, max_health, speed, player_id)
        
        assert unit.position == position
        assert unit.size == size
        assert unit.color == color
        assert unit.max_health == max_health
        assert unit.health == max_health  # Health starts at max
        assert unit.speed == speed
        assert unit.player_id == player_id
        assert isinstance(unit.current_behavior, object)  # Should have some behavior
        
    def test_unit_take_damage(self):
        """Test that taking damage works."""
        unit = Unit([100, 100], 15, (0, 0, 255), 50, 100, 0)
        
        # Initial health
        assert unit.health == 50
        
        # Take some damage
        destroyed = unit.take_damage(20)
        assert unit.health == 30
        assert not destroyed
        
        # Take fatal damage
        destroyed = unit.take_damage(40)
        assert unit.health == -10
        assert destroyed


class TestSquare:
    """Tests for the Square worker unit."""
    
    def test_square_initialization(self):
        """Test that a square worker initializes correctly."""
        position = [100, 200]
        player_id = 0
        
        square = Square(position, player_id)
        
        assert square.position == position
        assert square.size == UnitConfig.WORKER_SIZE
        assert square.max_health == UnitConfig.WORKER_HEALTH
        assert square.health == UnitConfig.WORKER_HEALTH
        assert square.speed == UnitConfig.WORKER_SPEED
        assert square.player_id == player_id
        assert square.max_carry_capacity == UnitConfig.WORKER_CARRY_CAPACITY
        
    @patch('behaviors.GatherBehavior')
    def test_square_gather(self, mock_gather_behavior):
        """Test that the gather method works."""
        # Setup
        square = Square([100, 100], 0)
        resource = MagicMock(spec=Resource)
        
        # Case 1: No slot available
        resource.assign_harvest_slot.return_value = None
        mock_gather_behavior.return_value = "mock_behavior"
        
        square.gather(resource)
        
        # Check behavior set without moving
        resource.assign_harvest_slot.assert_called_once_with(square)
        assert square.current_behavior == "mock_behavior"
        
        # Case 2: Slot available
        resource.reset_mock()
        mock_gather_behavior.reset_mock()
        resource.assign_harvest_slot.return_value = [150, 150]
        square.move_to = MagicMock()
        
        square.gather(resource)
        
        # Check moved to slot and behavior set
        resource.assign_harvest_slot.assert_called_once_with(square)
        square.move_to.assert_called_once_with([150, 150])
        assert square.current_behavior == "mock_behavior"


class TestResource:
    """Tests for the Resource class."""
    
    def test_resource_initialization(self):
        """Test that a resource initializes correctly."""
        position = [300, 300]
        amount = 400
        
        resource = Resource(position, amount)
        
        assert resource.position == position
        assert resource.amount == amount
        assert len(resource.slots) == ResourceConfig.NUM_SLOTS
        assert all(slot is None for slot in resource.slots)
        
    def test_resource_extract(self):
        """Test resource extraction."""
        resource = Resource([300, 300], 100)
        
        # Extract some resources
        extracted = resource.extract(30)
        assert extracted == 30
        assert resource.amount == 70
        
        # Extract more than available
        extracted = resource.extract(100)
        assert extracted == 70  # Only get what's left
        assert resource.amount == 0
        
        # Extract from empty resource
        extracted = resource.extract(10)
        assert extracted == 0
        assert resource.amount == 0 