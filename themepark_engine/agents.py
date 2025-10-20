
from dataclasses import dataclass
from typing import Optional, List, Tuple
import random
from .debug import DebugConfig

@dataclass
class GuestState:
    WANDERING = "wandering"
    WALKING_TO_QUEUE = "walking_to_queue"
    QUEUING = "queuing"
    RIDING = "riding"
    EXITING = "exiting"
    WAITING = "waiting"
    WALKING_TO_SHOP = "walking_to_shop"
    SHOPPING = "shopping"
    WALKING_TO_BIN = "walking_to_bin"
    USING_BIN = "using_bin"
    LEAVING = "leaving"  # Walking to park entrance to exit
    # Needs states
    WALKING_TO_FOOD = "walking_to_food"
    EATING = "eating"
    WALKING_TO_DRINK = "walking_to_drink"
    DRINKING = "drinking"
    WALKING_TO_RESTROOM = "walking_to_restroom"
    USING_RESTROOM = "using_restroom"

class Guest:
    # List of diverse guest emojis (person, man, woman with various skin tones)
    GUEST_SPRITES = [
        # Person (neutral)
        'guests/1F9D1.png',
        'guests/1F9D1-1F3FB.png',  # Light skin
        'guests/1F9D1-1F3FC.png',  # Medium-light skin
        'guests/1F9D1-1F3FD.png',  # Medium skin
        'guests/1F9D1-1F3FE.png',  # Medium-dark skin
        'guests/1F9D1-1F3FF.png',  # Dark skin
        # Man
        'guests/1F468.png',
        'guests/1F468-1F3FB.png',
        'guests/1F468-1F3FC.png',
        'guests/1F468-1F3FD.png',
        'guests/1F468-1F3FE.png',
        'guests/1F468-1F3FF.png',
        # Woman
        'guests/1F469.png',
        'guests/1F469-1F3FB.png',
        'guests/1F469-1F3FC.png',
        'guests/1F469-1F3FD.png',
        'guests/1F469-1F3FE.png',
        'guests/1F469-1F3FF.png',
    ]

    def __init__(self, x: float, y: float):
        # Position réelle (float pour mouvement fluide)
        self.x = float(x)
        self.y = float(y)
        # Position de grille (int pour logique de jeu)
        self.grid_x = int(x)
        self.grid_y = int(y)

        # Randomly assign a diverse sprite to this guest
        self.sprite = random.choice(Guest.GUEST_SPRITES)
        
        self.path: List[Tuple[int, int]] = []
        self.state = GuestState.WANDERING
        self.current_queue = None
        self.current_queue_tile = None
        self.queue_position = -1
        self.tile_position = -1  # Position dans la tuile (0 à capacity-1)
        
        # Guest preferences for ride selection
        self.thrill_preference = random.uniform(0.0, 1.0)  # 0 = calm rides, 1 = thrilling rides
        self.nausea_tolerance = random.uniform(0.0, 1.0)   # 0 = no nausea tolerance, 1 = high tolerance
        self.target_ride = None
        self.target_queue = None
        self.current_ride = None  # Ride currently on
        self.ride_exit_pos = None
        self.target_shop = None
        self.current_shop = None  # Shop currently visiting
        self.shop_timer = 0.0
        self.shop_duration = 2.0  # Time spent in shop
        self.id = random.randint(1000, 9999)  # Unique ID for debugging

        # Money and budget system
        self.budget = random.randint(75, 300)  # Total budget for park visit ($75-$300)
        self.money = self.budget  # Current money (reduced by entrance fee and purchases)

        # Time tracking
        self.entry_time = 0.0  # Game time when guest entered park (set by engine)

        # Needs system (0.0 = empty, 1.0 = full)
        self.hunger = random.uniform(0.7, 1.0)  # Starts mostly satisfied (0.0 = starving, 1.0 = full)
        self.thirst = random.uniform(0.6, 1.0)  # Starts moderately satisfied (0.0 = parched, 1.0 = hydrated)
        self.bladder = random.uniform(0.0, 0.2)  # Starts low (0.0 = empty, 1.0 = urgent)
        self.target_food = None  # Food shop target
        self.target_drink = None  # Drink shop target
        self.target_restroom = None  # Restroom target
        self.eating_timer = 0.0
        self.eating_duration = random.uniform(8.0, 12.0)  # Time to eat (8-12 seconds)
        self.drinking_timer = 0.0
        self.drinking_duration = random.uniform(3.0, 5.0)  # Time to drink (3-5 seconds)
        self.restroom_timer = 0.0
        self.restroom_duration = random.uniform(5.0, 8.0)  # Time in restroom (5-8 seconds)

        # Litter system
        self.has_litter = False  # Has litter to throw away
        self.litter_type = None  # Type of litter (soda, trash, vomit)
        self.target_bin = None  # Bin to use
        self.bin_use_timer = 0.0
        self.bin_use_duration = 0.5  # Time to use bin
        self.litter_hold_timer = 0.0  # Time holding litter before deciding
        self.litter_hold_duration = 0.0  # How long to hold litter (3-10s)
        
        # Système de mouvement fluide
        self.speed = 2.0  # Vitesse de mouvement (tiles par seconde)
        self.move_timer = 0.0
        self.ride_timer = 0.0
        self.ride_duration = 3.0  # Time spent on ride
        self.waiting_timer = 0.0
        self.waiting_duration = 2.0  # Time to wait before trying again
        
        # Interpolation de mouvement
        self.target_x = float(x)
        self.target_y = float(y)
        self.is_moving = False
        self.move_progress = 0.0

        # Guest satisfaction and mood
        self.happiness = 0.5  # 0.0 to 1.0, affects guest behavior
        self.excitement = 0.5  # 0.0 to 1.0, increased by mascots and rides
        self.satisfaction = 0.5  # 0.0 to 1.0, increased by security and cleanliness

        # Satisfaction tracking
        self.queue_wait_timer = 0.0  # Track time spent in queue for satisfaction penalty
        
    def tick(self, dt: float):
        # Mise à jour du mouvement fluide
        self._update_smooth_movement(dt)

        # Natural degradation of satisfaction metrics
        self._apply_natural_degradation(dt)

        # Update needs (hunger decreases, thirst decreases, bladder increases)
        self._update_needs(dt)

        # Update litter hold timer if guest has litter (in ANY state)
        if self.has_litter and self.litter_hold_timer < self.litter_hold_duration:
            self.litter_hold_timer += dt
            if int(self.litter_hold_timer) != int(self.litter_hold_timer - dt):  # Log every second
                DebugConfig.log('litter', f"Guest {self.id} holding litter: {self.litter_hold_timer:.1f}/{self.litter_hold_duration:.1f}s (state={self.state})")

        # Log state changes
        if hasattr(self, '_last_logged_state') and self._last_logged_state != self.state:
            DebugConfig.log('guests', f"Guest {self.id} state changed from {self._last_logged_state} to {self.state}")
        self._last_logged_state = self.state
        
        if self.state == GuestState.WANDERING:
            self._tick_wandering(dt)
        elif self.state == GuestState.WALKING_TO_QUEUE:
            self._tick_walking_to_queue(dt)
        elif self.state == GuestState.QUEUING:
            self._tick_queuing(dt)
        elif self.state == GuestState.RIDING:
            self._tick_riding(dt)
        elif self.state == GuestState.EXITING:
            self._tick_exiting(dt)
        elif self.state == GuestState.WAITING:
            self._tick_waiting(dt)
        elif self.state == GuestState.WALKING_TO_SHOP:
            self._tick_walking_to_shop(dt)
        elif self.state == GuestState.SHOPPING:
            self._tick_shopping(dt)
        elif self.state == GuestState.WALKING_TO_BIN:
            self._tick_walking_to_bin(dt)
        elif self.state == GuestState.USING_BIN:
            self._tick_using_bin(dt)
        elif self.state == GuestState.LEAVING:
            self._tick_leaving(dt)
        elif self.state == GuestState.WALKING_TO_FOOD:
            self._tick_walking_to_food(dt)
        elif self.state == GuestState.EATING:
            self._tick_eating(dt)
        elif self.state == GuestState.WALKING_TO_DRINK:
            self._tick_walking_to_drink(dt)
        elif self.state == GuestState.DRINKING:
            self._tick_drinking(dt)
        elif self.state == GuestState.WALKING_TO_RESTROOM:
            self._tick_walking_to_restroom(dt)
        elif self.state == GuestState.USING_RESTROOM:
            self._tick_using_restroom(dt)
    
    def _update_smooth_movement(self, dt: float):
        """Update smooth movement interpolation"""
        if self.is_moving:
            self.move_progress += dt * self.speed
            
            if self.move_progress >= 1.0:
                # Mouvement terminé
                old_pos = (self.grid_x, self.grid_y)
                self.x = self.target_x
                self.y = self.target_y
                self.grid_x = int(self.x)
                self.grid_y = int(self.y)
                self.is_moving = False
                self.move_progress = 0.0
                DebugConfig.log('guests', f"Visitor {self.id} movement complete: {old_pos} -> ({self.grid_x}, {self.grid_y})")
            else:
                # Interpolation linéaire
                self.x = self.x + (self.target_x - self.x) * (dt * self.speed)
                self.y = self.y + (self.target_y - self.y) * (dt * self.speed)
    
    def _start_movement_to(self, target_x: int, target_y: int):
        """Start smooth movement to target position"""
        if not self.is_moving:
            self.target_x = float(target_x)
            self.target_y = float(target_y)
            self.is_moving = True
            self.move_progress = 0.0
    
    def _move_in_direction(self, direction: str):
        """Move visitor in a specific direction based on tile orientation"""
        direction_map = {
            'N': (0, -1),
            'S': (0, 1),
            'E': (1, 0),
            'W': (-1, 0)
        }
        
        if direction in direction_map:
            dx, dy = direction_map[direction]
            target_x = self.grid_x + dx
            target_y = self.grid_y + dy
            
            # Check if target position is valid
            if self.game.grid.in_bounds(target_x, target_y):
                self._start_movement_to(target_x, target_y)
    
    def _tick_wandering(self, dt: float):
        """Handle wandering behavior"""
        if self.path and not self.is_moving:
            self._move_towards_next()
        elif not self.path:
            # Look for rides to queue for (handled by engine)
            # DebugConfig.log('guests', f"Guest {self.id} is wandering with no path, waiting for engine to find ride")  # Too frequent
            pass
    
    def _tick_walking_to_queue(self, dt: float):
        """Handle walking to queue behavior"""
        if self.path and not self.is_moving:
            self._move_towards_next()
        elif not self.path:
            # Reached the queue entrance, join the queue
            DebugConfig.log('guests', f"Guest {self.id} reached queue entrance")
            if self.target_queue and self.target_queue.can_enter():
                DebugConfig.log('guests', f"Guest {self.id} attempting to join queue")
                # Add to queue
                success = self.target_queue.add_visitor(self)
                if success:
                    self.current_queue = self.target_queue
                    self.state = GuestState.QUEUING
                    DebugConfig.log('guests', f"Guest {self.id} successfully joined queue at position {self.queue_position}")
                else:
                    DebugConfig.log('guests', f"Guest {self.id} failed to join queue")
                    self.state = GuestState.WANDERING
                    self.target_queue = None
                    self.target_ride = None
            else:
                # Queue is full, go back to wandering
                DebugConfig.log('guests', f"Guest {self.id} queue full or no target queue, returning to wandering")
                self.state = GuestState.WANDERING
                self.target_queue = None
                self.target_ride = None
    
    def _tick_queuing(self, dt: float):
        """Handle queuing behavior - visitors stay immobile in queue"""
        if not self.current_queue:
            self.state = GuestState.WANDERING
            return

        # Track time spent waiting in queue
        self.queue_wait_timer += dt

        # Apply satisfaction penalty every 5 seconds of waiting
        if self.queue_wait_timer >= 5.0:
            self.modify_satisfaction(-0.01, f"waiting in queue ({int(self.queue_wait_timer)}s)")
            self.queue_wait_timer = 0.0  # Reset timer

        # Visitors in queue should stay immobile and wait
        # The queue system will handle moving them forward when space becomes available
        # No movement logic needed here - just wait
    
    def _tick_riding(self, dt: float):
        """Handle riding behavior"""
        self.ride_timer += dt
        if self.ride_timer >= self.ride_duration:
            self._exit_ride()
    
    def _tick_exiting(self, dt: float):
        """Handle exiting behavior"""
        if self.ride_exit_pos:
            if not self.is_moving:
                if (self.grid_x, self.grid_y) != self.ride_exit_pos:
                    self._start_movement_to(self.ride_exit_pos[0], self.ride_exit_pos[1])
                else:
                    # Reached exit, go back to wandering
                    self.state = GuestState.WANDERING
                    self.ride_exit_pos = None
                    self.target_ride = None
                    self.current_ride = None
                    DebugConfig.log('guests', f"Guest {self.id} exited ride and returned to wandering")
    
    def _tick_waiting(self, dt: float):
        """Handle waiting behavior when queue is full"""
        self.waiting_timer += dt
        if self.waiting_timer >= self.waiting_duration:
            # Try to find a ride again
            self.waiting_timer = 0.0
            self.state = GuestState.WANDERING
    
    def _move_towards_next(self):
        """Move towards the next position in path"""
        if self.path:
            nx, ny = self.path[0]
            if (self.grid_x, self.grid_y) == (nx, ny):
                self.path.pop(0)
            else:
                self._start_movement_to(nx, ny)
    
    def _move_towards(self, target: Tuple[int, int]):
        """Start movement towards target"""
        self._start_movement_to(target[0], target[1])
    
    def _find_ride_to_queue(self):
        """Find a ride to queue for (placeholder - will be implemented with queue manager)"""
        # This will be implemented when we integrate with the queue system
        pass
    
    def _enter_ride(self):
        """Enter the ride"""
        if self.current_queue and self.current_queue.connected_ride:
            self.state = GuestState.RIDING
            self.ride_timer = 0.0
            # Position guest on the ride
            ride = self.current_queue.connected_ride
            ride_center_x = ride.x + ride.defn.size[0] // 2
            ride_center_y = ride.y + ride.defn.size[1] // 2
            self._start_movement_to(ride_center_x, ride_center_y)
    
    def _exit_ride(self):
        """Exit the ride"""
        if self.current_ride and self.current_ride.exit:
            self.ride_exit_pos = (self.current_ride.exit.x, self.current_ride.exit.y)
            self.state = GuestState.EXITING
            self.current_ride = None
    
    def _tick_riding(self, dt: float):
        """Handle riding state - wait for ride to finish"""
        # The ride will handle moving the guest to exit when finished
        pass
    
    def _tick_exiting(self, dt: float):
        """Handle exiting state - move to exit and then wander"""
        DebugConfig.log('guests', f"Visitor {self.id} in exiting state at ({self.grid_x}, {self.grid_y}), target: {self.ride_exit_pos}, moving: {self.is_moving}")
        if not self.is_moving and self.ride_exit_pos:
            # Check if we're already at the exit position
            if (self.grid_x, self.grid_y) == self.ride_exit_pos:
                # Already at exit, check if guest should vomit
                if self.current_ride and self.current_ride.defn.nausea >= 0.7:
                    # High nausea ride - chance to get vomit litter
                    import random
                    if random.random() < 0.3:  # 30% chance to vomit
                        self.has_litter = True
                        self.litter_type = "vomit"
                        self.litter_hold_duration = random.uniform(3.0, 10.0)
                        self.litter_hold_timer = 0.0
                        DebugConfig.log('litter', f"Guest {self.id} got vomit litter from high nausea ride")
                
                # Start wandering
                DebugConfig.log('guests', f"Visitor {self.id} already at exit {self.ride_exit_pos}, starting to wander")
                self.state = GuestState.WANDERING
                self.current_ride = None
                self.target_ride = None
                self.ride_exit_pos = None
            else:
                # Move to exit position
                DebugConfig.log('guests', f"Visitor {self.id} starting movement to exit {self.ride_exit_pos}")
                self._start_movement_to(self.ride_exit_pos[0], self.ride_exit_pos[1])
        elif not self.is_moving and not self.ride_exit_pos:
            # Exit reached, start wandering
            DebugConfig.log('guests', f"Visitor {self.id} reached exit, starting to wander")
            self.state = GuestState.WANDERING
            self.current_ride = None
            self.target_ride = None

    def _tick_walking_to_shop(self, dt: float):
        """Handle visitor walking to shop"""
        if not self.is_moving and self.path:
            # Continue following path
            next_pos = self.path.pop(0)
            self._start_movement_to(next_pos[0], next_pos[1])
        elif not self.is_moving and not self.path:
            # Reached shop entrance, start shopping
            if self.target_shop and self.target_shop.entrance:
                entrance_pos = (self.target_shop.entrance.x, self.target_shop.entrance.y)
                if (self.grid_x, self.grid_y) == entrance_pos:
                    DebugConfig.log('guests', f"Guest {self.id} reached shop {self.target_shop.defn.name}, starting shopping")
                    self.state = GuestState.SHOPPING
                    self.current_shop = self.target_shop
                    self.shop_timer = 0.0
                else:
                    # Not at entrance, find path to entrance
                    DebugConfig.log('guests', f"Guest {self.id} not at shop entrance, finding path")
                    self.state = GuestState.WANDERING
                    self.target_shop = None

    def _tick_shopping(self, dt: float):
        """Handle visitor shopping"""
        self.shop_timer += dt
        if self.shop_timer >= self.shop_duration:
            # Shopping finished, now has litter to throw away
            DebugConfig.log('litter', f"Guest {self.id} finished shopping at {self.current_shop.defn.name}")
            
            # If already has litter from previous shop, drop it immediately at current position
            if self.has_litter:
                DebugConfig.log('litter', f"Guest {self.id} already has litter ({self.litter_type}), dropping it at shop exit")
                # Use litter manager from game
                if hasattr(self, 'game') and self.game:
                    self.game.litter_manager.add_litter(self.grid_x, self.grid_y, self.litter_type)
                self.has_litter = False
                self.litter_type = None
                self.litter_hold_timer = 0.0
                self.litter_hold_duration = 0.0
            
            # Get new litter from current shop (use shop's litter type)
            self.has_litter = True
            self.litter_type = self.current_shop.defn.litter_type
            # Set random hold duration between 3 and 10 seconds
            self.litter_hold_duration = random.uniform(3.0, 10.0)
            self.litter_hold_timer = 0.0
            DebugConfig.log('litter', f"Guest {self.id} got {self.litter_type} litter, will hold for {self.litter_hold_duration:.1f}s")
            self.state = GuestState.WANDERING
            self.current_shop = None
            self.target_shop = None
            self.shop_timer = 0.0
    
    def _tick_walking_to_bin(self, dt: float):
        """Handle visitor walking to bin"""
        if not self.is_moving and self.path:
            # Continue following path
            next_pos = self.path.pop(0)
            self._start_movement_to(next_pos[0], next_pos[1])
        elif not self.is_moving and not self.path:
            # Reached bin, start using it
            if self.target_bin:
                bin_pos = (self.target_bin.x, self.target_bin.y)
                distance = abs(self.grid_x - bin_pos[0]) + abs(self.grid_y - bin_pos[1])
                if distance <= 1:  # Adjacent to bin
                    DebugConfig.log('guests', f"Guest {self.id} reached bin, using it")
                    self.state = GuestState.USING_BIN
                    self.bin_use_timer = 0.0
                else:
                    # Not at bin, give up and drop litter or wander
                    DebugConfig.log('guests', f"Guest {self.id} couldn't reach bin, giving up")
                    self.state = GuestState.WANDERING
                    self.target_bin = None
            else:
                self.state = GuestState.WANDERING
    
    def _tick_using_bin(self, dt: float):
        """Handle visitor using bin"""
        self.bin_use_timer += dt
        if self.bin_use_timer >= self.bin_use_duration:
            # Finished using bin
            if self.target_bin and self.target_bin.add_litter():
                DebugConfig.log('guests', f"Guest {self.id} successfully used bin")
                self.has_litter = False
                self.litter_type = None
                self.litter_hold_timer = 0.0
                self.litter_hold_duration = 0.0
            else:
                DebugConfig.log('guests', f"Guest {self.id} bin was full, dropping litter")
                # Bin full, will drop litter when wandering
            
            self.state = GuestState.WANDERING
            self.target_bin = None
            self.bin_use_timer = 0.0

    def _tick_leaving(self, dt: float):
        """Handle visitor leaving the park (walking to entrance to exit)"""
        # Guest is following path to park entrance
        # When path is empty, they have reached the entrance and can be removed
        if not self.path:
            # Reached entrance - guest will be removed by engine
            DebugConfig.log('guests', f"Guest {self.id} reached park entrance and is leaving (satisfaction: {self.satisfaction:.2f})")
            return

        # Continue walking along path
        if not self.is_moving and self.path:
            next_tile = self.path[0]
            self.path = self.path[1:]
            self._start_movement_to(next_tile[0], next_tile[1])

    def get_bin_search_radius(self) -> int:
        """Calculate bin search radius based on guest state"""
        base_radius = 20
        
        # If guest has a target (ride or shop)
        if self.target_ride:
            # Calculate distance to target ride
            if self.target_ride.entrance:
                entrance_pos = (self.target_ride.entrance.x, self.target_ride.entrance.y)
                distance = abs(self.grid_x - entrance_pos[0]) + abs(self.grid_y - entrance_pos[1])
                
                if distance < 10:  # Close to attraction
                    return 5
                elif distance >= 20:  # Far from attraction
                    return 10
                else:  # Medium distance
                    return 15
        elif self.target_shop:
            # Calculate distance to target shop
            if self.target_shop.entrance:
                entrance_pos = (self.target_shop.entrance.x, self.target_shop.entrance.y)
                distance = abs(self.grid_x - entrance_pos[0]) + abs(self.grid_y - entrance_pos[1])
                
                if distance < 10:
                    return 5
                elif distance >= 20:
                    return 10
                else:
                    return 15
        
        return base_radius
    
    def should_drop_litter_randomly(self) -> bool:
        """Decide if guest should drop litter (80% chance if no bin found)"""
        return random.random() < 0.8

    # ===== SATISFACTION SYSTEM METHODS =====

    def _apply_natural_degradation(self, dt: float):
        """Apply natural degradation to satisfaction metrics"""
        # Happiness decreases slowly (needs constant stimulation)
        self.happiness = max(0.0, self.happiness - 0.005 * dt)

        # Excitement fades quickly
        self.excitement = max(0.0, self.excitement - 0.01 * dt)

        # Satisfaction decreases very slowly
        self.satisfaction = max(0.0, self.satisfaction - 0.002 * dt)

    def _update_needs(self, dt: float):
        """Update guest needs (hunger, thirst, bladder)

        Rates per in-game hour (30s real time at x1 speed):
        - Hunger: -0.10/hour → -0.00333/s
        - Thirst: -0.15/hour → -0.005/s
        - Bladder: +0.08/hour → +0.00267/s

        Note: These are real-time rates. Game speed is handled by engine's dt scaling.
        """
        # Hunger decreases (0.0 = starving, 1.0 = full)
        self.hunger = max(0.0, self.hunger - 0.00333 * dt)

        # Thirst decreases faster (0.0 = parched, 1.0 = hydrated)
        self.thirst = max(0.0, self.thirst - 0.005 * dt)

        # Bladder increases (0.0 = empty, 1.0 = urgent)
        self.bladder = min(1.0, self.bladder + 0.00267 * dt)

        # Apply satisfaction penalties for unmet needs
        if self.hunger < 0.3:
            self.satisfaction = max(0.0, self.satisfaction - 0.02 * dt)
        if self.thirst < 0.3:
            self.satisfaction = max(0.0, self.satisfaction - 0.03 * dt)
        if self.bladder > 0.7:
            penalty = 0.03 * dt if self.bladder < 0.9 else 0.10 * dt
            self.satisfaction = max(0.0, self.satisfaction - penalty)

    def modify_happiness(self, amount: float, reason: str = ""):
        """Modify happiness (capped between 0.0 and 1.0)"""
        old_value = self.happiness
        self.happiness = max(0.0, min(1.0, self.happiness + amount))
        if abs(amount) >= 0.05:  # Only log significant changes
            DebugConfig.log('guests', f"Guest {self.id} happiness: {old_value:.2f} -> {self.happiness:.2f} ({amount:+.2f}) - {reason}")

    def modify_excitement(self, amount: float, reason: str = ""):
        """Modify excitement (capped between 0.0 and 1.0)"""
        old_value = self.excitement
        self.excitement = max(0.0, min(1.0, self.excitement + amount))
        if abs(amount) >= 0.05:  # Only log significant changes
            DebugConfig.log('guests', f"Guest {self.id} excitement: {old_value:.2f} -> {self.excitement:.2f} ({amount:+.2f}) - {reason}")

    def modify_satisfaction(self, amount: float, reason: str = ""):
        """Modify satisfaction (capped between 0.0 and 1.0)"""
        old_value = self.satisfaction
        self.satisfaction = max(0.0, min(1.0, self.satisfaction + amount))
        if abs(amount) >= 0.05:  # Only log significant changes
            DebugConfig.log('guests', f"Guest {self.id} satisfaction: {old_value:.2f} -> {self.satisfaction:.2f} ({amount:+.2f}) - {reason}")

    def apply_ride_completion_bonus(self):
        """Apply satisfaction boost after completing a ride"""
        self.modify_happiness(0.15, "completed ride")
        self.modify_excitement(0.20, "completed ride")

    def apply_shopping_bonus(self):
        """Apply satisfaction boost after shopping"""
        self.modify_happiness(0.10, "finished shopping")
        self.modify_satisfaction(0.05, "finished shopping")

    def apply_short_queue_bonus(self, queue_length: int):
        """Apply bonus for short queue (< 3 visitors)"""
        if queue_length < 3:
            self.modify_satisfaction(0.03, f"short queue ({queue_length} visitors)")

    def apply_long_queue_penalty(self, queue_length: int):
        """Apply penalty for very long queue (> 10 visitors)"""
        if queue_length > 10:
            self.modify_satisfaction(-0.05, f"very long queue ({queue_length} visitors)")

    def apply_bin_use_bonus(self):
        """Apply satisfaction boost for successfully using a bin"""
        self.modify_satisfaction(0.05, "used bin (good behavior)")

    def apply_litter_drop_penalty(self):
        """Apply satisfaction penalty for having to drop litter on ground"""
        self.modify_satisfaction(-0.08, "had to drop litter (no bin)")

    def apply_broken_ride_penalty(self):
        """Apply satisfaction penalty when targeted ride breaks down"""
        self.modify_happiness(-0.10, "ride broke down")
        self.modify_satisfaction(-0.15, "ride broke down")

    # ===== NEEDS SYSTEM STATE HANDLERS =====

    def _tick_walking_to_food(self, dt: float):
        """Handle visitor walking to food shop"""
        if not self.path:
            # Reached food shop - start eating
            self.state = GuestState.EATING
            self.eating_timer = 0.0
            DebugConfig.log('guests', f"Guest {self.id} started eating")
            return

        if not self.is_moving and self.path:
            next_tile = self.path[0]
            self.path = self.path[1:]
            self._start_movement_to(next_tile[0], next_tile[1])

    def _tick_eating(self, dt: float):
        """Handle visitor eating"""
        self.eating_timer += dt

        if self.eating_timer >= self.eating_duration:
            # Finished eating
            self.hunger = min(1.0, self.hunger + 0.8)  # Restore hunger
            self.thirst = min(1.0, self.thirst + 0.2)  # Slight thirst relief

            # Deduct money from guest (payment will be handled by engine)
            if self.target_shop:
                price = self.target_shop.defn.base_price
                if self.money >= price:
                    self.money -= price
                    self.modify_satisfaction(0.05, "ate food")
                else:
                    # Can't afford it - apply penalty
                    self.modify_satisfaction(-0.03, "couldn't afford food")
                    DebugConfig.log('guests', f"Guest {self.id} couldn't afford food (${price})")

            # Generate litter (trash) 80% chance
            if random.random() < 0.8:
                self.has_litter = True
                self.litter_type = "trash"
                self.litter_hold_duration = random.uniform(3.0, 10.0)
                self.litter_hold_timer = 0.0

            self.state = GuestState.WANDERING
            self.target_food = None
            self.target_shop = None  # Clear shop target
            DebugConfig.log('guests', f"Guest {self.id} finished eating (hunger: {self.hunger:.2f})")

    def _tick_walking_to_drink(self, dt: float):
        """Handle visitor walking to drink stand"""
        if not self.path:
            # Reached drink stand - start drinking
            self.state = GuestState.DRINKING
            self.drinking_timer = 0.0
            DebugConfig.log('guests', f"Guest {self.id} started drinking")
            return

        if not self.is_moving and self.path:
            next_tile = self.path[0]
            self.path = self.path[1:]
            self._start_movement_to(next_tile[0], next_tile[1])

    def _tick_drinking(self, dt: float):
        """Handle visitor drinking"""
        self.drinking_timer += dt

        if self.drinking_timer >= self.drinking_duration:
            # Finished drinking
            self.thirst = min(1.0, self.thirst + 0.9)  # Restore thirst
            self.bladder = min(1.0, self.bladder + 0.25)  # Increase bladder need

            # Deduct money from guest (payment will be handled by engine)
            if self.target_shop:
                price = self.target_shop.defn.base_price
                if self.money >= price:
                    self.money -= price
                    self.modify_satisfaction(0.03, "drank beverage")
                else:
                    # Can't afford it - apply penalty
                    self.modify_satisfaction(-0.02, "couldn't afford drink")
                    DebugConfig.log('guests', f"Guest {self.id} couldn't afford drink (${price})")

            # Generate litter (soda) 70% chance
            if random.random() < 0.7:
                self.has_litter = True
                self.litter_type = "soda"
                self.litter_hold_duration = random.uniform(3.0, 10.0)
                self.litter_hold_timer = 0.0

            self.state = GuestState.WANDERING
            self.target_drink = None
            self.target_shop = None  # Clear shop target
            DebugConfig.log('guests', f"Guest {self.id} finished drinking (thirst: {self.thirst:.2f}, bladder: {self.bladder:.2f})")

    def _tick_walking_to_restroom(self, dt: float):
        """Handle visitor walking to restroom"""
        if not self.path:
            # Reached restroom - try to enter
            if self.target_restroom and self.target_restroom.add_user(self):
                self.state = GuestState.USING_RESTROOM
                self.restroom_timer = 0.0
                DebugConfig.log('guests', f"Guest {self.id} started using restroom")
            else:
                # Restroom full, go back to wandering
                DebugConfig.log('guests', f"Guest {self.id} can't use restroom (full), going back to wandering")
                self.state = GuestState.WANDERING
                self.target_restroom = None
            return

        if not self.is_moving and self.path:
            next_tile = self.path[0]
            self.path = self.path[1:]
            self._start_movement_to(next_tile[0], next_tile[1])

    def _tick_using_restroom(self, dt: float):
        """Handle visitor using restroom"""
        self.restroom_timer += dt

        if self.restroom_timer >= self.restroom_duration:
            # Finished using restroom
            self.bladder = 0.0  # Reset bladder
            self.modify_satisfaction(0.08, "used restroom (relief)")

            # Remove from restroom occupancy
            if self.target_restroom:
                self.target_restroom.remove_user(self)

            self.state = GuestState.WANDERING
            self.target_restroom = None
            DebugConfig.log('guests', f"Guest {self.id} finished using restroom (bladder: {self.bladder:.2f})")