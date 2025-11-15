"""
Pathfinding module with A* algorithm and optimizations
Includes caching and frame-limited processing for better performance
"""

from heapq import heappush, heappop
from typing import Tuple, List, Optional, Callable


# ==================== PATHFINDING CACHE ====================

class PathCache:
    """Cache for pathfinding results to avoid recalculating the same paths"""

    def __init__(self, max_size: int = 1000, max_age: int = 120):
        """
        Args:
            max_size: Maximum number of cached paths
            max_age: Maximum age in frames before cache entry expires
        """
        self.cache = {}  # {(start, goal): (path, age)}
        self.max_size = max_size
        self.max_age = max_age
        self.current_frame = 0

    def get(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Get cached path if available and not expired"""
        key = (start, goal)
        if key in self.cache:
            path, frame_created = self.cache[key]
            age = self.current_frame - frame_created

            if age < self.max_age:
                return path
            else:
                # Expired, remove from cache
                del self.cache[key]

        return None

    def put(self, start: Tuple[int, int], goal: Tuple[int, int], path: List[Tuple[int, int]]):
        """Store path in cache"""
        key = (start, goal)

        # If cache is full, remove oldest entries
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = (path, self.current_frame)

    def _evict_oldest(self):
        """Remove 10% oldest entries to make room"""
        if not self.cache:
            return

        # Sort by age and remove oldest 10%
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
        num_to_remove = max(1, len(sorted_items) // 10)

        for i in range(num_to_remove):
            del self.cache[sorted_items[i][0]]

    def invalidate_around(self, x: int, y: int, radius: int = 3):
        """Invalidate cache entries near a position (when grid changes)"""
        to_remove = []

        for (start, goal) in self.cache.keys():
            # Check if start or goal is near the changed position
            if (abs(start[0] - x) <= radius and abs(start[1] - y) <= radius) or \
               (abs(goal[0] - x) <= radius and abs(goal[1] - y) <= radius):
                to_remove.append((start, goal))

        for key in to_remove:
            del self.cache[key]

    def clear(self):
        """Clear all cache"""
        self.cache.clear()

    def tick(self):
        """Call once per frame to update frame counter"""
        self.current_frame += 1


# ==================== PATHFINDING QUEUE ====================

class PathfindingQueue:
    """Queue system to limit pathfinding calculations per frame"""

    def __init__(self, max_per_frame: int = 10):
        """
        Args:
            max_per_frame: Maximum number of paths to calculate per frame
        """
        self.queue = []  # List of (priority, entity, start, goal, callback)
        self.max_per_frame = max_per_frame
        self.next_id = 0  # For FIFO ordering when priorities are equal

    def request_path(self, entity, start: Tuple[int, int], goal: Tuple[int, int],
                    callback: Callable, priority: int = 0):
        """
        Request a path calculation

        Args:
            entity: The entity requesting the path (for reference)
            start: Start position
            goal: Goal position
            callback: Function to call with (entity, path) when done
            priority: Lower number = higher priority (0 = highest)
        """
        # Use negative priority for heapq (min-heap)
        self.queue.append((-priority, self.next_id, entity, start, goal, callback))
        self.next_id += 1

    def process(self, grid, path_cache: PathCache, astar_func: Callable) -> int:
        """
        Process up to max_per_frame path requests

        Returns:
            Number of paths calculated this frame
        """
        if not self.queue:
            return 0

        # Sort by priority (highest first)
        self.queue.sort()

        processed = 0

        while self.queue and processed < self.max_per_frame:
            _, _, entity, start, goal, callback = self.queue.pop(0)

            # Try to get from cache first
            path = path_cache.get(start, goal)

            if path is None:
                # Calculate new path
                path = astar_func(grid, start, goal)

                # Cache it
                if path:
                    path_cache.put(start, goal, path)

            # Call callback with result
            callback(entity, path)
            processed += 1

        return processed

    def clear(self):
        """Clear all pending requests"""
        self.queue.clear()

    def size(self) -> int:
        """Get number of pending requests"""
        return len(self.queue)


# ==================== GLOBAL INSTANCES ====================

# Global cache and queue instances
_path_cache = PathCache(max_size=1000, max_age=120)
_pathfinding_queue = PathfindingQueue(max_per_frame=10)


# ==================== A* ALGORITHM ====================

def heuristic(a, b):
    """Manhattan distance heuristic"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """
    Standard A* pathfinding for regular entities

    Args:
        grid: MapGrid instance
        start: (x, y) start position
        goal: (x, y) goal position

    Returns:
        List of (x, y) positions from start to goal, or None if no path found
    """
    open = [(0, start)]
    came = {start: None}
    g = {start: 0}

    while open:
        _, cur = heappop(open)

        if cur == goal:
            # Reconstruct path
            path = []
            while cur is not None:
                path.append(cur)
                cur = came[cur]
            return list(reversed(path))

        x, y = cur

        # 4-directional movement (no diagonals - authentic 90s style!)
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if not grid.in_bounds(nx, ny) or (not grid.walkable(nx, ny) and (nx, ny) != goal):
                continue

            ng = g[cur] + 1

            if ng < g.get((nx, ny), 10**9):
                g[(nx, ny)] = ng
                heappush(open, (ng + heuristic((nx, ny), goal), (nx, ny)))
                came[(nx, ny)] = cur

    return None


def astar_for_engineers(grid, start, goal):
    """
    A* pathfinding specifically for engineers who can walk on any tile

    Args:
        grid: MapGrid instance
        start: (x, y) start position
        goal: (x, y) goal position

    Returns:
        List of (x, y) positions from start to goal, or None if no path found
    """
    open = [(0, start)]
    came = {start: None}
    g = {start: 0}

    while open:
        _, cur = heappop(open)

        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur)
                cur = came[cur]
            return list(reversed(path))

        x, y = cur

        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if not grid.in_bounds(nx, ny):
                continue

            ng = g[cur] + 1

            if ng < g.get((nx, ny), 10**9):
                g[(nx, ny)] = ng
                heappush(open, (ng + heuristic((nx, ny), goal), (nx, ny)))
                came[(nx, ny)] = cur

    return None


# ==================== OPTIMIZED API ====================

def get_path_cached(grid, start: Tuple[int, int], goal: Tuple[int, int],
                   for_engineers: bool = False) -> Optional[List[Tuple[int, int]]]:
    """
    Get path with caching (synchronous)

    Args:
        grid: MapGrid instance
        start: Start position
        goal: Goal position
        for_engineers: Use engineer pathfinding (can walk on any tile)

    Returns:
        Path as list of positions, or None if no path
    """
    # Try cache first
    path = _path_cache.get(start, goal)

    if path is None:
        # Calculate new path
        astar_func = astar_for_engineers if for_engineers else astar
        path = astar_func(grid, start, goal)

        # Cache result
        if path:
            _path_cache.put(start, goal, path)

    return path


def request_path_async(entity, start: Tuple[int, int], goal: Tuple[int, int],
                      callback: Callable, priority: int = 0, for_engineers: bool = False):
    """
    Request path asynchronously (will be calculated over multiple frames)

    Args:
        entity: Entity requesting the path
        start: Start position
        goal: Goal position
        callback: Function(entity, path) to call when path is ready
        priority: Lower number = higher priority (0 = highest)
        for_engineers: Use engineer pathfinding
    """
    astar_func = astar_for_engineers if for_engineers else astar

    # Wrap the astar function to match the queue's expected signature
    def wrapped_astar(grid, start, goal):
        return astar_func(grid, start, goal)

    _pathfinding_queue.request_path(entity, start, goal, callback, priority)


def process_pathfinding_queue(grid) -> int:
    """
    Process pathfinding queue (call once per frame)

    Returns:
        Number of paths calculated this frame
    """
    # Use astar as default (queue will specify if engineer pathfinding needed)
    return _pathfinding_queue.process(grid, _path_cache, astar)


def tick_pathfinding():
    """Call once per frame to update cache age"""
    _path_cache.tick()


def invalidate_cache_around(x: int, y: int, radius: int = 3):
    """Invalidate cache when grid changes"""
    _path_cache.invalidate_around(x, y, radius)


def clear_pathfinding_cache():
    """Clear all cached paths"""
    _path_cache.clear()


def get_queue_size() -> int:
    """Get number of pending pathfinding requests"""
    return _pathfinding_queue.size()
