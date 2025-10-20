"""
Litter and Bin system for OpenPark
Handles litter generation, bins placement, and cleanliness management
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional
import random


@dataclass
class BinDef:
    """Definition of a bin type"""
    id: str
    name: str
    cost: int
    capacity: int = 999  # Unlimited for now
    sprite: str = "bin"


class Litter:
    """Represents a piece of litter on the ground"""
    
    # Define litter types with their colors (RGB)
    LITTER_TYPES = {
        'soda': {'name': 'Soda', 'color': (139, 90, 43), 'dark_color': (100, 60, 30)},      # Brown
        'trash': {'name': 'Dechet', 'color': (218, 165, 32), 'dark_color': (184, 134, 11)}, # Yellow/Gold
        'vomit': {'name': 'Vomi', 'color': (107, 142, 35), 'dark_color': (85, 107, 47)}     # Green
    }
    
    def __init__(self, x: int, y: int, litter_type: str = "soda"):
        self.x = x
        self.y = y
        self.type = litter_type  # soda, trash, vomit
        self.age = 0.0  # How long it's been there
        # Random offset within the tile for visual variety (0.1 to 0.9 of tile size)
        self.offset_x = random.uniform(0.1, 0.9)
        self.offset_y = random.uniform(0.1, 0.9)
    
    def get_colors(self):
        """Get the colors for this litter type"""
        if self.type in self.LITTER_TYPES:
            return self.LITTER_TYPES[self.type]['color'], self.LITTER_TYPES[self.type]['dark_color']
        # Default to brown if type not found
        return (139, 90, 43), (100, 60, 30)
        
    def tick(self, dt: float):
        """Update litter age"""
        self.age += dt


class Bin:
    """Represents a trash bin that visitors can use"""
    
    def __init__(self, bin_def: BinDef, x: int, y: int):
        self.defn = bin_def
        self.x = x
        self.y = y
        self.current_capacity = 0
        self.id = id(self)  # Unique ID
        
    def can_accept_litter(self) -> bool:
        """Check if bin can accept more litter"""
        return self.current_capacity < self.defn.capacity
    
    def add_litter(self) -> bool:
        """Add litter to bin, return True if successful"""
        if self.can_accept_litter():
            self.current_capacity += 1
            return True
        return False
    
    def empty(self):
        """Empty the bin"""
        self.current_capacity = 0


class LitterManager:
    """Manages all litter and bins in the park"""

    def __init__(self, grid=None):
        self.litters: List[Litter] = []
        self.bins: List[Bin] = []
        self.grid = grid  # Reference to the map grid for tile validation

    def set_grid(self, grid):
        """Set the grid reference after initialization"""
        self.grid = grid

    def _find_valid_litter_position(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Find a valid position for litter (TILE_WALK or TILE_QUEUE_PATH only)
        Returns the closest valid position or None if none found

        NOTE: We only allow litter on walk paths and queue paths, NOT on ride entrance/exit
        because those tiles are visually covered by ride sprites, making litter appear
        to be floating on top of buildings.
        """
        if not self.grid:
            # If no grid available, use original position (backward compatibility)
            return (x, y)

        # TILE_WALK = 1, TILE_QUEUE_PATH = 5
        # Explicitly NOT including TILE_RIDE_ENTRANCE (2) or TILE_RIDE_EXIT (3)
        # to avoid visual issues with litter appearing on top of ride sprites
        VALID_TILES = [1, 5]  # Walk paths and Queue paths only

        # Check current position first
        if self.grid.in_bounds(x, y) and self.grid.get(x, y) in VALID_TILES:
            return (x, y)

        # Search in expanding radius (1, then 2, then 3 tiles away)
        for radius in range(1, 4):
            # Check all positions at this radius
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Skip if not at edge of radius square (to search in expanding rings)
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    check_x, check_y = x + dx, y + dy
                    if self.grid.in_bounds(check_x, check_y) and self.grid.get(check_x, check_y) in VALID_TILES:
                        return (check_x, check_y)

        # No valid position found within 3 tiles
        return None

    def add_litter(self, x: int, y: int, litter_type: str = None) -> Optional[Litter]:
        """Add a new piece of litter at position (or nearest valid position)"""
        # Find valid position for litter
        valid_pos = self._find_valid_litter_position(x, y)
        if not valid_pos:
            # No valid position found, don't create litter
            return None

        litter_x, litter_y = valid_pos

        # Check if tile already has too much litter
        litter_on_tile = self.get_litter_at(litter_x, litter_y)
        if len(litter_on_tile) >= 3:  # Max 3 per tile
            return None

        # If no type specified, choose randomly
        if litter_type is None:
            # Weight the probabilities: 50% soda, 40% trash, 10% vomit
            rand = random.random()
            if rand < 0.5:
                litter_type = "soda"
            elif rand < 0.9:
                litter_type = "trash"
            else:
                litter_type = "vomit"

        litter = Litter(litter_x, litter_y, litter_type)
        self.litters.append(litter)
        return litter
    
    def remove_litter(self, litter: Litter):
        """Remove a piece of litter"""
        if litter in self.litters:
            self.litters.remove(litter)
    
    def get_litter_at(self, x: int, y: int) -> List[Litter]:
        """Get all litter at a specific position"""
        return [l for l in self.litters if l.x == x and l.y == y]
    
    def add_bin(self, bin_def: BinDef, x: int, y: int) -> Optional[Bin]:
        """Add a new bin at position"""
        bin_obj = Bin(bin_def, x, y)
        self.bins.append(bin_obj)
        return bin_obj
    
    def remove_bin(self, bin_obj: Bin):
        """Remove a bin"""
        if bin_obj in self.bins:
            self.bins.remove(bin_obj)
    
    def get_bin_at(self, x: int, y: int) -> Optional[Bin]:
        """Get bin at specific position"""
        for bin_obj in self.bins:
            if bin_obj.x == x and bin_obj.y == y:
                return bin_obj
        return None
    
    def find_nearest_bin(self, x: int, y: int, max_radius: int) -> Optional[Bin]:
        """Find nearest bin within radius"""
        nearest = None
        min_distance = float('inf')
        
        for bin_obj in self.bins:
            if not bin_obj.can_accept_litter():
                continue
                
            distance = abs(bin_obj.x - x) + abs(bin_obj.y - y)  # Manhattan distance
            if distance <= max_radius and distance < min_distance:
                min_distance = distance
                nearest = bin_obj
        
        return nearest
    
    def get_cleanliness_score(self) -> float:
        """Calculate park cleanliness score (0-100)"""
        # Each litter reduces score
        impact_per_litter = 2.0
        score = 100.0 - (len(self.litters) * impact_per_litter)
        return max(0.0, min(100.0, score))
    
    def tick(self, dt: float):
        """Update all litter"""
        for litter in self.litters:
            litter.tick(dt)
    
    def get_litter_in_radius(self, x: int, y: int, radius: int) -> List[Litter]:
        """Get all litter within radius of position"""
        result = []
        for litter in self.litters:
            distance = abs(litter.x - x) + abs(litter.y - y)
            if distance <= radius:
                result.append(litter)
        return result


# Default bin definition
DEFAULT_BIN = BinDef(
    id="bin_standard",
    name="Trash Bin",
    cost=50,
    capacity=999,
    sprite="bin"
)

