# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: entities.py
# Description: Core game entities and mechanics. Defines players, crates, buttons, lifts, projectiles, collisions, and shared level state.
# ========================================

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

TILE_DEFAULT = 48
PLAYER_PUSH_FORCE = 1800.0


BUTTON_META: Dict[Tuple[int, int], Dict] = {}
LIFT_META: Dict[Tuple[int, int, int], Dict] = {}
TARGET_META: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
TELEPORT_META: Dict[Tuple[int, int], Tuple[int, int]] = {}
LASER_TILES: List[Tuple[int, int]] = []
GLOBAL_STATE = {"timer": 0.0}

LEVEL_REF = None


class Platform:
    """Simple drawable rectangular platform helper.
    
    Constructor Args:
        x: Value used to initialize this object.
        y: Value used to initialize this object.
        width: Value used to initialize this object.
        height: Value used to initialize this object.
        color: Value used to initialize this object."""
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        """Execute the __init__ operation.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
            width: Input value required by this function.
            height: Input value required by this function.
            color: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surface, camera):
        """Execute the draw operation.
        
        Args:
            surface: Input value required by this function.
            camera: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        sx, sy = camera.world_to_screen(self.rect.x, self.rect.y)
        pygame.draw.rect(surface, self.color, (sx, sy, self.rect.width, self.rect.height))


def update_level_mechanics(dt: float, level):
    
    """Advance global level mechanics such as timers and laser state.
    
    Args:
        dt: Input value required by this function.
        level: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    GLOBAL_STATE["timer"] += dt

    
    laser_active = (GLOBAL_STATE["timer"] % 3.0) < 1.5
    laser_char = "Z" if laser_active else "z"
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for tx, ty in LASER_TILES:
        # Important condition: this branch protects an alternate state or edge case.
        if level.tile_at(tx, ty) in ("Z", "z"):
            level.set_tile(tx, ty, laser_char)


def clamp(v: float, lo: float, hi: float) -> float:
    """Limit a numeric value to a closed range.
    
    Args:
        v: Input value required by this function.
        lo: Input value required by this function.
        hi: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if v < lo:
        return lo
    elif v > hi:
        return hi
    else:
        return v


def sign(v: float) -> int:
    """Return the sign of a number as -1, 0, or 1.
    
    Args:
        v: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if v < 0:
        return -1
    elif v > 0:
        return 1
    else:
        return 0


def lerp(a: float, b: float, t: float) -> float:
    """Linearly interpolate between two values.
    
    Args:
        a: Input value required by this function.
        b: Input value required by this function.
        t: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    return a + (b - a) * t


@dataclass
class InputFrame:
    """Network input snapshot sent from a client to the server.
    
    Constructor Args:
        None."""
    left: bool = False
    right: bool = False
    down: bool = False
    jump_held: bool = False
    jump_pressed: bool = False
    shoot_held: bool = False
    shoot_pressed: bool = False
    restart: bool = False
    ready: bool = False


class Camera2P:
    """Two-player camera helper that keeps both players visible.
    
    Constructor Args:
        w: Value used to initialize this object.
        h: Value used to initialize this object."""
    def __init__(self, w: int, h: int):
        """Execute the __init__ operation.
        
        Args:
            w: Input value required by this function.
            h: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.w = int(w)
        self.h = int(h)
        self.x = 0.0
        self.y = 0.0
        self.follow_hz = 5.0
        self.margin_left = max(150, int(w * 0.15))
        self.margin_right = max(450, int(w * 0.45))
        self.margin_y = max(120, int(h * 0.18))

    def view_rect_world(self) -> pygame.Rect:
        """Return the camera viewport rectangle in world coordinates.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float, r1: pygame.Rect, r2: pygame.Rect, level_w: int, level_h: int, look_x: float,
               look_y: float):
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
            r1: Input value required by this function.
            r2: Input value required by this function.
            level_w: Input value required by this function.
            level_h: Input value required by this function.
            look_x: Input value required by this function.
            look_y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        target = self.view_rect_world()

        def enforce(r: pygame.Rect):
            """Execute the enforce operation.
            
            Args:
                r: Input value required by this function.
            
            Returns:
                The result of the operation, or None when the function performs side effects only."""
            # Important condition: this branch protects an alternate state or edge case.
            if r.left < target.left + self.margin_left: target.left = r.left - self.margin_left
            # Important condition: this branch protects an alternate state or edge case.
            if r.right > target.right - self.margin_right: target.left = r.right + self.margin_right - self.w
            # Important condition: this branch protects an alternate state or edge case.
            if r.top < target.top + self.margin_y: target.top = r.top - self.margin_y
            # Important condition: this branch protects an alternate state or edge case.
            if r.bottom > target.bottom - self.margin_y: target.top = r.bottom + self.margin_y - self.h

        enforce(r1)
        enforce(r2)

        target.left += int(look_x)
        target.top += int(look_y)
        target.left = int(clamp(target.left, 0, max(0, level_w - self.w)))
        target.top = int(clamp(target.top, 0, max(0, level_h - self.h)))

        s = 1.0 - math.exp(-dt * self.follow_hz)
        self.x = lerp(self.x, float(target.left), s)
        self.y = lerp(self.y, float(target.top), s)

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return int(x - self.x), int(y - self.y)


def _safe_load_image(path: str) -> Optional[pygame.Surface]:
    """Load an image safely and return None on failure.
    
    Args:
        path: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    try:
        # Important condition: this branch protects an alternate state or edge case.
        if os.path.exists(path): return pygame.image.load(path).convert_alpha()
    except Exception:
        pass
    return None


def _extract_frames(img: pygame.Surface, fw: int, fh: int, max_frames: int = 4) -> List[pygame.Surface]:
    """Extract animation frames from a sprite sheet.
    
    Args:
        img: Input value required by this function.
        fw: Input value required by this function.
        fh: Input value required by this function.
        max_frames: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    frames: List[pygame.Surface] = []
    cols = max(1, img.get_width() // fw)
    rows = max(1, img.get_height() // fh)
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for r in range(rows):
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for c in range(cols):
            # Important condition: this branch protects an alternate state or edge case.
            if len(frames) >= max_frames: return frames
            fr = pygame.Surface((fw, fh), pygame.SRCALPHA)
            fr.blit(img, (0, 0), pygame.Rect(c * fw, r * fh, fw, fh))
            frames.append(fr)
    # Important condition: this branch protects an alternate state or edge case.
    if frames:
        return frames
    else:
        return [img]


def _palette_swap(surface: pygame.Surface, swaps: Dict[Tuple[int, int, int], Tuple[int, int, int]],
                  tol: int = 70) -> pygame.Surface:
    """Create a recolored copy of a surface using approximate color matches.
    
    Args:
        surface: Input value required by this function.
        swaps: Input value required by this function.
        tol: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    s = surface.copy().convert_alpha()
    px = pygame.PixelArray(s)
    w, h = s.get_size()

    def near(a, b):
        """Execute the near operation.
        
        Args:
            a: Input value required by this function.
            b: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol and abs(a[2] - b[2]) <= tol

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for y in range(h):
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for x in range(w):
            col = s.unmap_rgb(px[x, y])
            # Important condition: this branch protects an alternate state or edge case.
            if col.a == 0: continue
            rgb = (col.r, col.g, col.b)
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for k, v in swaps.items():
                # Important condition: this branch protects an alternate state or edge case.
                if near(rgb, k):
                    px[x, y] = (*v, col.a)
                    break
    del px
    return s


def _make_fallback_frames(fw: int, fh: int, accent: Tuple[int, int, int]) -> List[pygame.Surface]:
    """Create simple fallback animation frames when sprite assets are missing.
    
    Args:
        fw: Input value required by this function.
        fh: Input value required by this function.
        accent: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    SKIN = (245, 230, 210)
    CLOTH = (200, 0, 0)
    HAIR = (120, 80, 40)
    OUTLINE = (0, 0, 0)
    frames = []
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i in range(4):
        s = pygame.Surface((fw, fh), pygame.SRCALPHA)
        pygame.draw.circle(s, SKIN, (fw // 2, 14), 7)
        pygame.draw.rect(s, HAIR, (fw // 2 - 8, 6, 16, 6), border_radius=3)
        pygame.draw.rect(s, CLOTH, (7, 18, fw - 14, 16), border_radius=8)
        pygame.draw.rect(s, accent, (9, 20 + (i % 2), fw - 18, 6), border_radius=6)
        pygame.draw.rect(s, OUTLINE, (7, 18, fw - 14, 16), 2, border_radius=8)
        pygame.draw.circle(s, OUTLINE, (fw // 2, 14), 7, 2)
        frames.append(s)
    return frames



def _asset_path(filename: str) -> str:
    """Build an absolute path to an asset file.
    
    Args:
        filename: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)


def _remove_green_background(src: pygame.Surface) -> pygame.Surface:
    """Remove a chroma-key green background from a sprite sheet.
    
    Args:
        src: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    
    src = src.convert_alpha()
    src.set_colorkey((0, 255, 0))

    
    out = pygame.Surface(src.get_size(), pygame.SRCALPHA)
    out.blit(src, (0, 0))
    return out


def _crop_visible(surface: pygame.Surface) -> pygame.Surface:
    """Crop transparent padding from a surface.
    
    Args:
        surface: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    rect = surface.get_bounding_rect(min_alpha=8)
    # Important condition: this branch protects an alternate state or edge case.
    if rect.w <= 0 or rect.h <= 0:
        return surface
    return surface.subsurface(rect).copy()


def _fit_to_frame(surface: pygame.Surface, fw: int, fh: int) -> pygame.Surface:
    """Scale and place a sprite frame into a fixed-size animation frame.
    
    Args:
        surface: Input value required by this function.
        fw: Input value required by this function.
        fh: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    out = pygame.Surface((fw, fh), pygame.SRCALPHA)

    sw, sh = surface.get_size()
    # Important condition: this branch protects an alternate state or edge case.
    if sw <= 0 or sh <= 0:
        return out

    
    target_body_h = int(fh * 0.96)
    scale = target_body_h / sh

    new_w = max(1, int(sw * scale))
    new_h = max(1, int(sh * scale))

    scaled = pygame.transform.smoothscale(surface, (new_w, new_h))

    
    
    x = (fw - new_w) // 2
    y = fh - new_h
    out.blit(scaled, (x, y))
    return out


def _load_sprite_sheet_frames(path: str, fw: int, fh: int, cols: int = 4, rows: int = 2) -> List[pygame.Surface]:
    """Load a sprite sheet and split it into fitted animation frames.
    
    Args:
        path: Input value required by this function.
        fw: Input value required by this function.
        fh: Input value required by this function.
        cols: Input value required by this function.
        rows: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    try:
        # Important condition: this branch protects an alternate state or edge case.
        if not os.path.exists(path):
            return []

        sheet = pygame.image.load(path).convert_alpha()
        sheet = _remove_green_background(sheet)

        cell_w = sheet.get_width() // cols
        cell_h = sheet.get_height() // rows

        frames: List[pygame.Surface] = []

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for row in range(rows):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for col in range(cols):
                cell = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                cell.blit(sheet, (0, 0), pygame.Rect(col * cell_w, row * cell_h, cell_w, cell_h))
                cropped = _crop_visible(cell)
                fitted = _fit_to_frame(cropped, fw, fh)
                frames.append(fitted)

        return frames

    except Exception as e:
        print(f"[SPRITE SHEET ERROR] Could not load {path}: {e}")
        return []


_frames_cache: Dict[str, List[pygame.Surface]] = {}
_shoot_cache: Dict[str, Optional[pygame.Surface]] = {}


def load_shoot_image(palette: str) -> Optional[pygame.Surface]:
    """Load and cache a character shooting image.
    
    Args:
        palette: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if palette in _shoot_cache:
        return _shoot_cache[palette]

    filename = "joseph_shoot.png" if palette == "joseph" else "caesar_shoot.png"
    img = _safe_load_image(_asset_path(filename))
    _shoot_cache[palette] = img
    return img


def load_character_frames(palette: str, fw: int, fh: int) -> List[pygame.Surface]:
    """Load and cache character animation frames.
    
    Args:
        palette: Input value required by this function.
        fw: Input value required by this function.
        fh: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    cache_key = f"{palette}_{fw}_{fh}"
    # Important condition: this branch protects an alternate state or edge case.
    if cache_key in _frames_cache:
        return _frames_cache[cache_key]

    # Important condition: this branch protects an alternate state or edge case.
    if palette == "joseph":
        sheet_name = "joseph_sheet_clean.png"
        single_img_name = "joseph.png"
        color_fallback = (135, 70, 185)
    else:
        sheet_name = "caesar_sheet_clean.png"
        single_img_name = "caesar.png"
        color_fallback = (155, 210, 255)

    
    sheet_path = _asset_path(sheet_name)
    out = _load_sprite_sheet_frames(sheet_path, fw, fh, cols=4, rows=2)

    
    if not out:
        single_path = _asset_path(single_img_name)
        src = _safe_load_image(single_path)
        # Important condition: this branch protects an alternate state or edge case.
        if src:
            scaled = pygame.transform.scale(src, (fw, fh))
            out = [scaled]
        else:
            out = _make_fallback_frames(fw, fh, color_fallback)

    _frames_cache[cache_key] = out
    return out


class Button:
    """Interactive floor button that can open or close linked door tiles.
    
    Constructor Args:
        x: Value used to initialize this object.
        y: Value used to initialize this object."""
    def __init__(self, x: int, y: int):
        """Execute the __init__ operation.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.rect = pygame.Rect(x, y, TILE_DEFAULT, TILE_DEFAULT)
        self.pressed = False
        self.shot_pressed = False
        meta = BUTTON_META.get((x, y), {})
        self.is_heavy = meta.get("heavy", False)
        self.linked_doors = meta.get("doors", [])

    def _stands_on(self, r: pygame.Rect) -> bool:
        """Check whether another rectangle overlaps the button area.
        
        Args:
            r: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return self.rect.colliderect(r)

    def update(self, p1: pygame.Rect, p2: pygame.Rect, crate_rects: List[pygame.Rect],
               projectiles: List['Projectile'] = None):
        """Execute the update operation.
        
        Args:
            p1: Input value required by this function.
            p2: Input value required by this function.
            crate_rects: Input value required by this function.
            projectiles: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if projectiles is None:
            projectiles = []

        stand_1 = self._stands_on(p1)
        stand_2 = self._stands_on(p2)
        crates_on = sum(1 for c in crate_rects if self._stands_on(c))

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for p in projectiles:
            # Important condition: this branch protects an alternate state or edge case.
            if p.alive and self._stands_on(p.get_rect()):
                self.shot_pressed = True
                p.alive = False

        was_pressed = self.pressed
        # Important condition: this branch protects an alternate state or edge case.
        if self.is_heavy:
            self.pressed = (crates_on >= 1) or (stand_1 and stand_2)
        else:
            self.pressed = stand_1 or stand_2 or (crates_on >= 1) or self.shot_pressed

        # Important condition: this branch protects an alternate state or edge case.
        if LEVEL_REF and self.linked_doors and self.pressed != was_pressed:
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for tx, ty in self.linked_doors: LEVEL_REF.set_tile(tx, ty, "." if self.pressed else "#")


class Lift:
    """Moving platform or moving hazard that can carry riders.
    
    Constructor Args:
        x: Value used to initialize this object.
        top_y: Value used to initialize this object.
        bottom_y: Value used to initialize this object."""
    RIDE_TOL = 6

    def __init__(self, x: int, top_y: int, bottom_y: int):
        """Execute the __init__ operation.
        
        Args:
            x: Input value required by this function.
            top_y: Input value required by this function.
            bottom_y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.top_y = int(top_y)
        self.bottom_y = int(bottom_y)
        self.start_y = self.bottom_y
        self.target_y = self.bottom_y
        meta = LIFT_META.get((int(x), self.top_y, self.bottom_y), {})
        self.w = meta.get("width", 96)
        self.h = 24
        self.rect = pygame.Rect(int(x), self.bottom_y, self.w, self.h)
        self.is_horiz = meta.get("is_horiz", False)
        self.is_hazard = meta.get("is_hazard", False)
        self.left_x = int(x)
        self.right_x = meta.get("right_x", int(x))
        self.speed = meta.get("speed", 220.0)
        self.dir = 1
        self.horiz_x = float(x)
        self.last_dx = 0.0

    def update(self, dt: float) -> float:
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        old_y = self.rect.y
        self.last_dx = 0.0
        # Important condition: this branch protects an alternate state or edge case.
        if self.is_horiz:
            old_rect_x = self.rect.x
            self.horiz_x += self.speed * self.dir * dt
            # Important condition: this branch protects an alternate state or edge case.
            if self.horiz_x >= self.right_x:
                self.horiz_x = self.right_x;
                self.dir = -1
            elif self.horiz_x <= self.left_x:
                self.horiz_x = self.left_x;
                self.dir = 1
            self.rect.x = int(self.horiz_x)
            self.last_dx = float(self.rect.x - old_rect_x)
            return 0.0
        else:
            dist = self.target_y - self.rect.y
            # Important condition: this branch protects an alternate state or edge case.
            if abs(dist) <= 1:
                self.rect.y = self.target_y
            else:
                step = self.speed * dt * sign(dist)
                # Important condition: this branch protects an alternate state or edge case.
                if abs(step) >= abs(dist):
                    self.rect.y = self.target_y
                else:
                    self.rect.y += int(round(step))
            self.rect.y = int(clamp(self.rect.y, self.top_y, self.bottom_y))
            return float(self.rect.y - old_y)

    def carry_riders(self, dy: float, players: list, crates: list):
        """Move objects that are standing on a moving lift.
        
        Args:
            dy: Input value required by this function.
            players: Input value required by this function.
            crates: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if self.is_hazard: return
        dy_i = int(round(dy))
        dx_i = int(round(self.last_dx))
        # Important condition: this branch protects an alternate state or edge case.
        if dy_i == 0 and dx_i == 0: return

        def x_ok(a: pygame.Rect, b: pygame.Rect) -> bool:
            """Execute the x_ok operation.
            
            Args:
                a: Input value required by this function.
                b: Input value required by this function.
            
            Returns:
                The result of the operation, or None when the function performs side effects only."""
            return a.right > b.left and a.left < b.right

        def is_riding(r: pygame.Rect) -> bool:
            """Execute the is_riding operation.
            
            Args:
                r: Input value required by this function.
            
            Returns:
                The result of the operation, or None when the function performs side effects only."""
            return x_ok(r, self.rect) and abs(r.bottom - self.rect.top) <= self.RIDE_TOL

        def is_crushed(r: pygame.Rect) -> bool:
            """Execute the is_crushed operation.
            
            Args:
                r: Input value required by this function.
            
            Returns:
                The result of the operation, or None when the function performs side effects only."""
            return dy_i > 0 and x_ok(r, self.rect) and self.rect.bottom >= r.top and self.rect.top < r.centery

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for p in players:
            # Important condition: this branch protects an alternate state or edge case.
            if is_riding(p.rect):
                p.y += dy_i
                p.x += dx_i
                p.rect.y = int(p.y)
                p.rect.x = int(p.x)
                p.on_ground = True
                p.ground_type = "lift"
            elif is_crushed(p.rect):
                p.y += dy_i
                p.rect.y = int(p.y)
                p.vy = max(p.vy, 0.0)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for c in crates:
            # Important condition: this branch protects an alternate state or edge case.
            if is_riding(c.rect):
                c.y += dy_i
                c.x += dx_i
                c.rect.y = int(c.y)
                c.rect.x = int(c.x)
                c.on_ground = True
            elif is_crushed(c.rect):
                c.y += dy_i
                c.rect.y = int(c.y)
                c.vy = max(c.vy, 0.0)


@dataclass
class Projectile:
    """Small moving object fired by a player.
    
    Constructor Args:
        None."""
    x: float
    y: float
    vx: float
    vy: float
    w: int
    h: int
    kind: str
    alive: bool = True

    def get_rect(self) -> pygame.Rect:
        """Return the projectile rectangle.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


class ProjectileManager:
    """Owns and updates all active projectiles.
    
    Constructor Args:
        None."""
    def __init__(self):
        """Execute the __init__ operation.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.items: List[Projectile] = []

    def spawn(self, kind: str, x: float, y: float, facing: int):
        """Create a new projectile with the requested type and direction.
        
        Args:
            kind: Input value required by this function.
            x: Input value required by this function.
            y: Input value required by this function.
            facing: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if kind == "bottlecap":
            self.items.append(Projectile(x=x, y=y, vx=980.0 * facing, vy=-90.0, w=14, h=10, kind=kind))
        else:
            self.items.append(Projectile(x=x, y=y, vx=820.0 * facing, vy=-160.0, w=18, h=18, kind=kind))

    def update(self, dt: float, level, crates: list, lifts: list, players: list):
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
            level: Input value required by this function.
            crates: Input value required by this function.
            lifts: Input value required by this function.
            players: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for p in self.items:
            # Important condition: this branch protects an alternate state or edge case.
            if not p.alive: continue
            # Important condition: this branch protects an alternate state or edge case.
            if p.kind == "bubble": p.vy += 300.0 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            r = p.get_rect()

            # Important loop: iterates through game objects that must be processed every frame or build step.
            for lf in lifts:
                # Important condition: this branch protects an alternate state or edge case.
                if r.colliderect(lf.rect): p.alive = False; break
            # Important condition: this branch protects an alternate state or edge case.
            if not p.alive: continue
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for c in crates:
                # Important condition: this branch protects an alternate state or edge case.
                if r.colliderect(c.rect): p.alive = False; break
            # Important condition: this branch protects an alternate state or edge case.
            if not p.alive: continue

            # Important loop: iterates through game objects that must be processed every frame or build step.
            for tx, ty, ch in level.tiles_in_aabb(r, pad_tiles=1):
                tr = level.tile_rect(tx, ty)
                # Important condition: this branch protects an alternate state or edge case.
                if not r.colliderect(tr): continue
                # Important condition: this branch protects an alternate state or edge case.
                if ch == "O":
                    level.set_tile(tx, ty, "o")
                    p.alive = False
                    k = (tx * TILE_DEFAULT, ty * TILE_DEFAULT)
                    # Important condition: this branch protects an alternate state or edge case.
                    if k in TARGET_META:
                        # Important loop: iterates through game objects that must be processed every frame or build step.
                        for dx, dy in TARGET_META[k]: level.set_tile(dx, dy, ".")
                    break
                # Important condition: this branch protects an alternate state or edge case.
                if ch == "X": level.set_tile(tx, ty, "."); p.alive = False; break
                # Important condition: this branch protects an alternate state or edge case.
                if ch in level.FULL_SOLIDS or ch in level.ONE_WAY or ch in ("Z", "*", "S"): p.alive = False; break
            # Important condition: this branch protects an alternate state or edge case.
            if not (-4000 < p.x < level.width_px + 4000 and -4000 < p.y < level.height_px + 4000): p.alive = False
        self.items = [p for p in self.items if p.alive]

    def draw(self, screen: pygame.Surface, camera: Camera2P):
        """Execute the draw operation.
        
        Args:
            screen: Input value required by this function.
            camera: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for p in self.items:
            sx, sy = camera.world_to_screen(p.x, p.y)

            # Important condition: this branch protects an alternate state or edge case.
            if p.kind == "bottlecap":
                
                cx = sx + p.w // 2
                cy = sy + p.h // 2

                pygame.draw.circle(screen, (210, 20, 30), (cx, cy), 8)
                pygame.draw.circle(screen, (120, 0, 10), (cx, cy), 8, 2)
                pygame.draw.circle(screen, (255, 170, 170), (cx - 3, cy - 3), 3)

                
                pygame.draw.line(screen, (255, 90, 90), (cx - 16, cy), (cx - 7, cy), 3)
                pygame.draw.line(screen, (255, 150, 150), (cx - 13, cy - 5), (cx - 6, cy - 2), 2)

            elif p.kind == "bubble":
                
                cx = sx + p.w // 2
                cy = sy + p.h // 2

                pygame.draw.circle(screen, (170, 230, 255), (cx, cy), 11)
                pygame.draw.circle(screen, (80, 160, 230), (cx, cy), 11, 2)
                pygame.draw.circle(screen, (245, 255, 255), (cx - 4, cy - 4), 4)
                pygame.draw.circle(screen, (220, 245, 255), (cx + 4, cy + 3), 3, 1)




def _apply_friction(e, friction: float, dt: float):
    """Apply friction to a horizontal velocity value.
    
    Args:
        e: Input value required by this function.
        friction: Input value required by this function.
        dt: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    decel = friction * dt
    # Important condition: this branch protects an alternate state or edge case.
    if abs(e.vx) <= decel:
        e.vx = 0.0
    else:
        e.vx -= decel * sign(e.vx)


def _resolve_hits(entity, hits: List[Tuple[pygame.Rect, str, str]], axis: str, step: float, tx=None, ty=None):
    """Resolve collisions between a moving rectangle and level tiles.
    
    Args:
        entity: Input value required by this function.
        hits: Input value required by this function.
        axis: Input value required by this function.
        step: Input value required by this function.
        tx: Input value required by this function.
        ty: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if axis == "x":
        # Important condition: this branch protects an alternate state or edge case.
        if step > 0:
            entity.rect.right = min(r.left for r, _k, _ch in hits)
        else:
            entity.rect.left = max(r.right for r, _k, _ch in hits)
        entity.x = float(entity.rect.x)
        entity.vx = 0.0
        return

    # Important condition: this branch protects an alternate state or edge case.
    if step > 0:
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for r, _k, ch in hits:
            # Important condition: this branch protects an alternate state or edge case.
            if ch == "T":
                entity.rect.bottom = r.top
                entity.y = float(entity.rect.y)
                entity.vy = -1400.0
                entity.on_ground = False
                # Important condition: this branch protects an alternate state or edge case.
                if hasattr(entity, "ground_type"): entity.ground_type = None
                # Important condition: this branch protects an alternate state or edge case.
                if hasattr(entity, "respawn_pos"): entity.respawn_pos = (entity.rect.x, r.top - entity.rect.height)
                return

        entity.rect.bottom = min(r.top for r, _k, _ch in hits)
        entity.on_ground = True
        kinds = {k for _r, k, _ch in hits}
        chs = {ch for _r, _k, ch in hits}
        # Important condition: this branch protects an alternate state or edge case.
        if "lift" in kinds:
            entity.ground_type = "lift"
        elif "crate" in kinds:
            entity.ground_type = "crate"
        elif ">" in chs:
            entity.ground_type = "conv_right"
        elif "<" in chs:
            entity.ground_type = "conv_left"
        elif "I" in chs:
            entity.ground_type = "ice"
        else:
            entity.ground_type = "tile"
    else:
        entity.rect.top = max(r.bottom for r, _k, _ch in hits)
        # Important condition: this branch protects an alternate state or edge case.
        if hasattr(entity, "ground_type"): entity.ground_type = None

    entity.y = float(entity.rect.y)
    entity.vy = 0.0


def _crate_vs_crates(crate, crates: list, axis: str, step: float):
    """Resolve collisions between crates.
    
    Args:
        crate: Input value required by this function.
        crates: Input value required by this function.
        axis: Input value required by this function.
        step: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for other in crates:
        # Important condition: this branch protects an alternate state or edge case.
        if other is crate or not crate.rect.colliderect(other.rect): continue
        # Important condition: this branch protects an alternate state or edge case.
        if axis == "x":
            # Important condition: this branch protects an alternate state or edge case.
            if step > 0:
                crate.rect.right = other.rect.left
            else:
                crate.rect.left = other.rect.right
            crate.x = float(crate.rect.x)
            crate.vx = 0.0
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if step > 0:
                crate.rect.bottom = other.rect.top;
                crate.on_ground = True
            else:
                crate.rect.top = other.rect.bottom
            crate.y = float(crate.rect.y)
            crate.vy = 0.0


def _player_vs_crates(player, crates: list, axis: str, step: float, level, lifts: list, dt: float, move_dir: int):
    """Resolve pushing and collision interactions between a player and crates.
    
    Args:
        player: Input value required by this function.
        crates: Input value required by this function.
        axis: Input value required by this function.
        step: Input value required by this function.
        level: Input value required by this function.
        lifts: Input value required by this function.
        dt: Input value required by this function.
        move_dir: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for c in crates:
        # Important condition: this branch protects an alternate state or edge case.
        if not player.rect.colliderect(c.rect): continue
        # Important condition: this branch protects an alternate state or edge case.
        if axis == "x":
            # Important condition: this branch protects an alternate state or edge case.
            if move_dir != 0:
                c.vx += move_dir * (PLAYER_PUSH_FORCE * getattr(player, 'push_power', 1.0)) * dt
                c.vx = clamp(c.vx, -c.MAX_SPEED, c.MAX_SPEED)
            # Important condition: this branch protects an alternate state or edge case.
            if step > 0:
                overlap = player.rect.right - c.rect.left
                moved = c.try_push_x(overlap, level, crates, lifts)
                c.mark_pushed()
                player.rect.right = c.rect.left
                player.x = float(player.rect.x)
                # Important condition: this branch protects an alternate state or edge case.
                if moved < overlap - 0.5: player.vx = 0.0
            else:
                overlap = c.rect.right - player.rect.left
                moved = c.try_push_x(-overlap, level, crates, lifts)
                c.mark_pushed()
                player.rect.left = c.rect.right
                player.x = float(player.rect.x)
                # Important condition: this branch protects an alternate state or edge case.
                if -moved < overlap - 0.5: player.vx = 0.0
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if step > 0:
                player.rect.bottom = c.rect.top
                player.y = float(player.rect.y)
                player.vy = 0.0
                player.on_ground = True
                player.ground_type = "crate"
            else:
                player.rect.top = c.rect.bottom
                player.y = float(player.rect.y)
                player.vy = 0.0


def _step_axis(entity, delta: float, axis: str, max_step: float, level, crates: list, lifts: list, is_player: bool,
               dt: float = 0.0, move_dir: int = 0):
    """Move a rectangle along one axis while resolving collisions.
    
    Args:
        entity: Input value required by this function.
        delta: Input value required by this function.
        axis: Input value required by this function.
        max_step: Input value required by this function.
        level: Input value required by this function.
        crates: Input value required by this function.
        lifts: Input value required by this function.
        is_player: Input value required by this function.
        dt: Input value required by this function.
        move_dir: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if delta == 0.0: return
    steps = max(1, math.ceil(abs(delta) / max_step))
    step_px = delta / steps

    # Important condition: this branch protects an alternate state or edge case.
    if axis == "y":
        entity.on_ground = False
        # Important condition: this branch protects an alternate state or edge case.
        if hasattr(entity, "ground_type"): entity.ground_type = None

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for _ in range(steps):
        prev_bottom = entity.rect.bottom
        # Important condition: this branch protects an alternate state or edge case.
        if axis == "x":
            entity.x += step_px;
            entity.rect.x = int(entity.x)
        else:
            entity.y += step_px;
            entity.rect.y = int(entity.y)

        hits: List[Tuple[pygame.Rect, str, str]] = []

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for tx, ty, ch in level.tiles_in_aabb(entity.rect, pad_tiles=1):
            tr = level.tile_rect(tx, ty)
            # Important condition: this branch protects an alternate state or edge case.
            if ch in level.FULL_SOLIDS and entity.rect.colliderect(tr):
                hits.append((tr, "tile", ch))
            elif (is_player and axis == "y" and step_px > 0 and ch in level.ONE_WAY):
                # Important condition: this branch protects an alternate state or edge case.
                if entity.rect.colliderect(tr) and prev_bottom <= tr.top + 2:
                    hits.append((tr, "tile", ch))

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for lf in lifts:
            # Important condition: this branch protects an alternate state or edge case.
            if not getattr(lf, 'is_hazard', False) and entity.rect.colliderect(lf.rect): hits.append(
                (lf.rect, "lift", ""))

        # Important condition: this branch protects an alternate state or edge case.
        if hits:
            _resolve_hits(entity, hits, axis, step_px)
            continue

        # Important condition: this branch protects an alternate state or edge case.
        if is_player:
            _player_vs_crates(entity, crates, axis, step_px, level, lifts, dt, move_dir)
        else:
            _crate_vs_crates(entity, crates, axis, step_px)


class Crate:
    """Movable physics crate that can be pushed and can press buttons.
    
    Constructor Args:
        x: Value used to initialize this object.
        y: Value used to initialize this object."""
    MAX_SPEED = 320.0
    FRICTION = 3200.0
    AIR_DRAG = 320.0
    PUSH_GRACE = 0.14

    def __init__(self, x: float, y: float):
        """Execute the __init__ operation.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.w = 144
        self.h = 144
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        self.on_ground = False
        self._push_timer = 0.0
        self.ground_type = None

    def mark_pushed(self):
        """Record that a crate was pushed for animation or friction behavior.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self._push_timer = self.PUSH_GRACE

    def try_push_x(self, dx: float, level, crates: list, lifts: list) -> float:
        """Try to push a crate horizontally.
        
        Args:
            dx: Input value required by this function.
            level: Input value required by this function.
            crates: Input value required by this function.
            lifts: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if dx == 0: return 0.0
        old_x = self.x
        _step_axis(self, dx, "x", 16.0, level, crates, lifts, is_player=False)
        return self.x - old_x

    def update(self, dt: float, gravity: float, level, crates: list, lifts: list):
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
            gravity: Input value required by this function.
            level: Input value required by this function.
            crates: Input value required by this function.
            lifts: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self._push_timer = max(0.0, self._push_timer - dt)
        self.vy = clamp(self.vy + gravity * dt, -2000.0, 1700.0)
        # Important condition: this branch protects an alternate state or edge case.
        if self.on_ground and self._push_timer <= 0.0:
            _apply_friction(self, 400.0 if self.ground_type == "ice" else self.FRICTION, dt)
        else:
            _apply_friction(self, self.AIR_DRAG, dt)
        self.vx = clamp(self.vx, -self.MAX_SPEED, self.MAX_SPEED)

        # Important condition: this branch protects an alternate state or edge case.
        if self.on_ground:
            # Important condition: this branch protects an alternate state or edge case.
            if self.ground_type == "conv_right":
                self.x += 200.0 * dt
            elif self.ground_type == "conv_left":
                self.x -= 200.0 * dt

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for tx, ty, ch in level.tiles_in_aabb(self.rect, pad_tiles=0):
            # Important condition: this branch protects an alternate state or edge case.
            if ch == "W":
                self.vy -= 4000.0 * dt
                self.on_ground = False
                break

        _step_axis(self, self.vx * dt, "x", 16.0, level, crates, lifts, is_player=False)
        _step_axis(self, self.vy * dt, "y", 16.0, level, crates, lifts, is_player=False)


class Player:
    """Playable character with movement, collision, shooting, and drawing logic.
    
    Constructor Args:
        name: Value used to initialize this object.
        x: Value used to initialize this object.
        y: Value used to initialize this object.
        palette: Value used to initialize this object.
        controls: Value used to initialize this object."""
    ACCEL_GROUND = 6200.0
    ACCEL_AIR = 4200.0
    MAX_SPEED = 520.0
    FRICTION = 6800.0
    AIR_DRAG = 980.0
    GRAVITY_CAP = 1700.0
    COYOTE_TIME = 0.15
    JUMP_BUFFER = 0.10
    SHOOT_CD = 0.22

    def __init__(self, name: str, x: float, y: float, palette: str, controls: Dict[str, int]):
        """Execute the __init__ operation.
        
        Args:
            name: Input value required by this function.
            x: Input value required by this function.
            y: Input value required by this function.
            palette: Input value required by this function.
            controls: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.name = name
        self.controls = controls
        self.palette = palette
        self.w = 32
        self.h = 48
        
        
        self.frames = load_character_frames(palette, 64, 96)
        self.shoot_image = load_shoot_image(palette)
        self.projectile_kind = "bottlecap" if palette == "joseph" else "bubble"

        # Important condition: this branch protects an alternate state or edge case.
        if palette == "joseph":
            self.JUMP_SPEED = 960.0;
            self.DBL_JUMP_SPD = 960.0;
            self.push_power = 1.0
        else:
            self.JUMP_SPEED = 960.0;
            self.DBL_JUMP_SPD = 960.0;
            self.push_power = 0.2

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.on_ground = False
        self.ground_type = None
        self.facing = 1
        self.max_jumps = 2
        self._jumps_used = 0
        self._coyote = 0.0
        self._jump_buf = 0.0
        self._shoot_cd = 0.0
        self._shoot_anim_timer = 0.0
        self._teleport_cd = 0.0
        self.respawn_pos = (self.rect.x, self.rect.y)
        self._anim_t = 0.0
        self._anim_i = 0
        self.network_shooting = False
        self.network_shoot_timer = 0.0

        self.just_died = False
        self.safe_timer = 0.0
        self.last_ground_type = "tile"

    def update(self, dt: float, inp: InputFrame, gravity: float, level, crates: list, lifts: list, projectiles):
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
            inp: Input value required by this function.
            gravity: Input value required by this function.
            level: Input value required by this function.
            crates: Input value required by this function.
            lifts: Input value required by this function.
            projectiles: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self._shoot_cd = max(0.0, self._shoot_cd - dt)
        self._shoot_anim_timer = max(0.0, self._shoot_anim_timer - dt)
        self._teleport_cd = max(0.0, self._teleport_cd - dt)

        # Important condition: this branch protects an alternate state or edge case.
        if inp.down and self.on_ground:
            # Important condition: this branch protects an alternate state or edge case.
            if self.h == 48:
                self.h = 24
                self.rect.height = 24
                self.y += 24.0
                self.rect.y = int(self.y)
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if self.h == 24:
                test_r = pygame.Rect(self.rect.x, int(self.y - 24), self.w, 48)
                can_stand = True
                # Important loop: iterates through game objects that must be processed every frame or build step.
                for tx, ty, ch in level.tiles_in_aabb(test_r, pad_tiles=0):
                    # Important condition: this branch protects an alternate state or edge case.
                    if ch in level.FULL_SOLIDS and test_r.colliderect(level.tile_rect(tx, ty)):
                        can_stand = False
                        break
                # Important condition: this branch protects an alternate state or edge case.
                if can_stand or not self.on_ground:
                    self.h = 48
                    self.rect.height = 48
                    self.y -= 24.0
                    self.rect.y = int(self.y)

        # Important condition: this branch protects an alternate state or edge case.
        if self._teleport_cd <= 0.0:
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for tx, ty, ch in level.tiles_in_aabb(self.rect, pad_tiles=0):
                # Important condition: this branch protects an alternate state or edge case.
                if ch == "P":
                    dest = TELEPORT_META.get((tx * TILE_DEFAULT, ty * TILE_DEFAULT))
                    # Important condition: this branch protects an alternate state or edge case.
                    if dest:
                        self.x, self.y = dest[0], dest[1]
                        self.rect.x, self.rect.y = int(self.x), int(self.y)
                        self.vx = 0.0
                        self.vy = 0.0
                        self._teleport_cd = 1.0
                        break

        move_dir = (-1 if inp.left else 0) + (1 if inp.right else 0)
        # Important condition: this branch protects an alternate state or edge case.
        if move_dir: self.facing = move_dir

        # Important condition: this branch protects an alternate state or edge case.
        if inp.jump_pressed:
            self._jump_buf = self.JUMP_BUFFER
        else:
            self._jump_buf = max(0.0, self._jump_buf - dt)

        # Important condition: this branch protects an alternate state or edge case.
        if self.on_ground:
            self._coyote = self.COYOTE_TIME;
            self._jumps_used = 0
        else:
            self._coyote = max(0.0, self._coyote - dt)

        # Important condition: this branch protects an alternate state or edge case.
        if self.on_ground:
            fric = 400.0 if self.ground_type == "ice" else self.FRICTION
            # Important condition: this branch protects an alternate state or edge case.
            if move_dir:
                self.vx += move_dir * self.ACCEL_GROUND * dt
            else:
                _apply_friction(self, fric, dt)
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if move_dir: self.vx += move_dir * self.ACCEL_AIR * dt
            _apply_friction(self, self.AIR_DRAG, dt)

        self.vx = clamp(self.vx, -self.MAX_SPEED, self.MAX_SPEED)

        # Important condition: this branch protects an alternate state or edge case.
        if self._jump_buf > 0.0:
            # Important condition: this branch protects an alternate state or edge case.
            if self.on_ground or self._coyote > 0.0:
                self.vy = -self.JUMP_SPEED
                self.on_ground = False
                self._coyote = 0.0
                self._jump_buf = 0.0
                self._jumps_used = max(self._jumps_used, 1)
            elif self._jumps_used < self.max_jumps:
                self.vy = -self.DBL_JUMP_SPD
                self._jump_buf = 0.0
                self._jumps_used += 1

        # Important condition: this branch protects an alternate state or edge case.
        if not inp.jump_held and self.vy < -250.0: self.vy *= 0.92
        self.vy = clamp(self.vy + gravity * dt, -2000.0, self.GRAVITY_CAP)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for tx, ty, ch in level.tiles_in_aabb(self.rect, pad_tiles=0):
            # Important condition: this branch protects an alternate state or edge case.
            if ch == "W":
                self.vy -= 4500.0 * dt
                self.vy = clamp(self.vy, -900.0, self.GRAVITY_CAP)
                self.on_ground = False
                break

        # Important condition: this branch protects an alternate state or edge case.
        if inp.shoot_pressed and self._shoot_cd <= 0.0:
            mx = self.x + (self.w - 4 if self.facing > 0 else -10)
            my = self.y + self.h * 0.45
            projectiles.spawn(self.projectile_kind, mx, my, self.facing)
            self._shoot_cd = self.SHOOT_CD
            self._shoot_anim_timer = 0.60

        # Important condition: this branch protects an alternate state or edge case.
        if self.on_ground:
            # Important condition: this branch protects an alternate state or edge case.
            if self.ground_type == "conv_right":
                self.x += 200.0 * dt
            elif self.ground_type == "conv_left":
                self.x -= 200.0 * dt

        _step_axis(self, self.vx * dt, "x", 16.0, level, crates, lifts, is_player=True, dt=dt, move_dir=move_dir)
        _step_axis(self, self.vy * dt, "y", 16.0, level, crates, lifts, is_player=True, dt=dt, move_dir=move_dir)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for tx, ty, ch in level.tiles_in_aabb(self.rect, pad_tiles=0):
            # Important condition: this branch protects an alternate state or edge case.
            if ch in ("S", "Z", "*"):
                tr = level.tile_rect(tx, ty)
                # Important condition: this branch protects an alternate state or edge case.
                if self.rect.colliderect(tr.inflate(-8, -8)):
                    self.just_died = True
                    break

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for lf in lifts:
            # Important condition: this branch protects an alternate state or edge case.
            if lf.is_hazard and self.rect.colliderect(lf.rect.inflate(-4, -4)):
                self.just_died = True
                break

        
        if self.on_ground:
            self.last_ground_type = self.ground_type

        
        if self.on_ground and self.ground_type == "tile":
            self.safe_timer += dt
        elif not self.on_ground and self._coyote > 0.0 and getattr(self, "last_ground_type", "") == "tile":
            self.safe_timer += dt
        else:
            self.safe_timer = 0.0

        # Important condition: this branch protects an alternate state or edge case.
        if self.safe_timer > 1.2 and self.on_ground and self.ground_type == "tile" and abs(self.vx) < 50:
            self.respawn_pos = (self.rect.x, self.rect.y)

        self._anim_t += dt * (4.0 + abs(self.vx) / 120.0)
        # Important condition: this branch protects an alternate state or edge case.
        if self._anim_t >= 1.0:
            self._anim_t = 0.0
            self._anim_i = (self._anim_i + 1) % len(self.frames)

    def draw(self, screen: pygame.Surface, camera: Camera2P):
        """Execute the draw operation.
        
        Args:
            screen: Input value required by this function.
            camera: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        sx, sy = camera.world_to_screen(self.rect.x, self.rect.y)

        is_shooting_visual = (
            getattr(self, "_shoot_anim_timer", 0.0) > 0.0
            or getattr(self, "network_shoot_timer", 0.0) > 0.0
            or getattr(self, "network_shooting", False)
        )

        
        
        if is_shooting_visual and self.shoot_image:
            img = self.shoot_image
            # Important condition: this branch protects an alternate state or edge case.
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)

            
            
            target_w = 100
            target_h = 75

            img = pygame.transform.smoothscale(img, (target_w, target_h))

            # Important condition: this branch protects an alternate state or edge case.
            if self.facing >= 0:
                
                draw_x = sx - 14
            else:
                
                draw_x = sx + self.w - target_w + 14

            draw_y = sy + self.h - target_h + 4
            screen.blit(img, (draw_x, draw_y))
            return

        # Important condition: this branch protects an alternate state or edge case.
        if not self.frames:
            frame = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        else:
            
            
            last_x = getattr(self, "_last_draw_x", self.rect.x)
            last_y = getattr(self, "_last_draw_y", self.rect.y)
            dx = self.rect.x - last_x
            dy = self.rect.y - last_y
            self._last_draw_x = self.rect.x
            self._last_draw_y = self.rect.y

            moving = abs(dx) > 1
            jumping = dy < -1
            falling = dy > 1

            # Important condition: this branch protects an alternate state or edge case.
            if len(self.frames) >= 8:
                # Important condition: this branch protects an alternate state or edge case.
                if jumping:
                    frame_idx = 5
                elif falling:
                    
                    
                    frame_idx = 5
                elif moving:
                    walk_frames = [2, 3, 4]
                    frame_idx = walk_frames[self._anim_i % len(walk_frames)]
                else:
                    idle_frames = [0, 1]
                    frame_idx = idle_frames[self._anim_i % len(idle_frames)]
            else:
                frame_idx = self._anim_i % len(self.frames)

            frame = self.frames[frame_idx]

        
        
        if self.facing < 0:
            frame = pygame.transform.flip(frame, True, False)

        
        scale_factor = 1.85
        final_w = int(self.w * scale_factor)
        final_h = int(self.h * scale_factor)


        
        if self.h == 24:
            final_h = int(24 * scale_factor)
            final_w = int(self.w * scale_factor)

        final_w = max(1, final_w)
        final_h = max(1, final_h)

        
        scaled_frame = pygame.transform.scale(frame, (final_w, final_h))

        draw_x = sx + (self.w - final_w) // 2
        draw_y = sy + (self.h - final_h)

        screen.blit(scaled_frame, (draw_x, draw_y))
