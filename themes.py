# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: themes.py
# Description: Visual theme and rendering helpers. Draws backgrounds, tiles, hazards, goals, and environmental effects.
# ========================================

import pygame
import math
import random

TILE = 48

PALETTES = {
    "cave": {
        "bg_arch": (20, 16, 30),
        "bg_haze": (70, 40, 110, 16),
        "wall_fill": (32, 26, 45),
        "wall_border": (78, 60, 105),
        "plat_fill": (24, 20, 34),
        "plat_top": (170, 125, 200),
        "crumble_fill": (60, 50, 50),
        "crumble_border": (120, 100, 100),
        "crumble_line": (30, 20, 20),
        "spike_base": (40, 30, 45),
        "spike_tip": (180, 180, 200),
        "target_wall": (32, 26, 45),
        "bg_sky_top": (10, 6, 22),
        "bg_sky_bot": (24, 16, 84),
    },
    "snow": {
        "bg_arch": (150, 200, 230),
        "bg_haze": (200, 230, 255, 30),
        "wall_fill": (230, 245, 255),
        "wall_border": (150, 200, 250),
        "plat_fill": (180, 220, 250),
        "plat_top": (255, 255, 255),
        "crumble_fill": (170, 220, 250),
        "crumble_border": (100, 180, 220),
        "crumble_line": (150, 200, 240),
        "spike_base": (150, 200, 240),
        "spike_tip": (100, 180, 255),
        "target_wall": (230, 245, 255),
        "bg_sky_top": (160, 210, 240),
        "bg_sky_bot": (200, 240, 255),
    }
}


class SnowEffect:
    """Draws and updates a lightweight snow particle effect.
    
    Constructor Args:
        None."""
    def __init__(self):
        """Execute the __init__ operation.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.flakes = [
            [random.randrange(0, 2000), random.randrange(0, 1000), random.uniform(1, 3), random.uniform(2, 4)] for _ in
            range(150)]

    def draw(self, surf):
        """Execute the draw operation.
        
        Args:
            surf: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        w, h = surf.get_size()
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for flake in self.flakes:
            flake[1] += flake[2]
            flake[0] += random.uniform(-0.5, 0.5)
            # Important condition: this branch protects an alternate state or edge case.
            if flake[1] > h:
                flake[1] = random.randrange(-50, -10)
                flake[0] = random.randrange(0, w)
            pygame.draw.circle(surf, (255, 255, 255), (int(flake[0]), int(flake[1])), int(flake[3]))


_snow = SnowEffect()


# =========================
# Background images / transitions
# =========================

_BG_CACHE = {}


SNOW_BG_1 = "assets/swiss_bg_day.png"      
SNOW_BG_2 = "assets/swiss_bg_mid.png"      
SNOW_BG_3 = "assets/swiss_bg_sunset.png"   


BG_PARALLAX_SPEED = 0.03



BG_BLEND_CAM_DISTANCE = 42000.0


def _load_bg_scaled(path: str, size):
    """Load, scale, and cache a background image.
    
    Args:
        path: Input value required by this function.
        size: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    key = (path, size)
    # Important condition: this branch protects an alternate state or edge case.
    if key in _BG_CACHE:
        return _BG_CACHE[key]

    try:
        img = pygame.image.load(path).convert()
        img = pygame.transform.smoothscale(img, size)
        _BG_CACHE[key] = img
        return img
    except Exception:
        return None


def _draw_one_bg(target: pygame.Surface, bg: pygame.Surface, cam_x: float):
    """Draw a parallax background layer.
    
    Args:
        target: Input value required by this function.
        bg: Input value required by this function.
        cam_x: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    w, h = target.get_size()
    bg_w, bg_h = bg.get_size()

    max_shift = max(0, bg_w - w)

    # Important condition: this branch protects an alternate state or edge case.
    if max_shift > 0:
        shift = int(cam_x * BG_PARALLAX_SPEED)
        # Important condition: this branch protects an alternate state or edge case.
        if shift > max_shift:
            shift = max_shift
    else:
        shift = 0

    target.blit(bg, (-shift, 0))


def draw_bg_procedural(surf: pygame.Surface, gtime: float, cam_x: float, theme_name: str = "cave"):
    """Draw the themed background and optional parallax image blend.
    
    Args:
        surf: Input value required by this function.
        gtime: Input value required by this function.
        cam_x: Input value required by this function.
        theme_name: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    pal = PALETTES.get(theme_name, PALETTES["cave"])
    w, h = surf.get_size()

    # ============================================================
    
    # ============================================================
    if theme_name == "snow":
        bg_w = int(w * 1.28)
        bg_h = h
        size = (bg_w, bg_h)

        bg1 = _load_bg_scaled(SNOW_BG_1, size)
        bg2 = _load_bg_scaled(SNOW_BG_2, size)
        bg3 = _load_bg_scaled(SNOW_BG_3, size)

        # Important condition: this branch protects an alternate state or edge case.
        if bg1 is not None and bg2 is not None and bg3 is not None:
            
            progress = cam_x / BG_BLEND_CAM_DISTANCE
            # Important condition: this branch protects an alternate state or edge case.
            if progress < 0.0:
                progress = 0.0
            # Important condition: this branch protects an alternate state or edge case.
            if progress > 1.0:
                progress = 1.0

            base_layer = pygame.Surface((w, h), pygame.SRCALPHA)
            fade_layer = pygame.Surface((w, h), pygame.SRCALPHA)

            # Important condition: this branch protects an alternate state or edge case.
            if progress < 0.5:
                
                local_t = progress / 0.5
                _draw_one_bg(base_layer, bg1, cam_x)
                _draw_one_bg(fade_layer, bg2, cam_x)
                fade_layer.set_alpha(int(local_t * 255))
            else:
                
                local_t = (progress - 0.5) / 0.5
                _draw_one_bg(base_layer, bg2, cam_x)
                _draw_one_bg(fade_layer, bg3, cam_x)
                fade_layer.set_alpha(int(local_t * 255))

            surf.blit(base_layer, (0, 0))
            surf.blit(fade_layer, (0, 0))

            
            haze = pygame.Surface((w, h), pygame.SRCALPHA)
            haze.fill((230, 240, 255, 18))
            surf.blit(haze, (0, 0))

            _snow.draw(surf)
            return

    # ============================================================
    
    # ============================================================
    c_top = pal["bg_sky_top"]
    c_bot = pal["bg_sky_bot"]
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for y in range(0, h, 4):
        k = y / max(1, h - 1)
        r = int(c_top[0] * k + c_bot[0] * (1 - k))
        g = int(c_top[1] * k + c_bot[1] * (1 - k))
        b = int(c_top[2] * k + c_bot[2] * (1 - k))
        pygame.draw.rect(surf, (r, g, b), (0, y, w, 4))

    haze = pygame.Surface((w, h), pygame.SRCALPHA)
    haze.fill(pal["bg_haze"])
    surf.blit(haze, (0, 0))

    aw, gap = 96, 22
    offset = int(-cam_x * 0.18) % (aw + gap)
    x = -aw + offset
    base_y = int(h * 0.40)
    arch_h = int(h * 0.30)
    # Important loop: keeps running until the game, network, or UI state changes.
    while x < w + aw:
        pygame.draw.rect(surf, pal["bg_arch"], (x, base_y, aw, arch_h), border_radius=16)
        x += aw + gap

    # Important condition: this branch protects an alternate state or edge case.
    if theme_name == "snow":
        _snow.draw(surf)


def draw_tile(surf: pygame.Surface, ch: str, sx: int, sy: int, gtime: float, theme_name: str = "cave"):
    """Draw one level tile using the active theme palette.
    
    Args:
        surf: Input value required by this function.
        ch: Input value required by this function.
        sx: Input value required by this function.
        sy: Input value required by this function.
        gtime: Input value required by this function.
        theme_name: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    pal = PALETTES.get(theme_name, PALETTES["cave"])
    r = pygame.Rect(sx, sy, TILE, TILE)

    # Important condition: this branch protects an alternate state or edge case.
    if ch == "#":
        pygame.draw.rect(surf, pal["wall_fill"], r, border_radius=6)
        pygame.draw.rect(surf, pal["wall_border"], r, 2, border_radius=6)

    elif ch == "=":
        pygame.draw.rect(surf, pal["plat_fill"], (sx, sy + 10, TILE, TILE - 10), border_radius=6)
        pygame.draw.rect(surf, pal["plat_top"], (sx + 4, sy + 6, TILE - 8, 10), border_radius=4)

    elif ch == "C":
        pygame.draw.rect(surf, pal["crumble_fill"], r, border_radius=6)
        pygame.draw.rect(surf, pal["crumble_border"], r, 2, border_radius=6)
        lc = pal["crumble_line"]
        pygame.draw.line(surf, lc, (sx + 10, sy + 10), (sx + TILE - 15, sy + TILE - 10), 3)
        pygame.draw.line(surf, lc, (sx + 10, sy + TILE - 15), (sx + TILE // 2, sy + TILE // 2), 3)

    elif ch == "S":
        
        base_color = pal.get("spike_base", (50, 50, 60))
        pygame.draw.rect(surf, base_color, (sx, sy + TILE - 10, TILE, 10), border_radius=2)
        spike_color = pal.get("spike_tip", (200, 200, 210))

        pygame.draw.polygon(surf, spike_color,
                            [(sx + 2, sy + TILE - 10), (sx + 12, sy + 15), (sx + 22, sy + TILE - 10)])
        pygame.draw.polygon(surf, (255, 255, 255),
                            [(sx + 12, sy + 15), (sx + 15, sy + TILE - 10), (sx + 9, sy + TILE - 10)])

        pygame.draw.polygon(surf, spike_color,
                            [(sx + 14, sy + TILE - 10), (sx + 24, sy + 8), (sx + 34, sy + TILE - 10)])
        pygame.draw.polygon(surf, (255, 255, 255),
                            [(sx + 24, sy + 8), (sx + 27, sy + TILE - 10), (sx + 21, sy + TILE - 10)])

        pygame.draw.polygon(surf, spike_color,
                            [(sx + 26, sy + TILE - 10), (sx + 36, sy + 18), (sx + 46, sy + TILE - 10)])
        pygame.draw.polygon(surf, (255, 255, 255),
                            [(sx + 36, sy + 18), (sx + 39, sy + TILE - 10), (sx + 33, sy + TILE - 10)])

    elif ch == "*":
        
        cx, cy = sx + TILE // 2, sy + TILE // 2
        pygame.draw.rect(surf, (40, 40, 45), (cx - 8, cy, 16, TILE // 2), border_radius=3)
        pygame.draw.circle(surf, (30, 30, 35), (cx, cy), 14)
        rot = gtime * -20.0
        num_teeth = 8
        blade_color = (220, 220, 230)
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for i in range(num_teeth):
            angle = rot + i * (math.pi * 2 / num_teeth)
            outer_x = cx + math.cos(angle) * 24
            outer_y = cy + math.sin(angle) * 24
            inner_x1 = cx + math.cos(angle - 0.3) * 12
            inner_y1 = cy + math.sin(angle - 0.3) * 12
            inner_x2 = cx + math.cos(angle + 0.3) * 12
            inner_y2 = cy + math.sin(angle + 0.3) * 12
            pygame.draw.polygon(surf, blade_color, [(outer_x, outer_y), (inner_x1, inner_y1), (inner_x2, inner_y2)])
        pygame.draw.circle(surf, (150, 150, 160), (cx, cy), 16)
        pygame.draw.circle(surf, (255, 40, 40), (cx, cy), 6)
        pygame.draw.circle(surf, (255, 200, 100), (cx, cy), 2)

    elif ch == "O":
        pygame.draw.rect(surf, pal["target_wall"], r, border_radius=6)
        pygame.draw.circle(surf, (220, 40, 40), (sx + TILE // 2, sy + TILE // 2), 16)
        pygame.draw.circle(surf, (255, 255, 255), (sx + TILE // 2, sy + TILE // 2), 10)
        pygame.draw.circle(surf, (220, 40, 40), (sx + TILE // 2, sy + TILE // 2), 4)

    elif ch == "o":
        pygame.draw.rect(surf, pal["target_wall"], r, border_radius=6)
        pygame.draw.circle(surf, (40, 220, 80), (sx + TILE // 2, sy + TILE // 2), 16)
        pygame.draw.circle(surf, (255, 255, 255), (sx + TILE // 2, sy + TILE // 2), 10)
        pygame.draw.circle(surf, (40, 220, 80), (sx + TILE // 2, sy + TILE // 2), 4)

    elif ch == "X":
        pygame.draw.rect(surf, (38, 32, 54), r, border_radius=6)
        pygame.draw.rect(surf, (210, 160, 80), r, 2, border_radius=6)
        my = sy + TILE // 2
        pygame.draw.line(surf, (230, 190, 100), (sx + 6, my), (sx + TILE - 6, my), 2)
    elif ch == "R":
        pygame.draw.rect(surf, (220, 20, 20), r)
        pygame.draw.rect(surf, (100, 0, 0), r, 3)
    elif ch == "T":
        pygame.draw.rect(surf, (50, 100, 200), (sx + 4, sy + TILE - 12, TILE - 8, 12), border_radius=4)
        pygame.draw.rect(surf, (255, 100, 200), (sx, sy + TILE - 20, TILE, 8), border_radius=4)
        pygame.draw.line(surf, (150, 150, 150), (sx + 8, sy + TILE - 20), (sx + 8, sy + TILE - 12), 2)
        pygame.draw.line(surf, (150, 150, 150), (sx + TILE - 8, sy + TILE - 20), (sx + TILE - 8, sy + TILE - 12), 2)
    elif ch == ">":
        pygame.draw.rect(surf, (40, 40, 50), r, border_radius=4)
        pygame.draw.rect(surf, (100, 100, 120), r, 2, border_radius=4)
        offset = int(gtime * 60) % 20
        pygame.draw.polygon(surf, (200, 200, 50),
                            [(sx + offset, sy + 15), (sx + offset + 15, sy + TILE // 2), (sx + offset, sy + TILE - 15)])
    elif ch == "<":
        pygame.draw.rect(surf, (40, 40, 50), r, border_radius=4)
        pygame.draw.rect(surf, (100, 100, 120), r, 2, border_radius=4)
        offset = 20 - (int(gtime * 60) % 20)
        pygame.draw.polygon(surf, (200, 200, 50), [(sx + offset + 15, sy + 15), (sx + offset, sy + TILE // 2),
                                                   (sx + offset + 15, sy + TILE - 15)])
    elif ch == "W":
        offset = int(gtime * 100) % TILE
        pygame.draw.line(surf, (150, 200, 255), (sx + 10, sy + TILE - offset),
                         (sx + 10, max(sy, sy + TILE - offset - 15)), 2)
        pygame.draw.line(surf, (150, 200, 255), (sx + TILE - 10, sy + (TILE - offset + 20) % TILE),
                         (sx + TILE - 10, max(sy, sy + (TILE - offset + 20) % TILE - 15)), 2)
        pygame.draw.line(surf, (200, 230, 255), (sx + TILE // 2, sy + (TILE - offset + 10) % TILE),
                         (sx + TILE // 2, max(sy, sy + (TILE - offset + 10) % TILE - 25)), 3)
    elif ch == "B":
        pygame.draw.rect(surf, (18, 14, 28), r, border_radius=10)
        pygame.draw.rect(surf, (230, 80, 255), r, 2, border_radius=10)
        cx, cy = sx + TILE // 2, sy + TILE // 2
        pygame.draw.polygon(surf, (255, 180, 255), [(cx, cy - 10), (cx + 8, cy), (cx, cy + 10), (cx - 8, cy)])
        pygame.draw.rect(surf, (180, 40, 220), (sx + 8, sy + TILE - 14, TILE - 16, 8), border_radius=3)
    elif ch == "G":
        pygame.draw.rect(surf, (18, 14, 26), r, border_radius=6)
        pygame.draw.rect(surf, (255, 80, 80), r, 2, border_radius=6)
        pygame.draw.rect(surf, (255, 200, 100), (sx + 14, sy + 12, TILE - 28, TILE - 24), border_radius=4)
    elif ch == "P":
        pulse = abs(math.sin(gtime * 4)) * 4
        pygame.draw.circle(surf, (150, 50, 200), (sx + TILE // 2, sy + TILE // 2), 18 + int(pulse))
        pygame.draw.circle(surf, (200, 100, 255), (sx + TILE // 2, sy + TILE // 2), 12 + int(pulse // 2))
        pygame.draw.circle(surf, (255, 200, 255), (sx + TILE // 2, sy + TILE // 2), 6)
    elif ch == "I":
        pygame.draw.rect(surf, (180, 230, 255), r, border_radius=4)
        pygame.draw.rect(surf, (100, 200, 255), r, 2, border_radius=4)
        pygame.draw.line(surf, (220, 245, 255), (sx + 8, sy + 8), (sx + TILE - 8, sy + 8), 2)
    elif ch == "Z":
        pygame.draw.rect(surf, (255, 50, 50), (sx + TILE // 2 - 4, sy, 8, TILE))
        pygame.draw.rect(surf, (255, 200, 200), (sx + TILE // 2 - 2, sy, 4, TILE))
    elif ch == "z":
        pygame.draw.rect(surf, (100, 30, 30), (sx + TILE // 2 - 2, sy, 4, TILE))
