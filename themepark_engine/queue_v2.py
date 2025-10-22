"""
Improved Queue System for OpenPark v2
Features:
- Automatic direction detection
- Corner/turn support
- Better visitor flow
- Connection validation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING
from enum import Enum
from .map import TILE_QUEUE_PATH, TILE_WALK, TILE_RIDE_ENTRANCE
from .debug import DebugConfig

if TYPE_CHECKING:
    from .agents import Guest
    from .rides import Ride
    from .map import MapGrid


class QueueDirection(Enum):
    """Direction of queue flow"""
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    NORTHEAST = "NE"  # Corner from South to East
    NORTHWEST = "NW"  # Corner from South to West
    SOUTHEAST = "SE"  # Corner from North to East
    SOUTHWEST = "SW"  # Corner from North to West
    UNKNOWN = "?"


@dataclass
class QueueTileV2:
    """Enhanced queue tile with direction and flow"""
    x: int
    y: int
    direction: QueueDirection = QueueDirection.UNKNOWN
    visitors: List['Guest'] = field(default_factory=list)
    next_tile: Optional['QueueTileV2'] = None  # Tile suivante dans la queue
    prev_tile: Optional['QueueTileV2'] = None  # Tile précédente dans la queue
    is_entrance: bool = False  # Première tile (connectée au walk path)
    is_exit: bool = False  # Dernière tile (proche du ride)

    def get_capacity(self) -> int:
        """Get tile capacity based on direction"""
        # Reduced capacity for testing (2 visitors per tile)
        return 2

    def is_full(self) -> bool:
        return len(self.visitors) >= self.get_capacity()

    def can_enter(self) -> bool:
        return not self.is_full()

    def add_visitor(self, visitor: 'Guest') -> bool:
        """Add visitor to this tile"""
        if self.can_enter():
            self.visitors.append(visitor)
            visitor.current_queue_tile = self
            return True
        return False

    def remove_visitor(self, visitor: 'Guest'):
        """Remove visitor from this tile"""
        if visitor in self.visitors:
            self.visitors.remove(visitor)

    def get_visitor_index(self, visitor: 'Guest') -> int:
        """Get visitor's index in this tile"""
        if visitor in self.visitors:
            return self.visitors.index(visitor)
        return -1


class QueuePathV2:
    """Enhanced queue path with better flow management"""

    def __init__(self, tiles: List[QueueTileV2], connected_ride: Optional['Ride'] = None):
        self.tiles = tiles  # Ordered list from entrance to exit
        self.connected_ride = connected_ride
        self.visitors: List['Guest'] = []  # All visitors in queue

        # Link tiles together
        for i in range(len(tiles)):
            if i < len(tiles) - 1:
                tiles[i].next_tile = tiles[i + 1]
            if i > 0:
                tiles[i].prev_tile = tiles[i - 1]

        # Mark entrance and exit
        if tiles:
            tiles[0].is_entrance = True
            tiles[-1].is_exit = True

        # Calculate total capacity
        self.max_capacity = sum(tile.get_capacity() for tile in tiles)

    def can_enter(self) -> bool:
        """Check if a visitor can enter the queue"""
        return (len(self.visitors) < self.max_capacity and
                self.tiles and
                self.tiles[0].can_enter())

    def add_visitor(self, visitor: 'Guest') -> bool:
        """Add visitor to the queue"""
        if not self.can_enter():
            DebugConfig.log('queues', f"Queue full, cannot add visitor {visitor.id}")
            return False

        # Add to visitors list
        self.visitors.append(visitor)
        visitor.current_queue = self
        visitor.queue_position = len(self.visitors) - 1

        # Place visitor PHYSICALLY on entrance tile (tiles[0])
        entrance_tile = self.tiles[0]
        entrance_tile.add_visitor(visitor)
        visitor.current_queue_tile = entrance_tile

        # Position visitor at entrance
        visitor.grid_x = entrance_tile.x
        visitor.grid_y = entrance_tile.y
        visitor.x = float(entrance_tile.x)
        visitor.y = float(entrance_tile.y)
        visitor.target_x = float(entrance_tile.x)
        visitor.target_y = float(entrance_tile.y)
        visitor.is_moving = False

        DebugConfig.log('queues', f"Visitor {visitor.id} entered queue at ENTRANCE tile ({entrance_tile.x}, {entrance_tile.y})")

        # Start walking toward exit immediately
        self._update_visitor_target(visitor)

        return True

    def remove_visitor(self, visitor: 'Guest'):
        """Remove visitor from queue"""
        if visitor in self.visitors:
            # Remove from current tile
            if visitor.current_queue_tile:
                visitor.current_queue_tile.remove_visitor(visitor)

            # Remove from queue list
            self.visitors.remove(visitor)

            # Update targets for all remaining visitors (they might be able to advance now)
            for v in self.visitors:
                if not v.is_moving:
                    self._update_visitor_target(v)

            DebugConfig.log('queues', f"Visitor {visitor.id} removed from queue")

    def _update_visitor_target(self, visitor: 'Guest'):
        """Update where the visitor should walk to next in the queue"""
        if not visitor.current_queue_tile:
            return

        # Find current tile index
        current_tile_index = None
        for i, tile in enumerate(self.tiles):
            if tile == visitor.current_queue_tile:
                current_tile_index = i
                break

        if current_tile_index is None:
            DebugConfig.log('queues', f"Warning: Visitor {visitor.id} current_queue_tile not found in tiles")
            return

        # Try to find next available tile to walk to
        for next_index in range(current_tile_index + 1, len(self.tiles)):
            next_tile = self.tiles[next_index]

            # Can we move to this tile?
            if not next_tile.is_full():
                # Yes! Start walking there
                visitor._start_movement_to(next_tile.x, next_tile.y)
                DebugConfig.log('queues', f"Visitor {visitor.id} starting walk from tile {current_tile_index} to tile {next_index}")
                return
            else:
                # Tile is full, check if there's someone there
                if len(next_tile.visitors) > 0:
                    # Someone is blocking, stop here
                    DebugConfig.log('queues', f"Visitor {visitor.id} blocked at tile {current_tile_index}, tile {next_index} is full")
                    return

        # Reached the end, stay at current position
        DebugConfig.log('queues', f"Visitor {visitor.id} at tile {current_tile_index}, no further movement needed")

    def get_entrance_position(self) -> Optional[Tuple[int, int]]:
        """Get entrance position"""
        if self.tiles:
            return (self.tiles[0].x, self.tiles[0].y)
        return None

    def get_exit_position(self) -> Optional[Tuple[int, int]]:
        """Get exit position (near ride entrance)"""
        if self.tiles:
            return (self.tiles[-1].x, self.tiles[-1].y)
        return None

    def is_visitor_at_front(self, visitor: 'Guest') -> bool:
        """Check if visitor is at the front (last tile)"""
        return (visitor.current_queue_tile and
                visitor.current_queue_tile.is_exit and
                len(visitor.current_queue_tile.visitors) > 0 and
                visitor.current_queue_tile.visitors[0] == visitor)

    def can_board_ride(self, visitor: 'Guest') -> bool:
        """Check if visitor can board the ride"""
        return (self.is_visitor_at_front(visitor) and
                self.connected_ride and
                self.connected_ride.can_board())

    def tick(self, dt: float):
        """Update queue - check if visitors have finished moving and update their targets"""
        for visitor in self.visitors:
            if not visitor.is_moving and visitor.current_queue_tile:
                # Visitor finished moving, check if they reached a new tile
                current_pos = (visitor.grid_x, visitor.grid_y)
                tile_pos = (visitor.current_queue_tile.x, visitor.current_queue_tile.y)

                if current_pos != tile_pos:
                    # Visitor is on a different tile than recorded, update it
                    for tile in self.tiles:
                        if (tile.x, tile.y) == current_pos:
                            # Remove from old tile
                            visitor.current_queue_tile.remove_visitor(visitor)
                            # Add to new tile
                            tile.add_visitor(visitor)
                            visitor.current_queue_tile = tile
                            DebugConfig.log('queues', f"Visitor {visitor.id} reached tile ({tile.x}, {tile.y})")

                            # Update target for next movement
                            self._update_visitor_target(visitor)
                            break



class QueueManagerV2:
    """Enhanced queue manager with direction detection"""

    def __init__(self):
        self.queue_paths: List[QueuePathV2] = []
        self.ride_queues: Dict['Ride', QueuePathV2] = {}
        self.tile_map: Dict[Tuple[int, int], QueueTileV2] = {}  # (x, y) -> tile
        self.placement_links: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (x, y) -> (next_x, next_y) based on placement order

    def _detect_flow_direction(self, tiles: List[QueueTileV2], index: int) -> QueueDirection:
        """Detect queue flow direction based on ordered tiles

        Args:
            tiles: Ordered list of queue tiles (from entrance to exit)
            index: Index of current tile in the list

        Returns:
            Direction pointing toward the next tile (toward exit)
        """
        if index >= len(tiles) - 1:
            # Last tile - no next tile, use previous tile direction
            if index > 0:
                prev_tile = tiles[index - 1]
                curr_tile = tiles[index]
                dx = curr_tile.x - prev_tile.x
                dy = curr_tile.y - prev_tile.y
            else:
                # Single tile queue
                return QueueDirection.UNKNOWN
        else:
            # Use next tile to determine direction
            curr_tile = tiles[index]
            next_tile = tiles[index + 1]
            dx = next_tile.x - curr_tile.x
            dy = next_tile.y - curr_tile.y

        # Map delta to direction
        if dx == 1 and dy == 0:
            return QueueDirection.EAST
        elif dx == -1 and dy == 0:
            return QueueDirection.WEST
        elif dx == 0 and dy == 1:
            return QueueDirection.SOUTH
        elif dx == 0 and dy == -1:
            return QueueDirection.NORTH
        else:
            # Diagonal or unknown - shouldn't happen in valid queues
            return QueueDirection.UNKNOWN

    def detect_direction(self, grid: 'MapGrid', x: int, y: int) -> QueueDirection:
        """Detect queue direction based on adjacent tiles"""
        neighbors = []

        # Check all 4 directions
        directions = {
            'N': (x, y - 1),
            'S': (x, y + 1),
            'E': (x + 1, y),
            'W': (x - 1, y)
        }

        for dir_name, (nx, ny) in directions.items():
            if grid.in_bounds(nx, ny) and grid.get(nx, ny) == TILE_QUEUE_PATH:
                neighbors.append(dir_name)

        # Determine direction based on neighbors
        if len(neighbors) == 0:
            return QueueDirection.UNKNOWN
        elif len(neighbors) == 1:
            # Start or end of queue - direction points away from neighbor
            if neighbors[0] == 'N':
                return QueueDirection.SOUTH
            elif neighbors[0] == 'S':
                return QueueDirection.NORTH
            elif neighbors[0] == 'E':
                return QueueDirection.WEST
            elif neighbors[0] == 'W':
                return QueueDirection.EAST
        elif len(neighbors) == 2:
            # Straight line or corner
            if 'N' in neighbors and 'S' in neighbors:
                return QueueDirection.SOUTH  # Vertical line
            elif 'E' in neighbors and 'W' in neighbors:
                return QueueDirection.EAST  # Horizontal line
            elif 'N' in neighbors and 'E' in neighbors:
                return QueueDirection.SOUTHEAST  # Corner from N to E
            elif 'N' in neighbors and 'W' in neighbors:
                return QueueDirection.SOUTHWEST  # Corner from N to W
            elif 'S' in neighbors and 'E' in neighbors:
                return QueueDirection.NORTHEAST  # Corner from S to E
            elif 'S' in neighbors and 'W' in neighbors:
                return QueueDirection.NORTHWEST  # Corner from S to W

        return QueueDirection.UNKNOWN

    def find_queue_paths(self, grid: 'MapGrid', preserve_visitors: bool = True):
        """Find all queue paths on the grid

        Args:
            preserve_visitors: If True, preserve visitor data from existing paths (default: True)
        """
        # Save old queue paths with their visitors and ride connections
        old_paths_by_tiles = {}
        if preserve_visitors and self.queue_paths:
            for old_path in self.queue_paths:
                # Create a key based on tile positions
                tile_positions = tuple(sorted((tile.x, tile.y) for tile in old_path.tiles))
                old_paths_by_tiles[tile_positions] = old_path

        self.tile_map.clear()
        visited = set()
        paths = []

        # Find all queue tiles and create tile objects
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.get(x, y) == TILE_QUEUE_PATH and (x, y) not in visited:
                    # Start a new path from this tile
                    path_tiles = self._trace_queue_path(grid, x, y, visited)
                    if path_tiles:
                        # Order tiles from ENTRANCE (near walk path) to EXIT (near ride)
                        path_tiles = self._order_queue_tiles(path_tiles, grid)

                        # Detect directions for all tiles based on ordered flow
                        for i, tile in enumerate(path_tiles):
                            tile.direction = self._detect_flow_direction(path_tiles, i)
                            self.tile_map[(tile.x, tile.y)] = tile

                        queue_path = QueuePathV2(path_tiles)

                        # Try to restore visitors and ride connection from old path
                        if preserve_visitors:
                            tile_positions = tuple(sorted((tile.x, tile.y) for tile in path_tiles))
                            if tile_positions in old_paths_by_tiles:
                                old_path = old_paths_by_tiles[tile_positions]
                                # Restore visitors
                                queue_path.visitors = old_path.visitors
                                # Update visitor references to new tiles
                                for visitor in queue_path.visitors:
                                    visitor.current_queue = queue_path
                                    # Find the tile the visitor is on
                                    for tile in queue_path.tiles:
                                        if (tile.x, tile.y) == (visitor.grid_x, visitor.grid_y):
                                            visitor.current_queue_tile = tile
                                            # Add visitor to tile's visitors list
                                            if visitor not in tile.visitors:
                                                tile.visitors.append(visitor)
                                            break
                                # Restore ride connection
                                queue_path.connected_ride = old_path.connected_ride
                                if old_path.connected_ride:
                                    self.ride_queues[old_path.connected_ride] = queue_path
                                # Update movement targets for all visitors
                                for visitor in queue_path.visitors:
                                    if not visitor.is_moving:
                                        queue_path._update_visitor_target(visitor)
                                DebugConfig.log('queues', f"Restored {len(queue_path.visitors)} visitors to queue path")

                        paths.append(queue_path)
                        DebugConfig.log('queues', f"Found queue path with {len(path_tiles)} tiles")

        self.queue_paths = paths
        return paths

    def _trace_queue_path(self, grid: 'MapGrid', start_x: int, start_y: int,
                         visited: Set[Tuple[int, int]]) -> List[QueueTileV2]:
        """Trace a queue path from start position"""
        tiles = []
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()

            if (x, y) in visited:
                continue

            visited.add((x, y))
            tiles.append(QueueTileV2(x, y))

            # Check adjacent tiles
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (grid.in_bounds(nx, ny) and
                    grid.get(nx, ny) == TILE_QUEUE_PATH and
                    (nx, ny) not in visited):
                    stack.append((nx, ny))

        return tiles

    def _order_queue_tiles(self, tiles: List[QueueTileV2], grid: 'MapGrid') -> List[QueueTileV2]:
        """Order queue tiles from ENTRANCE (near walk path) to EXIT (near ride entrance)

        The entrance is the tile adjacent to a walk path.
        The exit is the tile adjacent to a ride entrance.
        """
        from .map import TILE_WALK, TILE_RIDE_ENTRANCE

        if not tiles:
            return tiles

        # Create a tile lookup map
        tile_map = {(tile.x, tile.y): tile for tile in tiles}

        # Find entrance tile (adjacent to walk path)
        # If multiple tiles are adjacent to walk paths, we need to find the CORRECT entrance
        # by checking the placement links
        potential_entrances = []
        for tile in tiles:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = tile.x + dx, tile.y + dy
                if grid.in_bounds(nx, ny) and grid.get(nx, ny) == TILE_WALK:
                    potential_entrances.append(tile)
                    break

        # Choose the correct entrance from placement links
        entrance_tile = None
        if len(potential_entrances) == 1:
            # Only one entrance, use it
            entrance_tile = potential_entrances[0]
        elif len(potential_entrances) > 1 and self.placement_links:
            # Multiple potential entrances - find the one in the placement chain
            # Build reverse links to check both directions
            reversed_links = {next_pos: prev_pos for prev_pos, next_pos in self.placement_links.items() if next_pos in tile_map}

            for candidate in potential_entrances:
                candidate_pos = (candidate.x, candidate.y)
                # Check if this tile is either:
                # 1. Start of chain (has outgoing link but no incoming)
                # 2. End of chain (has incoming link but no outgoing)
                has_outgoing = candidate_pos in self.placement_links
                has_incoming = candidate_pos in reversed_links

                if (has_outgoing and not has_incoming) or (has_incoming and not has_outgoing):
                    # This is a chain endpoint, use it as entrance
                    entrance_tile = candidate
                    DebugConfig.log('queues', f"Selected entrance at ({candidate.x}, {candidate.y}) from {len(potential_entrances)} candidates")
                    break

            # Fallback: if we couldn't determine from links, use first candidate
            if not entrance_tile:
                entrance_tile = potential_entrances[0]
                DebugConfig.log('queues', f"Could not determine entrance from links, using first candidate at ({entrance_tile.x}, {entrance_tile.y})")
        elif len(potential_entrances) > 1:
            # No placement links, just use first
            entrance_tile = potential_entrances[0]

        # Find exit tile (adjacent to ride entrance)
        exit_tile = None
        for tile in tiles:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = tile.x + dx, tile.y + dy
                if grid.in_bounds(nx, ny) and grid.get(nx, ny) == TILE_RIDE_ENTRANCE:
                    exit_tile = tile
                    break
            if exit_tile:
                break

        # Only try placement link ordering if queue is COMPLETE (has both entrance and exit)
        # This prevents weird behavior during construction
        if entrance_tile and exit_tile and self.placement_links:
            entrance_pos = (entrance_tile.x, entrance_tile.y)

            # Check if entrance has outgoing link (normal construction: W→RE)
            has_outgoing = entrance_pos in self.placement_links

            # Check if entrance is pointed to by another tile (reverse construction: RE→W)
            reversed_links = {next_pos: prev_pos for prev_pos, next_pos in self.placement_links.items() if next_pos in tile_map}
            has_incoming = entrance_pos in reversed_links

            links_to_use = self.placement_links
            start_pos = entrance_pos

            # If entrance is at the END of the chain (reverse construction)
            if has_incoming and not has_outgoing:
                DebugConfig.log('queues', f"Detected reverse construction - inverting placement links")

                # Follow the reversed chain to collect all tiles in this path
                temp_ordered = []
                visited = set()
                current_pos = entrance_pos

                while current_pos and current_pos in tile_map:
                    if current_pos in visited:
                        break
                    visited.add(current_pos)
                    temp_ordered.append(tile_map[current_pos])
                    current_pos = reversed_links.get(current_pos)

                # Check if we got all tiles in this queue path
                if len(temp_ordered) != len(tiles):
                    DebugConfig.log('queues', f"WARNING: Reverse chain only found {len(temp_ordered)}/{len(tiles)} tiles - some tiles not linked properly")
                    # Don't invert if we didn't get all tiles - fall back to BFS instead
                    DebugConfig.log('queues', f"Falling back to BFS due to incomplete reverse chain")
                else:
                    # Now we have all tiles in correct order (entrance→exit)
                    # Update placement_links to point in the correct direction
                    for i in range(len(temp_ordered) - 1):
                        curr_tile = temp_ordered[i]
                        next_tile = temp_ordered[i + 1]
                        curr_pos_tuple = (curr_tile.x, curr_tile.y)
                        next_pos_tuple = (next_tile.x, next_tile.y)

                        # Remove old reversed link if exists
                        if next_pos_tuple in self.placement_links and self.placement_links[next_pos_tuple] == curr_pos_tuple:
                            del self.placement_links[next_pos_tuple]

                        # Add correct forward link
                        self.placement_links[curr_pos_tuple] = next_pos_tuple

                    DebugConfig.log('queues', f"Successfully inverted {len(temp_ordered)} tiles from reverse construction")
                    return temp_ordered

            # Normal construction: follow forward links
            ordered_tiles = []
            visited = set()
            current_pos = start_pos

            while current_pos and current_pos in tile_map:
                if current_pos in visited:
                    break

                visited.add(current_pos)
                ordered_tiles.append(tile_map[current_pos])

                next_pos = links_to_use.get(current_pos)

                if next_pos and next_pos in tile_map:
                    current_pos = next_pos
                else:
                    break

            # If we successfully ordered using placement links, return
            if len(ordered_tiles) == len(tiles):
                DebugConfig.log('queues', f"Ordered {len(ordered_tiles)} queue tiles using placement links")
                return ordered_tiles
            else:
                DebugConfig.log('queues', f"Placement links only covered {len(ordered_tiles)}/{len(tiles)} tiles, falling back to BFS")

        # Fallback: Use BFS (old method)
        # Note: entrance_tile and exit_tile already found above
        if not entrance_tile or not exit_tile:
            DebugConfig.log('queues', f"Warning: Could not find entrance or exit tile for queue path")
            return tiles

        # Order tiles from entrance to exit using BFS
        ordered_tiles = []
        visited_positions = set()
        queue = [entrance_tile]

        while queue:
            current = queue.pop(0)
            current_pos = (current.x, current.y)

            if current_pos in visited_positions:
                continue

            visited_positions.add(current_pos)
            ordered_tiles.append(current)

            if current == exit_tile:
                break

            # Find adjacent queue tiles
            for other_tile in tiles:
                other_pos = (other_tile.x, other_tile.y)
                if other_pos in visited_positions:
                    continue

                distance = abs(current.x - other_tile.x) + abs(current.y - other_tile.y)
                if distance == 1:
                    queue.append(other_tile)

        # Add any remaining tiles
        for tile in tiles:
            tile_pos = (tile.x, tile.y)
            if tile_pos not in visited_positions:
                ordered_tiles.append(tile)

        DebugConfig.log('queues', f"Ordered {len(ordered_tiles)} queue tiles using BFS fallback")
        return ordered_tiles

    def connect_queue_to_ride(self, queue_path: QueuePathV2, ride: 'Ride'):
        """Connect a queue to a ride"""
        queue_path.connected_ride = ride
        self.ride_queues[ride] = queue_path
        DebugConfig.log('queues', f"Connected queue to ride {ride.defn.name}")

    def update_queue_system(self, grid: 'MapGrid'):
        """Update the queue system"""
        self.find_queue_paths(grid)

    def get_queue_for_ride(self, ride: 'Ride') -> Optional[QueuePathV2]:
        """Get the queue connected to a ride"""
        return self.ride_queues.get(ride)

    def get_tile_at(self, x: int, y: int) -> Optional[QueueTileV2]:
        """Get queue tile at position"""
        return self.tile_map.get((x, y))

    def record_tile_placement(self, x: int, y: int, prev_x: int = None, prev_y: int = None):
        """Record that a queue tile was placed, optionally linking it to the previous tile

        Args:
            x, y: Position of newly placed tile
            prev_x, prev_y: Position of previous tile in the chain (if dragging)
        """
        if prev_x is not None and prev_y is not None:
            # Link previous tile to this new tile
            self.placement_links[(prev_x, prev_y)] = (x, y)
            DebugConfig.log('queues', f"Linked queue tile ({prev_x}, {prev_y}) -> ({x}, {y})")

    # Compatibility methods for engine.py placement system
    def can_orient_waypoint(self, grid: 'MapGrid', x: int, y: int, direction: str) -> bool:
        """Check if a queue waypoint can be oriented (compatibility method)"""
        # In V2, we auto-detect direction, so always return True if it's a valid queue tile
        return grid.get(x, y) == TILE_QUEUE_PATH

    def orient_queue_waypoint(self, grid: 'MapGrid', x: int, y: int, direction: str):
        """Orient a queue waypoint (compatibility method)"""
        # In V2, direction is auto-detected during update_queue_system
        # This is just a stub for compatibility
        pass

    def remove_queue_waypoint(self, grid: 'MapGrid', x: int, y: int):
        """Remove a queue waypoint (compatibility method)"""
        # Remove the tile from the grid - the queue system will update automatically
        from .map import TILE_GRASS
        grid.set(x, y, TILE_GRASS)

        # Remove from tile map if it exists
        if (x, y) in self.tile_map:
            del self.tile_map[(x, y)]

        # The queue paths will be rebuilt on next update_queue_system call
        DebugConfig.log('queues', f"Removed queue waypoint at ({x}, {y})")

    def evacuate_queue_for_broken_ride(self, ride: 'Ride'):
        """Evacuate all visitors from a queue when ride breaks down"""
        queue_path = self.get_queue_for_ride(ride)
        if queue_path:
            DebugConfig.log('queues', f"Evacuating queue for broken ride {ride.defn.name}")
            # Remove all visitors from the queue
            visitors_to_evacuate = queue_path.visitors.copy()
            for visitor in visitors_to_evacuate:
                # Remove from queue
                queue_path.remove_visitor(visitor)
                # Reset visitor state
                visitor.state = 'wandering'
                visitor.current_queue = None
                visitor.current_queue_tile = None
                visitor.queue_position = -1
                DebugConfig.log('queues', f"Evacuated visitor {visitor.id} from broken ride queue")

    def can_visitor_board_ride(self, visitor: 'Guest') -> bool:
        """Check if visitor can board their ride (compatibility method)"""
        if not visitor.current_queue:
            return False
        return visitor.current_queue.can_board_ride(visitor)

    def board_visitor_on_ride(self, visitor: 'Guest') -> bool:
        """Board a visitor on their ride (compatibility method)"""
        if not visitor.current_queue:
            return False

        queue_path = visitor.current_queue
        if not queue_path.connected_ride:
            return False

        ride = queue_path.connected_ride

        # Check if visitor is at front and ride can accept them
        if queue_path.is_visitor_at_front(visitor) and ride.can_board():
            # Remove from queue
            queue_path.remove_visitor(visitor)

            # Clean up visitor queue references to prevent teleportation
            visitor.current_queue = None
            visitor.current_queue_tile = None
            visitor.queue_position = -1

            # Board the ride
            ride.board_visitor(visitor)

            DebugConfig.log('queues', f"Visitor {visitor.id} boarded ride {ride.defn.name}")
            return True

        return False
