
from pathlib import Path
import pygame
BASE = Path(__file__).resolve().parent
PLACEHOLDERS = BASE / 'assets' / 'placeholders'
ORIGINAL = BASE / 'assets' / 'original'
_cache = {}
COLORS = {
    'tile_grass': (60,160,60),
    'tile_walk': (180,180,180),
    'tile_shop': (190,160,120),
    'ride_carousel': (230,200,80),
    'ride_bumper': (200,80,80),
    'shop_soda': (80,160,220),
    'shop_icecream': (240,180,220),
    'shop_restaurant': (160,100,60),
    'shop_gift': (120,80,160),
    'shop_entrance': (100,200,100),
    'shop_disconnected': (255,100,100),
    'employee_engineer': (100,100,255),
    'employee_maintenance': (255,200,100),
    'employee_security': (100,255,100),
    'employee_mascot': (255,100,255),
    'ride_broken': (255,0,0),
    'employee_working': (0,255,0),
    'employee_moving': (0,150,255),
    'guest': (255,255,255),
    'bin': (60,179,113),  # Vert pour les poubelles
    'litter': (139,90,43),  # Marron pour les détritus
}

def _try_load(path: Path):
    try:
        surf = pygame.image.load(path.as_posix())
        return surf.convert_alpha() if surf.get_masks()[3] else surf.convert()
    except Exception:
        return None

def _fallback_surface(key: str, size=(32, 32)):
    color = COLORS.get(key, (200, 50, 50))
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)
    return surf

def load_image(name: str) -> pygame.Surface:
    if name in _cache:
        return _cache[name]
    p = Path(name)
    candidates = []
    if p.suffix:
        candidates += [ORIGINAL / name, PLACEHOLDERS / name]
    else:
        for ext in ('.png', '.bmp'):
            candidates += [ORIGINAL / f"{name}{ext}", PLACEHOLDERS / f"{name}{ext}"]
    for c in candidates:
        if c.exists():
            surf = _try_load(c)
            if surf:
                _cache[name] = surf
                return surf
    surf = _fallback_surface(name)
    _cache[name] = surf
    return surf
