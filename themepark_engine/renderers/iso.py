
from __future__ import annotations
import pygame, math
from dataclasses import dataclass

@dataclass
class IsoCamera:
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0
    def pan(self, dx, dy): self.x += dx; self.y += dy
    def set_zoom(self, z): self.zoom = max(0.5, min(3.0, z))

class IsoRenderer:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, tile_w=72, tile_h=36, oblique_tilt=10.0):
        self.screen = screen
        self.font = font
        self.base_tile_w = float(tile_w)
        self.base_tile_h = float(tile_h)
        # OBLIQUE param (φ): tilt angle controlling skew: tanφ
        self.oblique_tilt = float(oblique_tilt)
        self.camera = IsoCamera(0,0,1.0)
        self.origin = (screen.get_width()//2, 96)
        self._recalc()
        self._rebuild_surfaces()

    def _recalc(self):
        self._tw = max(2, int(self.base_tile_w * self.camera.zoom))
        self._th = max(2, int(self.base_tile_h * self.camera.zoom))
        # oblique skew
        self._skew = math.tan(math.radians(self.oblique_tilt))
        self._skew = max(-5.0, min(5.0, self._skew))

    def set_projection(self, tile_w:int, tile_h:int):
        self.base_tile_w = float(tile_w)
        self.base_tile_h = float(tile_h)
        self._recalc(); self._rebuild_surfaces()


    def set_oblique_tilt(self, tilt_deg: float):
        self.oblique_tilt = float(tilt_deg)
        self._recalc(); self._rebuild_surfaces()

    def tile_size(self):
        return (self._tw, self._th)

    # --- Basis vectors for tile surface polygon ---
    def _basis_vectors(self):
        tw, th = self.tile_size()
        # oblique: x horizontal, y skewed right by skew*tw and down by th
        v1 = (tw, 0.0)
        v2 = (self._skew*tw, th)
        return v1, v2

    def _build_tile(self, color_rgba, outline_rgba=(0,0,0,120)):
        v1, v2 = self._basis_vectors()
        def add(p,q): return (p[0]+q[0], p[1]+q[1])
        def mul(p,s): return (p[0]*s, p[1]*s)
        pts = [ add(mul(v1,0.5), mul(v2,0.5)), add(mul(v1,-0.5), mul(v2,0.5)),
                add(mul(v1,-0.5), mul(v2,-0.5)), add(mul(v1,0.5), mul(v2,-0.5)) ]
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
        w = int(math.ceil(maxx - minx + 2)); h = int(math.ceil(maxy - miny + 2))
        surf = pygame.Surface((w,h), pygame.SRCALPHA)
        pts_surf = [ (p[0]-minx+1, p[1]-miny+1) for p in pts ]
        pygame.draw.polygon(surf, color_rgba, pts_surf)
        pygame.draw.polygon(surf, outline_rgba, pts_surf, 1)
        return surf, (minx - 1, miny - 1)
    
    def _build_arrow(self, direction: str):
        """Build an arrow surface for the given direction"""
        tw, th = self.tile_size()
        surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        
        # Couleur de la flèche - plus visible
        color = (255, 255, 0, 255)  # Jaune vif, opaque
        outline_color = (0, 0, 0, 255)  # Contour noir
        
        # Points de la flèche selon la direction - plus grande
        center_x, center_y = tw // 2, th // 2
        size = min(tw, th) // 3  # Plus grande que avant (était //4)
        
        if direction == 'N':
            # Flèche vers le haut
            points = [
                (center_x, center_y - size),
                (center_x - size//2, center_y - size//3),
                (center_x - size//4, center_y - size//3),
                (center_x - size//4, center_y),
                (center_x + size//4, center_y),
                (center_x + size//4, center_y - size//3),
                (center_x + size//2, center_y - size//3)
            ]
        elif direction == 'S':
            # Flèche vers le bas
            points = [
                (center_x, center_y + size),
                (center_x - size//2, center_y + size//3),
                (center_x - size//4, center_y + size//3),
                (center_x - size//4, center_y),
                (center_x + size//4, center_y),
                (center_x + size//4, center_y + size//3),
                (center_x + size//2, center_y + size//3)
            ]
        elif direction == 'E':
            # Flèche vers la droite
            points = [
                (center_x + size, center_y),
                (center_x + size//3, center_y - size//2),
                (center_x + size//3, center_y - size//4),
                (center_x, center_y - size//4),
                (center_x, center_y + size//4),
                (center_x + size//3, center_y + size//4),
                (center_x + size//3, center_y + size//2)
            ]
        else:  # 'W'
            # Flèche vers la gauche
            points = [
                (center_x - size, center_y),
                (center_x - size//3, center_y - size//2),
                (center_x - size//3, center_y - size//4),
                (center_x, center_y - size//4),
                (center_x, center_y + size//4),
                (center_x - size//3, center_y + size//4),
                (center_x - size//3, center_y + size//2)
            ]
        
        # Dessiner la flèche avec contour
        pygame.draw.polygon(surf, color, points)
        pygame.draw.polygon(surf, outline_color, points, 2)
        return surf

    def _rebuild_surfaces(self):
        self.grass_tile, self.grass_off = self._build_tile((60,160,60,255))
        self.walk_tile,  self.walk_off  = self._build_tile((180,180,180,255))
        self.entrance_tile, self.entrance_off = self._build_tile((0,255,0,255))  # Green for entrance
        self.exit_tile, self.exit_off = self._build_tile((255,0,0,255))  # Red for exit
        self.ride_footprint_tile, self.ride_footprint_off = self._build_tile((100,100,200,180))  # Blue for ride footprint
        self.shop_entrance_tile, self.shop_entrance_off = self._build_tile((0,255,100,255))  # Light green for shop entrance
        self.shop_footprint_tile, self.shop_footprint_off = self._build_tile((200,150,100,180))  # Brown for shop footprint
        self.queue_tile, self.queue_off = self._build_tile((255,165,0,255))  # Orange for queue paths
        self.park_entrance_tile, self.park_entrance_off = self._build_tile((255,215,0,255))  # Gold for park entrance
        self.restroom_footprint_tile, self.restroom_footprint_off = self._build_tile((180,130,200,180))  # Purple/lavender for restroom footprint
        self.bin_tile, self.bin_off = self._build_tile((100,200,100,200))  # Green for bins
        self.hl_ok,      self.hl_ok_off = self._build_tile((255,255,0,80))
        self.hl_bad,     self.hl_bad_off= self._build_tile((255,0,0,80))
        self.hl_preview, self.hl_preview_off = self._build_tile((0,255,255,60))
        
        # Flèches directionnelles pour les queues
        self.arrow_north = self._build_arrow('N')
        self.arrow_south = self._build_arrow('S')
        self.arrow_east = self._build_arrow('E')
        self.arrow_west = self._build_arrow('W')

    # --- Mapping ---
    def grid_to_screen(self, gx:int, gy:int):
        tw, th = self.tile_size()
        sx = (gx + gy * self._skew) * tw - self.camera.x + self.origin[0]
        sy = gy * th - self.camera.y + self.origin[1]
        return sx, sy

    def screen_to_grid(self, sx:int, sy:int):
        tw, th = self.tile_size()
        ox = sx + self.camera.x - self.origin[0]
        oy = sy + self.camera.y - self.origin[1]
        gy = oy / th
        gx = (ox / tw) - gy * self._skew
        return round(gx), round(gy)

    # --- Depth ordering ---
    def _depth_key(self, x:int, y:int):
        # oblique: draw by increasing y then x for stability
        return (y, x)

    def _blit_tile(self, surf, off, sx, sy):
        self.screen.blit(surf, (sx + off[0], sy + off[1]))

    def draw_map(self, grid):
        coords = [(x,y) for y in range(grid.height) for x in range(grid.width)]
        coords.sort(key=lambda p: self._depth_key(p[0], p[1]))
        for x,y in coords:
            sx, sy = self.grid_to_screen(x, y)
            t = grid.get(x, y)
            if t==1: self._blit_tile(self.walk_tile, self.walk_off, sx, sy)
            elif t==2: self._blit_tile(self.entrance_tile, self.entrance_off, sx, sy)
            elif t==3: self._blit_tile(self.exit_tile, self.exit_off, sx, sy)
            elif t==4: self._blit_tile(self.ride_footprint_tile, self.ride_footprint_off, sx, sy)
            elif t==5: self._blit_tile(self.queue_tile, self.queue_off, sx, sy)
            elif t==6: self._blit_tile(self.shop_entrance_tile, self.shop_entrance_off, sx, sy)
            elif t==7: self._blit_tile(self.shop_footprint_tile, self.shop_footprint_off, sx, sy)
            elif t==8: self._blit_tile(self.park_entrance_tile, self.park_entrance_off, sx, sy)
            elif t==9: self._blit_tile(self.restroom_footprint_tile, self.restroom_footprint_off, sx, sy)
            elif t==10: self._blit_tile(self.bin_tile, self.bin_off, sx, sy)
            else: self._blit_tile(self.grass_tile, self.grass_off, sx, sy)

    def draw_objects(self, objects):
        objects.sort(key=lambda t: self._depth_key(t[1][0], t[1][1]))
        for spr,(x,y) in objects:
            sx, sy = self.grid_to_screen(x, y)
            self.screen.blit(spr, (sx - spr.get_width()//2, sy - spr.get_height()))

    def draw_highlight(self, gx, gy, ok=True, preview=False):
        sx, sy = self.grid_to_screen(gx, gy)
        if preview:
            img, off = (self.hl_preview, self.hl_preview_off)
        else:
            img, off = (self.hl_ok, self.hl_ok_off) if ok else (self.hl_bad, self.hl_bad_off)
        self._blit_tile(img, off, sx, sy)
    
    def draw_ride_preview(self, gx, gy, width, height, ok=True):
        """Draw a preview of a multi-tile ride"""
        for x in range(gx, gx + width):
            for y in range(gy, gy + height):
                self.draw_highlight(x, y, ok=ok, preview=True)
    
    def draw_queue_arrows(self, queue_paths, show_arrows=True):
        """Draw queue path indicators"""
        if not show_arrows:
            return
        
        total_tiles = 0
        occupied_tiles = 0
        
        for queue_path in queue_paths:
            for tile in queue_path.tiles:
                total_tiles += 1
                sx, sy = self.grid_to_screen(tile.x, tile.y)
                
                # Dessiner un indicateur de queue
                if tile.is_entrance:
                    # Entrée de queue - cercle vert
                    pygame.draw.circle(self.screen, (0, 255, 0), (sx + 16, sy + 16), 8, 2)
                elif tile.is_exit:
                    # Sortie de queue - cercle rouge
                    pygame.draw.circle(self.screen, (255, 0, 0), (sx + 16, sy + 16), 8, 2)
                elif len(tile.visitors) > 0:
                    # Tuile occupée - cercle jaune
                    occupied_tiles += 1
                    pygame.draw.circle(self.screen, (255, 255, 0), (sx + 16, sy + 16), 6, 2)
                else:
                    # Tuile libre - petit point
                    pygame.draw.circle(self.screen, (128, 128, 128), (sx + 16, sy + 16), 3)
                
                # Ajouter un petit indicateur de connexion si la queue est connectée à un manège
                if queue_path.connected_ride:
                    # Dessiner un petit cercle vert pour indiquer la connexion
                    center_x = sx + self.tile_size()[0] // 2
                    center_y = sy + self.tile_size()[1] // 2
                    pygame.draw.circle(self.screen, (0, 255, 0, 200), (center_x, center_y), 3)
        
        # Debug info only when there are tiles but no occupied ones
        if total_tiles > 0 and occupied_tiles == 0:
            # Removed excessive debug print that was causing crashes
            pass
    
    def draw_cardinal_points(self):
        """Draw cardinal points on screen corners"""
        # Define corner positions and their corresponding cardinal points
        corners = [
            (10, 10, "NW"),      # Top-left: Northwest
            (self.screen.get_width() - 50, 10, "NE"),  # Top-right: Northeast
            (10, self.screen.get_height() - 30, "SW"),  # Bottom-left: Southwest
            (self.screen.get_width() - 50, self.screen.get_height() - 30, "SE")  # Bottom-right: Southeast
        ]
        
        # Draw cardinal points
        for x, y, cardinal in corners:
            # Create a small rectangle background
            rect = pygame.Rect(x, y, 40, 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), rect)  # Semi-transparent black background
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)  # White border
            
            # Draw the cardinal point text
            text_surface = self.font.render(cardinal, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def draw_direction_legend(self):
        """Draw a legend showing direction arrows"""
        # Position the legend in the top-right corner
        legend_x = self.screen.get_width() - 120
        legend_y = 50
        
        # Draw legend background
        legend_rect = pygame.Rect(legend_x, legend_y, 100, 120)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), legend_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), legend_rect, 2)
        
        # Draw direction arrows with labels
        directions = [
            (legend_x + 50, legend_y + 20, self.arrow_north, "N"),
            (legend_x + 50, legend_y + 80, self.arrow_south, "S"),
            (legend_x + 20, legend_y + 50, self.arrow_west, "W"),
            (legend_x + 80, legend_y + 50, self.arrow_east, "E")
        ]
        
        for x, y, arrow, label in directions:
            # Draw arrow
            arrow_rect = arrow.get_rect(center=(x, y))
            self.screen.blit(arrow, arrow_rect)
            
            # Draw label
            label_surface = self.font.render(label, True, (255, 255, 255))
            label_rect = label_surface.get_rect(center=(x, y + 25))
            self.screen.blit(label_surface, label_rect)
