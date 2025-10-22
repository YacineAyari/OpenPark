
from dataclasses import dataclass
from typing import List, Tuple, Optional, TYPE_CHECKING
from .debug import DebugConfig

if TYPE_CHECKING:
    from .agents import Guest

@dataclass
class RideDef:
    id: str
    name: str
    build_cost: int
    ticket_price: int
    capacity: int
    thrill: float
    nausea: float
    maint_cost: int
    breakdown_chance: float
    ride_duration: float
    sprite: str
    size: List[int]  # [width, height]
    entrance_cost: int
    exit_cost: int

@dataclass
class RideEntrance:
    x: int
    y: int
    connected: bool = False

@dataclass
class RideExit:
    x: int
    y: int
    connected: bool = False

class Ride:
    def __init__(self, defn: RideDef, x: int, y: int):
        self.defn = defn
        self.x = x
        self.y = y
        self.entrance: Optional[RideEntrance] = None
        self.exit: Optional[RideExit] = None
        self.operational = True
        self.current_visitors = []  # Visitors currently on the ride
        self.ride_timer = 0.0  # Timer for current ride cycle
        self.ride_duration = defn.ride_duration  # Ride duration from definition
        self.is_launched = False  # Whether the ride is currently running
        self.waiting_visitors = []  # Visitors waiting to board
        self.waiting_timer = 0.0  # Timer for waiting to launch
        self.max_wait_time = 5.0  # Maximum wait time before launching
        self.is_broken = False
        self.being_repaired = False
        self.breakdown_timer = 0.0
        
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y) bounds of the ride"""
        return (self.x, self.y, self.x + self.defn.size[0] - 1, self.y + self.defn.size[1] - 1)
    
    def get_perimeter_tiles(self) -> List[Tuple[int, int]]:
        """Get all tiles around the ride perimeter (including inside corners, excluding outside corners)"""
        min_x, min_y, max_x, max_y = self.get_bounds()
        perimeter = []
        
        # Top and bottom edges (including corners)
        for x in range(min_x, max_x + 1):
            perimeter.append((x, min_y - 1))  # Top edge
            perimeter.append((x, max_y + 1))  # Bottom edge
            
        # Left and right edges (excluding corners to avoid duplicates)
        for y in range(min_y + 1, max_y):
            perimeter.append((min_x - 1, y))  # Left edge
            perimeter.append((max_x + 1, y))  # Right edge
            
        return perimeter
    
    def is_inside_corner(self, x: int, y: int) -> bool:
        """Check if position is an inside corner of the ride"""
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        # Inside corners are the four corners of the ride itself
        inside_corners = [
            (min_x, min_y),     # Top-left
            (max_x, min_y),     # Top-right  
            (min_x, max_y),     # Bottom-left
            (max_x, max_y)      # Bottom-right
        ]
        
        return (x, y) in inside_corners
    
    def is_outside_corner(self, x: int, y: int) -> bool:
        """Check if position is an outside corner of the ride"""
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        # Outside corners are the four corners around the ride perimeter
        outside_corners = [
            (min_x - 1, min_y - 1),  # Top-left outside
            (max_x + 1, min_y - 1),  # Top-right outside
            (min_x - 1, max_y + 1),  # Bottom-left outside
            (max_x + 1, max_y + 1)   # Bottom-right outside
        ]
        
        return (x, y) in outside_corners
    
    def can_place_entrance(self, x: int, y: int) -> bool:
        """Check if entrance can be placed at given position"""
        if self.entrance is not None:
            return False  # Already has entrance
        # Allow inside corners but prevent outside corners
        if self.is_outside_corner(x, y):
            return False
        return (x, y) in self.get_perimeter_tiles() or self.is_inside_corner(x, y)
    
    def can_place_exit(self, x: int, y: int) -> bool:
        """Check if exit can be placed at given position"""
        if self.exit is not None:
            return False  # Already has exit
        if self.entrance and (x, y) == (self.entrance.x, self.entrance.y):
            return False  # Cannot place exit at entrance location
        # Allow inside corners but prevent outside corners
        if self.is_outside_corner(x, y):
            return False
        return (x, y) in self.get_perimeter_tiles() or self.is_inside_corner(x, y)
    
    def place_entrance(self, x: int, y: int) -> bool:
        """Place entrance at given position"""
        if self.can_place_entrance(x, y):
            self.entrance = RideEntrance(x, y)
            return True
        return False
    
    def place_exit(self, x: int, y: int) -> bool:
        """Place exit at given position"""
        if self.can_place_exit(x, y):
            self.exit = RideExit(x, y)
            return True
        return False
    
    def get_entrance_position(self) -> Optional[Tuple[int, int]]:
        """Get the position of the ride entrance"""
        if self.entrance:
            return (self.entrance.x, self.entrance.y)
        return None
    
    def can_board(self) -> bool:
        """Check if a visitor can board the ride"""
        # Cannot board if ride is broken or being repaired
        if self.is_broken or self.being_repaired:
            DebugConfig.log('rides', f"Ride {self.defn.name} can_board: False (broken: {self.is_broken}, being_repaired: {self.being_repaired})")
            return False

        # Use the ride's actual capacity from its definition
        result = len(self.current_visitors) < self.defn.capacity and not self.is_launched
        DebugConfig.log('rides', f"Ride {self.defn.name} can_board: {result} (visitors: {len(self.current_visitors)}/{self.defn.capacity}, launched: {self.is_launched})")
        if len(self.current_visitors) > 0:
            DebugConfig.log('rides', f"Ride {self.defn.name} has visitors: {[v.id for v in self.current_visitors]}")
        return result
    
    def board_visitor(self, visitor: 'Guest') -> bool:
        """Add a visitor to the ride"""
        if self.can_board():
            self.current_visitors.append(visitor)
            visitor.state = "riding"
            visitor.current_ride = self

            # Move visitor to the center of the ride (not teleport - set position directly)
            ride_center_x = self.x + self.defn.size[0] // 2
            ride_center_y = self.y + self.defn.size[1] // 2
            visitor.grid_x = ride_center_x
            visitor.grid_y = ride_center_y
            visitor.x = float(ride_center_x)
            visitor.y = float(ride_center_y)
            visitor.target_x = float(ride_center_x)
            visitor.target_y = float(ride_center_y)
            visitor.is_moving = False  # Stop any movement

            DebugConfig.log('rides', f"Visitor {visitor.id} boarded ride {self.defn.name} at center ({ride_center_x}, {ride_center_y}). Total visitors: {len(self.current_visitors)}")

            # Check if ride should launch now (launch when at least 50% full)
            if len(self.current_visitors) >= max(1, self.defn.capacity // 2):
                self.launch_ride()
            else:
                # Start waiting timer if not launched yet
                if not self.is_launched and self.waiting_timer == 0.0:
                    self.waiting_timer = 0.0  # Reset timer
                    DebugConfig.log('rides', f"Ride {self.defn.name} waiting for more visitors ({len(self.current_visitors)}/{self.defn.capacity})")

            return True
        DebugConfig.log('rides', f"Visitor {visitor.id} cannot board ride {self.defn.name}. Current visitors: {len(self.current_visitors)}")
        return False
    
    def launch_ride(self):
        """Launch the ride when ready"""
        # Launch if not already launched and has visitors
        if not self.is_launched and len(self.current_visitors) > 0:
            self.is_launched = True
            self.ride_timer = 0.0
            self.waiting_timer = 0.0  # Reset waiting timer
            DebugConfig.log('rides', f"Ride {self.defn.name} launched with {len(self.current_visitors)} visitors (capacity: {self.defn.capacity})")
    
    def _handle_breakdown(self):
        """Handle ride breakdown - evacuate visitors IMMEDIATELY and clear queue"""
        # Evacuate current visitors IMMEDIATELY (no exit animation, instant teleport out)
        for visitor in self.current_visitors:
            # Immediately teleport visitor to exit position
            if self.exit:
                visitor.grid_x = self.exit.x
                visitor.grid_y = self.exit.y
                visitor.x = float(self.exit.x)
                visitor.y = float(self.exit.y)
                visitor.target_x = float(self.exit.x)
                visitor.target_y = float(self.exit.y)
                visitor.is_moving = False
                DebugConfig.log('rides', f"Visitor {visitor.id} evacuated IMMEDIATELY to exit ({self.exit.x}, {self.exit.y}) due to breakdown")

            # Reset visitor state
            visitor.state = "wandering"
            visitor.current_ride = None
            visitor.target_ride = None
            visitor.ride_exit_pos = None

            # Apply breakdown penalty
            visitor.apply_broken_ride_penalty()

        self.current_visitors.clear()
        self.is_launched = False
        self.ride_timer = 0.0
        self.waiting_timer = 0.0

        # Clear waiting visitors
        for visitor in self.waiting_visitors:
            visitor.state = "wandering"
            visitor.target_ride = None
            visitor.current_queue = None
            visitor.current_queue_tile = None
            visitor.queue_position = -1
            visitor.tile_position = -1
            DebugConfig.log('rides', f"Clearing waiting visitor {visitor.id} due to breakdown")

        self.waiting_visitors.clear()
        DebugConfig.log('rides', f"Ride {self.defn.name} evacuated all visitors IMMEDIATELY due to breakdown")
    
    def tick(self, dt: float):
        """Update ride state"""
        # Handle breakdowns
        if not self.is_broken and not self.being_repaired:
            self.breakdown_timer += dt
            if self.breakdown_timer >= 1.0:  # Check every second
                import random
                if random.random() < self.defn.breakdown_chance:
                    self.is_broken = True
                    self._handle_breakdown()
                    DebugConfig.log('rides', f"Ride {self.defn.name} has broken down!")
                self.breakdown_timer = 0.0
        
        # Don't operate if broken
        if self.is_broken:
            return
        
        # Handle waiting timer if not launched yet
        if not self.is_launched and len(self.current_visitors) > 0:
            self.waiting_timer += dt
            if self.waiting_timer >= self.max_wait_time:
                DebugConfig.log('rides', f"Ride {self.defn.name} launching due to timeout ({len(self.current_visitors)} visitors)")
                self.launch_ride()
        
        if self.is_launched:
            self.ride_timer += dt
            if self.ride_timer >= self.ride_duration:
                # Ride finished, move visitors to exit
                DebugConfig.log('rides', f"Ride {self.defn.name} finished. Visitors exiting: {len(self.current_visitors)}")
                for visitor in self.current_visitors:
                    visitor.state = "exiting"
                    visitor.current_ride = None
                    visitor.target_ride = None
                    # Set exit position for visitor
                    if self.exit:
                        visitor.ride_exit_pos = (self.exit.x, self.exit.y)
                        DebugConfig.log('rides', f"Visitor {visitor.id} exiting ride to position {visitor.ride_exit_pos}")
                    else:
                        DebugConfig.log('rides', f"Visitor {visitor.id} exiting ride but no exit defined")
                
                self.current_visitors.clear()
                self.is_launched = False
                self.ride_timer = 0.0
                self.waiting_timer = 0.0  # Reset waiting timer
