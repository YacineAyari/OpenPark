"""
Simple Queue System for OpenPark
Based on classic 2.5D oblique games like Theme Park (Bullfrog, 1994)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING
from .map import TILE_QUEUE_PATH
from .debug import DebugConfig

if TYPE_CHECKING:
    from .agents import Guest
    from .rides import Ride


@dataclass
class SimpleQueueTile:
    """Simple queue tile with basic properties"""
    x: int
    y: int
    visitors: List['Guest'] = None  # Liste des visiteurs sur cette tuile
    is_entrance: bool = False
    is_exit: bool = False
    orientation: str = "horizontal"  # "horizontal" ou "vertical"
    
    def __post_init__(self):
        if self.visitors is None:
            self.visitors = []
    
    def get_capacity(self) -> int:
        """Retourne la capacité de la tuile selon son orientation"""
        return 5 if self.orientation == "horizontal" else 4
    
    def is_full(self) -> bool:
        return len(self.visitors) >= self.get_capacity()
    
    def can_enter(self) -> bool:
        return not self.is_full()
    
    def add_visitor(self, visitor: 'Guest') -> bool:
        """Ajoute un visiteur à cette tuile"""
        if self.can_enter():
            self.visitors.append(visitor)
            return True
        return False
    
    def remove_visitor(self, visitor: 'Guest'):
        """Retire un visiteur de cette tuile"""
        if visitor in self.visitors:
            self.visitors.remove(visitor)
    
    def get_visitor_position(self, visitor: 'Guest') -> int:
        """Retourne la position du visiteur dans cette tuile (0 à capacity-1)"""
        if visitor in self.visitors:
            return self.visitors.index(visitor)
        return -1


class SimpleQueuePath:
    """Simple linear queue path"""
    def __init__(self, tiles: List[SimpleQueueTile], connected_ride: Optional['Ride'] = None):
        self.tiles = tiles  # Liste ordonnée des tuiles
        self.connected_ride = connected_ride
        self.visitors: List['Guest'] = []  # Liste des visiteurs dans la queue
        self.entrance_tile = tiles[0] if tiles else None
        self.exit_tile = tiles[-1] if tiles else None
        
        # Calculer la capacité totale
        self.max_capacity = sum(tile.get_capacity() for tile in tiles)
        
        # Marquer l'entrée et la sortie
        if self.entrance_tile:
            self.entrance_tile.is_entrance = True
        if self.exit_tile:
            self.exit_tile.is_exit = True
    
    def can_enter(self) -> bool:
        """Vérifie si un visiteur peut entrer dans la queue"""
        return len(self.visitors) < self.max_capacity and self.entrance_tile.can_enter()
    
    def add_visitor(self, visitor: 'Guest') -> bool:
        """Ajoute un visiteur à la queue"""
        DebugConfig.log('queues', f"SimpleQueuePath.add_visitor called for visitor {visitor.id}")
        DebugConfig.log('queues', f"Queue capacity: {self.max_capacity}, current visitors: {len(self.visitors)}")
        
        if not self.can_enter():
            DebugConfig.log('queues', f"Queue cannot accept visitor {visitor.id}")
            return False
        
        self.visitors.append(visitor)
        visitor.queue_position = len(self.visitors) - 1
        visitor.current_queue = self
        
        DebugConfig.log('queues', f"Visitor {visitor.id} added to visitors list, total: {len(self.visitors)}")
        
        # Réorganiser tous les visiteurs dans les tuiles
        self._distribute_visitors_across_tiles()
        
        DebugConfig.log('queues', f"Visitor {visitor.id} entered queue at position {visitor.queue_position}")
        return True
    
    def remove_visitor(self, visitor: 'Guest'):
        """Retire un visiteur de la queue"""
        if visitor in self.visitors:
            # Libérer la tuile
            if visitor.current_queue_tile:
                visitor.current_queue_tile.remove_visitor(visitor)
            
            # Retirer de la liste
            self.visitors.remove(visitor)
            
            # Mettre à jour les positions des autres visiteurs
            for i, v in enumerate(self.visitors):
                v.queue_position = i
            
            # Déplacer les visiteurs vers l'avant
            self._move_visitors_forward()
            
            DebugConfig.log('queues', f"Visitor {visitor.id} removed from queue")
    
    def _distribute_visitors_across_tiles(self):
        """Distribue tous les visiteurs dans les tuiles disponibles"""
        DebugConfig.log('queues', f"Distributing {len(self.visitors)} visitors across {len(self.tiles)} tiles")
        
        # Vider toutes les tuiles
        for tile in self.tiles:
            tile.visitors.clear()
        
        # Distribuer les visiteurs dans les tuiles
        visitor_index = 0
        for tile_index, tile in enumerate(self.tiles):
            DebugConfig.log('queues', f"Tile {tile_index} at ({tile.x}, {tile.y}) - capacity: {tile.get_capacity()}")
            # Remplir cette tuile avec les visiteurs suivants
            while visitor_index < len(self.visitors) and len(tile.visitors) < tile.get_capacity():
                visitor = self.visitors[visitor_index]
                tile.add_visitor(visitor)
                visitor.current_queue_tile = tile
                visitor.tile_position = tile.get_visitor_position(visitor)
                visitor.queue_position = visitor_index
                
                # Mettre à jour la position du visiteur
                visitor.grid_x = tile.x
                visitor.grid_y = tile.y
                visitor.x = float(tile.x)
                visitor.y = float(tile.y)
                
                DebugConfig.log('queues', f"Visitor {visitor.id} placed on tile {tile_index} at ({tile.x}, {tile.y}) - position {visitor.tile_position}/{tile.get_capacity()}")
                visitor_index += 1
        
        # Vérifier la distribution finale
        for tile_index, tile in enumerate(self.tiles):
            DebugConfig.log('queues', f"Final tile {tile_index} has {len(tile.visitors)} visitors")
    
    def _move_visitors_forward(self):
        """Déplace tous les visiteurs vers l'avant dans la queue"""
        # Réorganiser tous les visiteurs dans les tuiles disponibles
        self._distribute_visitors_across_tiles()
    
    def get_next_position(self, visitor: 'Guest') -> Optional[Tuple[int, int]]:
        """Retourne la position suivante dans la queue"""
        if visitor.queue_position < len(self.tiles) - 1:
            next_tile = self.tiles[visitor.queue_position + 1]
            return (next_tile.x, next_tile.y)
        return None
    
    def is_at_front(self, visitor: 'Guest') -> bool:
        """Vérifie si le visiteur est en tête de queue"""
        return visitor.queue_position == 0
    
    def can_board_ride(self, visitor: 'Guest') -> bool:
        """Vérifie si le visiteur peut monter dans l'attraction"""
        return (self.is_at_front(visitor) and 
                self.connected_ride and 
                self.connected_ride.can_board())
    
    def get_entrance_position(self) -> Optional[Tuple[int, int]]:
        """Retourne la position d'entrée de la queue"""
        if self.entrance_tile:
            return (self.entrance_tile.x, self.entrance_tile.y)
        return None
    
    def update_visitor_positions(self):
        """Met à jour les positions des visiteurs dans la queue"""
        # Réorganiser tous les visiteurs dans les tuiles
        self._distribute_visitors_across_tiles()


class SimpleQueueManager:
    """Gestionnaire simple des files d'attente"""
    def __init__(self):
        self.queue_paths: List[SimpleQueuePath] = []
        self.ride_queues: Dict['Ride', SimpleQueuePath] = {}
        self.tile_cache: Dict[Tuple[int, int], SimpleQueueTile] = {}
    
    def create_queue_path(self, start_pos: Tuple[int, int], 
                         direction: str, length: int, 
                         connected_ride: Optional['Ride'] = None) -> SimpleQueuePath:
        """Crée une file d'attente simple en ligne droite"""
        tiles = []
        x, y = start_pos
        
        for i in range(length):
            # Créer ou récupérer la tuile
            tile = self._get_or_create_tile(x, y)
            tiles.append(tile)
            
            # Avancer selon la direction
            if direction == 'E':
                x += 1
            elif direction == 'W':
                x -= 1
            elif direction == 'S':
                y += 1
            elif direction == 'N':
                y -= 1
        
        # Créer le chemin de queue
        queue_path = SimpleQueuePath(tiles, connected_ride)
        self.queue_paths.append(queue_path)
        
        if connected_ride:
            self.ride_queues[connected_ride] = queue_path
        
        DebugConfig.log('queues', f"Created queue path with {length} tiles starting at {start_pos}")
        return queue_path
    
    def _get_or_create_tile(self, x: int, y: int) -> SimpleQueueTile:
        """Crée ou récupère une tuile de queue"""
        pos = (x, y)
        if pos not in self.tile_cache:
            self.tile_cache[pos] = SimpleQueueTile(x, y)
        return self.tile_cache[pos]
    
    def find_queue_paths(self, grid) -> List[SimpleQueuePath]:
        """Trouve tous les chemins de queue dans la grille"""
        from .map import TILE_QUEUE_PATH
        
        visited = set()
        queue_paths = []
        queue_tile_count = 0
        
        # Compter les tuiles de queue
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.get(x, y) == TILE_QUEUE_PATH:
                    queue_tile_count += 1
        
        # DebugConfig.log('queues', f"Found {queue_tile_count} queue tiles in grid")  # Too frequent
        
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.get(x, y) == TILE_QUEUE_PATH and (x, y) not in visited:
                    DebugConfig.log('queues', f"Starting new queue path at ({x}, {y})")
                    # Trouver un nouveau chemin de queue
                    tiles = self._trace_queue_path(grid, x, y, visited)
                    if tiles:
                        DebugConfig.log('queues', f"Created queue path with {len(tiles)} tiles")
                        # Créer le chemin de queue
                        queue_path = SimpleQueuePath(tiles)
                        queue_paths.append(queue_path)
        
        # Mettre à jour la liste des chemins
        self.queue_paths = queue_paths
        
        # DebugConfig.log('queues', f"Found {len(queue_paths)} queue paths")  # Too frequent
        return queue_paths
    
    def _trace_queue_path(self, grid, start_x: int, start_y: int, visited: Set[Tuple[int, int]]) -> List[SimpleQueueTile]:
        """Trace un chemin de queue connecté"""
        from .map import TILE_QUEUE_PATH
        
        stack = [(start_x, start_y)]
        tiles = []
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or not grid.in_bounds(x, y) or grid.get(x, y) != TILE_QUEUE_PATH:
                continue
            
            visited.add((x, y))
            tile = self._get_or_create_tile(x, y)
            
            # Déterminer l'orientation de la tuile
            tile.orientation = self._determine_tile_orientation(grid, x, y)
            
            tiles.append(tile)
            
            # Ajouter les tuiles adjacentes
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and grid.in_bounds(nx, ny) and grid.get(nx, ny) == TILE_QUEUE_PATH:
                    stack.append((nx, ny))
        
        return tiles
    
    def _determine_tile_orientation(self, grid, x: int, y: int) -> str:
        """Détermine l'orientation d'une tuile de queue"""
        from .map import TILE_QUEUE_PATH
        
        # Compter les tuiles de queue adjacentes horizontalement et verticalement
        horizontal_neighbors = 0
        vertical_neighbors = 0
        
        # Vérifier les voisins horizontaux (gauche et droite)
        if grid.in_bounds(x-1, y) and grid.get(x-1, y) == TILE_QUEUE_PATH:
            horizontal_neighbors += 1
        if grid.in_bounds(x+1, y) and grid.get(x+1, y) == TILE_QUEUE_PATH:
            horizontal_neighbors += 1
            
        # Vérifier les voisins verticaux (haut et bas)
        if grid.in_bounds(x, y-1) and grid.get(x, y-1) == TILE_QUEUE_PATH:
            vertical_neighbors += 1
        if grid.in_bounds(x, y+1) and grid.get(x, y+1) == TILE_QUEUE_PATH:
            vertical_neighbors += 1
        
        # Si plus de voisins horizontaux, c'est horizontal
        if horizontal_neighbors > vertical_neighbors:
            return "horizontal"
        elif vertical_neighbors > horizontal_neighbors:
            return "vertical"
        else:
            # Par défaut, horizontal
            return "horizontal"
    
    def get_queue_for_ride(self, ride: 'Ride') -> Optional[SimpleQueuePath]:
        """Retourne la file d'attente pour une attraction"""
        DebugConfig.log('queues', f"Looking for queue for ride {ride.defn.name}")
        queue_path = self.ride_queues.get(ride)
        if queue_path:
            DebugConfig.log('queues', f"Found queue for ride {ride.defn.name}")
        else:
            DebugConfig.log('queues', f"No queue found for ride {ride.defn.name}")
        return queue_path
    
    def connect_queue_to_ride(self, queue_path: SimpleQueuePath, ride: 'Ride'):
        """Connecte une file d'attente à une attraction"""
        queue_path.connected_ride = ride
        self.ride_queues[ride] = queue_path
        DebugConfig.log('queues', f"Connected queue to ride {ride.defn.name}")
    
    def can_visitor_enter_queue(self, ride: 'Ride') -> bool:
        """Vérifie si un visiteur peut entrer dans la queue d'une attraction"""
        queue_path = self.get_queue_for_ride(ride)
        if not queue_path:
            return False
        return queue_path.can_enter()
    
    def add_visitor_to_queue(self, visitor: 'Guest', ride: 'Ride') -> bool:
        """Ajoute un visiteur à la queue d'une attraction"""
        DebugConfig.log('queues', f"Attempting to add visitor {visitor.id} to queue for ride {ride.defn.name}")
        queue_path = self.get_queue_for_ride(ride)
        if not queue_path:
            DebugConfig.log('queues', f"No queue found for ride {ride.defn.name}")
            return False
        DebugConfig.log('queues', f"Found queue for ride {ride.defn.name}, adding visitor {visitor.id}")
        success = queue_path.add_visitor(visitor)
        if success:
            DebugConfig.log('queues', f"Visitor {visitor.id} successfully added to queue")
        else:
            DebugConfig.log('queues', f"Failed to add visitor {visitor.id} to queue")
        return success
    
    def remove_visitor_from_queue(self, visitor: 'Guest'):
        """Retire un visiteur de sa queue actuelle"""
        if visitor.current_queue:
            visitor.current_queue.remove_visitor(visitor)
            visitor.current_queue = None
            visitor.current_queue_tile = None
            visitor.queue_position = -1
    
    def get_visitor_queue_position(self, visitor: 'Guest') -> Optional[Tuple[int, int]]:
        """Retourne la position du visiteur dans sa queue"""
        if visitor.current_queue_tile:
            return (visitor.current_queue_tile.x, visitor.current_queue_tile.y)
        return None
    
    def can_visitor_board_ride(self, visitor: 'Guest') -> bool:
        """Vérifie si un visiteur peut monter dans l'attraction"""
        if visitor.current_queue:
            return visitor.current_queue.can_board_ride(visitor)
        return False
    
    def board_visitor_on_ride(self, visitor: 'Guest') -> bool:
        """Fait monter un visiteur dans l'attraction"""
        if not self.can_visitor_board_ride(visitor):
            return False
        
        # Faire monter dans l'attraction
        if visitor.current_queue and visitor.current_queue.connected_ride:
            ride = visitor.current_queue.connected_ride
            success = ride.board_visitor(visitor)
            if success:
                # Retirer de la queue seulement après avoir monté avec succès
                self.remove_visitor_from_queue(visitor)
                visitor.current_ride = ride
                visitor.state = "riding"
                visitor.ride_timer = 0.0
                DebugConfig.log('queues', f"Visitor {visitor.id} boarded ride {ride.defn.name}")
                return True
        
        return False
    
    def update_queue_system(self, grid):
        """Met à jour le système de queue"""
        # Trouver tous les chemins de queue
        self.find_queue_paths(grid)
        
        # Connecter les queues aux attractions
        self._connect_queues_to_rides()
        
        # Mettre à jour les positions des visiteurs dans toutes les queues
        for queue_path in self.queue_paths:
            queue_path.update_visitor_positions()
    
    def _connect_queues_to_rides(self):
        """Connecte automatiquement les queues aux attractions"""
        # Cette méthode peut être étendue pour connecter automatiquement
        # les queues aux attractions proches
        pass
    
    def remove_queue_waypoint(self, x: int, y: int, grid):
        """Retire un waypoint de queue (pour compatibilité)"""
        # Pour compatibilité avec l'ancien système
        pos = (x, y)
        if pos in self.tile_cache:
            tile = self.tile_cache[pos]
            if tile.visitor:
                self.remove_visitor_from_queue(tile.visitor)
            del self.tile_cache[pos]
            DebugConfig.log('queues', f"Removed queue tile at {pos}")
    
    def orient_queue_waypoint(self, grid, x: int, y: int, direction: str):
        """Orient un waypoint de queue (pour compatibilité)"""
        # Pour compatibilité avec l'ancien système
        # Dans le système simple, l'orientation n'est pas nécessaire
        DebugConfig.log('queues', f"Orientation not needed in simple queue system at ({x}, {y})")
    
    def can_orient_waypoint(self, grid, x: int, y: int, direction: str) -> bool:
        """Vérifie si un waypoint peut être orienté (pour compatibilité)"""
        # Dans le système simple, l'orientation est toujours possible
        return True
    
    def evacuate_queue_for_broken_ride(self, ride: 'Ride'):
        """Évacue tous les visiteurs d'une queue pour une attraction cassée"""
        queue_path = self.get_queue_for_ride(ride)
        if queue_path:
            # Évacuer tous les visiteurs de cette queue
            visitors_to_evacuate = queue_path.visitors.copy()
            for visitor in visitors_to_evacuate:
                visitor.state = "wandering"
                visitor.target_ride = None
                visitor.current_queue = None
                visitor.current_queue_tile = None
                visitor.queue_position = -1
                visitor.tile_position = -1
                DebugConfig.log('queues', f"Evacuating visitor {visitor.id} from queue due to ride breakdown")
            
            # Vider la queue
            queue_path.visitors.clear()
            for tile in queue_path.tiles:
                tile.visitors.clear()
            
            DebugConfig.log('queues', f"Evacuated queue for broken ride {ride.defn.name}")