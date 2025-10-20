
import json, pygame, math
from pathlib import Path
from . import assets
from .map import MapGrid, TILE_WALK, TILE_GRASS, TILE_RIDE_ENTRANCE, TILE_RIDE_EXIT, TILE_RIDE_FOOTPRINT, TILE_QUEUE_PATH, TILE_SHOP_ENTRANCE, TILE_SHOP_FOOTPRINT, TILE_PARK_ENTRANCE, TILE_RESTROOM_FOOTPRINT, TILE_BIN
from .pathfinding import astar
from .agents import Guest
from .rides import Ride, RideDef, RideEntrance, RideExit
from .shops import Shop, ShopDef, ShopEntrance
from .restrooms import Restroom, RestroomDef
from .employees import EmployeeDef, Engineer, MaintenanceWorker, SecurityGuard, Mascot
from .economy import Economy
from .ui import Toolbar
from .renderers.iso import IsoRenderer
from .ui_parts.debug_menu import DebugMenu
from .queues import SimpleQueueManager
from .serpent_queue import SerpentQueueManager, Direction, Movement, MovementType
from .debug import DebugConfig
from .litter import LitterManager, BinDef, DEFAULT_BIN, Litter
from .save_load import (SaveLoadManager, serialize_grid, serialize_ride, serialize_shop,
                         serialize_employee, serialize_guest, serialize_bin, serialize_litter,
                         serialize_restroom)

DATA = Path(__file__).resolve().parent / 'data'

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 800))
        pygame.display.set_caption('OpenPark — Oblique Mode')
        self.clock = pygame.time.Clock(); self.font = pygame.font.SysFont('Arial', 16)
        self.grid = MapGrid(64, 64); self.economy = Economy()
        self.queue_manager = SimpleQueueManager()
        self.litter_manager = LitterManager(self.grid)  # Add litter management system with grid reference
        self.save_load_manager = SaveLoadManager()  # Save/Load system
        data = json.load(open(DATA/'objects.json','r'))
        self.ride_defs = {r['id']: RideDef(**r) for r in data.get('rides', [])}
        self.shop_defs = {s['id']: ShopDef(**s) for s in data.get('shops', [])}
        self.employee_defs = {e['id']: EmployeeDef(**e) for e in data.get('employees', [])}
        self.bin_defs = {b['id']: BinDef(**b) for b in data.get('bins', [])}  # Load bin definitions
        self.restroom_defs = {r['id']: RestroomDef(**r) for r in data.get('restrooms', [])}  # Load restroom definitions
        self.proj_presets = [tuple(p) for p in data.get('projection_presets', [(64,32)])]
        default_proj = tuple(data.get('projection_default', [64,32]))
        default_tilt = float(data.get('tilt_default', 10.0))

        # Load time system configuration
        time_config = data.get('time_system', {})
        self.day_duration_real_minutes = time_config.get('day_duration_minutes', 12.0)
        self.starting_hour = time_config.get('starting_hour', 9)
        self.max_visitor_stay_days = time_config.get('max_visitor_stay_days', 10)

        self.rides = []; self.shops = []; self.employees = []; self.restrooms = []
        # Guests will be spawned at park entrance
        import random
        self.guests = []
        self.spr_cache = {}  # Sprite cache with zoom levels
        # Oblique tilt default at 10°
        self.renderer = IsoRenderer(self.screen, self.font, default_proj[0], default_proj[1], oblique_tilt=default_tilt)
        self.proj_index = max(0, self.proj_presets.index(default_proj) if default_proj in self.proj_presets else 0)
        self.debug_menu = DebugMenu(self.font, self.proj_presets, self.proj_index, oblique_tilt=default_tilt)
        self.toolbar = Toolbar(self.font, self.ride_defs, self.shop_defs, self.employee_defs, self.bin_defs, self.restroom_defs)
        self.dragging=False; self.drag_start=(0,0); self.cam_start=(0,0)
        self.path_dragging=False; self.last_path_pos=None

        # Entrance fee configuration panel
        self.entrance_fee_panel_open = False
        self.entrance_fee_slider_dragging = False
        self.ride_placement_mode = None  # 'ride', 'entrance', 'exit'
        self.selected_ride = None
        self.employee_placement_mode = None
        self.last_queue_pos = None  # Track last queue tile for orientation
        self.mouse_direction = 'S'  # Default direction for queue tiles
        self.last_mouse_pos = None  # Track mouse movement for direction
        self.serpent_manager = SerpentQueueManager()
        self.serpent_mode = False  # Toggle for serpent queue placement
        self.serpent_start_pos = None  # Start position for serpent queue

        # Park entrance system
        self.park_entrance = None  # (x, y) tuple for entrance center
        self.entrance_width = 5  # 5 tiles wide
        self.guest_spawn_timer = 0.0  # Timer for spawning guests
        self.guest_spawn_rate = self._calculate_spawn_rate()  # Dynamic spawn rate based on entrance fee
        self.guests_entered = 0  # Track total guests entered
        self.guests_left = 0  # Track total guests who left

        # Time system
        self.game_time = 0.0  # Game time in seconds (in-game)
        self.game_speed = 1.0  # Current game speed (0=paused, 1=normal, 2=fast, 3=very fast)
        self.game_day = 1  # Current day
        self.game_hour = self.starting_hour  # Current hour (0-23)
        self.game_minute = 0  # Current minute (0-59)

        # Park open/close system
        self.park_open = False  # Park starts closed, player opens with 'O' key
        self.park_just_closed = False  # Flag to trigger evacuation

        # Create park entrance at south center of map
        self._create_park_entrance()

        # Center camera on park entrance at game start
        if self.park_entrance:
            # Calculate world position of entrance (before camera offset)
            gx, gy = self.park_entrance
            tw, th = self.renderer.tile_size()
            entrance_world_x = (gx + gy * self.renderer._skew) * tw
            entrance_world_y = gy * th

            # Calculate camera offset to center entrance in viewport
            screen_center_x = self.screen.get_width() // 2
            # Position entrance at 70% of screen height (lower on screen, more space above)
            screen_entrance_y = int(self.screen.get_height() * 0.70)

            # Camera position that puts entrance centered horizontally and lower vertically
            self.renderer.camera.x = entrance_world_x + self.renderer.origin[0] - screen_center_x
            self.renderer.camera.y = entrance_world_y + self.renderer.origin[1] - screen_entrance_y

            DebugConfig.log('engine', f"Camera centered on park entrance at grid ({gx}, {gy})")

        # No test objects - let the game start normally

    def sprite(self, name:str):
        # Create cache key with zoom level to scale sprites appropriately
        zoom = self.renderer.camera.zoom
        cache_key = (name, zoom)

        if cache_key not in self.spr_cache:
            # Load base sprite
            base_sprite = assets.load_image(name)

            # Scale sprite according to zoom
            if zoom != 1.0:
                # Calculate new size based on zoom
                new_width = int(base_sprite.get_width() * zoom)
                new_height = int(base_sprite.get_height() * zoom)
                # Ensure minimum size of 1x1
                new_width = max(1, new_width)
                new_height = max(1, new_height)
                scaled_sprite = pygame.transform.smoothscale(base_sprite, (new_width, new_height))
                self.spr_cache[cache_key] = scaled_sprite
            else:
                self.spr_cache[cache_key] = base_sprite

        return self.spr_cache[cache_key]

    def _can_place_ride(self, ride_def, gx, gy):
        """Check if a ride can be placed at the given position"""
        if not self.grid.in_bounds(gx, gy): return False
        if not self.grid.in_bounds(gx + ride_def.size[0] - 1, gy + ride_def.size[1] - 1): return False
        
        # Check if all tiles in the ride area are grass (not occupied by other rides)
        for x in range(gx, gx + ride_def.size[0]):
            for y in range(gy, gy + ride_def.size[1]):
                if self.grid.get(x, y) != TILE_GRASS:
                    return False
        return True
    
    def _get_ride_at_position(self, gx, gy):
        """Get the ride at the given position, if any"""
        for ride in self.rides:
            min_x, min_y, max_x, max_y = ride.get_bounds()
            if min_x <= gx <= max_x and min_y <= gy <= max_y:
                return ride
        return None
    
    def _mark_ride_footprint(self, ride):
        """Mark the ride's footprint on the map"""
        min_x, min_y, max_x, max_y = ride.get_bounds()
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if self.grid.in_bounds(x, y):
                    self.grid.set(x, y, TILE_RIDE_FOOTPRINT)
    
    def _clear_ride_footprint(self, ride):
        """Clear the ride's footprint from the map"""
        min_x, min_y, max_x, max_y = ride.get_bounds()
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if self.grid.in_bounds(x, y):
                    self.grid.set(x, y, TILE_GRASS)
    
    def _is_on_ride(self, gx, gy):
        """Check if a position is on any ride/shop footprint or ride entrance/exit"""
        return self.grid.get(gx, gy) in (TILE_RIDE_FOOTPRINT, TILE_SHOP_FOOTPRINT, TILE_RIDE_ENTRANCE, TILE_RIDE_EXIT)
    
    def _can_connect_queue_tile(self, gx, gy):
        """Check if a queue tile can be placed at this position (connects to existing queue or is first tile)"""
        # If it's the first queue tile, allow it
        if self.last_queue_pos is None:
            return True
        
        # Check if it's adjacent to the last placed queue tile
        lx, ly = self.last_queue_pos
        if abs(gx - lx) + abs(gy - ly) == 1:  # Adjacent (Manhattan distance = 1)
            return True
        
        # Check if it's adjacent to any existing queue tile
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = gx + dx, gy + dy
            if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_QUEUE_PATH:
                return True
        
        return False
    
    def _calculate_mouse_direction(self, current_pos, last_pos):
        """Calculate direction based on mouse movement"""
        if last_pos is None:
            return 'S'  # Default direction
        
        dx = current_pos[0] - last_pos[0]
        dy = current_pos[1] - last_pos[1]
        
        # Determine primary direction based on movement
        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        else:
            return 'S' if dy > 0 else 'N'
    
    def _get_queue_tile_connections(self, gx, gy):
        """Get number of connections for a queue tile"""
        from .map import TILE_QUEUE_PATH
        connections = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = gx + dx, gy + dy
            if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_QUEUE_PATH:
                connections += 1
        return connections
    
    def _get_adjacent_queue_direction(self, gx, gy):
        """Get the direction to an adjacent queue tile"""
        from .map import TILE_QUEUE_PATH
        
        # Check all four directions for adjacent queue tiles
        for dx, dy, direction in [(0, 1, 'S'), (0, -1, 'N'), (1, 0, 'E'), (-1, 0, 'W')]:
            nx, ny = gx + dx, gy + dy
            if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_QUEUE_PATH:
                return direction
        return None
    
    def _get_opposite_direction(self, direction):
        """Get the opposite direction"""
        opposites = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        return opposites.get(direction, 'S')
    
    def create_serpent_queue(self, start_x: int, start_y: int, width: int, height: int):
        """Create a serpent queue in the specified area"""
        # Convert to Direction enum
        initial_direction = Direction.EAST
        
        # Create serpent pattern
        movements = self.serpent_manager.placer.create_serpent_pattern(width, height, start_x, start_y)
        
        # Place the serpent queue
        success = self.serpent_manager.place_serpent_queue(start_x, start_y, initial_direction, movements, self.grid)
        
        if success:
            # Update queue system
            self._update_queue_system()
            return True
        
        return False
    
    def create_custom_serpent_queue(self, start_x: int, start_y: int, pattern_string: str):
        """Create a custom serpent queue from a pattern string"""
        # Convert to Direction enum
        initial_direction = Direction.EAST
        
        # Create movements from pattern
        movements = self.serpent_manager.placer.create_custom_pattern(pattern_string)
        
        # Place the serpent queue
        success = self.serpent_manager.place_serpent_queue(start_x, start_y, initial_direction, movements, self.grid)
        
        if success:
            # Update queue system
            self._update_queue_system()
            return True
        
        return False
    
    def _connect_queue_to_ride(self, queue_path, ride):
        """Connect a queue path to a ride"""
        queue_path.connected_ride = ride
        self.queue_manager.ride_queues[ride] = queue_path
    
    def _update_queue_system(self):
        """Update the queue system - find and connect queue paths to rides"""
        # Update the simple queue system
        # DebugConfig.log('engine', "Updating queue system")  # Too frequent
        self.queue_manager.update_queue_system(self.grid)
        
        # Connect queues to rides based on proximity to entrances
        DebugConfig.log('engine', f"Connecting queues to rides, found {len(self.rides)} rides")
        for queue_path in self.queue_manager.queue_paths:
            if not queue_path.connected_ride:
                DebugConfig.log('engine', f"Checking unconnected queue path with {len(queue_path.tiles)} tiles")
                # Find the closest ride entrance
                for ride in self.rides:
                    DebugConfig.log('engine', f"Checking ride {ride.defn.name}")
                    if ride.entrance:
                        entrance_pos = (ride.entrance.x, ride.entrance.y)
                        DebugConfig.log('engine', f"Ride {ride.defn.name} has entrance at {entrance_pos}")
                        # Check if queue path is connected to ride entrance
                        for tile in queue_path.tiles:
                            tile_pos = (tile.x, tile.y)
                            if tile_pos == entrance_pos:
                                DebugConfig.log('engine', f"Connecting queue at {tile_pos} to ride {ride.defn.name} (exact match)")
                                self.queue_manager.connect_queue_to_ride(queue_path, ride)
                                break
                        
                        # Check if queue path is adjacent to ride entrance
                        for tile in queue_path.tiles:
                            tile_pos = (tile.x, tile.y)
                            distance = abs(tile_pos[0] - entrance_pos[0]) + abs(tile_pos[1] - entrance_pos[1])
                            if distance == 1:  # Adjacent
                                DebugConfig.log('engine', f"Connecting queue at {tile_pos} to ride {ride.defn.name} (adjacent)")
                                self.queue_manager.connect_queue_to_ride(queue_path, ride)
                                break
                    else:
                        DebugConfig.log('engine', f"Ride {ride.defn.name} has no entrance")
    
    def _find_ride_for_guest(self, guest):
        """Find a ride for a guest to queue for"""
        DebugConfig.log('engine', f"Looking for ride for guest {guest.id}")
        # Look for rides with available queue space and connected queues
        # Randomize ride selection to avoid always choosing the same ride
        import random
        available_rides = []
        for ride in self.rides:
            DebugConfig.log('engine', f"Checking ride {ride.defn.name}")
            if ride.entrance and ride.exit:
                DebugConfig.log('engine', f"Ride {ride.defn.name} has entrance and exit")
                queue_path = self.queue_manager.get_queue_for_ride(ride)
                if queue_path and queue_path.can_enter():
                    DebugConfig.log('engine', "Queue found and can accept visitor")
                    # Pathfind to the entrance of the queue
                    queue_entrance = queue_path.get_entrance_position()
                    if queue_entrance:
                        DebugConfig.log('engine', f"Queue entrance at {queue_entrance}")
                        path = astar(self.grid, (guest.grid_x, guest.grid_y), queue_entrance)
                        if path:
                            # Add this ride to available rides list
                            available_rides.append((ride, queue_path, queue_entrance, path))
                            DebugConfig.log('engine', f"Ride {ride.defn.name} added to available rides")
                        else:
                            DebugConfig.log('engine', "No path found to queue entrance")
                    else:
                        DebugConfig.log('engine', "No queue entrance found")
                else:
                    DebugConfig.log('engine', "No queue or queue cannot accept visitor")
            else:
                DebugConfig.log('engine', f"Ride {ride.defn.name} missing entrance or exit")
        
        # Select ride based on guest preferences and availability
        if available_rides:
            # Score rides based on guest preferences
            scored_rides = []
            for ride, queue_path, queue_entrance, path in available_rides:
                # Calculate preference score (0-1, higher is better)
                thrill_score = 1.0 - abs(guest.thrill_preference - ride.defn.thrill)
                nausea_score = 1.0 - abs(guest.nausea_tolerance - ride.defn.nausea)
                preference_score = (thrill_score + nausea_score) / 2.0
                
                # Add some randomness to avoid always choosing the same ride
                random_factor = random.uniform(0.8, 1.2)
                final_score = preference_score * random_factor
                
                scored_rides.append((final_score, ride, queue_path, queue_entrance, path))
                DebugConfig.log('engine', f"Ride {ride.defn.name} scored {final_score:.2f} for guest {guest.id} (thrill: {thrill_score:.2f}, nausea: {nausea_score:.2f})")
            
            # Select the ride with the highest score
            scored_rides.sort(key=lambda x: x[0], reverse=True)
            selected_score, selected_ride, queue_path, queue_entrance, path = scored_rides[0]
            
            guest.path = path[1:]
            guest.target_ride = selected_ride
            guest.target_queue = queue_path
            guest.state = "walking_to_queue"
            DebugConfig.log('engine', f"Guest {guest.id} selected ride {selected_ride.defn.name} (score: {selected_score:.2f}), walking to queue entrance at {queue_entrance}")
        else:
            DebugConfig.log('engine', f"No available rides found for guest {guest.id}")
    
    def _handle_guest_boarding(self, guest):
        """Handle guest boarding a ride"""
        DebugConfig.log('engine', f"Handling boarding for guest {guest.id}")
        if self.queue_manager.can_visitor_board_ride(guest):
            DebugConfig.log('engine', f"Guest {guest.id} can board ride")
            # Board the ride
            if self.queue_manager.board_visitor_on_ride(guest):
                DebugConfig.log('engine', f"Guest {guest.id} successfully boarded ride")
                guest.state = "riding"
                # The ride will launch automatically when it reaches capacity
            else:
                DebugConfig.log('engine', f"Guest {guest.id} failed to board ride")
        else:
            DebugConfig.log('engine', f"Guest {guest.id} cannot board ride")

    def handle_events(self):
        placing = self.toolbar.active
        hover=None
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return False, placing, hover
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return False, placing, hover
                elif e.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.renderer.camera.set_zoom(self.renderer.camera.zoom+0.1)
                    self.renderer._recalc()
                    self.renderer._rebuild_surfaces()
                    self.spr_cache.clear()  # Clear sprite cache on zoom change
                elif e.key==pygame.K_MINUS:
                    self.renderer.camera.set_zoom(self.renderer.camera.zoom-0.1)
                    self.renderer._recalc()
                    self.renderer._rebuild_surfaces()
                    self.spr_cache.clear()  # Clear sprite cache on zoom change

                # Game speed controls
                elif e.key==pygame.K_SPACE:
                    # Toggle pause
                    self.game_speed = 1.0 if self.game_speed == 0 else 0
                    DebugConfig.log('engine', f"Game speed: {'PAUSED' if self.game_speed == 0 else 'x1'}")
                elif e.key==pygame.K_1:
                    self.game_speed = 1.0
                    DebugConfig.log('engine', "Game speed: x1")
                elif e.key==pygame.K_2:
                    self.game_speed = 2.0
                    DebugConfig.log('engine', "Game speed: x2")
                elif e.key==pygame.K_3:
                    self.game_speed = 3.0
                    DebugConfig.log('engine', "Game speed: x3")

                # Park open/close toggle
                elif e.key==pygame.K_o:
                    self.park_open = not self.park_open
                    if not self.park_open:
                        self.park_just_closed = True  # Trigger evacuation
                    status = "OPEN" if self.park_open else "CLOSED"
                    DebugConfig.log('engine', f"Park is now {status}")

                # Save/Load controls
                elif e.key==pygame.K_F5:
                    # Quick save
                    save_path = self.save_game("quicksave")
                    print(f"✓ Quick saved to: {save_path}")
                elif e.key==pygame.K_F9:
                    # Quick load
                    if self.load_game("quicksave"):
                        print("✓ Quick load successful!")
                    else:
                        print("✗ Quick load failed - no save found")

            # Mouse wheel zoom control
            if e.type == pygame.MOUSEWHEEL:
                # Get mouse position
                mouse_pos = pygame.mouse.get_pos()

                # Convert mouse screen position to grid coordinates BEFORE zoom
                old_grid_x, old_grid_y = self.renderer.screen_to_grid(mouse_pos[0], mouse_pos[1])

                # e.y > 0 = scroll up (zoom in), e.y < 0 = scroll down (zoom out)
                zoom_delta = e.y * 0.15  # 0.15 per wheel notch for smooth zooming
                old_zoom = self.renderer.camera.zoom
                new_zoom = old_zoom + zoom_delta
                self.renderer.camera.set_zoom(new_zoom)
                self.renderer._recalc()

                # Convert the same grid point back to screen coordinates AFTER zoom
                new_screen_x, new_screen_y = self.renderer.grid_to_screen(old_grid_x, old_grid_y)

                # Adjust camera so the grid point under mouse stays in the same screen position
                self.renderer.camera.x += (new_screen_x - mouse_pos[0])
                self.renderer.camera.y += (new_screen_y - mouse_pos[1])

                self.renderer._rebuild_surfaces()
                self.spr_cache.clear()  # Clear sprite cache on zoom change

            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                action = self.debug_menu.handle_mouse(e)
                if action:
                    if action[0]=='proj':
                        self.proj_index=action[1]
                        tw,th=self.proj_presets[self.proj_index]
                        self.renderer.set_projection(tw,th)
                    elif action[0]=='tilt_oblique':
                        self.renderer.set_oblique_tilt(action[1])
                    elif action[0]=='toggle_arrows':
                        # L'état est déjà mis à jour dans le debug menu
                        pass
                if e.type==pygame.MOUSEMOTION:
                    # Gérer le survol des boutons de la toolbar et sous-menus
                    screen_height = self.screen.get_height()
                    toolbar_y = screen_height - 48
                    # Vérifier si la souris est dans la toolbar ou ses sous-menus
                    if e.pos[1] >= toolbar_y or self._is_in_toolbar_area(e.pos, screen_height):
                        self.toolbar.handle_mouse_move(e.pos, screen_height)
                if e.type==pygame.MOUSEBUTTONDOWN:
                    if e.button==2:
                        self.dragging=True; self.drag_start=e.pos; self.cam_start=(self.renderer.camera.x, self.renderer.camera.y)
                    elif e.button==1:
                        # Handle entrance fee panel interactions first (modal priority)
                        if self.entrance_fee_panel_open:
                            # Check if clicking on close button
                            if hasattr(self, 'entrance_fee_close_button_rect') and self.entrance_fee_close_button_rect.collidepoint(e.pos):
                                self.entrance_fee_panel_open = False
                                continue
                            # Check if clicking on slider
                            elif hasattr(self, 'entrance_fee_slider_rect') and self.entrance_fee_slider_rect.collidepoint(e.pos):
                                self.entrance_fee_slider_dragging = True
                                # Calculate new fee based on click position
                                slider_x = self.entrance_fee_slider_rect.x
                                slider_width = self.entrance_fee_slider_rect.width
                                click_ratio = (e.pos[0] - slider_x) / slider_width
                                click_ratio = max(0.0, min(1.0, click_ratio))
                                new_fee = int(self.entrance_fee_slider_min + click_ratio * (self.entrance_fee_slider_max - self.entrance_fee_slider_min))
                                self.set_entrance_fee(new_fee)
                                continue
                            # Click outside panel closes it
                            else:
                                panel_width = 400
                                panel_height = 300
                                panel_x = (self.screen.get_width() - panel_width) // 2
                                panel_y = (self.screen.get_height() - panel_height) // 2
                                panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
                                if not panel_rect.collidepoint(e.pos):
                                    self.entrance_fee_panel_open = False
                                continue

                        gx,gy=self.renderer.screen_to_grid(*e.pos); hover=(gx,gy)
                        # Vérifier si le clic est dans la toolbar ou ses sous-menus
                        screen_height = self.screen.get_height()
                        toolbar_y = screen_height - 48
                        if e.pos[1] >= toolbar_y or self._is_in_toolbar_area(e.pos, screen_height):
                            clicked=self.toolbar.handle_click(e.pos, screen_height)
                            if clicked=='debug_toggle':
                                self.debug_menu.toggle()
                            elif clicked=='entrance_fee_config':
                                self.entrance_fee_panel_open = not self.entrance_fee_panel_open
                            elif clicked and clicked not in ['paths', 'rides', 'shops', 'employees', 'tools', 'bins']: 
                                placing=self.toolbar.active
                                # Reset placement modes when selecting a new tool
                                if not placing.startswith('ride_'):
                                    self.ride_placement_mode = None
                                    self.selected_ride = None
                                if not placing.startswith('restroom_'):
                                    self.restroom_placement_mode = None
                                    self.selected_restroom = None
                                if not placing.startswith('employee_'):
                                    self.employee_placement_mode = None
                        else:
                            # Fermer les sous-menus si clic ailleurs
                            self.toolbar.expanded_group = None
                            if self.grid.in_bounds(gx,gy):
                                if placing=='walk_path':
                                    if not self._is_on_ride(gx, gy):
                                        self.grid.set(gx,gy,TILE_WALK)
                                        self.path_dragging=True; self.last_path_pos=(gx,gy)
                                        # Check shop and restroom connections when placing walk paths
                                        self._update_shop_connections()
                                        self._update_restroom_connections()
                                elif placing=='queue_path':
                                    if not self._is_on_ride(gx, gy):
                                        # Place the queue tile
                                        self.grid.set(gx,gy,TILE_QUEUE_PATH)
                                        self.path_dragging=True; self.last_path_pos=(gx,gy)
                                        
                                        # Check if this tile is adjacent to an existing queue tile
                                        adjacent_direction = self._get_adjacent_queue_direction(gx, gy)
                                        if adjacent_direction:
                                            # Check if we can orient this waypoint (no conflicts)
                                            if self.queue_manager.can_orient_waypoint(self.grid, gx, gy, adjacent_direction):
                                                # Orient this waypoint towards the adjacent tile
                                                self.queue_manager.orient_queue_waypoint(self.grid, gx, gy, adjacent_direction)
                                        
                                        self.last_mouse_pos = e.pos
                                elif placing.startswith('ride_') and self.ride_placement_mode is None:
                                    rd=self.ride_defs.get(placing)
                                    if rd:
                                        # Calculate top-left position for centered placement
                                        place_x, place_y = self._get_placement_position(gx, gy, rd.size[0], rd.size[1])
                                        if self._can_place_ride(rd, place_x, place_y):
                                            new_ride = Ride(rd, place_x, place_y)
                                            self.rides.append(new_ride)
                                            self.economy.add_expense(rd.build_cost)
                                            # Mark the ride footprint on the map
                                            self._mark_ride_footprint(new_ride)
                                            # Force queue system update to connect nearby queues
                                            self._update_queue_system()
                                            # Enter entrance placement mode
                                            self.ride_placement_mode = 'entrance'
                                            self.selected_ride = new_ride
                                            placing = 'place_entrance'
                                elif placing.startswith('shop_'):
                                    sd=self.shop_defs.get(placing)
                                    if sd:
                                        # Calculate top-left position for centered placement
                                        place_x, place_y = self._get_placement_position(gx, gy, sd.size[0], sd.size[1])
                                        if self._can_place_shop(sd, place_x, place_y):
                                            new_shop = Shop(sd, place_x, place_y)
                                            self.shops.append(new_shop)
                                            self.economy.add_expense(sd.build_cost)
                                            # Mark the shop footprint on the map
                                            self._mark_shop_footprint(new_shop)
                                            # Auto-create entrance on middle south tile
                                            width, height = sd.size
                                            entrance_x = place_x + width // 2
                                            entrance_y = place_y + height - 1
                                            entrance = ShopEntrance(sd.id, entrance_x, entrance_y, 'S')
                                            new_shop.entrance = entrance
                                            # Mark shop as connected since we validated walk path in _can_place_shop
                                            new_shop.connected_to_path = True
                                            DebugConfig.log('engine', f"Placed {sd.name} at ({place_x}, {place_y}) with auto south entrance at ({entrance_x}, {entrance_y})")
                                elif self.ride_placement_mode == 'entrance' and self.selected_ride:
                                    if self.selected_ride.can_place_entrance(gx, gy):
                                        self.selected_ride.place_entrance(gx, gy)
                                        self.grid.set(gx, gy, TILE_RIDE_ENTRANCE)
                                        self.economy.add_expense(self.selected_ride.defn.entrance_cost)
                                        # Update queue system to connect to this entrance
                                        self._update_queue_system()
                                        # Enter exit placement mode
                                        self.ride_placement_mode = 'exit'
                                elif self.ride_placement_mode == 'exit' and self.selected_ride:
                                    if self.selected_ride.can_place_exit(gx, gy):
                                        self.selected_ride.place_exit(gx, gy)
                                        self.grid.set(gx, gy, TILE_RIDE_EXIT)
                                        self.economy.add_expense(self.selected_ride.defn.exit_cost)
                                        # Exit placement mode
                                        self.ride_placement_mode = None
                                        self.selected_ride = None
                                elif placing.startswith('restroom_'):
                                    # Handle restroom placement (like bins - adjacent to walk paths)
                                    rd = self.restroom_defs.get(placing)
                                    if rd:
                                        # Calculate top-left position for centered placement
                                        place_x, place_y = self._get_placement_position(gx, gy, rd.size[0], rd.size[1])
                                        if self._can_place_restroom(rd, place_x, place_y):
                                            # Check if restroom is adjacent to a walk path
                                            if self._is_restroom_adjacent_to_path(rd, place_x, place_y):
                                                new_restroom = Restroom(rd, place_x, place_y)
                                                self.restrooms.append(new_restroom)
                                                self.economy.add_expense(rd.build_cost)
                                                # Mark the restroom footprint on the map
                                                self._mark_restroom_footprint(new_restroom)
                                                # Check path connection
                                                self._check_restroom_path_connection(new_restroom)
                                                DebugConfig.log('engine', f"Placed {rd.name} at ({place_x}, {place_y})")
                                elif placing.startswith('employee_'):
                                    # Handle employee placement
                                    employee_def = self.employee_defs.get(placing)
                                    if employee_def:
                                        # Check placement restrictions based on employee type
                                        can_place = False
                                        if employee_def.type == 'security':
                                            # Security guards can only be placed on paths
                                            can_place = self.grid.get(gx, gy) == TILE_WALK
                                        elif employee_def.type == 'maintenance':
                                            # Maintenance workers can be placed on paths or grass
                                            can_place = self.grid.get(gx, gy) in [TILE_WALK, TILE_GRASS]
                                        elif employee_def.type == 'mascot':
                                            # Mascots can be placed on paths or queue paths
                                            can_place = self.grid.get(gx, gy) in [TILE_WALK, TILE_QUEUE_PATH]
                                        else:  # engineer
                                            # Engineers can be placed anywhere
                                            can_place = True
                                        
                                        if can_place:
                                            # Create appropriate employee type
                                            if employee_def.type == 'engineer':
                                                employee = Engineer(employee_def, gx, gy)
                                            elif employee_def.type == 'maintenance':
                                                employee = MaintenanceWorker(employee_def, gx, gy)
                                                # Set placement type for maintenance worker
                                                employee.set_placement_type(self.grid.get(gx, gy))
                                            elif employee_def.type == 'security':
                                                employee = SecurityGuard(employee_def, gx, gy)
                                            elif employee_def.type == 'mascot':
                                                employee = Mascot(employee_def, gx, gy)
                                            else:
                                                continue
                                            
                                            self.employees.append(employee)
                                            self.economy.add_expense(employee_def.salary)  # Pay first hour
                                            DebugConfig.log('engine', f"Placed {employee_def.name} at ({gx}, {gy})")
                                elif placing.startswith('bin_'):
                                    # Handle bin placement
                                    bin_def = self.bin_defs.get(placing)
                                    if bin_def:
                                        # Bins must be placed on GRASS adjacent to WALK
                                        if self.grid.get(gx, gy) == TILE_GRASS:
                                            # Check if adjacent to a walk path
                                            adjacent_to_walk = False
                                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                                nx, ny = gx + dx, gy + dy
                                                if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_WALK:
                                                    adjacent_to_walk = True
                                                    break
                                            
                                            if adjacent_to_walk:
                                                # Check if there's already a bin here
                                                existing_bin = self.litter_manager.get_bin_at(gx, gy)
                                                if not existing_bin:
                                                    bin_obj = self.litter_manager.add_bin(bin_def, gx, gy)
                                                    if bin_obj:
                                                        self.grid.set(gx, gy, TILE_BIN)
                                                        self.economy.add_expense(bin_def.cost)
                                                        DebugConfig.log('engine', f"Placed {bin_def.name} at ({gx}, {gy}) for ${bin_def.cost}")
                                                else:
                                                    DebugConfig.log('engine', f"Bin already exists at ({gx}, {gy})")
                                            else:
                                                DebugConfig.log('engine', f"Cannot place bin at ({gx}, {gy}) - not adjacent to walk path")
                                        else:
                                            DebugConfig.log('engine', f"Cannot place bin at ({gx}, {gy}) - must be on grass")
                    elif e.button==3:
                        gx,gy=self.renderer.screen_to_grid(*e.pos); hover=(gx,gy)
                        if self.grid.in_bounds(gx,gy):
                            # Check if clicking on a ride
                            ride = self._get_ride_at_position(gx, gy)
                            if ride:
                                # Remove the ride and clear its footprint
                                self._clear_ride_footprint(ride)
                                self.rides.remove(ride)
                                # Clear entrance and exit tiles
                                if ride.entrance:
                                    self.grid.set(ride.entrance.x, ride.entrance.y, TILE_GRASS)
                                if ride.exit:
                                    self.grid.set(ride.exit.x, ride.exit.y, TILE_GRASS)
                                # Reset placement mode if this was the selected ride
                                if self.selected_ride == ride:
                                    self.ride_placement_mode = None
                                    self.selected_ride = None
                            # Check if clicking on a shop
                            shop = self._get_shop_at_position(gx, gy)
                            if shop:
                                # Remove shop footprint
                                self._clear_shop_footprint(shop)
                                # Remove from shops list
                                self.shops.remove(shop)
                            # Check if clicking on a restroom
                            restroom = self._get_restroom_at_position(gx, gy)
                            if restroom:
                                # Remove restroom footprint
                                self._clear_restroom_footprint(restroom)
                                # Remove from list
                                self.restrooms.remove(restroom)
                            # Check if clicking on an employee
                            employee = self._get_employee_at_position(gx, gy)
                            if employee:
                                self.employees.remove(employee)
                            # Check if clicking on a bin
                            bin_obj = self.litter_manager.get_bin_at(gx, gy)
                            if bin_obj:
                                self.litter_manager.remove_bin(bin_obj)
                                self.grid.set(gx, gy, TILE_GRASS)
                                DebugConfig.log('engine', f"Removed bin at ({gx}, {gy})")
                            else:
                                # Check if clicking on a queue tile
                                if self.grid.get(gx, gy) == TILE_QUEUE_PATH:
                                    # Remove queue waypoint and reorient adjacent waypoints
                                    self.queue_manager.remove_queue_waypoint(self.grid, gx, gy)
                                    self.grid.set(gx,gy,TILE_GRASS)
                                else:
                                    # Regular tile clearing
                                    self.grid.set(gx,gy,TILE_GRASS)
                elif e.type==pygame.MOUSEBUTTONUP:
                    if e.button==2: self.dragging=False
                    elif e.button==1:
                        self.entrance_fee_slider_dragging = False
                        self.path_dragging=False
                        self.last_path_pos=None
                        self.last_queue_pos=None
                        self.last_mouse_pos=None
                elif e.type==pygame.MOUSEMOTION:
                    # Handle entrance fee slider dragging
                    if self.entrance_fee_slider_dragging and hasattr(self, 'entrance_fee_slider_rect'):
                        slider_x = self.entrance_fee_slider_rect.x
                        slider_width = self.entrance_fee_slider_rect.width
                        drag_ratio = (e.pos[0] - slider_x) / slider_width
                        drag_ratio = max(0.0, min(1.0, drag_ratio))
                        new_fee = int(self.entrance_fee_slider_min + drag_ratio * (self.entrance_fee_slider_max - self.entrance_fee_slider_min))
                        self.set_entrance_fee(new_fee)
                    elif self.dragging:
                        dx=e.pos[0]-self.drag_start[0]
                        dy=e.pos[1]-self.drag_start[1]
                        self.renderer.camera.x=self.cam_start[0]-dx
                        self.renderer.camera.y=self.cam_start[1]-dy
                    elif self.path_dragging and (placing=='walk_path' or placing=='queue_path'):
                        gx,gy=self.renderer.screen_to_grid(*e.pos)
                        if self.grid.in_bounds(gx,gy) and (gx,gy) != self.last_path_pos and not self._is_on_ride(gx, gy):
                            if placing=='walk_path': 
                                self.grid.set(gx,gy,TILE_WALK)
                                self.last_path_pos=(gx,gy)
                            elif placing=='queue_path':
                                # Place queue tile during drag
                                self.grid.set(gx,gy,TILE_QUEUE_PATH)
                                self.last_path_pos=(gx,gy)
                                
                                # Check if this tile is adjacent to an existing queue tile
                                adjacent_direction = self._get_adjacent_queue_direction(gx, gy)
                                if adjacent_direction:
                                    # Check if we can orient this waypoint (no conflicts)
                                    if self.queue_manager.can_orient_waypoint(self.grid, gx, gy, adjacent_direction):
                                        # Orient this waypoint towards the adjacent tile
                                        self.queue_manager.orient_queue_waypoint(self.grid, gx, gy, adjacent_direction)
                                
                                self.last_mouse_pos = e.pos
        # keyboard pan
        keys=pygame.key.get_pressed(); sp=600*self.clock.get_time()/1000.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.renderer.camera.pan(-sp,0)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.renderer.camera.pan(+sp,0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.renderer.camera.pan(0,-sp)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.renderer.camera.pan(0,+sp)
        mx,my=pygame.mouse.get_pos(); hover=self.renderer.screen_to_grid(mx,my)
        return True, placing, hover

    def _get_placement_position(self, hover_x, hover_y, width, height):
        """
        Calculate top-left corner position for centered placement

        When placing multi-tile objects, we want the cursor to be at the center
        of the object, not the top-left corner. This method converts the cursor
        position to the top-left corner position.

        Args:
            hover_x, hover_y: Current cursor position on grid
            width, height: Size of the object in tiles

        Returns:
            (x, y): Top-left corner position for placement
        """
        return (hover_x - width // 2, hover_y - height // 2)

    def _create_park_entrance(self):
        """Create fixed park entrance at south center of map"""
        # Calculate entrance position: south center of map
        entrance_x = self.grid.width // 2 - (self.entrance_width // 2)  # Center the entrance
        entrance_y = self.grid.height - 3  # 3 tiles from bottom

        # Store entrance center position for guest spawning
        self.park_entrance = (entrance_x + self.entrance_width // 2, entrance_y)

        # Mark entrance tiles (TILE_PARK_ENTRANCE)
        for x in range(entrance_x, entrance_x + self.entrance_width):
            if self.grid.in_bounds(x, entrance_y):
                self.grid.set(x, entrance_y, TILE_PARK_ENTRANCE)

        # Add walkable path in front of entrance (connection to park)
        for x in range(entrance_x, entrance_x + self.entrance_width):
            if self.grid.in_bounds(x, entrance_y - 1):
                self.grid.set(x, entrance_y - 1, TILE_WALK)

        DebugConfig.log('engine', f"Park entrance created at {self.park_entrance} (width: {self.entrance_width} tiles)")

    def _calculate_spawn_rate(self):
        """Calculate guest spawn rate based on entrance fee (progressive system)

        Lower entrance fee = faster spawning (more guests)
        Higher entrance fee = slower spawning (fewer guests)

        Formula: spawn_rate = 2.0 + (entrance_fee / 100) * 4.0

        Examples:
        - $10 fee → 2.4s (fast)
        - $50 fee → 4.0s (normal)
        - $100 fee → 6.0s (slow)
        - $200 fee → 10.0s (very slow)
        """
        entrance_fee = self.economy.park_entrance_fee
        spawn_rate = 2.0 + (entrance_fee / 100.0) * 4.0
        return max(1.0, min(15.0, spawn_rate))  # Clamp between 1s and 15s

    def set_entrance_fee(self, amount):
        """Set park entrance fee and recalculate spawn rate"""
        self.economy.set_entrance_fee(amount)
        self.guest_spawn_rate = self._calculate_spawn_rate()
        DebugConfig.log('engine', f"Entrance fee set to ${amount}, spawn rate: {self.guest_spawn_rate:.1f}s")

    def _spawn_guests_at_entrance(self, dt):
        """Spawn guests at park entrance at regular intervals"""
        if not self.park_entrance:
            return  # No entrance created yet

        # Only spawn guests if park is open
        if not self.park_open:
            return

        self.guest_spawn_timer += dt

        # Spawn a new guest when timer exceeds spawn rate
        if self.guest_spawn_timer >= self.guest_spawn_rate:
            self.guest_spawn_timer = 0.0  # Reset timer

            # Spawn guest at entrance position (with slight random offset for variety)
            import random
            offset_x = random.uniform(-1.5, 1.5)  # Spread guests across entrance width
            spawn_x = self.park_entrance[0] + offset_x
            spawn_y = self.park_entrance[1]

            # Create potential guest and check if they can afford entrance fee
            new_guest = Guest(spawn_x, spawn_y)
            entrance_fee = self.economy.park_entrance_fee

            # Check if guest can afford entrance fee
            if new_guest.budget >= entrance_fee:
                # Guest can afford - deduct entrance fee and spawn them
                new_guest.money -= entrance_fee
                new_guest.entry_time = self.game_time  # Record entry time for stay limit
                self.economy.collect_entrance_fee(entrance_fee)
                self.guests.append(new_guest)
                self.guests_entered += 1

                DebugConfig.log('engine', f"Guest {new_guest.id} entered park (paid ${entrance_fee}, has ${new_guest.money} left). Total entered: {self.guests_entered}")
            else:
                # Guest cannot afford - refuse entry
                self.economy.guests_refused += 1
                DebugConfig.log('engine', f"Guest refused entry (budget ${new_guest.budget} < fee ${entrance_fee}). Total refused: {self.economy.guests_refused}")

    def _evacuate_park(self):
        """Force all guests to leave the park when it closes"""
        if not self.park_entrance:
            return

        from .pathfinding import astar

        evacuation_count = 0
        for guest in self.guests:
            # Only evacuate guests who are not already leaving
            if guest.state != "leaving":
                guest_pos = (int(guest.x), int(guest.y))
                entrance_pos = self.park_entrance

                # Find path to park entrance
                path = astar(self.grid, guest_pos, entrance_pos)

                if path and len(path) > 1:
                    guest.path = path[1:]  # Skip current position
                else:
                    # Can't find path, teleport to entrance
                    guest.x = float(entrance_pos[0])
                    guest.y = float(entrance_pos[1])
                    guest.grid_x = entrance_pos[0]
                    guest.grid_y = entrance_pos[1]
                    guest.path = []

                # Set guest to leaving state
                guest.state = "leaving"
                guest.target_ride = None
                guest.target_shop = None
                guest.target_queue = None
                guest.current_queue = None
                evacuation_count += 1

        if evacuation_count > 0:
            DebugConfig.log('engine', f"Park closed - evacuating {evacuation_count} guests")

    def _handle_leaving_guests(self):
        """Handle guests wanting to leave the park (unhappy or satisfied)"""
        if not self.park_entrance:
            return  # No entrance to leave from

        guests_to_remove = []

        for guest in self.guests:
            # Calculate time in park (in-game days)
            time_in_park_seconds = self.game_time - guest.entry_time
            time_in_park_days = time_in_park_seconds / 86400.0  # 86400 seconds = 1 day

            # Check if guest should leave
            # Reasons: unhappy (satisfaction < 20%), stayed too long (> max_visitor_stay_days), or no money left
            should_leave = False
            leave_reason = ""

            if guest.satisfaction < 0.2:
                should_leave = True
                leave_reason = f"unhappy (satisfaction: {guest.satisfaction:.2f})"
            elif time_in_park_days > self.max_visitor_stay_days:
                should_leave = True
                leave_reason = f"max stay exceeded ({time_in_park_days:.1f} days > {self.max_visitor_stay_days} days)"
            elif guest.money <= 0:
                should_leave = True
                leave_reason = "out of money"

            if guest.state != "leaving" and should_leave:
                # Guest is unhappy and wants to leave
                guest_pos = (int(guest.x), int(guest.y))
                entrance_pos = self.park_entrance

                # Find path to park entrance
                path = astar(self.grid, guest_pos, entrance_pos)

                if path and len(path) > 1:
                    guest.path = path[1:]  # Skip current position
                    guest.state = "leaving"
                    guest.target_ride = None
                    guest.target_shop = None
                    guest.target_queue = None
                    DebugConfig.log('engine', f"Guest {guest.id} is leaving ({leave_reason})")
                else:
                    # Can't find path to entrance, teleport to entrance
                    guest.x = float(entrance_pos[0])
                    guest.y = float(entrance_pos[1])
                    guest.grid_x = entrance_pos[0]
                    guest.grid_y = entrance_pos[1]
                    guest.state = "leaving"
                    guest.path = []
                    DebugConfig.log('engine', f"Guest {guest.id} teleported to entrance (no path found)")

            # Remove guests who have reached the entrance
            if guest.state == "leaving" and not guest.path and not guest.is_moving:
                guests_to_remove.append(guest)
                self.guests_left += 1
                DebugConfig.log('engine', f"Guest {guest.id} left the park. Total left: {self.guests_left}")

        # Remove guests who have left
        for guest in guests_to_remove:
            self.guests.remove(guest)

    def update(self, dt):
        # Calculate scaled delta time based on game speed
        # When paused (game_speed = 0), scaled_dt = 0, so entities don't move
        scaled_dt = dt * self.game_speed

        # Update game time based on speed (independent visual clock)
        # 1 in-game day = day_duration_real_minutes real minutes at speed x1
        # Speed multiplier: 0 (paused), 1 (normal), 2 (fast), 3 (very fast)
        if self.game_speed > 0:
            # Convert real time to game time
            # day_duration_real_minutes real minutes = 24 hours = 1440 minutes = 86400 seconds in-game
            seconds_per_real_second = (86400.0 / (self.day_duration_real_minutes * 60.0)) * self.game_speed
            game_dt = dt * seconds_per_real_second
            self.game_time += game_dt

            # Calculate current day, hour, minute
            total_seconds = self.game_time
            total_minutes = int(total_seconds / 60)
            total_hours = total_minutes / 60

            # Calculate day (starting from day 1)
            self.game_day = int(total_hours / 24) + 1

            # Calculate hour and minute (starting from starting_hour)
            hours_since_start = total_hours % 24
            self.game_hour = int((self.starting_hour + hours_since_start) % 24)
            self.game_minute = total_minutes % 60

        # Handle park closure evacuation
        if self.park_just_closed:
            self._evacuate_park()
            self.park_just_closed = False

        # Spawn guests at park entrance (only if park is open and not paused)
        if self.game_speed > 0:
            self._spawn_guests_at_entrance(dt)

        # Handle unhappy guests leaving the park
        self._handle_leaving_guests()

        # Update queue system
        self._update_queue_system()

        # Update litter manager
        self.litter_manager.tick(scaled_dt)

        # Update guests
        pts=[(x,y) for y in range(self.grid.height) for x in range(self.grid.width) if self.grid.walkable(x,y)]
        import random
        # DebugConfig.log('engine', f"Processing {len(self.guests)} guests")  # Too frequent
        for g in self.guests:
            # Track guest state before tick
            previous_state = g.state
            previous_shop = g.current_shop
            previous_target_shop = g.target_shop

            g.tick(scaled_dt)

            # Check if guest just finished shopping (state changed from SHOPPING to something else)
            if previous_state == "shopping" and g.state != "shopping" and previous_shop:
                # Guest finished shopping, add revenue
                shop_price = previous_shop.defn.base_price
                self.economy.add_income(shop_price)
                DebugConfig.log('engine', f"Guest {g.id} finished shopping at {previous_shop.defn.name}, revenue: ${shop_price}")

                # Apply shopping satisfaction bonus
                g.apply_shopping_bonus()

            # Check if guest just finished eating (state changed from EATING to something else)
            if previous_state == "eating" and g.state != "eating" and previous_target_shop:
                # Guest finished eating, add revenue (guest already paid in tick handler)
                food_price = previous_target_shop.defn.base_price
                self.economy.add_income(food_price)
                DebugConfig.log('engine', f"Guest {g.id} finished eating at {previous_target_shop.defn.name}, revenue: ${food_price}")

            # Check if guest just finished drinking (state changed from DRINKING to something else)
            if previous_state == "drinking" and g.state != "drinking" and previous_target_shop:
                # Guest finished drinking, add revenue (guest already paid in tick handler)
                drink_price = previous_target_shop.defn.base_price
                self.economy.add_income(drink_price)
                DebugConfig.log('engine', f"Guest {g.id} finished drinking at {previous_target_shop.defn.name}, revenue: ${drink_price}")

            # Check if guest just finished riding (state changed from RIDING to EXITING)
            if previous_state == "riding" and g.state == "exiting":
                # Apply ride completion bonus
                g.apply_ride_completion_bonus()

            # Check if guest just joined a queue (state changed to QUEUING)
            if g.state == "queuing" and previous_state != "queuing" and g.current_queue:
                queue_length = len(g.current_queue.visitors)
                g.apply_short_queue_bonus(queue_length)
                g.apply_long_queue_penalty(queue_length)

            # Check if guest successfully used bin (state changed from USING_BIN to WANDERING)
            if previous_state == "using_bin" and g.state == "wandering" and not g.has_litter:
                g.apply_bin_use_bonus()
        
        # Update employees
        for employee in self.employees:
            employee.tick(scaled_dt)
            # Pay salary every hour (3600 seconds)
            if employee.salary_timer >= 3600.0:
                self.economy.cash -= employee.defn.salary
                employee.salary_timer = 0.0
                DebugConfig.log('engine', f"Paid salary to {employee.defn.name}: ${employee.defn.salary}")
        
        # Assign maintenance workers to litter and gardening
        self._assign_maintenance_workers_to_litter()
        self._assign_maintenance_workers_to_gardening()

        # Assign security guards to patrol
        self._assign_security_guards_to_patrol()

        # Assign mascots to crowds
        self._assign_mascots_to_crowds()

        # Apply employee effects on guests
        self._apply_employee_effects_on_guests()

        # Apply litter proximity penalties
        self._apply_litter_proximity_penalties()

        # Apply park cleanliness bonus
        self._apply_park_cleanliness_bonus()

        # Update rides
        for ride in self.rides:
            ride.tick(scaled_dt)
        
        # Assign engineers to broken rides
        self._assign_engineers_to_broken_rides()
        
        # Handle broken rides - evacuate queues
        self._handle_broken_rides()
        
        # Debug: Check for stuck visitors in rides
        for ride in self.rides:
            if len(ride.current_visitors) > 0:
                DebugConfig.log('engine', f"Ride {ride.defn.name} has {len(ride.current_visitors)} visitors: {[v.id for v in ride.current_visitors]}")
        
        # Debug: Check rides status (only if debug enabled)
        if DebugConfig.RIDES and len(self.rides) > 0:
            DebugConfig.log('engine', f"Found {len(self.rides)} rides: {[r.defn.name for r in self.rides]}")
            for ride in self.rides:
                DebugConfig.log('engine', f"Ride {ride.defn.name} at ({ride.x}, {ride.y}), broken: {ride.is_broken}, being_repaired: {ride.being_repaired}")
        
        for g in self.guests:
            # PRIORITY: Handle litter first if timer expired and guest is in a "free" state
            # Allow litter dropping in wandering, walking_to_queue, walking_to_shop states
            if (g.has_litter and 
                g.litter_hold_timer >= g.litter_hold_duration and
                g.state in ["wandering", "walking_to_queue", "walking_to_shop"]):
                DebugConfig.log('litter', f"Guest {g.id} litter hold timer expired ({g.litter_hold_timer:.1f}/{g.litter_hold_duration:.1f}), handling litter at ({g.grid_x}, {g.grid_y}) in state {g.state}")
                self._handle_guest_litter(g)
                # After handling litter, skip other processing this tick to avoid immediate redirection
                continue
            
            if g.state == "wandering" and not g.path and pts:
                goal=random.choice(pts); p=astar(self.grid,(g.grid_x,g.grid_y),goal)
                if p: g.path=p[1:]
            elif g.state == "walking_to_queue":
                # Guest is walking to queue, no additional pathfinding needed
                DebugConfig.log('engine', f"Engine processing guest {g.id} walking to queue")
                pass
            elif g.state == "walking_to_shop":
                # Guest is walking to shop, no additional pathfinding needed
                DebugConfig.log('engine', f"Engine processing guest {g.id} walking to shop")
                pass
            elif g.state == "shopping":
                # Guest is shopping, no additional processing needed
                DebugConfig.log('engine', f"Engine processing guest {g.id} shopping")
                pass
            elif g.state == "wandering":
                # Look for rides or shops to visit (only if not handling litter)
                DebugConfig.log('engine', f"Engine processing wandering guest {g.id}")
                self._find_attraction_for_guest(g)
            elif g.state == "queuing":
                # Check if guest can board the ride
                DebugConfig.log('engine', f"Engine processing queuing guest {g.id}")
                # Check if guest is actually in a queue
                DebugConfig.log('engine', f"Guest {g.id} queuing state check - current_queue: {g.current_queue}, visitors in queue: {len(g.current_queue.visitors) if g.current_queue else 'None'}, queue_position: {g.queue_position}")
                if not g.current_queue:
                    DebugConfig.log('engine', f"Guest {g.id} is in queuing state but has no current_queue, resetting to wandering")
                    g.state = "wandering"
                    g.current_queue = None
                    g.target_queue = None
                    g.target_ride = None
                elif g not in g.current_queue.visitors:
                    DebugConfig.log('engine', f"Guest {g.id} is in queuing state but not in queue visitors list, resetting to wandering")
                    g.state = "wandering"
                    g.current_queue = None
                    g.target_queue = None
                    g.target_ride = None
                else:
                    self._handle_guest_boarding(g)
        
        # Update rides
        for r in self.rides: r.tick(dt)

    def _is_in_toolbar_area(self, pos, screen_height):
        """Vérifier si la position est dans la zone de la toolbar ou ses sous-menus"""
        toolbar_y = screen_height - 48
        
        # Vérifier si un sous-menu est ouvert
        if self.toolbar.expanded_group and self.toolbar.expanded_group in self.toolbar.groups:
            group_data = self.toolbar.groups[self.toolbar.expanded_group]
            items = group_data['items']
            
            if items:
                group_index = list(self.toolbar.groups.keys()).index(self.toolbar.expanded_group)
                submenu_x = 12 + group_index * 150
                submenu_y = toolbar_y - len(items) * 40 - 10
                submenu_width = 200
                submenu_height = len(items) * 40 + 10
                
                # Vérifier si la position est dans le sous-menu
                if (submenu_x <= pos[0] <= submenu_x + submenu_width and 
                    submenu_y <= pos[1] <= submenu_y + submenu_height):
                    return True
        
        return False

    def _can_place_shop(self, shop_def, x, y):
        """Vérifier si un shop peut être placé à la position donnée"""
        width, height = shop_def.size

        # Enforce 3x3 minimum size
        if width < 3 or height < 3:
            return False

        # Vérifier que toutes les tuiles sont dans les limites et libres
        for dx in range(width):
            for dy in range(height):
                gx, gy = x + dx, y + dy
                if not self.grid.in_bounds(gx, gy):
                    return False
                if self.grid.get(gx, gy) != TILE_GRASS:
                    return False

        # Vérifier que la case du milieu sud est adjacente à un chemin (TILE_WALK)
        # Middle south tile is at (x + width // 2, y + height - 1)
        entrance_x = x + width // 2
        entrance_y = y + height - 1

        # Check if the tile directly south of the middle south tile is a walk path
        south_tile_x = entrance_x
        south_tile_y = entrance_y + 1

        if not self.grid.in_bounds(south_tile_x, south_tile_y):
            return False

        if self.grid.get(south_tile_x, south_tile_y) != TILE_WALK:
            return False

        return True

    def _mark_shop_footprint(self, shop):
        """Marquer l'empreinte du shop sur la grille"""
        width, height = shop.defn.size
        for dx in range(width):
            for dy in range(height):
                gx, gy = shop.x + dx, shop.y + dy
                self.grid.set(gx, gy, TILE_SHOP_FOOTPRINT)

    def _is_on_shop(self, x, y):
        """Vérifier si une position est sur un shop"""
        return self.grid.get(x, y) == TILE_SHOP_FOOTPRINT

    def _get_shop_at_position(self, x, y):
        """Obtenir le shop à une position donnée"""
        for shop in self.shops:
            width, height = shop.defn.size
            if (shop.x <= x < shop.x + width and 
                shop.y <= y < shop.y + height):
                return shop
        return None

    def _clear_shop_footprint(self, shop):
        """Effacer l'empreinte du shop de la grille"""
        width, height = shop.defn.size
        for dx in range(width):
            for dy in range(height):
                gx, gy = shop.x + dx, shop.y + dy
                self.grid.set(gx, gy, TILE_GRASS)

    def _update_shop_connections(self):
        """Mettre à jour les connexions de tous les shops"""
        for shop in self.shops:
            # Check if middle south tile is still adjacent to a walk path
            width, height = shop.defn.size
            entrance_x = shop.x + width // 2
            entrance_y = shop.y + height - 1
            south_tile_x = entrance_x
            south_tile_y = entrance_y + 1

            if self.grid.in_bounds(south_tile_x, south_tile_y) and self.grid.get(south_tile_x, south_tile_y) == TILE_WALK:
                shop.connected_to_path = True
            else:
                shop.connected_to_path = False

    # ========== Restroom Helper Methods ==========
    def _can_place_restroom(self, restroom_def, x, y):
        """Vérifier si un restroom peut être placé à la position donnée"""
        width, height = restroom_def.size

        # Vérifier que toutes les tuiles sont dans les limites et libres
        for dx in range(width):
            for dy in range(height):
                gx, gy = x + dx, y + dy
                if not self.grid.in_bounds(gx, gy):
                    return False
                if self.grid.get(gx, gy) != TILE_GRASS:
                    return False

        return True

    def _mark_restroom_footprint(self, restroom):
        """Marquer l'empreinte du restroom sur la grille"""
        width, height = restroom.defn.size
        for dx in range(width):
            for dy in range(height):
                gx, gy = restroom.x + dx, restroom.y + dy
                self.grid.set(gx, gy, TILE_RESTROOM_FOOTPRINT)

    def _is_restroom_adjacent_to_path(self, restroom_def, x, y):
        """Vérifier si le restroom serait adjacent à un chemin (comme les bins)"""
        width, height = restroom_def.size

        # Vérifier toutes les tuiles autour du périmètre du restroom
        for dx in range(width):
            for dy in range(height):
                rx, ry = x + dx, y + dy
                # Vérifier les 4 directions autour de cette tuile
                for nx_offset, ny_offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = rx + nx_offset, ry + ny_offset
                    if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_WALK:
                        return True
        return False

    def _check_restroom_path_connection(self, restroom):
        """Vérifier si le restroom est connecté à un chemin"""
        width, height = restroom.defn.size

        # Vérifier toutes les tuiles autour du périmètre du restroom
        for dx in range(width):
            for dy in range(height):
                rx, ry = restroom.x + dx, restroom.y + dy
                # Vérifier les 4 directions autour de cette tuile
                for nx_offset, ny_offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = rx + nx_offset, ry + ny_offset
                    if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_WALK:
                        restroom.connected_to_path = True
                        return

        restroom.connected_to_path = False

    def _get_restroom_at_position(self, x, y):
        """Obtenir le restroom à une position donnée"""
        for restroom in self.restrooms:
            width, height = restroom.defn.size
            if (restroom.x <= x < restroom.x + width and
                restroom.y <= y < restroom.y + height):
                return restroom
        return None

    def _clear_restroom_footprint(self, restroom):
        """Effacer l'empreinte du restroom de la grille"""
        width, height = restroom.defn.size
        for dx in range(width):
            for dy in range(height):
                gx, gy = restroom.x + dx, restroom.y + dy
                self.grid.set(gx, gy, TILE_GRASS)

    def _update_restroom_connections(self):
        """Mettre à jour les connexions de tous les restrooms"""
        for restroom in self.restrooms:
            self._check_restroom_path_connection(restroom)

    def _find_attraction_for_guest(self, guest):
        """Trouver une attraction (ride ou shop) pour un visiteur"""
        import random

        # ========== NEEDS-BASED PRIORITY SYSTEM ==========
        # Check if guest has urgent needs (prioritize over attractions)

        # Priority 1: Bladder (most urgent if > 0.7)
        if guest.bladder > 0.7:
            restroom, path = self._find_nearest_restroom(guest)
            if restroom and path:
                guest.path = path
                guest.target_restroom = restroom
                guest.state = "walking_to_restroom"
                urgency = "CRITICAL" if guest.bladder > 0.85 else "urgent"
                DebugConfig.log('engine', f"Guest {guest.id} has {urgency} bladder need ({guest.bladder:.2f}), walking to restroom")
                return
            else:
                # No restroom available, apply penalty
                DebugConfig.log('engine', f"Guest {guest.id} needs restroom but none available!")
                guest.modify_satisfaction(-0.05, "no restroom available")

        # Priority 2: Thirst (urgent if < 0.3)
        if guest.thirst < 0.3:
            drink_shop, path = self._find_nearest_drink_shop(guest)
            if drink_shop and path:
                guest.path = path
                guest.target_shop = drink_shop
                guest.state = "walking_to_drink"
                urgency = "CRITICAL" if guest.thirst < 0.15 else "urgent"
                DebugConfig.log('engine', f"Guest {guest.id} has {urgency} thirst ({guest.thirst:.2f}), walking to drink shop")
                return
            else:
                # No drink shop available, apply penalty
                DebugConfig.log('engine', f"Guest {guest.id} needs drink but none available!")
                guest.modify_satisfaction(-0.03, "no drink shop available")

        # Priority 3: Hunger (urgent if < 0.3)
        if guest.hunger < 0.3:
            food_shop, path = self._find_nearest_food_shop(guest)
            if food_shop and path:
                guest.path = path
                guest.target_shop = food_shop
                guest.state = "walking_to_food"
                urgency = "CRITICAL" if guest.hunger < 0.15 else "urgent"
                DebugConfig.log('engine', f"Guest {guest.id} has {urgency} hunger ({guest.hunger:.2f}), walking to food shop")
                return
            else:
                # No food shop available, apply penalty
                DebugConfig.log('engine', f"Guest {guest.id} needs food but none available!")
                guest.modify_satisfaction(-0.03, "no food shop available")

        # ========== NORMAL ATTRACTION FINDING ==========
        # No urgent needs, proceed with normal behavior

        # 20% chance to just wander without targeting anything
        if random.random() < 0.2:
            DebugConfig.log('engine', f"Guest {guest.id} chose to just wander")
            return

        # Probabilité de choisir un shop vs une attraction (30% shops, 70% rides)
        if random.random() < 0.3:
            # Chercher un shop
            available_shops = []
            for shop in self.shops:
                if shop.connected_to_path:
                    # Calculate shop entrance position (middle south tile)
                    width, height = shop.defn.size
                    entrance_x = shop.x + width // 2
                    entrance_y = shop.y + height - 1
                    shop_entrance = (entrance_x, entrance_y)
                    path = astar(self.grid, (guest.grid_x, guest.grid_y), shop_entrance)
                    if path:
                        available_shops.append((shop, shop_entrance, path))
            
            if available_shops:
                # Choisir un shop au hasard
                selected_shop, shop_entrance, path = random.choice(available_shops)
                guest.path = path[1:]
                guest.target_shop = selected_shop
                guest.state = "walking_to_shop"
                DebugConfig.log('engine', f"Guest {guest.id} selected shop {selected_shop.defn.name}, walking to entrance at {shop_entrance}")
                return
        
        # Chercher une attraction
        available_rides = []
        for ride in self.rides:
            if ride.entrance and ride.exit:
                queue_path = self.queue_manager.get_queue_for_ride(ride)
                if queue_path and queue_path.can_enter():
                    queue_entrance = queue_path.get_entrance_position()
                    if queue_entrance:
                        path = astar(self.grid, (guest.grid_x, guest.grid_y), queue_entrance)
                        if path:
                            available_rides.append((ride, queue_path, queue_entrance, path))
        
        if available_rides:
            # Calculer les scores basés sur les préférences du visiteur
            scored_rides = []
            for ride, queue_path, queue_entrance, path in available_rides:
                thrill_score = 1.0 - abs(guest.thrill_preference - ride.defn.thrill)
                nausea_score = 1.0 - abs(guest.nausea_tolerance - ride.defn.nausea)
                preference_score = (thrill_score + nausea_score) / 2.0
                random_factor = random.uniform(0.8, 1.2)
                final_score = preference_score * random_factor
                scored_rides.append((final_score, ride, queue_path, queue_entrance, path))
            
            scored_rides.sort(key=lambda x: x[0], reverse=True)
            selected_score, selected_ride, queue_path, queue_entrance, path = scored_rides[0]
            
            guest.path = path[1:]
            guest.target_ride = selected_ride
            guest.target_queue = queue_path
            guest.state = "walking_to_queue"
            DebugConfig.log('engine', f"Guest {guest.id} selected ride {selected_ride.defn.name} (score: {selected_score:.2f}), walking to queue entrance at {queue_entrance}")
        else:
            DebugConfig.log('engine', f"No available attractions found for guest {guest.id}")

    def _find_nearest_food_shop(self, guest):
        """Trouver le food shop le plus proche pour un visiteur"""
        nearest_shop = None
        nearest_path = None
        shortest_distance = float('inf')

        for shop in self.shops:
            # Only consider food shops that are connected to paths
            if shop.defn.shop_type == "food" and shop.connected_to_path:
                # Calculate shop entrance position (middle south tile)
                width, height = shop.defn.size
                entrance_x = shop.x + width // 2
                entrance_y = shop.y + height - 1
                shop_entrance = (entrance_x, entrance_y)
                path = astar(self.grid, (guest.grid_x, guest.grid_y), shop_entrance)
                if path:
                    distance = len(path)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        nearest_shop = shop
                        nearest_path = path[1:]  # Exclude current position

        if nearest_shop:
            return nearest_shop, nearest_path
        return None, None

    def _find_nearest_drink_shop(self, guest):
        """Trouver le drink shop le plus proche pour un visiteur"""
        nearest_shop = None
        nearest_path = None
        shortest_distance = float('inf')

        for shop in self.shops:
            # Only consider drink shops that are connected to paths
            if shop.defn.shop_type == "drink" and shop.connected_to_path:
                # Calculate shop entrance position (middle south tile)
                width, height = shop.defn.size
                entrance_x = shop.x + width // 2
                entrance_y = shop.y + height - 1
                shop_entrance = (entrance_x, entrance_y)
                path = astar(self.grid, (guest.grid_x, guest.grid_y), shop_entrance)
                if path:
                    distance = len(path)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        nearest_shop = shop
                        nearest_path = path[1:]  # Exclude current position

        if nearest_shop:
            return nearest_shop, nearest_path
        return None, None

    def _find_nearest_restroom(self, guest):
        """Trouver le restroom le plus proche pour un visiteur"""
        nearest_restroom = None
        nearest_path = None
        shortest_distance = float('inf')

        for restroom in self.restrooms:
            # Only consider restrooms that are connected to paths and not full
            if restroom.connected_to_path and not restroom.is_full():
                # Find the nearest walkable tile adjacent to the restroom
                width, height = restroom.defn.size
                best_target = None
                best_path = None
                best_dist = float('inf')

                # Check all tiles around the restroom perimeter
                for dx in range(width):
                    for dy in range(height):
                        rx, ry = restroom.x + dx, restroom.y + dy
                        # Check adjacent tiles (WALK tiles only)
                        for nx_offset, ny_offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = rx + nx_offset, ry + ny_offset
                            if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_WALK:
                                # Try pathfinding to this tile
                                path = astar(self.grid, (guest.grid_x, guest.grid_y), (nx, ny))
                                if path and len(path) < best_dist:
                                    best_dist = len(path)
                                    best_target = (nx, ny)
                                    best_path = path[1:]  # Exclude current position

                if best_path and best_dist < shortest_distance:
                    shortest_distance = best_dist
                    nearest_restroom = restroom
                    nearest_path = best_path

        if nearest_restroom:
            return nearest_restroom, nearest_path
        return None, None

    def _draw_entrance_fee_panel(self):
        """Draw entrance fee configuration panel"""
        if not self.entrance_fee_panel_open:
            return

        # Panel dimensions and position (centered on screen)
        panel_width = 400
        panel_height = 300
        panel_x = (self.screen.get_width() - panel_width) // 2
        panel_y = (self.screen.get_height() - panel_height) // 2

        # Semi-transparent background overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect)
        pygame.draw.rect(self.screen, (100, 150, 200), panel_rect, 3)

        # Title
        title_text = "Configuration du Prix d'Entrée"
        title_surf = self.font.render(title_text, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
        self.screen.blit(title_surf, title_rect)

        # Current fee display
        current_fee = self.economy.park_entrance_fee
        fee_text = f"Prix actuel: ${current_fee}"
        fee_surf = self.font.render(fee_text, True, (200, 255, 200))
        self.screen.blit(fee_surf, (panel_x + 20, panel_y + 70))

        # Spawn rate display
        spawn_rate_text = f"Affluence: 1 visiteur / {self.guest_spawn_rate:.1f}s"
        spawn_surf = self.font.render(spawn_rate_text, True, (200, 200, 255))
        self.screen.blit(spawn_surf, (panel_x + 20, panel_y + 95))

        # Entrance revenue display
        revenue_text = f"Revenus entrée: ${self.economy.entrance_revenue}"
        revenue_surf = self.font.render(revenue_text, True, (255, 255, 150))
        self.screen.blit(revenue_surf, (panel_x + 20, panel_y + 120))

        # Guests refused display
        refused_text = f"Visiteurs refusés: {self.economy.guests_refused}"
        refused_surf = self.font.render(refused_text, True, (255, 150, 150))
        self.screen.blit(refused_surf, (panel_x + 20, panel_y + 145))

        # Slider for entrance fee ($5 - $300)
        slider_x = panel_x + 20
        slider_y = panel_y + 190
        slider_width = panel_width - 40
        slider_height = 20

        # Slider background
        slider_bg_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (80, 80, 90), slider_bg_rect)
        pygame.draw.rect(self.screen, (150, 150, 160), slider_bg_rect, 2)

        # Slider handle position (based on current fee: $5-$300)
        min_fee = 5
        max_fee = 300
        fee_ratio = (current_fee - min_fee) / (max_fee - min_fee)
        handle_x = slider_x + int(fee_ratio * slider_width)
        handle_rect = pygame.Rect(handle_x - 8, slider_y - 4, 16, slider_height + 8)
        pygame.draw.rect(self.screen, (100, 200, 255), handle_rect)
        pygame.draw.rect(self.screen, (150, 220, 255), handle_rect, 2)

        # Slider labels
        min_label = self.font.render("$5", True, (200, 200, 200))
        max_label = self.font.render("$300", True, (200, 200, 200))
        self.screen.blit(min_label, (slider_x, slider_y + slider_height + 5))
        max_label_rect = max_label.get_rect()
        max_label_rect.right = slider_x + slider_width
        max_label_rect.top = slider_y + slider_height + 5
        self.screen.blit(max_label, max_label_rect)

        # Store slider rect for mouse interaction
        self.entrance_fee_slider_rect = slider_bg_rect
        self.entrance_fee_slider_min = min_fee
        self.entrance_fee_slider_max = max_fee

        # Close button
        close_button_rect = pygame.Rect(panel_x + panel_width - 80, panel_y + panel_height - 50, 60, 30)
        pygame.draw.rect(self.screen, (80, 80, 100), close_button_rect)
        pygame.draw.rect(self.screen, (150, 150, 180), close_button_rect, 2)
        close_text = self.font.render("Fermer", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_button_rect.center)
        self.screen.blit(close_text, close_text_rect)
        self.entrance_fee_close_button_rect = close_button_rect

    def draw(self, hover=None):
        self.screen.fill((20,60,90))
        # Supprimer l'ancienne barre en haut
        # pygame.draw.rect(self.screen,(30,30,30),(0,0,self.screen.get_width(),48))
        self.renderer.draw_map(self.grid)
        
        # Dessiner les flèches de queue si activées
        if self.debug_menu.show_queue_arrows:
            queue_paths = self.queue_manager.find_queue_paths(self.grid)
            self.renderer.draw_queue_arrows(queue_paths, True)
        
        # Dessiner les points cardinaux et la légende des directions
        self.renderer.draw_cardinal_points()
        self.renderer.draw_direction_legend()
        
        objs=[]
        for r in self.rides:
            # Centrer le sprite du ride sur son empreinte (comme pour les shops)
            width, height = r.defn.size
            center_x = r.x + width / 2 - 0.5
            center_y = r.y + height / 2 - 0.5
            objs.append((self.sprite(r.defn.sprite),(center_x,center_y)))
            # Indicateur visuel si l'attraction est en panne
            if r.is_broken:
                # Dessiner un indicateur rouge pour montrer que l'attraction est en panne
                indicator_x = center_x + width / 2 - 0.5
                indicator_y = center_y - height / 2 + 0.5
                # Utiliser un sprite rouge pour l'indicateur de panne
                broken_sprite = self.sprite('ride_broken')
                broken_sprite = pygame.transform.scale(broken_sprite, (16, 16))
                objs.append((broken_sprite,(indicator_x,indicator_y)))
        for s in self.shops: 
            # Centrer le sprite du shop sur son empreinte
            width, height = s.defn.size
            center_x = s.x + width / 2 - 0.5
            center_y = s.y + height / 2 - 0.5
            objs.append((self.sprite(s.defn.sprite),(center_x,center_y)))
            
            # Dessiner l'entrée du shop si elle existe
            if s.entrance:
                objs.append((self.sprite('shop_entrance'),(s.entrance.x,s.entrance.y)))
            
            # Indicateur visuel si le shop n'est pas connecté à un chemin
            if s.entrance and not s.connected_to_path:
                # Dessiner un indicateur rouge pour montrer que le shop n'est pas accessible
                indicator_x = center_x + width / 2 - 0.5
                indicator_y = center_y - height / 2 + 0.5
                # Utiliser un sprite plus grand pour l'indicateur
                disconnected_sprite = self.sprite('shop_disconnected')
                # Redimensionner pour le rendre plus visible
                disconnected_sprite = pygame.transform.scale(disconnected_sprite, (16, 16))
                objs.append((disconnected_sprite,(indicator_x,indicator_y)))

        # Render restrooms
        for r in self.restrooms:
            # Centrer le sprite du restroom sur son empreinte
            width, height = r.defn.size
            center_x = r.x + width / 2 - 0.5
            center_y = r.y + height / 2 - 0.5
            objs.append((self.sprite(r.defn.sprite),(center_x,center_y)))

            # Indicateur visuel si le restroom n'est pas connecté à un chemin
            if not r.connected_to_path:
                # Dessiner un indicateur rouge pour montrer que le restroom n'est pas accessible
                indicator_x = center_x + width / 2 - 0.5
                indicator_y = center_y - height / 2 + 0.5
                # Utiliser un sprite pour l'indicateur
                disconnected_sprite = self.sprite('shop_disconnected')  # Reuse shop disconnected sprite
                disconnected_sprite = pygame.transform.scale(disconnected_sprite, (16, 16))
                objs.append((disconnected_sprite,(indicator_x,indicator_y)))

        # Render guests with satisfaction indicators
        for g in self.guests:
            objs.append((self.sprite(g.sprite),(g.x,g.y)))  # Utiliser les positions flottantes pour le rendu avec sprite diversifié

            # Add satisfaction indicator above guest
            satisfaction_color = self._get_satisfaction_color(g.satisfaction)
            indicator_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(indicator_surf, satisfaction_color, (5, 5), 4)
            pygame.draw.circle(indicator_surf, (255, 255, 255), (5, 5), 4, 1)  # White border
            indicator_x = g.x + 0.5
            indicator_y = g.y - 0.6
            objs.append((indicator_surf,(indicator_x,indicator_y)))

        for employee in self.employees:
            employee_sprite = self.sprite(employee.defn.sprite)
            # Use render position for smooth movement (MaintenanceWorker has interpolation)
            from .employees import MaintenanceWorker
            if isinstance(employee, MaintenanceWorker):
                render_pos = employee.get_render_position()
                objs.append((employee_sprite, render_pos))
                # Use render position for indicator too
                indicator_x = render_pos[0] + 0.5
                indicator_y = render_pos[1] - 0.5
            else:
                objs.append((employee_sprite,(employee.x,employee.y)))
                # Indicateur visuel si l'employé travaille ou se déplace
                indicator_x = employee.x + 0.5
                indicator_y = employee.y - 0.5

            if employee.state == "working":
                # Dessiner un indicateur vert pour montrer que l'employé travaille
                working_sprite = self.sprite('employee_working')
                working_sprite = pygame.transform.scale(working_sprite, (12, 12))
                objs.append((working_sprite,(indicator_x,indicator_y)))
            elif employee.state == "moving_to_ride":
                # Dessiner un indicateur bleu pour montrer que l'ingénieur se déplace
                moving_sprite = self.sprite('employee_moving')
                moving_sprite = pygame.transform.scale(moving_sprite, (12, 12))
                objs.append((moving_sprite,(indicator_x,indicator_y)))
            elif employee.state == "moving_to_litter":
                # Indicateur orange pour déplacement vers détritus
                litter_moving_sprite = self.sprite('employee_moving')  # Utilise le même sprite mais on peut le colorer
                litter_moving_sprite = pygame.transform.scale(litter_moving_sprite, (12, 12))
                # Teinter en orange
                litter_moving_sprite = litter_moving_sprite.copy()
                litter_moving_sprite.fill((255, 165, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((litter_moving_sprite,(indicator_x,indicator_y)))
            elif employee.state == "cleaning":
                # Indicateur vert vif pour nettoyage
                cleaning_sprite = self.sprite('employee_working')
                cleaning_sprite = pygame.transform.scale(cleaning_sprite, (12, 12))
                # Teinter en vert vif
                cleaning_sprite = cleaning_sprite.copy()
                cleaning_sprite.fill((0, 255, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((cleaning_sprite,(indicator_x,indicator_y)))
            elif employee.state == "moving_to_garden":
                # Indicateur bleu-vert pour déplacement vers jardin
                garden_moving_sprite = self.sprite('employee_moving')
                garden_moving_sprite = pygame.transform.scale(garden_moving_sprite, (12, 12))
                # Teinter en cyan
                garden_moving_sprite = garden_moving_sprite.copy()
                garden_moving_sprite.fill((0, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((garden_moving_sprite,(indicator_x,indicator_y)))
            elif employee.state == "gardening":
                # Indicateur vert nature pour jardinage
                gardening_sprite = self.sprite('employee_working')
                gardening_sprite = pygame.transform.scale(gardening_sprite, (12, 12))
                # Teinter en vert nature
                gardening_sprite = gardening_sprite.copy()
                gardening_sprite.fill((34, 139, 34, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((gardening_sprite,(indicator_x,indicator_y)))
            elif employee.state == "mowing":
                # Indicateur vert clair pour tonte de pelouse
                mowing_sprite = self.sprite('employee_working')
                mowing_sprite = pygame.transform.scale(mowing_sprite, (12, 12))
                # Teinter en vert clair (lawn green)
                mowing_sprite = mowing_sprite.copy()
                mowing_sprite.fill((124, 252, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((mowing_sprite,(indicator_x,indicator_y)))
            elif employee.state == "patrolling":
                # Indicateur jaune pour patrouille (maintenance workers)
                patrol_sprite = self.sprite('employee_moving')
                patrol_sprite = pygame.transform.scale(patrol_sprite, (12, 12))
                # Teinter en jaune
                patrol_sprite = patrol_sprite.copy()
                patrol_sprite.fill((255, 255, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                objs.append((patrol_sprite,(indicator_x,indicator_y)))

            # Security Guard specific indicators
            from .employees import SecurityGuard, Mascot
            if isinstance(employee, SecurityGuard):
                if employee.state == "patrolling":
                    # Indicateur bleu pour patrouille de sécurité
                    security_sprite = self.sprite('employee_working')
                    security_sprite = pygame.transform.scale(security_sprite, (12, 12))
                    # Teinter en bleu
                    security_sprite = security_sprite.copy()
                    security_sprite.fill((0, 100, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    objs.append((security_sprite,(indicator_x,indicator_y)))

            # Mascot specific indicators
            if isinstance(employee, Mascot):
                if employee.state == "moving_to_crowd":
                    # Indicateur magenta pour déplacement vers foule
                    mascot_moving_sprite = self.sprite('employee_moving')
                    mascot_moving_sprite = pygame.transform.scale(mascot_moving_sprite, (12, 12))
                    # Teinter en magenta
                    mascot_moving_sprite = mascot_moving_sprite.copy()
                    mascot_moving_sprite.fill((255, 0, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    objs.append((mascot_moving_sprite,(indicator_x,indicator_y)))
                elif employee.state == "entertaining":
                    # Indicateur étoile dorée pour animation
                    mascot_entertain_sprite = self.sprite('employee_working')
                    mascot_entertain_sprite = pygame.transform.scale(mascot_entertain_sprite, (12, 12))
                    # Teinter en or/jaune vif
                    mascot_entertain_sprite = mascot_entertain_sprite.copy()
                    mascot_entertain_sprite.fill((255, 215, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    objs.append((mascot_entertain_sprite,(indicator_x,indicator_y)))
        
        # Render litter and bins
        # Render bins first (so they appear behind visitors)
        for bin_obj in self.litter_manager.bins:
            bin_sprite = self.sprite(bin_obj.defn.sprite)
            objs.append((bin_sprite,(bin_obj.x, bin_obj.y)))
        
        # Render litter (smaller, visible sprites with random positions and colors)
        for litter in self.litter_manager.litters:
            # Create a small litter sprite with type-specific colors
            litter_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            color, dark_color = litter.get_colors()
            litter_surf.fill(color)  # Base color
            pygame.draw.circle(litter_surf, dark_color, (6, 6), 5)  # Darker center
            # Use the random offset stored in the litter object
            objs.append((litter_surf,(litter.x + litter.offset_x, litter.y + litter.offset_y)))
        
        self.renderer.draw_objects(objs)
        if hover and self.grid.in_bounds(*hover):
            ok=True
            if self.toolbar.active.startswith('shop_'):
                sd = self.shop_defs.get(self.toolbar.active)
                if sd:
                    # Calculate top-left position for centered placement
                    place_x, place_y = self._get_placement_position(hover[0], hover[1], sd.size[0], sd.size[1])
                    ok = self._can_place_shop(sd, place_x, place_y)
                    # Draw shop preview at centered position
                    self.renderer.draw_ride_preview(place_x, place_y, sd.size[0], sd.size[1], ok=ok)
            elif self.toolbar.active.startswith('restroom_'):
                rd = self.restroom_defs.get(self.toolbar.active)
                if rd:
                    # Calculate top-left position for centered placement
                    place_x, place_y = self._get_placement_position(hover[0], hover[1], rd.size[0], rd.size[1])
                    ok = self._can_place_restroom(rd, place_x, place_y) and self._is_restroom_adjacent_to_path(rd, place_x, place_y)
                    # Draw restroom preview at centered position
                    self.renderer.draw_ride_preview(place_x, place_y, rd.size[0], rd.size[1], ok=ok)
            elif self.toolbar.active.startswith('ride_'):
                rd = self.ride_defs.get(self.toolbar.active)
                if rd:
                    # Calculate top-left position for centered placement
                    place_x, place_y = self._get_placement_position(hover[0], hover[1], rd.size[0], rd.size[1])
                    ok = self._can_place_ride(rd, place_x, place_y)
                    # Draw ride preview at centered position
                    self.renderer.draw_ride_preview(place_x, place_y, rd.size[0], rd.size[1], ok=ok)
            elif self.ride_placement_mode == 'entrance' and self.selected_ride:
                ok = self.selected_ride.can_place_entrance(*hover)
            elif self.ride_placement_mode == 'exit' and self.selected_ride:
                ok = self.selected_ride.can_place_exit(*hover)
            elif self.toolbar.active == 'walk_path':
                ok = not self._is_on_ride(*hover)
            elif self.toolbar.active == 'queue_path':
                ok = not self._is_on_ride(*hover) and (self.last_queue_pos is None or self._can_connect_queue_tile(*hover))
            elif self.toolbar.active.startswith('bin_'):
                # Check if bin can be placed here (GRASS adjacent to WALK)
                if self.grid.get(*hover) == TILE_GRASS:
                    adjacent_to_walk = False
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = hover[0] + dx, hover[1] + dy
                        if self.grid.in_bounds(nx, ny) and self.grid.get(nx, ny) == TILE_WALK:
                            adjacent_to_walk = True
                            break
                    ok = adjacent_to_walk and not self.litter_manager.get_bin_at(*hover)
                else:
                    ok = False
            
            # Only draw single-tile highlight if not drawing multi-tile preview
            if not ((self.toolbar.active.startswith('ride_') and self.ride_defs.get(self.toolbar.active)) or
                    (self.toolbar.active.startswith('shop_') and self.shop_defs.get(self.toolbar.active)) or
                    (self.toolbar.active.startswith('restroom_') and self.restroom_defs.get(self.toolbar.active))):
                self.renderer.draw_highlight(*hover, ok=ok)
        
        # Draw path preview when dragging
        if self.path_dragging and self.last_path_pos:
            mx, my = pygame.mouse.get_pos()
            # Toolbar maintenant en bas, donc preview partout sauf dans la toolbar
            screen_height = self.screen.get_height()
            toolbar_y = screen_height - 48
            if my < toolbar_y:  # Only show preview above toolbar
                preview_gx, preview_gy = self.renderer.screen_to_grid(mx, my)
                if self.grid.in_bounds(preview_gx, preview_gy) and (preview_gx, preview_gy) != self.last_path_pos and not self._is_on_ride(preview_gx, preview_gy):
                    # Show a semi-transparent preview of where the path will be placed
                    if self.toolbar.active == 'walk_path':
                        self.renderer.draw_highlight(preview_gx, preview_gy, ok=True, preview=True)
                    elif self.toolbar.active == 'queue_path':
                        can_connect = self.last_queue_pos is None or self._can_connect_queue_tile(preview_gx, preview_gy)
                        self.renderer.draw_highlight(preview_gx, preview_gy, ok=can_connect, preview=True)
        mode_text = ""
        if self.ride_placement_mode == 'entrance':
            mode_text = " | Place Entrance"
        elif self.ride_placement_mode == 'exit':
            mode_text = " | Place Exit"
        
        # Calculate park stats
        num_guests = len(self.guests)
        avg_happiness = sum(g.happiness for g in self.guests) / num_guests if num_guests > 0 else 0.0
        avg_satisfaction = sum(g.satisfaction for g in self.guests) / num_guests if num_guests > 0 else 0.0
        avg_excitement = sum(g.excitement for g in self.guests) / num_guests if num_guests > 0 else 0.0

        # Count employees by type
        from .employees import Engineer, MaintenanceWorker, SecurityGuard, Mascot
        num_engineers = len([e for e in self.employees if isinstance(e, Engineer)])
        num_maintenance = len([e for e in self.employees if isinstance(e, MaintenanceWorker)])
        num_security = len([e for e in self.employees if isinstance(e, SecurityGuard)])
        num_mascots = len([e for e in self.employees if isinstance(e, Mascot)])

        # Count litter
        num_litter = len(self.litter_manager.litters)
        num_bins = len(self.litter_manager.bins)

        # Compter les files d'attente connectées
        queue_paths = self.queue_manager.find_queue_paths(self.grid)
        connected_queues = sum(1 for qp in queue_paths if qp.connected_ride)
        total_queues = len(queue_paths)

        # Draw stats panel (top-left corner)
        stats_bg = pygame.Surface((550, 230), pygame.SRCALPHA)
        stats_bg.fill((20, 20, 20, 200))  # Semi-transparent dark background
        self.screen.blit(stats_bg, (8, 8))

        # Main HUD line
        hud=f"Cash: ${self.economy.cash}  |  Guests: {num_guests} (In: {self.guests_entered} | Out: {self.guests_left})  |  Rides: {len(self.rides)}  |  Shops: {len(self.shops)}{mode_text}"
        self.screen.blit(self.font.render(hud,True,(255,255,255)),(12,12))

        # Time and park status line
        y_offset = 32
        park_status_text = "OPEN" if self.park_open else "CLOSED"
        park_status_color = (100, 255, 100) if self.park_open else (255, 100, 100)
        speed_text = "PAUSED" if self.game_speed == 0 else f"x{int(self.game_speed)}"
        speed_color = (255, 150, 0) if self.game_speed == 0 else (150, 255, 150)
        time_text = f"Day {self.game_day}  {self.game_hour:02d}:{self.game_minute:02d}"

        self.screen.blit(self.font.render(f"Park:", True, (200,200,200)), (12, y_offset))
        self.screen.blit(self.font.render(park_status_text, True, park_status_color), (60, y_offset))
        self.screen.blit(self.font.render(f"|  Time:", True, (200,200,200)), (140, y_offset))
        self.screen.blit(self.font.render(time_text, True, (200,220,255)), (200, y_offset))
        self.screen.blit(self.font.render(f"|  Speed:", True, (200,200,200)), (320, y_offset))
        self.screen.blit(self.font.render(speed_text, True, speed_color), (390, y_offset))

        # Guest satisfaction line with color coding
        y_offset += 20
        happiness_color = self._get_satisfaction_color(avg_happiness)
        satisfaction_color = self._get_satisfaction_color(avg_satisfaction)
        excitement_color = self._get_satisfaction_color(avg_excitement)
        self.screen.blit(self.font.render(f"Happiness:", True, (200,200,200)), (12, y_offset))
        self.screen.blit(self.font.render(f"{avg_happiness*100:.0f}%", True, happiness_color), (110, y_offset))

        self.screen.blit(self.font.render(f"Satisfaction:", True, (200,200,200)), (170, y_offset))
        self.screen.blit(self.font.render(f"{avg_satisfaction*100:.0f}%", True, satisfaction_color), (270, y_offset))

        # Guest needs line
        y_offset += 20
        avg_hunger = sum(g.hunger for g in self.guests) / num_guests if num_guests > 0 else 1.0
        avg_thirst = sum(g.thirst for g in self.guests) / num_guests if num_guests > 0 else 1.0
        avg_bladder = sum(g.bladder for g in self.guests) / num_guests if num_guests > 0 else 0.0
        hunger_color = (255, 100, 100) if avg_hunger < 0.3 else (255, 255, 100) if avg_hunger < 0.6 else (100, 255, 100)
        thirst_color = (255, 100, 100) if avg_thirst < 0.3 else (255, 255, 100) if avg_thirst < 0.6 else (100, 255, 100)
        bladder_color = (255, 100, 100) if avg_bladder > 0.7 else (255, 255, 100) if avg_bladder > 0.5 else (100, 255, 100)

        # Count facilities
        num_food_shops = len([s for s in self.shops if s.defn.shop_type == "food"])
        num_drink_shops = len([s for s in self.shops if s.defn.shop_type == "drink"])
        num_restrooms = len(self.restrooms)

        self.screen.blit(self.font.render(f"Hunger:", True, (200,200,200)), (12, y_offset))
        self.screen.blit(self.font.render(f"{avg_hunger*100:.0f}%", True, hunger_color), (75, y_offset))
        self.screen.blit(self.font.render(f"Thirst:", True, (200,200,200)), (130, y_offset))
        self.screen.blit(self.font.render(f"{avg_thirst*100:.0f}%", True, thirst_color), (185, y_offset))
        self.screen.blit(self.font.render(f"Bladder:", True, (200,200,200)), (240, y_offset))
        self.screen.blit(self.font.render(f"{avg_bladder*100:.0f}%", True, bladder_color), (310, y_offset))
        self.screen.blit(self.font.render(f"|  Facilities: {num_food_shops}F {num_drink_shops}D {num_restrooms}R", True, (180,220,255)), (370, y_offset))

        # Entrance fee and revenue line
        y_offset += 20
        entrance_fee_text = f"Entrance Fee: ${self.economy.park_entrance_fee}  |  Revenue: ${self.economy.entrance_revenue}  |  Refused: {self.economy.guests_refused}"
        self.screen.blit(self.font.render(entrance_fee_text, True, (200,255,200)), (12, y_offset))

        # Employees line
        y_offset += 20
        employees_text = f"Employees: {num_engineers}E {num_maintenance}M {num_security}S {num_mascots}Mc"
        self.screen.blit(self.font.render(employees_text, True, (180,220,255)), (12, y_offset))

        # Litter and bins line
        y_offset += 20
        litter_color = (255, 100, 100) if num_litter > 10 else (150, 255, 150) if num_litter < 5 else (255, 255, 150)
        litter_text = f"Litter: {num_litter}  |  Bins: {num_bins}  |  Queues: {connected_queues}/{total_queues}"
        self.screen.blit(self.font.render(litter_text, True, litter_color), (12, y_offset))

        # Technical info line (smaller)
        y_offset += 20
        tech_info = f"Zoom: {self.renderer.camera.zoom:.2f}  Tile: {int(self.renderer.base_tile_w)}x{int(self.renderer.base_tile_h)}  φ: {self.debug_menu.oblique_tilt:.1f}°"
        self.screen.blit(self.font.render(tech_info, True, (150,150,150)), (12, y_offset))

        # Save/Load controls line
        y_offset += 20
        save_controls = "F5: Quick Save  |  F9: Quick Load"
        self.screen.blit(self.font.render(save_controls, True, (200,200,255)), (12, y_offset))

        # Dessiner la toolbar et ses sous-menus au premier plan (en dernier)
        self.toolbar.draw(self.screen)
        self.debug_menu.draw(self.screen)

        # Draw entrance fee panel (modal, on top of everything)
        self._draw_entrance_fee_panel()

        pygame.display.flip()

    def _get_employee_at_position(self, x, y):
        """Get employee at position"""
        for employee in self.employees:
            if employee.x == x and employee.y == y:
                return employee
        return None

    def _assign_engineers_to_broken_rides(self):
        """Assign available engineers to broken rides"""
        # Find broken rides that need repair
        broken_rides = [ride for ride in self.rides if ride.is_broken and not ride.being_repaired]
        
        # Find idle engineers
        idle_engineers = [emp for emp in self.employees if emp.defn.type == 'engineer' and emp.state == 'idle']
        
        # Debug logging
        if DebugConfig.EMPLOYEES:
            DebugConfig.log('engine', f"Found {len(broken_rides)} broken rides, {len(idle_engineers)} idle engineers")
            DebugConfig.log('engine', f"Total employees: {len(self.employees)}")
            if self.employees:
                DebugConfig.log('engine', f"Employee types: {[emp.defn.type for emp in self.employees]}")
                DebugConfig.log('engine', f"Employee states: {[emp.state for emp in self.employees]}")
        
        # Assign engineers to broken rides
        for i, ride in enumerate(broken_rides):
            if i < len(idle_engineers):
                engineer = idle_engineers[i]
                engineer.start_repair(ride, self.grid)
                DebugConfig.log('engine', f"Assigned engineer {engineer.id} to repair {ride.defn.name}")

    def _assign_maintenance_workers_to_litter(self):
        """Assign available maintenance workers to clean litter or patrol/garden"""
        from .employees import MaintenanceWorker

        # Find idle maintenance workers on paths
        idle_path_workers = [emp for emp in self.employees
                           if isinstance(emp, MaintenanceWorker)
                           and emp.state == 'idle'
                           and emp.placement_type == 'path']

        # For each idle path worker, find nearest litter or start patrol
        for worker in idle_path_workers:
            # Check if patrol timer expired first
            should_patrol = worker.patrol_timer >= worker.patrol_duration

            nearest_litter = worker.find_nearest_litter(self.litter_manager, self.grid)
            if nearest_litter:
                # Check if no other worker is already targeting this litter
                already_targeted = any(
                    isinstance(emp, MaintenanceWorker)
                    and emp.target_litter == nearest_litter
                    and emp.state in ['moving_to_litter', 'cleaning']
                    for emp in self.employees
                )

                if not already_targeted:
                    success = worker.start_cleaning(nearest_litter, self.grid)
                    if success:
                        DebugConfig.log('engine', f"Assigned maintenance worker {worker.id} to clean litter at ({nearest_litter.x}, {nearest_litter.y})")
                    else:
                        DebugConfig.log('engine', f"Maintenance worker {worker.id} failed to start cleaning, will try patrol")
                elif should_patrol:
                    # Litter already targeted by someone else, start patrol instead
                    success = worker.start_patrol(self.grid)
                    if success:
                        DebugConfig.log('engine', f"Maintenance worker {worker.id} started patrol (no available litter)")
                    else:
                        # Patrol failed, reset timer to retry
                        DebugConfig.log('engine', f"Maintenance worker {worker.id} patrol failed (litter targeted), will retry")
                        worker.patrol_timer = 0.0
            elif should_patrol:
                # No litter found and timer expired, start patrol
                success = worker.start_patrol(self.grid)
                if success:
                    DebugConfig.log('engine', f"Maintenance worker {worker.id} started patrol (no litter found)")
                else:
                    # Patrol failed, reset timer to 0 to retry immediately
                    DebugConfig.log('engine', f"Maintenance worker {worker.id} patrol failed, will retry")
                    worker.patrol_timer = 0.0  # Reset to 0, not negative!

        # Handle cleaning completion - remove litter
        for worker in [emp for emp in self.employees if isinstance(emp, MaintenanceWorker)]:
            if worker.state == 'cleaning' and worker.target_litter:
                # Check if cleaning just started (timer near 0)
                # Remove litter when cleaning completes
                if worker.cleaning_timer >= worker.cleaning_duration - 0.05:  # Just before completion
                    if worker.target_litter in self.litter_manager.litters:
                        self.litter_manager.remove_litter(worker.target_litter)
                        DebugConfig.log('engine', f"Maintenance worker {worker.id} removed litter at ({worker.target_litter.x}, {worker.target_litter.y})")

    def _assign_maintenance_workers_to_gardening(self):
        """Assign available grass maintenance workers to gardening tasks"""
        from .employees import MaintenanceWorker
        import random

        # Find idle maintenance workers on grass
        idle_grass_workers = [emp for emp in self.employees
                             if isinstance(emp, MaintenanceWorker)
                             and emp.state == 'idle'
                             and emp.placement_type == 'grass']

        # For each idle grass worker, start continuous mowing
        for worker in idle_grass_workers:
            # Check if patrol timer expired
            if worker.patrol_timer >= worker.patrol_duration:
                # Start continuous lawn mowing (worker will move tile by tile)
                worker.start_mowing(self.grid)
                DebugConfig.log('engine', f"Assigned maintenance worker {worker.id} to start continuous lawn mowing - pattern: {worker.lawn_mowing_pattern}")

        # Update mowing workers - move them to next tile when ready
        mowing_workers = [emp for emp in self.employees
                         if isinstance(emp, MaintenanceWorker)
                         and emp.state == 'mowing']

        DebugConfig.log('engine', f"Found {len(mowing_workers)} workers in mowing state")

        for worker in mowing_workers:
            DebugConfig.log('engine', f"Worker {worker.id} gardening_timer: {worker.gardening_timer:.3f}, mowing_speed: {worker.mowing_speed:.3f}")

            # Check if worker finished mowing current tile
            if worker.gardening_timer >= worker.mowing_speed:
                DebugConfig.log('engine', f"Worker {worker.id} timer expired, getting next position")

                # Get next position in mowing pattern
                next_pos = worker._get_next_mowing_position(self.grid)

                if next_pos:
                    # Move worker to next position instantly (simulate mowing)
                    DebugConfig.log('engine', f"Worker {worker.id} moving from ({int(worker.x)}, {int(worker.y)}) to ({next_pos[0]}, {next_pos[1]})")
                    worker.x = float(next_pos[0])
                    worker.y = float(next_pos[1])
                    worker.gardening_timer = 0.0
                    DebugConfig.log('engine', f"Maintenance worker {worker.id} moved to next mowing position ({next_pos[0]}, {next_pos[1]})")
                else:
                    # No more grass to mow, go back to idle
                    DebugConfig.log('engine', f"Worker {worker.id} no next position found, going idle")
                    worker.state = "idle"
                    worker.patrol_timer = worker.patrol_duration  # Trigger immediate restart
                    DebugConfig.log('engine', f"Maintenance worker {worker.id} finished mowing pattern, restarting")

    def _assign_security_guards_to_patrol(self):
        """Assign idle security guards to patrol and update nearby guests"""
        from .employees import SecurityGuard

        # Find idle security guards
        idle_guards = [emp for emp in self.employees
                      if isinstance(emp, SecurityGuard)
                      and emp.state == 'idle']

        # Start patrol for idle guards
        for guard in idle_guards:
            if guard.patrol_timer >= guard.patrol_duration:
                success = guard.start_patrol(self.grid)
                if success:
                    DebugConfig.log('engine', f"Security guard {guard.id} started patrol")
                else:
                    # Failed to find patrol path, retry soon (set to small value, not negative)
                    guard.patrol_timer = 0.0  # Reset to 0 to retry immediately next frame

        # Update all security guards' nearby guest detection
        for guard in [emp for emp in self.employees if isinstance(emp, SecurityGuard)]:
            nearby_count = guard.update_nearby_guests(self.guests)
            if nearby_count > 0:
                DebugConfig.log('engine', f"Security guard {guard.id} protecting {nearby_count} guests")

    def _assign_mascots_to_crowds(self):
        """Assign idle mascots to find and entertain crowds"""
        from .employees import Mascot

        # Find idle mascots
        idle_mascots = [emp for emp in self.employees
                       if isinstance(emp, Mascot)
                       and emp.state == 'idle']

        # Find crowds for idle mascots
        for mascot in idle_mascots:
            if mascot.search_timer >= mascot.search_duration:
                # Find best crowd location (prioritize queues 70% of time)
                crowd_location = mascot.find_best_crowd_location(self.guests, self.queue_manager)

                if crowd_location:
                    success = mascot.start_moving_to_crowd(crowd_location, self.grid)
                    if success:
                        DebugConfig.log('engine', f"Mascot {mascot.id} moving to crowd at {crowd_location}")
                        mascot.search_timer = 0.0  # Reset timer on success
                    else:
                        # Failed to find path, reset timer to retry (don't go negative!)
                        mascot.search_timer = 0.0  # Reset to 0 to retry immediately next frame
                else:
                    # No crowd found, reset timer to retry (don't go negative!)
                    DebugConfig.log('engine', f"Mascot {mascot.id} found no crowd, will retry")
                    mascot.search_timer = 0.0  # Reset to 0 to retry immediately next frame

        # Update all mascots' nearby guest detection
        for mascot in [emp for emp in self.employees if isinstance(emp, Mascot)]:
            nearby_count = mascot.update_nearby_guests(self.guests)
            if nearby_count > 0 and mascot.state == "entertaining":
                DebugConfig.log('engine', f"Mascot {mascot.id} entertaining {nearby_count} guests")

    def _apply_employee_effects_on_guests(self):
        """Apply effects from SecurityGuards and Mascots to nearby guests"""
        from .employees import SecurityGuard, Mascot

        # Apply SecurityGuard effects (+5% satisfaction for guests in security radius)
        for guard in [emp for emp in self.employees if isinstance(emp, SecurityGuard)]:
            if guard.state == "patrolling" and guard.nearby_guests:
                for guest in guard.nearby_guests:
                    # Apply satisfaction boost (capped at 1.0)
                    guest.satisfaction = min(1.0, guest.satisfaction + 0.05)
                DebugConfig.log('engine', f"Security guard {guard.id} boosted satisfaction for {len(guard.nearby_guests)} guests")

        # Apply Mascot effects (+10% excitement for guests in entertainment radius)
        for mascot in [emp for emp in self.employees if isinstance(emp, Mascot)]:
            if mascot.state == "entertaining" and mascot.nearby_guests:
                for guest in mascot.nearby_guests:
                    # Apply excitement boost (capped at 1.0)
                    guest.excitement = min(1.0, guest.excitement + 0.10)
                    # Also small happiness boost (+3%)
                    guest.happiness = min(1.0, guest.happiness + 0.03)
                DebugConfig.log('engine', f"Mascot {mascot.id} boosted excitement for {len(mascot.nearby_guests)} guests")

    def _apply_litter_proximity_penalties(self):
        """Apply satisfaction penalties to guests near litter"""
        for guest in self.guests:
            # Count litter within 3 tiles radius
            litter_count = 0
            for litter in self.litter_manager.litters:
                distance = abs(guest.grid_x - litter.x) + abs(guest.grid_y - litter.y)
                if distance <= 3:
                    litter_count += 1

            # Apply penalty based on nearby litter (-2% per litter item)
            if litter_count > 0:
                penalty = -0.02 * litter_count
                guest.modify_satisfaction(penalty, f"nearby litter ({litter_count} items)")

    def _apply_park_cleanliness_bonus(self):
        """Apply satisfaction bonus based on overall park cleanliness"""
        total_litter = len(self.litter_manager.litters)

        # Calculate cleanliness rating (fewer litter = cleaner park)
        # Very clean park (< 5 litter): +2% satisfaction per tick
        if total_litter < 5:
            for guest in self.guests:
                guest.modify_satisfaction(0.02, "very clean park")

    def _get_satisfaction_color(self, value):
        """Return color based on satisfaction value (0.0-1.0)"""
        if value >= 0.7:
            return (100, 255, 100)  # Green - high satisfaction
        elif value >= 0.4:
            return (255, 255, 100)  # Yellow - medium satisfaction
        else:
            return (255, 100, 100)  # Red - low satisfaction

    def _handle_broken_rides(self):
        """Handle broken rides - evacuate queues and prevent new visitors"""
        for ride in self.rides:
            if ride.is_broken and not hasattr(ride, '_queue_evacuated'):
                # Evacuate queue for this broken ride (only once)
                self.queue_manager.evacuate_queue_for_broken_ride(ride)
                ride._queue_evacuated = True
                
                # Prevent new visitors from targeting this ride and apply penalty
                for guest in self.guests:
                    if guest.target_ride == ride:
                        guest.target_ride = None
                        guest.target_queue = None
                        guest.state = "wandering"
                        guest.apply_broken_ride_penalty()  # Apply satisfaction penalty
                        DebugConfig.log('engine', f"Guest {guest.id} redirected from broken ride {ride.defn.name}")
            
            # Reset evacuation flag when ride is repaired
            if not ride.is_broken and hasattr(ride, '_queue_evacuated'):
                delattr(ride, '_queue_evacuated')
    
    def _handle_guest_litter(self, guest):
        """Handle guest with litter - try to find bin or drop it"""
        import random
        # Calculate search radius based on guest's state
        search_radius = guest.get_bin_search_radius()
        
        # Try to find a bin
        nearest_bin = self.litter_manager.find_nearest_bin(guest.grid_x, guest.grid_y, search_radius)
        
        if nearest_bin:
            # Bin found! Try to go to it
            # Check if bin is on path to target
            # For simplicity, just go to bin (70% chance)
            if random.random() < 0.7:
                # Find path to bin
                from .pathfinding import astar
                bin_pos = (nearest_bin.x, nearest_bin.y)
                guest_pos = (guest.grid_x, guest.grid_y)
                
                path = astar(self.grid, guest_pos, bin_pos)
                if path and len(path) > 1:
                    guest.path = path[1:]  # Skip current position
                    guest.target_bin = nearest_bin
                    guest.state = "walking_to_bin"
                    DebugConfig.log('guests', f"Guest {guest.id} found bin at {bin_pos}, going there")
                else:
                    # Can't reach bin, drop litter
                    if guest.should_drop_litter_randomly():
                        self.litter_manager.add_litter(guest.grid_x, guest.grid_y, guest.litter_type)
                        guest.has_litter = False
                        guest.litter_type = None
                        guest.litter_hold_timer = 0.0
                        guest.litter_hold_duration = 0.0
                        guest.apply_litter_drop_penalty()  # Apply satisfaction penalty
                        DebugConfig.log('guests', f"Guest {guest.id} dropped litter (couldn't reach bin)")
            else:
                # Decided not to go to bin, drop litter
                if guest.should_drop_litter_randomly():
                    self.litter_manager.add_litter(guest.grid_x, guest.grid_y, guest.litter_type)
                    guest.has_litter = False
                    guest.litter_type = None
                    guest.litter_hold_timer = 0.0
                    guest.litter_hold_duration = 0.0
                    guest.apply_litter_drop_penalty()  # Apply satisfaction penalty
                    DebugConfig.log('guests', f"Guest {guest.id} dropped litter (chose not to go to bin)")
        else:
            # No bin found, drop litter
            if guest.should_drop_litter_randomly():
                self.litter_manager.add_litter(guest.grid_x, guest.grid_y, guest.litter_type)
                guest.has_litter = False
                guest.litter_type = None
                guest.litter_hold_timer = 0.0
                guest.litter_hold_duration = 0.0
                guest.apply_litter_drop_penalty()  # Apply satisfaction penalty
                DebugConfig.log('guests', f"Guest {guest.id} dropped litter (no bin found)")

    def save_game(self, save_name: str = None) -> str:
        """
        Save the current game state

        Args:
            save_name: Optional custom save name

        Returns:
            Path to the saved file
        """
        game_state = {
            # Grid state
            'grid': serialize_grid(self.grid),

            # Game entities
            'rides': [serialize_ride(ride) for ride in self.rides],
            'shops': [serialize_shop(shop) for shop in self.shops],
            'employees': [serialize_employee(emp) for emp in self.employees],
            'guests': [serialize_guest(guest) for guest in self.guests],
            'restrooms': [serialize_restroom(restroom) for restroom in self.restrooms],

            # Litter system
            'bins': [serialize_bin(bin_obj) for bin_obj in self.litter_manager.bins],
            'litter': [serialize_litter(litter) for litter in self.litter_manager.litters],

            # Economy
            'economy': {
                'cash': self.economy.cash,
                'park_entrance_fee': self.economy.park_entrance_fee,
                'entrance_revenue': self.economy.entrance_revenue,
                'guests_refused': self.economy.guests_refused
            },

            # Time system
            'time': {
                'game_time': self.game_time,
                'game_day': self.game_day,
                'game_hour': self.game_hour,
                'game_minute': self.game_minute,
                'game_speed': self.game_speed,
                'park_open': self.park_open
            },

            # Park settings
            'park_settings': {
                'entrance_position': self.park_entrance,
                'entrance_width': self.entrance_width
            },

            # Statistics
            'statistics': {
                'guests_entered': self.guests_entered,
                'guests_left': self.guests_left
            }
        }

        save_path = self.save_load_manager.save_game(game_state, save_name)
        print(f"Game saved to: {save_path}")
        return save_path

    def load_game(self, save_name: str) -> bool:
        """
        Load a saved game state

        Args:
            save_name: Name of the save file to load

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            game_state = self.save_load_manager.load_game(save_name)

            # Clear current state
            self.rides.clear()
            self.shops.clear()
            self.employees.clear()
            self.guests.clear()
            self.restrooms.clear()
            self.litter_manager.bins.clear()
            self.litter_manager.litters.clear()

            # Restore grid
            grid_data = game_state['grid']
            for x in range(grid_data['width']):
                for y in range(grid_data['height']):
                    self.grid.set(x, y, grid_data['tiles'][x][y])

            # Restore rides
            for ride_data in game_state['rides']:
                rd = self.ride_defs.get(ride_data['id'])
                if rd:
                    ride = Ride(rd, ride_data['x'], ride_data['y'])
                    ride.operational = ride_data.get('operational', True)
                    ride.ride_timer = ride_data.get('ride_timer', 0.0)
                    ride.ride_duration = ride_data.get('ride_duration', 3.0)
                    ride.is_launched = ride_data.get('is_launched', False)
                    ride.waiting_timer = ride_data.get('waiting_timer', 0.0)
                    ride.max_wait_time = ride_data.get('max_wait_time', 5.0)
                    ride.is_broken = ride_data.get('is_broken', False)
                    ride.being_repaired = ride_data.get('being_repaired', False)
                    ride.breakdown_timer = ride_data.get('breakdown_timer', 0.0)
                    # Note: current_visitors and waiting_visitors will be restored after guests are loaded
                    if ride_data['entrance']:
                        ride.entrance = RideEntrance(ride_data['entrance']['x'], ride_data['entrance']['y'])
                    if ride_data['exit']:
                        ride.exit = RideExit(ride_data['exit']['x'], ride_data['exit']['y'])
                    self.rides.append(ride)

            # Restore shops
            for shop_data in game_state['shops']:
                sd = self.shop_defs.get(shop_data['id'])
                if sd:
                    shop = Shop(sd, shop_data['x'], shop_data['y'])
                    if shop_data['entrance']:
                        shop.entrance = ShopEntrance(shop_data['id'], shop_data['entrance']['x'], shop_data['entrance']['y'], 'S')
                    shop.connected_to_path = shop_data['connected_to_path']
                    self.shops.append(shop)

            # Restore employees
            for emp_data in game_state['employees']:
                emp_def = self.employee_defs.get(emp_data['id'])
                if emp_def:
                    if emp_def.type == 'engineer':
                        emp = Engineer(emp_def, emp_data['x'], emp_data['y'])
                        if 'target_x' in emp_data:
                            emp.target_x = emp_data.get('target_x')
                            emp.target_y = emp_data.get('target_y')
                        if 'repair_timer' in emp_data:
                            emp.repair_timer = emp_data.get('repair_timer', 0.0)
                        # Restore target ride reference
                        if 'target_ride_x' in emp_data and 'target_ride_y' in emp_data:
                            target_x = emp_data['target_ride_x']
                            target_y = emp_data['target_ride_y']
                            # Find the ride at this position
                            for ride in self.rides:
                                if ride.x == target_x and ride.y == target_y:
                                    emp.target_object = ride
                                    # If engineer was moving to ride, recalculate path
                                    if emp_data.get('state') == 'moving_to_ride':
                                        from .pathfinding import astar_for_engineers
                                        engineer_pos = (int(emp_data['x']), int(emp_data['y']))
                                        ride_pos = (ride.x, ride.y)
                                        path = astar_for_engineers(self.grid, engineer_pos, ride_pos)
                                        if path:
                                            emp.path = path[1:]  # Exclude starting position
                                    break
                    elif emp_def.type == 'maintenance':
                        emp = MaintenanceWorker(emp_def, emp_data['x'], emp_data['y'])
                        if 'placement_type' in emp_data:
                            emp.placement_type = emp_data['placement_type']
                        if 'target_x' in emp_data:
                            emp.target_x = emp_data.get('target_x')
                            emp.target_y = emp_data.get('target_y')
                    elif emp_def.type == 'security':
                        emp = SecurityGuard(emp_def, emp_data['x'], emp_data['y'])
                    elif emp_def.type == 'mascot':
                        emp = Mascot(emp_def, emp_data['x'], emp_data['y'])
                    else:
                        continue
                    emp.state = emp_data.get('state', 'idle')
                    # Reset transitional states to idle
                    if emp.state == 'moving_to_nearby':
                        emp.state = 'idle'
                    if 'employee_id' in emp_data:
                        emp.id = emp_data['employee_id']
                    self.employees.append(emp)

            # Restore guests
            for guest_data in game_state['guests']:
                guest = Guest(guest_data['x'], guest_data['y'])
                guest.id = guest_data.get('id', guest.id)
                guest.grid_x = guest_data.get('grid_x', int(guest_data['x']))
                guest.grid_y = guest_data.get('grid_y', int(guest_data['y']))
                guest.state = guest_data.get('state', 'wandering')
                guest.satisfaction = guest_data.get('satisfaction', 0.5)
                guest.happiness = guest_data.get('happiness', 0.5)
                guest.excitement = guest_data.get('excitement', 0.5)
                guest.money = guest_data.get('money', 100)
                guest.budget = guest_data.get('budget', guest.money)
                guest.entry_time = guest_data.get('entry_time', 0.0)
                guest.thrill_preference = guest_data.get('thrill_preference', 0.5)
                guest.nausea_tolerance = guest_data.get('nausea_tolerance', 0.5)
                guest.sprite = guest_data.get('sprite', guest.sprite)
                guest.hunger = guest_data.get('hunger', 1.0)
                guest.thirst = guest_data.get('thirst', 1.0)
                guest.bladder = guest_data.get('bladder', 0.0)
                guest.has_litter = guest_data.get('has_litter', False)
                guest.litter_type = guest_data.get('litter_type', None)
                guest.litter_hold_timer = guest_data.get('litter_hold_timer', 0.0)
                guest.litter_hold_duration = guest_data.get('litter_hold_duration', 0.0)
                self.guests.append(guest)

            # Restore restrooms
            for restroom_data in game_state['restrooms']:
                rd = self.restroom_defs.get(restroom_data['id'])
                if rd:
                    restroom = Restroom(rd, restroom_data['x'], restroom_data['y'])
                    restroom.connected_to_path = restroom_data.get('connected_to_path', False)
                    # Note: current_occupancy is saved but cannot be restored without guest references
                    # Guests will re-enter restrooms through normal gameplay after load
                    self.restrooms.append(restroom)

            # Restore bins
            for bin_data in game_state['bins']:
                bin_def = self.bin_defs.get(bin_data['id'])
                if bin_def:
                    bin_obj = self.litter_manager.add_bin(bin_def, bin_data['x'], bin_data['y'])
                    if bin_obj:
                        bin_obj.current_capacity = bin_data['current_capacity']

            # Restore litter
            for litter_data in game_state['litter']:
                litter = Litter(litter_data['x'], litter_data['y'], litter_data['type'])
                litter.age = litter_data['age']
                litter.offset_x = litter_data['offset_x']
                litter.offset_y = litter_data['offset_y']
                self.litter_manager.litters.append(litter)

            # Restore economy
            economy_data = game_state['economy']
            self.economy.cash = economy_data.get('cash', 10000)
            self.economy.park_entrance_fee = economy_data.get('park_entrance_fee', 50)
            self.economy.entrance_revenue = economy_data.get('entrance_revenue', 0)
            self.economy.guests_refused = economy_data.get('guests_refused', 0)

            # Restore time
            time_data = game_state['time']
            self.game_time = time_data['game_time']
            self.game_day = time_data['game_day']
            self.game_hour = time_data['game_hour']
            self.game_minute = time_data['game_minute']
            self.game_speed = time_data['game_speed']
            self.park_open = time_data['park_open']

            # Restore park settings
            park_data = game_state['park_settings']
            self.park_entrance = tuple(park_data['entrance_position']) if park_data['entrance_position'] else None
            self.entrance_width = park_data.get('entrance_width', 5)

            # Restore statistics
            stats_data = game_state['statistics']
            self.guests_entered = stats_data.get('guests_entered', 0)
            self.guests_left = stats_data.get('guests_left', 0)

            # Update queue system
            self._update_queue_system()

            print(f"Game loaded successfully from: {save_name}")
            return True

        except Exception as e:
            print(f"Error loading game: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        running=True
        while running:
            dt=self.clock.tick(60)/1000.0
            running,_,hover=self.handle_events(); self.update(dt); self.draw(hover)
        pygame.quit()
