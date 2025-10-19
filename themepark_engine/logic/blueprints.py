from dataclasses import dataclass
@dataclass
class RideBlueprint:
    id:str; name:str; size:tuple; entrance:tuple; exit:tuple
@dataclass
class ShopBlueprint:
    id:str; name:str; size:tuple; door:tuple
