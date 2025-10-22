from dataclasses import dataclass
from typing import Optional, List, Tuple
import random
from .debug import DebugConfig

@dataclass
class EmployeeType:
    ENGINEER = "engineer"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    MASCOT = "mascot"

@dataclass
class EmployeeDef:
    id: str
    name: str
    type: str
    salary: int  # Coût par heure
    sprite: str
    efficiency: float = 1.0  # Efficacité du travail

@dataclass
class Employee:
    defn: EmployeeDef
    x: int
    y: int
    state: str = "idle"  # idle, working, moving
    target_object = None  # Attraction, chemin, etc.
    work_timer: float = 0.0
    work_duration: float = 0.0
    salary_timer: float = 0.0
    id: int = 0
    
    def __post_init__(self):
        if self.id == 0:
            self.id = random.randint(10000, 99999)

class Engineer(Employee):
    def __init__(self, defn: EmployeeDef, x: int, y: int):
        super().__init__(defn, x, y)
        self.repair_timer = 0.0
        self.repair_duration = 5.0  # Temps pour réparer une attraction
        self.path = []  # Chemin vers l'attraction à réparer
        self.speed = 2.0  # Vitesse de déplacement
        self.move_timer = 0.0
        self.move_duration = 0.5  # Temps pour se déplacer d'une tuile à l'autre
        self.is_moving = False
        self.move_progress = 0.0
        self.target_x = None
        self.target_y = None
        self.salary_negotiation_manager = None  # Set by engine
        
    def can_repair(self, ride) -> bool:
        """Vérifier si l'ingénieur peut réparer cette attraction"""
        return ride.is_broken and not ride.being_repaired
        
    def start_repair(self, ride, grid=None):
        """Commencer la réparation d'une attraction"""
        DebugConfig.log('employees', f"Engineer {self.id} start_repair called for {ride.defn.name}")
        DebugConfig.log('employees', f"Engineer {self.id} current position: ({self.x}, {self.y})")
        self.state = "moving_to_ride"
        self.target_object = ride
        ride.being_repaired = True
        self.repair_timer = 0.0
        
        # Calculer le chemin vers l'attraction
        if grid:
            from .pathfinding import astar_for_engineers
            ride_entrance = (ride.x, ride.y)  # Position de l'attraction
            engineer_pos = (int(self.x), int(self.y))
            
            DebugConfig.log('employees', f"Engineer {self.id} at {engineer_pos}, trying to reach {ride.defn.name} at {ride_entrance}")
            
            path = astar_for_engineers(grid, engineer_pos, ride_entrance)
            if path:
                self.path = path[1:]  # Exclure la position de départ
                DebugConfig.log('employees', f"Engineer {self.id} found path to {ride.defn.name}: {len(self.path)} steps")
                DebugConfig.log('employees', f"Engineer {self.id} path: {self.path}")
            else:
                DebugConfig.log('employees', f"Engineer {self.id} cannot find path to {ride.defn.name}")
                self.state = "idle"
                ride.being_repaired = False
                return
        else:
            DebugConfig.log('employees', f"No grid provided to engineer {self.id}")
        
        DebugConfig.log('employees', f"Engineer {self.id} moving to repair {ride.defn.name}")
        
    def tick(self, dt: float):
        """Mise à jour de l'ingénieur"""
        self.salary_timer += dt

        # Check for negotiation penalty
        efficiency_penalty = 0.0
        if self.salary_negotiation_manager:
            efficiency_penalty = self.salary_negotiation_manager.get_efficiency_penalty('engineer', self.id)

            # If on strike (100% penalty), don't work at all
            if efficiency_penalty >= 1.0:
                if self.state == "working":
                    self.state = "idle"
                    if self.target_object:
                        self.target_object.being_repaired = False
                        self.target_object = None
                    DebugConfig.log('employees', f"Engineer {self.id} on strike, stopped working")
                return

        if self.state == "moving_to_ride":
            self._update_movement(dt)
        elif self.state == "moving_to_nearby":
            self._update_movement_to_nearby(dt)
        elif self.state == "working" and self.target_object:
            # Apply efficiency penalty to repair speed
            effective_dt = dt * (1.0 - efficiency_penalty)
            self.repair_timer += effective_dt
            if self.repair_timer >= self.repair_duration:
                # Réparation terminée
                self.target_object.is_broken = False
                self.target_object.being_repaired = False

                # Move engineer to a nearby position and wait
                self._start_move_to_nearby_position()

                self.target_object = None
                self.repair_timer = 0.0
                DebugConfig.log('employees', f"Engineer {self.id} finished repair and moved to nearby position")
    
    def _update_movement(self, dt: float):
        """Mise à jour du mouvement de l'ingénieur"""
        if not self.path:
            # Arrivé à destination, commencer la réparation
            if self.target_object:
                self.state = "working"
                self.repair_timer = 0.0
                DebugConfig.log('employees', f"Engineer {self.id} arrived at {self.target_object.defn.name}, starting repair")
            return
        
        # Déplacer vers la prochaine position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0
            if DebugConfig.EMPLOYEES:
                DebugConfig.log('employees', f"Engineer {self.id} moving to ({self.target_x}, {self.target_y})")
        
        # Mouvement tuile par tuile avec délai
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            # Arrivé à la position cible
            DebugConfig.log('employees', f"Engineer {self.id} reached target ({self.target_x}, {self.target_y})")
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0
    
    def _update_movement_to_nearby(self, dt: float):
        """Mise à jour du mouvement vers une position proche"""
        if not self.path:
            # Arrivé à destination
            self.state = "idle"
            DebugConfig.log('employees', f"Engineer {self.id} arrived at nearby position")
            return
        
        # Déplacer vers la prochaine position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0
            if DebugConfig.EMPLOYEES:
                DebugConfig.log('employees', f"Engineer {self.id} moving to ({self.target_x}, {self.target_y})")
        
        # Mouvement tuile par tuile avec délai
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            # Arrivé à la position cible
            DebugConfig.log('employees', f"Engineer {self.id} reached target ({self.target_x}, {self.target_y})")
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0
    
    def _start_move_to_nearby_position(self):
        """Start moving engineer to a nearby position after repair"""
        if not self.target_object:
            return
        
        # Find a nearby position (2-3 tiles away from the ride)
        import random
        from .pathfinding import astar_for_engineers
        ride_x, ride_y = self.target_object.x, self.target_object.y
        
        # Try to find a nearby position
        for attempt in range(10):
            # Random offset between 2-4 tiles
            offset_x = random.randint(-4, 4)
            offset_y = random.randint(-4, 4)
            
            # Skip if too close or same position
            if abs(offset_x) < 2 and abs(offset_y) < 2:
                continue
            
            new_x = ride_x + offset_x
            new_y = ride_y + offset_y
            
            # Check bounds (assuming grid is 64x64)
            if 0 <= new_x < 64 and 0 <= new_y < 64:
                # Calculate path using A* pathfinding
                engineer_pos = (int(self.x), int(self.y))
                target_pos = (new_x, new_y)
                
                # We need the grid to calculate path, but we don't have it here
                # For now, calculate a simple Manhattan path
                path = []
                current_x, current_y = int(self.x), int(self.y)
                
                # Move horizontally first
                while current_x != new_x:
                    if current_x < new_x:
                        current_x += 1
                    else:
                        current_x -= 1
                    path.append((current_x, current_y))
                
                # Then move vertically
                while current_y != new_y:
                    if current_y < new_y:
                        current_y += 1
                    else:
                        current_y -= 1
                    path.append((current_x, current_y))
                
                if path:
                    self.state = "moving_to_nearby"
                    self.path = path
                    self.is_moving = False
                    self.move_progress = 0.0
                    DebugConfig.log('employees', f"Engineer {self.id} starting move to nearby position ({new_x}, {new_y}) with path of {len(path)} steps")
                    return
        
        # Fallback: stay at current position
        self.state = "idle"
        DebugConfig.log('employees', f"Engineer {self.id} stayed at current position after repair")
    
    def _move_to_nearby_position(self):
        """Move engineer to a nearby position after repair (legacy method)"""
        # This method is kept for compatibility but should not be used
        self.state = "idle"

class MaintenanceWorker(Employee):
    def __init__(self, defn: EmployeeDef, x: int, y: int):
        super().__init__(defn, x, y)
        self.cleaning_timer = 0.0
        self.cleaning_duration = 0.5  # Temps pour nettoyer un détritus
        self.gardening_timer = 0.0
        self.gardening_duration = 2.0  # Temps pour entretenir le jardin
        self.patrol_timer = 0.0
        self.patrol_duration = 0.0  # Pas de délai - travail continu immédiat
        self.target_litter = None  # Litter object being cleaned
        self.path = []
        self.is_moving = False
        self.move_progress = 0.0
        self.target_x = float(x)
        self.target_y = float(y)
        self.placement_type = None  # 'path' or 'grass'
        self.patrol_radius = 10  # Rayon de patrouille
        self.speed = 2.0  # Vitesse de mouvement (tiles par seconde)
        self.move_duration = 0.5  # Durée pour se déplacer d'une tuile à l'autre
        self.initial_x = x  # Position initiale pour la patrouille
        self.initial_y = y
        self.target_garden_spot = None  # Position de jardin à entretenir
        self.lawn_mowing_pattern = 'horizontal'  # 'horizontal' or 'vertical'
        self.lawn_mowing_offset = 0  # Current offset in the pattern
        self.lawn_mowing_direction = 1  # 1 = right/down, -1 = left/up
        self.lawn_mowing_row = 0  # Current row/column in pattern
        self.mowing_speed = 0.3  # Duration to mow one tile (seconds)
        self.salary_negotiation_manager = None  # Set by engine

    def get_render_position(self):
        """Get the position to render the worker (interpolated during movement)"""
        # If moving, lerp between current and target
        if self.is_moving and self.move_progress > 0:
            t = min(1.0, self.move_progress / self.move_duration)
            lerp_x = self.x + (self.target_x - self.x) * t
            lerp_y = self.y + (self.target_y - self.y) * t
            return (lerp_x, lerp_y)
        return (float(self.x), float(self.y))

    def set_placement_type(self, tile_type):
        """Définir le type de placement (chemin ou pelouse)"""
        if tile_type == 1:  # TILE_WALK
            self.placement_type = "path"
            DebugConfig.log('employees', f"Maintenance worker {self.id} assigned to path cleaning")
        elif tile_type == 0:  # TILE_GRASS
            self.placement_type = "grass"
            DebugConfig.log('employees', f"Maintenance worker {self.id} assigned to garden maintenance")
        
    def find_nearest_litter(self, litter_manager, grid):
        """Trouver le détritus le plus proche sur un chemin ou file d'attente"""
        if not litter_manager or self.placement_type != "path":
            DebugConfig.log('employees', f"Maintenance worker {self.id} cannot search for litter - litter_manager: {litter_manager is not None}, placement_type: {self.placement_type}")
            return None

        nearest_litter = None
        min_distance = float('inf')

        DebugConfig.log('employees', f"Maintenance worker {self.id} searching for litter in {len(litter_manager.litters)} litters")

        for litter in litter_manager.litters:
            # Vérifier si le détritus est sur un chemin, file d'attente, entrée ou sortie d'attraction
            # TILE_WALK = 1, TILE_RIDE_ENTRANCE = 2, TILE_RIDE_EXIT = 3, TILE_QUEUE_PATH = 5
            tile_type = grid.get(litter.x, litter.y)
            if grid.in_bounds(litter.x, litter.y) and tile_type in [1, 2, 3, 5]:
                distance = abs(self.x - litter.x) + abs(self.y - litter.y)
                if distance <= self.patrol_radius and distance < min_distance:
                    min_distance = distance
                    nearest_litter = litter

        if nearest_litter:
            DebugConfig.log('employees', f"Maintenance worker {self.id} found nearest litter at ({nearest_litter.x}, {nearest_litter.y}), distance: {min_distance:.1f}")
        else:
            DebugConfig.log('employees', f"Maintenance worker {self.id} found NO litter within radius {self.patrol_radius}")

        return nearest_litter
    
    def start_cleaning(self, litter, grid):
        """Commencer à se diriger vers un détritus pour le nettoyer"""
        from .pathfinding import astar
        self.target_litter = litter
        litter_pos = (int(litter.x), int(litter.y))
        worker_pos = (int(self.x), int(self.y))

        # Check if already at litter position
        if worker_pos == litter_pos:
            # Already at litter, start cleaning immediately
            self.state = "cleaning"
            self.cleaning_timer = 0.0
            self.patrol_timer = 0.0
            DebugConfig.log('employees', f"Maintenance worker {self.id} already at litter, starting to clean immediately")
            return True

        # Find path to litter
        path = astar(grid, worker_pos, litter_pos)
        if path and len(path) > 1:
            self.path = path[1:]  # Skip current position
            self.state = "moving_to_litter"
            self.patrol_timer = 0.0  # Reset patrol timer
            DebugConfig.log('employees', f"Maintenance worker {self.id} moving to clean litter at {litter_pos}")
            return True
        else:
            DebugConfig.log('employees', f"Maintenance worker {self.id} couldn't find path to litter at {litter_pos}")
            self.target_litter = None
            return False
        
    def start_gardening(self, garden_spot, grid):
        """Commencer l'entretien du jardin à une position spécifique"""
        from .pathfinding import astar
        self.target_garden_spot = garden_spot
        garden_pos = (int(garden_spot[0]), int(garden_spot[1]))
        worker_pos = (int(self.x), int(self.y))

        # Find path to garden spot
        path = astar(grid, worker_pos, garden_pos)
        if path and len(path) > 1:
            self.path = path[1:]  # Skip current position
            self.state = "moving_to_garden"
            self.patrol_timer = 0.0  # Reset patrol timer
            DebugConfig.log('employees', f"Maintenance worker {self.id} moving to garden at {garden_pos}")
        elif worker_pos == garden_pos:
            # Already at the spot, start gardening immediately
            self.state = "gardening"
            self.gardening_timer = 0.0
            self.patrol_timer = 0.0  # Reset patrol timer
            DebugConfig.log('employees', f"Maintenance worker {self.id} started gardening at current position")
        else:
            DebugConfig.log('employees', f"Maintenance worker {self.id} couldn't find path to garden at {garden_pos}")
            self.target_garden_spot = None

    def start_mowing(self, grid):
        """Démarrer la tonte de pelouse en mouvement continu"""
        self.state = "mowing"
        self.gardening_timer = 0.0
        self.patrol_timer = 0.0
        # Initialize mowing from current position
        self.lawn_mowing_row = 0
        # IMPORTANT: Update initial position to current position for each new cycle
        # This allows the agent to restart from wherever it finished the last cycle
        self.initial_x = int(self.x)
        self.initial_y = int(self.y)
        DebugConfig.log('employees', f"Maintenance worker {self.id} starting continuous lawn mowing from ({self.initial_x}, {self.initial_y}) - pattern: {self.lawn_mowing_pattern}")

    def _get_next_mowing_position(self, grid):
        """Calcule la prochaine position dans le pattern de tonte (avec gestion d'obstacles)"""
        current_x = int(self.x)
        current_y = int(self.y)

        if self.lawn_mowing_pattern == 'horizontal':
            # Tonte horizontale : gauche ↔ droite, ligne par ligne
            next_x = current_x + self.lawn_mowing_direction
            next_y = current_y

            # Check if we reached the end of the row (patrol radius OR grid bounds)
            reached_end = (abs(next_x - self.initial_x) > self.patrol_radius or
                          not grid.in_bounds(next_x, next_y))

            if reached_end:
                # Move to next row and reverse direction
                next_x = current_x
                next_y = current_y + 1
                self.lawn_mowing_direction *= -1
                self.lawn_mowing_row += 1

                DebugConfig.log('employees', f"Worker {self.id} reached end of row at ({current_x}, {current_y}), moving to next row ({next_x}, {next_y}), direction now: {self.lawn_mowing_direction}")

                # Check if we finished all rows (patrol radius OR grid bounds)
                if abs(next_y - self.initial_y) > self.patrol_radius or not grid.in_bounds(next_x, next_y):
                    # Finished horizontal pattern, switch to vertical for NEXT cycle
                    DebugConfig.log('employees', f"Worker {self.id} finished horizontal pattern, will switch to vertical on next cycle")
                    self.lawn_mowing_pattern = 'vertical'
                    self.lawn_mowing_row = 0
                    self.lawn_mowing_direction = 1
                    # Return None to signal completion - engine will restart
                    return None

        else:  # vertical
            # Tonte verticale : haut ↔ bas, colonne par colonne
            next_x = current_x
            next_y = current_y + self.lawn_mowing_direction

            # Check if we reached the end of the column (patrol radius OR grid bounds)
            reached_end = (abs(next_y - self.initial_y) > self.patrol_radius or
                          not grid.in_bounds(next_x, next_y))

            if reached_end:
                # Move to next column and reverse direction
                next_x = current_x + 1
                next_y = current_y
                self.lawn_mowing_direction *= -1
                self.lawn_mowing_row += 1

                DebugConfig.log('employees', f"Worker {self.id} reached end of column at ({current_x}, {current_y}), moving to next column ({next_x}, {next_y}), direction now: {self.lawn_mowing_direction}")

                # Check if we finished all columns (patrol radius OR grid bounds)
                if abs(next_x - self.initial_x) > self.patrol_radius or not grid.in_bounds(next_x, next_y):
                    # Finished vertical pattern, switch to horizontal for NEXT cycle
                    DebugConfig.log('employees', f"Worker {self.id} finished vertical pattern, will switch to horizontal on next cycle")
                    self.lawn_mowing_pattern = 'horizontal'
                    self.lawn_mowing_row = 0
                    self.lawn_mowing_direction = 1
                    # Return None to signal completion - engine will restart
                    return None

        # Check if next position is valid
        if not grid.in_bounds(next_x, next_y):
            DebugConfig.log('employees', f"Worker {self.id} next position ({next_x}, {next_y}) out of bounds")
            return None

        tile_type = grid.get(next_x, next_y)

        # If it's grass, we can mow it
        if tile_type == 0:  # TILE_GRASS
            return (next_x, next_y)

        # If it's an obstacle, try to go around
        DebugConfig.log('employees', f"Worker {self.id} found obstacle at ({next_x}, {next_y}), trying to go around")

        if self.lawn_mowing_pattern == 'horizontal':
            # Try moving to next row
            alt_next_x = current_x
            alt_next_y = current_y + 1
            self.lawn_mowing_direction *= -1
            if grid.in_bounds(alt_next_x, alt_next_y) and grid.get(alt_next_x, alt_next_y) == 0:
                DebugConfig.log('employees', f"Worker {self.id} going around obstacle to ({alt_next_x}, {alt_next_y})")
                return (alt_next_x, alt_next_y)
        else:  # vertical
            # Try moving to next column
            alt_next_x = current_x + 1
            alt_next_y = current_y
            self.lawn_mowing_direction *= -1
            if grid.in_bounds(alt_next_x, alt_next_y) and grid.get(alt_next_x, alt_next_y) == 0:
                DebugConfig.log('employees', f"Worker {self.id} going around obstacle to ({alt_next_x}, {alt_next_y})")
                return (alt_next_x, alt_next_y)

        DebugConfig.log('employees', f"Worker {self.id} cannot find valid next position")
        return None

    def find_next_lawn_mowing_spot(self, grid):
        """Trouve le prochain spot pour la tonte en ligne (gauche-droite ou haut-bas)"""
        import random

        # Alternate between horizontal and vertical mowing patterns
        if self.lawn_mowing_offset >= self.patrol_radius * 2:
            self.lawn_mowing_offset = 0
            # Switch pattern
            self.lawn_mowing_pattern = 'vertical' if self.lawn_mowing_pattern == 'horizontal' else 'horizontal'

        # Try to find a grass spot in a systematic pattern
        for attempt in range(20):
            if self.lawn_mowing_pattern == 'horizontal':
                # Mow left to right, line by line
                row_offset = self.lawn_mowing_offset // (self.patrol_radius * 2 + 1)
                col_offset = self.lawn_mowing_offset % (self.patrol_radius * 2 + 1) - self.patrol_radius
                target_x = int(self.initial_x + col_offset)
                target_y = int(self.initial_y + row_offset - self.patrol_radius)
            else:
                # Mow top to bottom, column by column
                col_offset = self.lawn_mowing_offset // (self.patrol_radius * 2 + 1)
                row_offset = self.lawn_mowing_offset % (self.patrol_radius * 2 + 1) - self.patrol_radius
                target_x = int(self.initial_x + col_offset - self.patrol_radius)
                target_y = int(self.initial_y + row_offset)

            self.lawn_mowing_offset += 1

            # Check if position is valid grass
            if grid.in_bounds(target_x, target_y) and grid.get(target_x, target_y) == 0:  # TILE_GRASS
                # Check if not too close to current position (at least 1 tile away)
                distance = abs(target_x - self.x) + abs(target_y - self.y)
                if distance >= 1:
                    return (target_x, target_y)

        # Fallback: random grass spot
        for attempt in range(10):
            offset_x = random.randint(-self.patrol_radius, self.patrol_radius)
            offset_y = random.randint(-self.patrol_radius, self.patrol_radius)
            target_x = int(self.initial_x + offset_x)
            target_y = int(self.initial_y + offset_y)

            if grid.in_bounds(target_x, target_y) and grid.get(target_x, target_y) == 0:
                distance = abs(target_x - self.x) + abs(target_y - self.y)
                if distance >= 1:
                    return (target_x, target_y)

        return None

    def start_patrol(self, grid):
        """Commencer une patrouille aléatoire dans le rayon"""
        from .pathfinding import astar
        import random

        # Essayer de trouver une position accessible dans le rayon de patrouille
        for attempt in range(10):
            # Choisir une position aléatoire dans le rayon
            offset_x = random.randint(-self.patrol_radius, self.patrol_radius)
            offset_y = random.randint(-self.patrol_radius, self.patrol_radius)

            target_x = int(self.initial_x + offset_x)
            target_y = int(self.initial_y + offset_y)

            # Vérifier que la position est dans les limites
            if not grid.in_bounds(target_x, target_y):
                continue

            # Vérifier que la position est accessible selon le type de placement
            tile_type = grid.get(target_x, target_y)
            valid_tile = False

            if self.placement_type == "path":
                # Path workers can walk on paths
                valid_tile = grid.walkable(target_x, target_y)
            elif self.placement_type == "grass":
                # Grass workers can walk on grass and paths
                valid_tile = tile_type in [0, 1]  # TILE_GRASS or TILE_WALK

            if not valid_tile:
                continue

            # Trouver un chemin vers cette position
            worker_pos = (int(self.x), int(self.y))
            target_pos = (target_x, target_y)
            path = astar(grid, worker_pos, target_pos)

            if path and len(path) > 1:
                self.path = path[1:]
                self.state = "patrolling"
                self.is_moving = False
                self.move_progress = 0.0
                self.patrol_timer = 0.0  # Reset patrol timer
                DebugConfig.log('employees', f"Maintenance worker {self.id} starting patrol to ({target_x}, {target_y})")
                return True

        # Si aucun chemin trouvé après 10 tentatives, rester en idle
        DebugConfig.log('employees', f"Maintenance worker {self.id} couldn't find patrol path, staying idle")
        return False
        
    def tick(self, dt: float):
        """Mise à jour de l'employé de maintenance"""
        self.salary_timer += dt

        # Check for negotiation penalty
        efficiency_penalty = 0.0
        if self.salary_negotiation_manager:
            efficiency_penalty = self.salary_negotiation_manager.get_efficiency_penalty('maintenance', self.id)

            # If on strike (100% penalty), don't work at all
            if efficiency_penalty >= 1.0:
                if self.state in ["cleaning", "gardening", "mowing", "moving_to_litter", "moving_to_garden"]:
                    self.state = "idle"
                    self.target_litter = None
                    self.target_garden_spot = None
                    DebugConfig.log('employees', f"Maintenance worker {self.id} on strike, stopped working")
                return

        if self.state == "idle":
            # Idle: look for work or start patrol
            self.patrol_timer += dt
            # Note: Do NOT reset patrol_timer here, it will be reset by engine
            # when work is assigned or patrol starts

        elif self.state == "patrolling":
            self._update_patrol_movement(dt)

        elif self.state == "moving_to_litter":
            self._update_movement_to_litter(dt)

        elif self.state == "moving_to_garden":
            self._update_movement_to_garden(dt)

        elif self.state == "cleaning":
            # Apply efficiency penalty to cleaning speed
            effective_dt = dt * (1.0 - efficiency_penalty)
            self.cleaning_timer += effective_dt
            if self.cleaning_timer >= self.cleaning_duration:
                # Cleaning finished
                DebugConfig.log('employees', f"Maintenance worker {self.id} finished cleaning, going idle, patrol_timer: {self.patrol_timer:.2f}")
                self.state = "idle"
                self.target_litter = None
                self.cleaning_timer = 0.0
                # DO NOT reset patrol_timer - it should stay at 0.0 to trigger immediate reassignment

        elif self.state == "gardening":
            # Apply efficiency penalty to gardening speed
            effective_dt = dt * (1.0 - efficiency_penalty)
            self.gardening_timer += effective_dt
            if self.gardening_timer >= self.gardening_duration:
                self.state = "idle"
                self.gardening_timer = 0.0
                self.target_garden_spot = None
                DebugConfig.log('employees', f"Maintenance worker {self.id} finished gardening")

        elif self.state == "mowing":
            # Apply efficiency penalty to mowing
            effective_dt = dt * (1.0 - efficiency_penalty)
            self._update_mowing(effective_dt)
    
    def _update_movement_to_litter(self, dt: float):
        """Mise à jour du mouvement vers un détritus"""
        if not self.path:
            # Arrived at litter, start cleaning
            if self.target_litter:
                self.state = "cleaning"
                self.cleaning_timer = 0.0
                DebugConfig.log('employees', f"Maintenance worker {self.id} arrived at litter, starting to clean")
            else:
                self.state = "idle"
            return

        # Move to next position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0

        # Tile-by-tile movement with delay
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0

    def _update_movement_to_garden(self, dt: float):
        """Mise à jour du mouvement vers un spot de jardin"""
        if not self.path:
            # Arrived at garden spot, start gardening
            if self.target_garden_spot:
                self.state = "gardening"
                self.gardening_timer = 0.0
                DebugConfig.log('employees', f"Maintenance worker {self.id} arrived at garden spot, starting to garden")
            else:
                self.state = "idle"
            return

        # Move to next position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0

        # Tile-by-tile movement with delay
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0

    def _update_mowing(self, dt: float):
        """Mise à jour de la tonte de pelouse en mouvement continu"""
        # Increment timer for current tile
        self.gardening_timer += dt

        # Log timer value for debugging
        if self.gardening_timer >= self.mowing_speed:
            DebugConfig.log('employees', f"Maintenance worker {self.id} timer reached {self.gardening_timer:.3f}s (threshold: {self.mowing_speed:.3f}s) at tile ({int(self.x)}, {int(self.y)})")

        # DO NOT RESET TIMER HERE! The engine will reset it after moving the worker.
        # The timer needs to stay >= mowing_speed so the engine can detect it.

    def _update_patrol_movement(self, dt: float):
        """Mise à jour du mouvement de patrouille"""
        if not self.path:
            # Arrived at patrol destination, immediately trigger next patrol
            self.state = "idle"
            self.patrol_timer = self.patrol_duration  # Set timer to trigger immediate patrol
            DebugConfig.log('employees', f"Maintenance worker {self.id} finished patrol, triggering next patrol immediately")
            return

        # Move to next position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0

        # Tile-by-tile movement with delay
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0

class SecurityGuard(Employee):
    def __init__(self, defn: EmployeeDef, x: int, y: int):
        super().__init__(defn, x, y)
        self.patrol_timer = 0.0
        self.patrol_duration = 0.0  # Pas de délai - patrouille continue
        self.security_radius = 5  # Rayon de sécurité autour du gardien
        self.patrol_radius = 15  # Rayon de patrouille
        self.initial_x = x  # Position initiale
        self.initial_y = y
        self.path = []
        self.is_moving = False
        self.move_progress = 0.0
        self.target_x = float(x)
        self.target_y = float(y)
        self.speed = 2.0  # Vitesse de déplacement
        self.move_duration = 0.5  # Durée pour se déplacer d'une tuile
        self.nearby_guests = []  # Liste des visiteurs à proximité
        self.salary_negotiation_manager = None  # Set by engine

    def start_patrol(self, grid):
        """Commencer une patrouille sur les chemins"""
        from .pathfinding import astar
        import random

        # Essayer de trouver une position accessible sur les chemins
        for attempt in range(10):
            # Choisir une position aléatoire dans le rayon
            offset_x = random.randint(-self.patrol_radius, self.patrol_radius)
            offset_y = random.randint(-self.patrol_radius, self.patrol_radius)

            target_x = int(self.initial_x + offset_x)
            target_y = int(self.initial_y + offset_y)

            # Vérifier que la position est dans les limites
            if not grid.in_bounds(target_x, target_y):
                continue

            # Security guards can ONLY walk on paths
            if not grid.walkable(target_x, target_y):
                continue

            # Trouver un chemin vers cette position
            guard_pos = (int(self.x), int(self.y))
            target_pos = (target_x, target_y)
            path = astar(grid, guard_pos, target_pos)

            if path and len(path) > 1:
                self.path = path[1:]
                self.state = "patrolling"
                self.is_moving = False
                self.move_progress = 0.0
                self.patrol_timer = 0.0
                DebugConfig.log('employees', f"Security guard {self.id} starting patrol to ({target_x}, {target_y})")
                return True

        # Si aucun chemin trouvé, rester en idle
        DebugConfig.log('employees', f"Security guard {self.id} couldn't find patrol path, staying idle")
        return False

    def update_nearby_guests(self, guests):
        """Mettre à jour la liste des visiteurs à proximité"""
        self.nearby_guests = []
        guard_x = int(self.x)
        guard_y = int(self.y)

        for guest in guests:
            # Calculer la distance Manhattan
            distance = abs(guest.grid_x - guard_x) + abs(guest.grid_y - guard_y)

            # Si le visiteur est dans le rayon de sécurité
            if distance <= self.security_radius:
                self.nearby_guests.append(guest)

        return len(self.nearby_guests)

    def tick(self, dt: float):
        """Mise à jour du gardien"""
        self.salary_timer += dt

        # Check for negotiation penalty
        efficiency_penalty = 0.0
        if self.salary_negotiation_manager:
            efficiency_penalty = self.salary_negotiation_manager.get_efficiency_penalty('security', self.id)

            # If on strike (100% penalty), don't work at all
            if efficiency_penalty >= 1.0:
                if self.state == "patrolling":
                    self.state = "idle"
                    self.path = []
                    DebugConfig.log('employees', f"Security guard {self.id} on strike, stopped patrolling")
                return

        if self.state == "idle":
            # Idle: increment patrol timer
            self.patrol_timer += dt

        elif self.state == "patrolling":
            # Security effectiveness is reduced by penalty, but movement continues
            # (Penalty affects their ability to provide security, not their movement)
            self._update_patrol_movement(dt)

    def _update_patrol_movement(self, dt: float):
        """Mise à jour du mouvement de patrouille"""
        if not self.path:
            # Arrivé à destination, recommencer immédiatement
            self.state = "idle"
            self.patrol_timer = self.patrol_duration  # Trigger immediate next patrol
            DebugConfig.log('employees', f"Security guard {self.id} finished patrol, triggering next patrol immediately")
            return

        # Move to next position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0

        # Tile-by-tile movement with delay
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0

class Mascot(Employee):
    def __init__(self, defn: EmployeeDef, x: int, y: int):
        super().__init__(defn, x, y)
        self.entertainment_timer = 0.0
        self.entertainment_duration = random.uniform(5.0, 8.0)  # Temps d'animation variable
        self.excitement_boost = 0.10  # Boost d'excitation pour les visiteurs (+10%)
        self.happiness_boost = 0.03  # Boost de bonheur pour les visiteurs (+3%)
        self.entertainment_radius = 3  # Rayon d'animation
        self.detection_radius = 20  # Rayon pour détecter les visiteurs
        self.initial_x = x
        self.initial_y = y
        self.path = []
        self.is_moving = False
        self.move_progress = 0.0
        self.target_x = float(x)
        self.target_y = float(y)
        self.speed = 1.5  # Plus lent que les autres (plus théâtral)
        self.move_duration = 0.7  # Plus lent
        self.nearby_guests = []  # Liste des visiteurs à proximité
        self.target_hotspot = None  # Position de la foule cible
        self.search_timer = 0.0
        self.search_duration = 0.0  # Pas de délai - recherche continue
        self.salary_negotiation_manager = None  # Set by engine

    def find_best_crowd_location(self, guests, queue_manager):
        """Trouver le meilleur endroit avec des visiteurs (priorise les files d'attente)"""
        import random

        DebugConfig.log('employees', f"Mascot {self.id} searching for crowds - {len(guests)} guests, queue_manager: {queue_manager is not None}")

        # 70% chance de chercher dans les files d'attente
        if random.random() < 0.7 and queue_manager:
            # Chercher les files d'attente avec le plus de visiteurs
            best_queue = None
            max_visitors = 0

            for queue_path in queue_manager.queue_paths:
                visitor_count = len(queue_path.visitors)
                if visitor_count > max_visitors and visitor_count >= 3:
                    # Au moins 3 visiteurs pour que ça vaille le coup
                    best_queue = queue_path
                    max_visitors = visitor_count

            if best_queue and best_queue.tiles:
                # Choisir une position au milieu de la file
                middle_idx = len(best_queue.tiles) // 2
                target_tile = best_queue.tiles[middle_idx]
                DebugConfig.log('employees', f"Mascot {self.id} found queue with {max_visitors} visitors")
                return (target_tile.x, target_tile.y)

        # 30% chance ou fallback: chercher sur les chemins avec beaucoup de visiteurs
        crowd_positions = {}  # {(x, y): visitor_count}

        for guest in guests:
            pos = (guest.grid_x, guest.grid_y)
            # Regrouper par zone de 2x2 tuiles
            zone = (pos[0] // 2, pos[1] // 2)
            crowd_positions[zone] = crowd_positions.get(zone, 0) + 1

        # Trouver la zone avec le plus de visiteurs
        if crowd_positions:
            best_zone = max(crowd_positions.items(), key=lambda x: x[1])
            if best_zone[1] >= 3:  # Au moins 3 visiteurs
                # Convertir la zone en position réelle
                target_x = best_zone[0][0] * 2
                target_y = best_zone[0][1] * 2
                DebugConfig.log('employees', f"Mascot {self.id} found crowd at ({target_x}, {target_y}) with {best_zone[1]} visitors")
                return (target_x, target_y)

        DebugConfig.log('employees', f"Mascot {self.id} found NO crowds")
        return None

    def start_moving_to_crowd(self, target_pos, grid):
        """Se déplacer vers une foule"""
        from .pathfinding import astar

        mascot_pos = (int(self.x), int(self.y))

        DebugConfig.log('employees', f"Mascot {self.id} at {mascot_pos} trying to reach crowd at {target_pos}")

        # Mascots can walk on paths (TILE_WALK=1) and queue paths (TILE_QUEUE_PATH=5)
        # We need custom pathfinding for this
        path = self._find_path_for_mascot(grid, mascot_pos, target_pos)

        if path and len(path) > 1:
            self.path = path[1:]
            self.state = "moving_to_crowd"
            self.is_moving = False
            self.move_progress = 0.0
            self.target_hotspot = target_pos
            DebugConfig.log('employees', f"Mascot {self.id} moving to crowd at {target_pos} - path length: {len(self.path)}")
            return True

        DebugConfig.log('employees', f"Mascot {self.id} couldn't find path to crowd at {target_pos} from {mascot_pos}")
        return False

    def _find_path_for_mascot(self, grid, start, goal):
        """Pathfinding pour mascotte (chemins + files d'attente)"""
        from .pathfinding import astar
        import heapq

        # A* modifié pour accepter TILE_WALK (1) et TILE_QUEUE_PATH (5)
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))

            # Check neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if not grid.in_bounds(neighbor[0], neighbor[1]):
                    continue

                tile_type = grid.get(neighbor[0], neighbor[1])
                # Mascots can walk on paths (1) and queue paths (5)
                if tile_type not in [1, 5]:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None

    def _heuristic(self, a, b):
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def start_entertaining(self):
        """Commencer l'animation pour divertir les visiteurs"""
        self.state = "entertaining"
        self.entertainment_timer = 0.0
        self.entertainment_duration = random.uniform(5.0, 8.0)
        DebugConfig.log('employees', f"Mascot {self.id} started entertaining for {self.entertainment_duration:.1f}s")

    def update_nearby_guests(self, guests):
        """Mettre à jour la liste des visiteurs à proximité"""
        self.nearby_guests = []
        mascot_x = int(self.x)
        mascot_y = int(self.y)

        for guest in guests:
            distance = abs(guest.grid_x - mascot_x) + abs(guest.grid_y - mascot_y)
            if distance <= self.entertainment_radius:
                self.nearby_guests.append(guest)

        return len(self.nearby_guests)

    def tick(self, dt: float):
        """Mise à jour de la mascotte"""
        self.salary_timer += dt

        # Check for negotiation penalty
        efficiency_penalty = 0.0
        if self.salary_negotiation_manager:
            efficiency_penalty = self.salary_negotiation_manager.get_efficiency_penalty('mascot', self.id)

            # If on strike (100% penalty), don't work at all
            if efficiency_penalty >= 1.0:
                if self.state in ["entertaining", "moving_to_crowd"]:
                    self.state = "idle"
                    self.path = []
                    self.target_hotspot = None
                    DebugConfig.log('employees', f"Mascot {self.id} on strike, stopped entertaining")
                return

        if self.state == "idle":
            self.search_timer += dt
            # Log only once per second to avoid spam
            if int(self.search_timer) != int(self.search_timer - dt):
                DebugConfig.log('employees', f"Mascot {self.id} idle, search_timer: {self.search_timer:.2f}")

        elif self.state == "moving_to_crowd":
            self._update_movement_to_crowd(dt)

        elif self.state == "entertaining":
            # Mascot entertainment effectiveness is reduced by penalty
            # This affects how much boost guests receive
            effective_dt = dt * (1.0 - efficiency_penalty)
            self.entertainment_timer += effective_dt
            if self.entertainment_timer >= self.entertainment_duration:
                # Animation terminée, chercher une nouvelle foule
                DebugConfig.log('employees', f"Mascot {self.id} finished entertaining")
                self.state = "idle"
                self.entertainment_timer = 0.0
                self.target_hotspot = None
                self.search_timer = 0.0  # Reset search timer

    def _update_movement_to_crowd(self, dt: float):
        """Mise à jour du mouvement vers la foule"""
        if not self.path:
            # Arrivé à destination, commencer l'animation
            self.start_entertaining()
            return

        # Move to next position
        if not self.is_moving:
            next_pos = self.path.pop(0)
            self.target_x = float(next_pos[0])
            self.target_y = float(next_pos[1])
            self.is_moving = True
            self.move_progress = 0.0

        # Tile-by-tile movement with delay
        self.move_progress += dt * self.speed
        if self.move_progress >= self.move_duration:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.move_progress = 0.0
