# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: level.py
# Description: Level construction code. Builds the tile map, spawn points, obstacles, buttons, doors, hazards, and goal locations.
# ========================================

from __future__ import annotations
from entities import Button
from dataclasses import dataclass
from typing import List, Tuple
import pygame

TILE = 48
MAIN_FLOOR_ROW = 60

@dataclass
class Level:
    """Stores tile-map data, map dimensions, spawns, and tile collision helpers.
    
    Constructor Args:
        None."""
    grid: List[List[str]]
    width_tiles: int
    height_tiles: int
    width_px: int
    height_px: int
    spawn1_px: Tuple[int, int]
    spawn2_px: Tuple[int, int]

    
    theme: str = "snow"

    FULL_SOLIDS = {"#", "X", "R", "T", "C", ">", "<", "O", "o", "I"}
    ONE_WAY = {"="}

    def tile_at(self, tx: int, ty: int) -> str:
        """Return the tile character at a given grid coordinate.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if 0 <= ty < self.height_tiles and 0 <= tx < self.width_tiles:
            return self.grid[ty][tx]
        return "."

    def set_tile(self, tx: int, ty: int, ch: str) -> None:
        """Replace the tile character at a given grid coordinate.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
            ch: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if 0 <= ty < self.height_tiles and 0 <= tx < self.width_tiles:
            self.grid[ty][tx] = ch

    def tile_rect(self, tx: int, ty: int) -> pygame.Rect:
        """Return the world-space rectangle for a tile coordinate.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)

    def tiles_in_aabb(self, aabb: pygame.Rect, pad_tiles: int = 1):
        """Return non-empty tiles near an axis-aligned rectangle.
        
        Args:
            aabb: Input value required by this function.
            pad_tiles: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        left = aabb.left // TILE - pad_tiles
        right = aabb.right // TILE + pad_tiles
        top = aabb.top // TILE - pad_tiles
        bottom = aabb.bottom // TILE + pad_tiles
        out = []
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for ty in range(top, bottom + 1):
            # Important condition: this branch protects an alternate state or edge case.
            if ty < 0 or ty >= self.height_tiles:
                continue
            row = self.grid[ty]
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for tx in range(left, right + 1):
                # Important condition: this branch protects an alternate state or edge case.
                if tx < 0 or tx >= self.width_tiles:
                    continue
                ch = row[tx]
                # Important condition: this branch protects an alternate state or edge case.
                if ch != ".":
                    out.append((tx, ty, ch))
        return out

def build_level():
    """Build the tile map, object spawn lists, metadata, and goal positions for the level.
    
    Args:
        None.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    import entities
    entities.BUTTON_META.clear()
    entities.LIFT_META.clear()
    entities.TARGET_META.clear()
    entities.TELEPORT_META.clear()
    entities.LASER_TILES.clear()

    W_TILES = 1200
    H_TILES = 80
    FLOOR_THICK = 3
    BEDROCK_ROW = 76

    grid = [["." for _ in range(W_TILES)] for _ in range(H_TILES)]

    state = {"offset_x": 0}

    def setc(x: int, y: int, ch: str):
        """Set a tile while applying the current level-building X offset.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
            ch: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        rx = x + state["offset_x"]
        # Important condition: this branch protects an alternate state or edge case.
        if 0 <= rx < W_TILES and 0 <= y < H_TILES:
            grid[y][rx] = ch

    def rect_fill(x0: int, x1: int, y0: int, y1: int, ch: str):
        """Fill a rectangular tile area with one tile character.
        
        Args:
            x0: Input value required by this function.
            x1: Input value required by this function.
            y0: Input value required by this function.
            y1: Input value required by this function.
            ch: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for x in range(x0, x1):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for y in range(y0, y1):
                setc(x, y, ch)

    def floor_fill(x0: int, x1: int, row: int = MAIN_FLOOR_ROW, thick: int = FLOOR_THICK, ch: str = "#"):
        """Fill a horizontal floor segment with solid tiles.
        
        Args:
            x0: Input value required by this function.
            x1: Input value required by this function.
            row: Input value required by this function.
            thick: Input value required by this function.
            ch: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for x in range(x0, x1):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for y in range(row, min(H_TILES, row + thick)):
                setc(x, y, ch)

    def floor_clear(x0: int, x1: int, row: int = MAIN_FLOOR_ROW, thick: int = FLOOR_THICK):
        """Clear a horizontal floor segment back to empty tiles.
        
        Args:
            x0: Input value required by this function.
            x1: Input value required by this function.
            row: Input value required by this function.
            thick: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for x in range(x0, x1):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for y in range(row, min(H_TILES, row + thick)):
                setc(x, y, ".")

    def platform(x0: int, x1: int, row: int, ch: str = "#"):
        """Place a one-tile-high platform segment.
        
        Args:
            x0: Input value required by this function.
            x1: Input value required by this function.
            row: Input value required by this function.
            ch: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for x in range(x0, x1):
            setc(x, row, ch)

    crate_spawns: list[Tuple[int, int]] = []
    button_spawns: list[Tuple[int, int]] = []
    lift_specs: list[Tuple[int, int, int]] = []
    goal_tiles: list[Tuple[int, int]] = []

    def place_teleporter(tx: int, ty: int, dest_tx: int, dest_ty: int):
        """Place a teleporter tile and register its destination metadata.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
            dest_tx: Input value required by this function.
            dest_ty: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, ty, "P")
        rx = tx + state["offset_x"]
        rdest_x = dest_tx + state["offset_x"]
        entities.TELEPORT_META[(rx * TILE, ty * TILE)] = (rdest_x * TILE, dest_ty * TILE)

    def place_laser(tx: int, ty: int):
        """Place a laser tile and register it for timed updates.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, ty, "Z")
        rx = tx + state["offset_x"]
        entities.LASER_TILES.append((rx, ty))

        button_objects = []

        
        bunker_btn = Button(20, 10)

        
        bunker_btn.linked_doors = [(22, 10), (22, 11), (22, 12)]

        button_objects.append(bunker_btn)

    def place_crate(tx: int, top_row: int):
        """Register a crate spawn and clear the space around it.
        
        Args:
            tx: Input value required by this function.
            top_row: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        rx = tx + state["offset_x"]
        crate_spawns.append((rx * TILE, top_row * TILE))
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for dx in range(3):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for dy in range(3):
                setc(tx + dx, top_row + dy, ".")

    def place_button(tx: int, floor_row: int):
        """Place a basic button and register its spawn position.
        
        Args:
            tx: Input value required by this function.
            floor_row: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, floor_row - 1, "B")
        rx = tx + state["offset_x"]
        button_spawns.append((rx * TILE, (floor_row - 1) * TILE))

    def place_button_with_doors(tx: int, floor_row: int, doors_list: list):
        """Place a button and connect it to door tiles.
        
        Args:
            tx: Input value required by this function.
            floor_row: Input value required by this function.
            doors_list: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, floor_row - 1, "B")
        rx = tx + state["offset_x"]
        px, py = rx * TILE, (floor_row - 1) * TILE
        button_spawns.append((px, py))
        shifted_doors = [(dx + state["offset_x"], dy) for dx, dy in doors_list]
        entities.BUTTON_META[(px, py)] = {"heavy": False, "doors": shifted_doors}

    def place_heavy_button_with_doors(tx: int, floor_row: int, doors_list: list):
        """Place a heavy button and connect it to door tiles.
        
        Args:
            tx: Input value required by this function.
            floor_row: Input value required by this function.
            doors_list: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, floor_row - 1, "B")
        rx = tx + state["offset_x"]
        px, py = rx * TILE, (floor_row - 1) * TILE
        button_spawns.append((px, py))
        shifted_doors = [(dx + state["offset_x"], dy) for dx, dy in doors_list]
        entities.BUTTON_META[(px, py)] = {"heavy": True, "doors": shifted_doors}

    def place_target_door(tx: int, ty: int, doors_list: list):
        """Place a target and connect it to door tiles.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
            doors_list: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, ty, "O")
        rx = tx + state["offset_x"]
        shifted_doors = [(dx + state["offset_x"], dy) for dx, dy in doors_list]
        entities.TARGET_META[(rx * TILE, ty * TILE)] = shifted_doors

    def place_hazard_h(tx: int, ty: int, end_tx: int, speed=200.0):
        """Place a horizontal moving hazard platform.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
            end_tx: Input value required by this function.
            speed: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        rx = tx + state["offset_x"]
        rend_tx = end_tx + state["offset_x"]
        px, py = rx * TILE, ty * TILE
        lift_specs.append((px, py, py))
        entities.LIFT_META[(px, py, py)] = {"is_horiz": True, "right_x": rend_tx * TILE, "speed": speed,
                                            "is_hazard": True}

    def place_goal(tx: int, ty: int):
        """Place a goal tile and register it.
        
        Args:
            tx: Input value required by this function.
            ty: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        setc(tx, ty, "G")
        rx = tx + state["offset_x"]
        goal_tiles.append((rx, ty))

    # ============================================================
    
    # ============================================================
    rect_fill(0, W_TILES, BEDROCK_ROW, H_TILES, "#")
    rect_fill(0, 5, 0, H_TILES, "#")
    rect_fill(W_TILES - 5, W_TILES, 0, H_TILES, "#")

    
    floor_fill(0, W_TILES, MAIN_FLOOR_ROW, FLOOR_THICK, "#")

    
    spawn1_px = (6 * TILE, 55 * TILE)
    spawn2_px = (8 * TILE, 55 * TILE)

    # ============================================================
    
    # ============================================================
    state["offset_x"] = -1080

    
    floor_clear(1100, 1250, MAIN_FLOOR_ROW, FLOOR_THICK)
    rect_fill(1100, 1250, 65, 68, "S")

    platform(1085, 1102, 58, "#")

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i in range(15):
        setc(1104 + i * 2, 57 - i, "C")

    place_hazard_h(1112, 50, 1118, 160.0)
    place_hazard_h(1122, 42, 1128, 180.0)

    platform(1134, 1138, 42, "#")

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i in range(10):
        setc(1140 + i, 41 - i, "C")

    place_hazard_h(1145, 33, 1152, 220.0)

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i in range(8):
        setc(1151 + i * 2, 32 + i, "C")

    platform(1167, 1180, 40, "#")
    rect_fill(1185, 1190, 5, 70, "W")

    platform(1195, 1250, 20, "#")

    place_hazard_h(1200, 19, 1210, 200.0)
    place_hazard_h(1215, 19, 1225, 300.0)
    place_hazard_h(1230, 19, 1245, 450.0)

    
    state["offset_x"] = 0
    platform(170, 174, 20, "#")
    platform(174, 178, 24, "#")
    platform(178, 185, 28, "#")

    # ============================================================
    
    # ============================================================
    state["offset_x"] = -805

    
    rect_fill(1090, 1093, 30, 59, "#")
    main_door_tiles = [(x, y) for x in range(1090, 1093) for y in range(30, 58)]

    
    rect_fill(990, 1110, 5, 35, "#")  
    rect_fill(1000, 1100, 10, 30, ".")  
    platform(990, 1015, 28, "#")  

    
    rect_fill(990, 1000, 24, 28, ".")

    rect_fill(1015, 1075, 29, 30, "S")  
    rect_fill(1015, 1075, 10, 11, "S")  

    platform(1020, 1023, 24, "I")
    platform(1033, 1036, 20, "I")
    platform(1047, 1050, 24, "I")
    platform(1062, 1075, 20, "I")

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for y in range(15, 28):
        place_laser(1028, y)
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for y in range(12, 22):
        place_laser(1042, y)
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for y in range(15, 28):
        place_laser(1056, y)

    platform(1075, 1100, 28, "#")  

    
    place_target_door(1085, 25, main_door_tiles)

    
    place_teleporter(1090, 27, 1080, 57)

    
    state["offset_x"] = 0
    
    
    rect_fill(288, 292, 28, 50, "#")
    platform(270, 304, 59, "#")

    # ============================================================
    
    # ============================================================
    state["offset_x"] = -508

    floor_clear(810, 950, MAIN_FLOOR_ROW, FLOOR_THICK)
    rect_fill(810, 950, 65, 68, "S")

    platform(812, 816, 59, "T")
    platform(821, 825, 52, "T")
    platform(830, 834, 45, "T")
    platform(839, 843, 38, "T")

    platform(848, 858, 30, "#")

    platform(863, 867, 30, "T")
    platform(873, 877, 28, "T")
    platform(883, 887, 26, "T")
    platform(893, 897, 24, "T")
    platform(903, 907, 22, "T")
    platform(913, 917, 20, "T")

    platform(923, 940, 20, "#")
    platform(942, 945, 30, "#")
    platform(945, 950, 40, "#")

    
    state["offset_x"] = 0
    platform(442, 446, 40, "#")
    platform(446, 450, 43, "#")

    # ============================================================
    
    # ============================================================
    state["offset_x"] = -1000

    
    platform(1450, 1455, 45, "#")  
    
    platform(1460, 1600, 45, "#")  

    
    rect_fill(1480, 1482, 35, 45, "#")
    place_button_with_doors(1470, 60, [(x, y) for x in range(1480, 1482) for y in range(35, 45)])

    
    rect_fill(1495, 1497, 46, 60, "#")
    place_target_door(1485, 40, [(x, y) for x in range(1495, 1497) for y in range(46, 60)])

    
    rect_fill(1530, 1532, 46, 60, "#")
    place_button_with_doors(1510, 45, [(x, y) for x in range(1530, 1532) for y in range(46, 60)])

    
    place_crate(1540, 57)
    rect_fill(1570, 1572, 35, 45, "#")
    place_button_with_doors(1560, 60, [(x, y) for x in range(1570, 1572) for y in range(35, 45)])

    
    rect_fill(1620, 1623, 30, 60, "#")
    place_heavy_button_with_doors(1610, 60, [(x, y) for x in range(1620, 1623) for y in range(30, 60)])

    platform(1623, 1650, 58, "#")

    
    
    place_goal(1640, 57)



    level = Level(
        grid=grid,
        width_tiles=W_TILES,
        height_tiles=H_TILES,
        width_px=W_TILES * TILE,
        height_px=H_TILES * TILE,
        spawn1_px=spawn1_px,
        spawn2_px=spawn2_px,
        theme="snow"
    )
    entities.LEVEL_REF = level

    return level, crate_spawns, button_spawns, lift_specs, goal_tiles
