
from heapq import heappush, heappop

def heuristic(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def astar(grid,start,goal):
    open=[(0,start)]; came={start:None}; g={start:0}
    while open:
        _,cur=heappop(open)
        if cur==goal:
            path=[]
            while cur is not None: path.append(cur); cur=came[cur]
            return list(reversed(path))
        x,y=cur
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if not grid.in_bounds(nx,ny) or (not grid.walkable(nx,ny) and (nx,ny)!=goal):
                continue
            ng=g[cur]+1
            if ng<g.get((nx,ny),10**9):
                g[(nx,ny)]=ng
                heappush(open,(ng+heuristic((nx,ny),goal),(nx,ny)))
                came[(nx,ny)]=cur
    return None

def astar_for_engineers(grid,start,goal):
    """A* pathfinding specifically for engineers who can walk on any tile"""
    open=[(0,start)]; came={start:None}; g={start:0}
    while open:
        _,cur=heappop(open)
        if cur==goal:
            path=[]
            while cur is not None: path.append(cur); cur=came[cur]
            return list(reversed(path))
        x,y=cur
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if not grid.in_bounds(nx,ny):
                continue
            ng=g[cur]+1
            if ng<g.get((nx,ny),10**9):
                g[(nx,ny)]=ng
                heappush(open,(ng+heuristic((nx,ny),goal),(nx,ny)))
                came[(nx,ny)]=cur
    return None
