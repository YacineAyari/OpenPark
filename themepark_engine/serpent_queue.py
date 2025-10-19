from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum

class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"

class MovementType(Enum):
    STRAIGHT = "straight"
    TURN_RIGHT = "turn_right"
    TURN_LEFT = "turn_left"
    BRANCH = "branch"

@dataclass
class Movement:
    """Represents a movement in the queue sequence"""
    movement_type: MovementType
    direction: Optional[Direction] = None

@dataclass
class QueueTile:
    """Represents a queue tile with position and direction"""
    x: int
    y: int
    direction: Direction
    tile_type: str  # "straight", "turn_right", "turn_left", "branch"
    
    def __iter__(self):
        return iter((self.x, self.y))

class SerpentQueuePlacer:
    """Places queue tiles following a serpent pattern"""
    
    def __init__(self):
        self.direction_map = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        
        self.turn_right_map = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH
        }
        
        self.turn_left_map = {
            Direction.NORTH: Direction.WEST,
            Direction.WEST: Direction.SOUTH,
            Direction.SOUTH: Direction.EAST,
            Direction.EAST: Direction.NORTH
        }
    
    def place_serpent_queue(self, start_x: int, start_y: int, initial_direction: Direction, 
                           movements: List[Movement], grid) -> List[QueueTile]:
        """Place a serpent queue following the movement sequence"""
        tiles = []
        x, y = start_x, start_y
        current_direction = initial_direction
        
        # Place the first tile
        first_tile = QueueTile(x, y, current_direction, "straight")
        tiles.append(first_tile)
        
        for movement in movements:
            if movement.movement_type == MovementType.STRAIGHT:
                x, y = self._move_position(x, y, current_direction)
                tile = QueueTile(x, y, current_direction, "straight")
                tiles.append(tile)
                
            elif movement.movement_type == MovementType.TURN_RIGHT:
                # Place turn tile at current position
                turn_tile = QueueTile(x, y, current_direction, "turn_right")
                tiles.append(turn_tile)
                
                # Update direction
                current_direction = self.turn_right_map[current_direction]
                
                # Move to next position
                x, y = self._move_position(x, y, current_direction)
                next_tile = QueueTile(x, y, current_direction, "straight")
                tiles.append(next_tile)
                
            elif movement.movement_type == MovementType.TURN_LEFT:
                # Place turn tile at current position
                turn_tile = QueueTile(x, y, current_direction, "turn_left")
                tiles.append(turn_tile)
                
                # Update direction
                current_direction = self.turn_left_map[current_direction]
                
                # Move to next position
                x, y = self._move_position(x, y, current_direction)
                next_tile = QueueTile(x, y, current_direction, "straight")
                tiles.append(next_tile)
                
            elif movement.movement_type == MovementType.BRANCH:
                # Place branch tile
                branch_tile = QueueTile(x, y, current_direction, "branch")
                tiles.append(branch_tile)
                # Note: Branch handling would require more complex logic
        
        return tiles
    
    def _move_position(self, x: int, y: int, direction: Direction) -> Tuple[int, int]:
        """Move position based on direction"""
        dx, dy = self.direction_map[direction]
        return x + dx, y + dy
    
    def create_serpent_pattern(self, width: int, height: int, start_x: int, start_y: int) -> List[Movement]:
        """Create a serpent pattern that fits in the given dimensions"""
        movements = []
        current_direction = Direction.EAST
        
        # Calculate how many tiles we can fit
        total_tiles = width * height
        tiles_placed = 1  # First tile already placed
        
        for row in range(height):
            if row % 2 == 0:  # Even rows: left to right
                # Move right for (width - 1) tiles
                for _ in range(width - 1):
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.STRAIGHT))
                        tiles_placed += 1
                
                # Turn down at the end of row (except last row)
                if row < height - 1 and tiles_placed < total_tiles:
                    movements.append(Movement(MovementType.TURN_RIGHT))
                    tiles_placed += 1
                    
                    # Move down one tile
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.STRAIGHT))
                        tiles_placed += 1
                    
                    # Turn right
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.TURN_RIGHT))
                        tiles_placed += 1
                        
            else:  # Odd rows: right to left
                # Move left for (width - 1) tiles
                for _ in range(width - 1):
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.STRAIGHT))
                        tiles_placed += 1
                
                # Turn down at the end of row (except last row)
                if row < height - 1 and tiles_placed < total_tiles:
                    movements.append(Movement(MovementType.TURN_LEFT))
                    tiles_placed += 1
                    
                    # Move down one tile
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.STRAIGHT))
                        tiles_placed += 1
                    
                    # Turn left
                    if tiles_placed < total_tiles:
                        movements.append(Movement(MovementType.TURN_LEFT))
                        tiles_placed += 1
        
        return movements
    
    def create_custom_pattern(self, pattern_string: str) -> List[Movement]:
        """Create movements from a pattern string like 'RRRDRRRDLLL'"""
        movements = []
        
        for char in pattern_string.upper():
            if char == 'R':  # Right
                movements.append(Movement(MovementType.STRAIGHT, Direction.EAST))
            elif char == 'L':  # Left
                movements.append(Movement(MovementType.STRAIGHT, Direction.WEST))
            elif char == 'U':  # Up
                movements.append(Movement(MovementType.STRAIGHT, Direction.NORTH))
            elif char == 'D':  # Down
                movements.append(Movement(MovementType.STRAIGHT, Direction.SOUTH))
            elif char == 'TR':  # Turn Right
                movements.append(Movement(MovementType.TURN_RIGHT))
            elif char == 'TL':  # Turn Left
                movements.append(Movement(MovementType.TURN_LEFT))
            elif char == 'B':  # Branch
                movements.append(Movement(MovementType.BRANCH))
        
        return movements

class SerpentQueueManager:
    """Manages serpent queue placement and validation"""
    
    def __init__(self):
        self.placer = SerpentQueuePlacer()
        self.placed_queues = []
    
    def place_serpent_queue(self, start_x: int, start_y: int, initial_direction: Direction, 
                           movements: List[Movement], grid) -> bool:
        """Place a serpent queue and validate placement"""
        # Check if placement is valid
        if not self._validate_placement(start_x, start_y, movements, grid):
            return False
        
        # Place the tiles
        tiles = self.placer.place_serpent_queue(start_x, start_y, initial_direction, movements, grid)
        
        # Apply tiles to grid
        from .map import TILE_QUEUE_PATH
        for tile in tiles:
            if grid.in_bounds(tile.x, tile.y):
                grid.set(tile.x, tile.y, TILE_QUEUE_PATH)
        
        # Store the queue
        self.placed_queues.append({
            'start_pos': (start_x, start_y),
            'direction': initial_direction,
            'movements': movements,
            'tiles': tiles
        })
        
        return True
    
    def _validate_placement(self, start_x: int, start_y: int, movements: List[Movement], grid) -> bool:
        """Validate that the placement doesn't conflict with existing tiles"""
        x, y = start_x, start_y
        current_direction = Direction.EAST  # Default direction
        
        # Check if start position is valid
        if not grid.in_bounds(x, y) or grid.get(x, y) != 0:  # 0 = TILE_GRASS
            return False
        
        for movement in movements:
            if movement.movement_type == MovementType.STRAIGHT:
                x, y = self.placer._move_position(x, y, current_direction)
            elif movement.movement_type == MovementType.TURN_RIGHT:
                current_direction = self.placer.turn_right_map[current_direction]
                x, y = self.placer._move_position(x, y, current_direction)
            elif movement.movement_type == MovementType.TURN_LEFT:
                current_direction = self.placer.turn_left_map[current_direction]
                x, y = self.placer._move_position(x, y, current_direction)
            
            # Check if position is valid
            if not grid.in_bounds(x, y) or grid.get(x, y) != 0:
                return False
        
        return True
    
    def create_serpent_in_area(self, min_x: int, min_y: int, max_x: int, max_y: int, grid) -> bool:
        """Create a serpent queue that fits in the specified area"""
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        movements = self.placer.create_serpent_pattern(width, height, min_x, min_y)
        
        return self.place_serpent_queue(min_x, min_y, Direction.EAST, movements, grid)
    
    def get_queue_tiles(self) -> List[QueueTile]:
        """Get all placed queue tiles"""
        all_tiles = []
        for queue in self.placed_queues:
            all_tiles.extend(queue['tiles'])
        return all_tiles

