
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class ShopDef:
    id: str
    name: str
    build_cost: int
    base_price: int
    sprite: str
    size: List[int]  # [width, height] en tuiles
    entrance_cost: int = 0  # Coût pour placer l'entrée
    litter_type: str = "trash"  # Type de détritus généré (soda, trash, vomit)

@dataclass
class ShopEntrance:
    shop_id: str
    x: int
    y: int
    facing: str  # Direction vers laquelle l'entrée pointe

@dataclass
class Shop:
    defn: ShopDef
    x: int
    y: int
    facing: str = 'S'
    entrance: Optional[ShopEntrance] = None
    connected_to_path: bool = False
