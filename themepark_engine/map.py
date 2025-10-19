
TILE_GRASS = 0
TILE_WALK  = 1
TILE_RIDE_ENTRANCE = 2
TILE_RIDE_EXIT = 3
TILE_RIDE_FOOTPRINT = 4
TILE_QUEUE_PATH = 5
TILE_SHOP_ENTRANCE = 6
TILE_SHOP_FOOTPRINT = 7
class MapGrid:
    def __init__(self,w,h):
        self.width=w; self.height=h
        self.tiles=[TILE_GRASS]*(w*h)
    def idx(self,x,y): return y*self.width+x
    def in_bounds(self,x,y): return 0<=x<self.width and 0<=y<self.height
    def get(self,x,y): return self.tiles[self.idx(x,y)]
    def set(self,x,y,v): self.tiles[self.idx(x,y)]=v
    def walkable(self,x,y): return self.get(x,y) in (TILE_WALK, TILE_RIDE_ENTRANCE, TILE_RIDE_EXIT, TILE_QUEUE_PATH, TILE_SHOP_ENTRANCE)
    def walkable_for_engineers(self,x,y): return True  # Engineers can walk on any tile
