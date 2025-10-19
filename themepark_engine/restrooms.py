
from dataclasses import dataclass
from typing import List

@dataclass
class RestroomDef:
    id: str
    name: str
    build_cost: int
    usage_fee: int
    capacity: int
    sprite: str
    size: List[int]  # [width, height] in tiles

@dataclass
class Restroom:
    defn: RestroomDef
    x: int
    y: int
    connected_to_path: bool = False
    current_users: List = None  # List of guests currently using this restroom

    def __post_init__(self):
        if self.current_users is None:
            self.current_users = []

    def is_full(self) -> bool:
        """Check if restroom is at capacity"""
        return len(self.current_users) >= self.defn.capacity

    def add_user(self, guest):
        """Add a guest to the restroom"""
        if not self.is_full():
            self.current_users.append(guest)
            return True
        return False

    def remove_user(self, guest):
        """Remove a guest from the restroom"""
        if guest in self.current_users:
            self.current_users.remove(guest)
