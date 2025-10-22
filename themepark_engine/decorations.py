"""
Decoration system for OpenPark.
Decorations are purely cosmetic objects that enhance the visual appeal of the park.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DecorationDef:
    """Definition of a decoration type"""
    id: str
    name: str
    cost: int
    sprite: str
    size: List[int]  # [width, height]
    walkable: bool  # Whether guests/employees can walk through it


class Decoration:
    """Instance of a decoration in the park"""

    def __init__(self, defn: DecorationDef, x: int, y: int):
        self.defn = defn
        self.x = x
        self.y = y
        self.width, self.height = defn.size

    def get_sprite_path(self):
        """Get the sprite path for rendering"""
        return self.defn.sprite

    def to_dict(self):
        """Serialize decoration to dictionary for saving"""
        return {
            'id': self.defn.id,
            'x': self.x,
            'y': self.y
        }

    @staticmethod
    def from_dict(data, deco_defs):
        """Deserialize decoration from dictionary"""
        defn = deco_defs.get(data['id'])
        if not defn:
            return None
        return Decoration(defn, data['x'], data['y'])
