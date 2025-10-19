"""
Debug configuration module for OpenPark
Centralized control of debug logging for different entities
"""

class DebugConfig:
    """Centralized debug configuration"""
    
    # Entity-specific debug flags (all disabled by default)
    GUESTS = False          # Guest movement, state changes, pathfinding
    RIDES = False           # Ride operations, boarding, launching
    QUEUES = False          # Queue system, visitor management
    ENGINE = True           # Engine updates, game loop
    EMPLOYEES = True        # Employee behavior, movement, work
    PATHFINDING = False     # A* pathfinding algorithm
    UI = False              # UI interactions, toolbar
    ECONOMY = False         # Economic calculations
    RENDERING = False       # Rendering operations
    LITTER = False          # Litter and bin system

    # Global debug flag
    ENABLED = True          # Master switch for all debug logs
    
    @classmethod
    def log(cls, category: str, message: str):
        """Log a debug message if the category is enabled"""
        if not cls.ENABLED:
            return
            
        category_upper = category.upper()
        if hasattr(cls, category_upper) and getattr(cls, category_upper):
            print(f"DEBUG [{category}]: {message}")
    
    @classmethod
    def enable_category(cls, category: str):
        """Enable debug for a specific category"""
        category_upper = category.upper()
        if hasattr(cls, category_upper):
            setattr(cls, category_upper, True)
            # Removed print to prevent crash
    
    @classmethod
    def disable_category(cls, category: str):
        """Disable debug for a specific category"""
        category_upper = category.upper()
        if hasattr(cls, category_upper):
            setattr(cls, category_upper, False)
            # Removed print to prevent crash
    
    @classmethod
    def enable_all(cls):
        """Enable all debug categories"""
        cls.ENABLED = True
        debug_categories = ['GUESTS', 'RIDES', 'QUEUES', 'ENGINE', 'PATHFINDING', 'UI', 'ECONOMY', 'RENDERING', 'EMPLOYEES']
        for category in debug_categories:
            setattr(cls, category, True)
        # Removed print to prevent crash
    
    @classmethod
    def disable_all(cls):
        """Disable all debug categories"""
        cls.ENABLED = False
        debug_categories = ['GUESTS', 'RIDES', 'QUEUES', 'ENGINE', 'PATHFINDING', 'UI', 'ECONOMY', 'RENDERING', 'EMPLOYEES']
        for category in debug_categories:
            setattr(cls, category, False)
        # Removed print to prevent crash
    
    @classmethod
    def get_status(cls):
        """Get current debug status"""
        status = {
            'enabled': cls.ENABLED,
            'categories': {}
        }
        debug_categories = ['GUESTS', 'RIDES', 'QUEUES', 'ENGINE', 'PATHFINDING', 'UI', 'ECONOMY', 'RENDERING', 'EMPLOYEES']
        for category in debug_categories:
            status['categories'][category.lower()] = getattr(cls, category)
        return status
