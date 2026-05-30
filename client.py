# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: client.py
# Description: Client-side game code. Connects to the server, sends player input, receives game state, and renders the game UI.
# ========================================

import os
import pygame
import socket
import pickle
import time
import sys
import math
import threading
import struct
import logging
from pathlib import Path

from level import build_level, TILE
import entities
import themes
from ai_helper import get_ai_hint

# Client display constants.
WINDOW_W = 1280
WINDOW_H = 720
FPS = 60
VIEW_SCALE = 0.65

from entities import Player, Crate, Lift, Button, InputFrame, update_level_mechanics

# =========================
# File logging
# =========================
# Logs are written only to logs/jojo_game.log and are not printed to the Run console.
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE_PATH = LOGS_DIR / "jojo_game.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(filename=str(LOG_FILE_PATH), level=logging.INFO, format=LOG_FORMAT, encoding="utf-8")
logger = logging.getLogger("jojo.client")



def draw_colored_projectiles(screen, camera, state):
    """Draw projectile fallback graphics using simple colored shapes.
    
    Args:
        screen: Input value required by this function.
        camera: Input value required by this function.
        state: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if not state:
        return

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for pr in state.get("projectiles", []):
        try:
            px = pr[0]
            py = pr[1]

            
            
            kind = "bottlecap"
            # Important condition: this branch protects an alternate state or edge case.
            if len(pr) >= 3 and isinstance(pr[2], str):
                kind = pr[2]
            elif len(pr) >= 5 and isinstance(pr[4], str):
                kind = pr[4]
        except Exception:
            continue

        sx, sy = camera.world_to_screen(px, py)

        # Important condition: this branch protects an alternate state or edge case.
        if kind == "bubble":
            
            pygame.draw.circle(screen, (170, 230, 255), (sx, sy), 12)
            pygame.draw.circle(screen, (80, 160, 230), (sx, sy), 12, 2)
            pygame.draw.circle(screen, (245, 255, 255), (sx - 4, sy - 4), 4)
            pygame.draw.circle(screen, (220, 245, 255), (sx + 4, sy + 3), 3, 1)
        else:
            
            pygame.draw.circle(screen, (210, 20, 30), (sx, sy), 9)
            pygame.draw.circle(screen, (120, 0, 10), (sx, sy), 9, 2)
            pygame.draw.circle(screen, (255, 170, 170), (sx - 3, sy - 3), 3)
            pygame.draw.line(screen, (255, 90, 90), (sx - 18, sy), (sx - 8, sy), 3)


_PROJECTILE_IMAGE_CACHE = {}


def _client_asset_path(filename: str) -> str:
    """Build an absolute path to an asset used by the client.
    
    Args:
        filename: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)


def _load_projectile_image(filename: str, size):
    """Load, scale, and cache a projectile image asset.
    
    Args:
        filename: Input value required by this function.
        size: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    key = (filename, size)
    # Important condition: this branch protects an alternate state or edge case.
    if key in _PROJECTILE_IMAGE_CACHE:
        return _PROJECTILE_IMAGE_CACHE[key]

    path = _client_asset_path(filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, size)
        _PROJECTILE_IMAGE_CACHE[key] = img
        logger.info(f"[PROJECTILE IMAGE OK] loaded {path}")
        return img
    except Exception as e:
        logger.info(f"[PROJECTILE IMAGE ERROR] Could not load {path}: {e}")
        _PROJECTILE_IMAGE_CACHE[key] = None
        return None


def draw_projectiles_with_images(screen, camera, state):
    """Draw projectiles using image assets when available, with shape fallbacks.
    
    Args:
        screen: Input value required by this function.
        camera: Input value required by this function.
        state: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if not state:
        return

    projectiles = state.get("projectiles", [])
    # Important loop: iterates through game objects that must be processed every frame or build step.
    for pr in projectiles:
        try:
            px = pr[0]
            py = pr[1]

            
            
            kind = "bottlecap"
            # Important condition: this branch protects an alternate state or edge case.
            if len(pr) >= 3 and isinstance(pr[2], str):
                kind = pr[2]
            elif len(pr) >= 5 and isinstance(pr[4], str):
                kind = pr[4]
        except Exception:
            continue

        sx, sy = camera.world_to_screen(px, py)

        # Important condition: this branch protects an alternate state or edge case.
        if kind == "bubble":
            img = _load_projectile_image("caesar_bubble.png", (34, 34))
            # Important condition: this branch protects an alternate state or edge case.
            if img:
                screen.blit(img, (sx - img.get_width() // 2, sy - img.get_height() // 2))
            else:
                pygame.draw.circle(screen, (160, 220, 255), (sx, sy), 14)
        else:
            img = _load_projectile_image("joseph_cap.png", (26, 26))
            # Important condition: this branch protects an alternate state or edge case.
            if img:
                angle = (pygame.time.get_ticks() * 0.9) % 360
                img_rot = pygame.transform.rotozoom(img, angle, 1.0)
                screen.blit(img_rot, (sx - img_rot.get_width() // 2, sy - img_rot.get_height() // 2))
            else:
                pygame.draw.circle(screen, (230, 40, 40), (sx, sy), 10)


_PROJECTILE_IMAGE_CACHE = {}


def _client_asset_path(filename: str) -> str:
    """Build an absolute path to an asset used by the client.
    
    Args:
        filename: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)


def _load_projectile_image(filename: str, size: tuple[int, int]):
    """Load, scale, and cache a projectile image asset.
    
    Args:
        filename: Input value required by this function.
        size: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    key = (filename, size)
    # Important condition: this branch protects an alternate state or edge case.
    if key in _PROJECTILE_IMAGE_CACHE:
        return _PROJECTILE_IMAGE_CACHE[key]

    try:
        path = _client_asset_path(filename)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, size)
        _PROJECTILE_IMAGE_CACHE[key] = img
        return img
    except Exception as e:
        logger.info(f"[PROJECTILE IMAGE ERROR] Could not load {filename}: {e}")
        _PROJECTILE_IMAGE_CACHE[key] = None
        return None






# =========================
# Communication constants
# =========================
# Every value used by the socket protocol is stored in a named constant.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)

PROTOCOL_HEADER_SIZE_BYTES = 4
PROTOCOL_LENGTH_FORMAT = "!I"
PROTOCOL_LENGTH_INDEX = 0
MIN_MESSAGE_SIZE_BYTES = 1
MAX_MESSAGE_SIZE_MEGABYTES = 10
BYTES_IN_KILOBYTE = 1024
MAX_MESSAGE_SIZE_BYTES = MAX_MESSAGE_SIZE_MEGABYTES * BYTES_IN_KILOBYTE * BYTES_IN_KILOBYTE

def recv_exact(sock, n):
    """Receive exactly the requested number of bytes from a socket.
    
    Args:
        sock: Input value required by this function.
        n: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    assert sock is not None, "recv_exact requires an open socket"
    assert isinstance(n, int) and n > 0, "recv_exact requires a positive byte count"
    data = b""
    # Important loop: keeps running until the game, network, or UI state changes.
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        # Important condition: this branch protects an alternate state or edge case.
        if not chunk:
            logger.warning("Socket closed while waiting for %s bytes; received %s bytes", n, len(data))
            return None
        data += chunk
    return data


def send_msg(sock, obj):
    """Serialize one Python object and send it using the length-prefixed network protocol.
    
    Args:
        sock: Input value required by this function.
        obj: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    assert sock is not None, "send_msg requires an open socket"
    payload = pickle.dumps(obj)
    if not (MIN_MESSAGE_SIZE_BYTES <= len(payload) <= MAX_MESSAGE_SIZE_BYTES):
        raise ValueError("Outgoing message size is outside the allowed range")
    assert payload, "Serialized payload must not be empty"
    header = struct.pack(PROTOCOL_LENGTH_FORMAT, len(payload))
    logger.debug("Sending %s-byte message of type %s", len(payload), type(obj).__name__)
    sock.sendall(header + payload)


def recv_msg(sock):
    """Read one complete length-prefixed message and deserialize it.
    
    Args:
        sock: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    assert sock is not None, "recv_msg requires an open socket"
    header = recv_exact(sock, PROTOCOL_HEADER_SIZE_BYTES)
    # Important condition: this branch protects an alternate state or edge case.
    if header is None:
        return None
    msg_len = struct.unpack(PROTOCOL_LENGTH_FORMAT, header)[PROTOCOL_LENGTH_INDEX]
    if not (MIN_MESSAGE_SIZE_BYTES <= msg_len <= MAX_MESSAGE_SIZE_BYTES):
        raise ValueError("Incoming message size is outside the allowed range")
    assert msg_len > 0, "Message length must be positive after validation"
    payload = recv_exact(sock, msg_len)
    # Important condition: this branch protects an alternate state or edge case.
    if payload is None:
        return None
    obj = pickle.loads(payload)
    logger.debug("Received %s-byte message of type %s", msg_len, type(obj).__name__)
    return obj

SPLIT_DIALOGUE = [
    ("Joseph", "Looks like there are two different paths. We can't go together from here."),
    ("Caesar", "Right, we have to split up. I'll take the high road, you go low!"),
    ("Joseph", "Got it. Don't fall down up there!")
]


class AutoDialogue:
    """Controls a timed dialogue sequence shown on the client.
    
    Constructor Args:
        script: Value used to initialize this object."""
    def __init__(self, script):
        """Execute the __init__ operation.
        
        Args:
            script: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.script = script
        self.active = False
        self.current_idx = 0
        self.timer = 0.0
        self.time_per_line = 4.0

    def trigger(self):
        """Execute the trigger operation.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if not self.active and self.current_idx == 0:
            self.active = True
            self.timer = 0.0

    def update_and_draw(self, dt, screen, font):
        """Execute the update_and_draw operation.
        
        Args:
            dt: Input value required by this function.
            screen: Input value required by this function.
            font: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if not self.active: return
        self.timer += dt
        # Important condition: this branch protects an alternate state or edge case.
        if self.timer >= self.time_per_line:
            self.timer = 0.0
            self.current_idx += 1
            # Important condition: this branch protects an alternate state or edge case.
            if self.current_idx >= len(self.script):
                self.active = False
                return
        speaker, text = self.script[self.current_idx]
        dialog_h = 110
        overlay = pygame.Surface((WINDOW_W, dialog_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, WINDOW_H - dialog_h))
        color = (150, 200, 255) if speaker == "Joseph" else (255, 200, 150)
        speaker_img = font.render(speaker + ":", True, color)
        screen.blit(speaker_img, (50, WINDOW_H - dialog_h + 20))
        text_img = font.render(text, True, (240, 240, 240))
        screen.blit(text_img, (70, WINDOW_H - dialog_h + 55))


def show_lobby_screen(screen, clock, my_id, shared_state, client):
    """Display and update the pre-game lobby screen until both players are ready.
    
    Args:
        screen: Input value required by this function.
        clock: Input value required by this function.
        my_id: Input value required by this function.
        shared_state: Input value required by this function.
        client: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    title_font = pygame.font.SysFont("consolas", 56, bold=True)
    info_font = pygame.font.SysFont("consolas", 25, bold=True)
    key_font = pygame.font.SysFont("consolas", 20)
    mode_font = pygame.font.SysFont("consolas", 23, bold=True)

    player_name = "JOSEPH" if my_id == 0 else "CAESAR"
    player_color = (150, 200, 255) if my_id == 0 else (255, 200, 150)

    my_ready = False
    waiting = True
    selected_game_mode = "normal"

    # Important loop: keeps running until the game, network, or UI state changes.
    while waiting:
        screen.fill((20, 20, 30))

        title = title_font.render("JOJO CO-OP LOBBY", True, (255, 215, 0))
        screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 42))

        you_are = info_font.render(f"YOU ARE: {player_name}", True, player_color)
        screen.blit(you_are, (WINDOW_W // 2 - you_are.get_width() // 2, 115))

        both_connected = False
        p1_ready = False
        p2_ready = False

        with shared_state["lock"]:
            # Important condition: this branch protects an alternate state or edge case.
            if shared_state["data"] is not None:
                glob = shared_state["data"].get("global", {})
                # Important condition: this branch protects an alternate state or edge case.
                if glob.get("players_connected", 0) == 2:
                    both_connected = True

                ready_list = glob.get("players_ready", [False, False])
                p1_ready = ready_list[0]
                p2_ready = ready_list[1]
                selected_game_mode = glob.get("game_mode", selected_game_mode)

        # Important condition: this branch protects an alternate state or edge case.
        if p1_ready and p2_ready:
            waiting = False
            break

        # =========================
        # Game Mode Panel
        # =========================
        mode_title = mode_font.render("GAME MODE", True, (255, 215, 0))
        screen.blit(mode_title, (WINDOW_W // 2 - mode_title.get_width() // 2, 155))

        normal_selected = selected_game_mode == "normal"
        speed_selected = selected_game_mode == "speedrun"

        normal_color = (100, 255, 140) if normal_selected else (170, 170, 170)
        speed_color = (100, 255, 140) if speed_selected else (170, 170, 170)

        normal_txt = mode_font.render("[1] NORMAL", True, normal_color)
        speed_txt = mode_font.render("[2] SPEEDRUN", True, speed_color)

        screen.blit(normal_txt, (WINDOW_W // 2 - 240, 190))
        screen.blit(speed_txt, (WINDOW_W // 2 + 40, 190))

        # Important condition: this branch protects an alternate state or edge case.
        if selected_game_mode == "speedrun":
            desc = "Speedrun: finish the level before the timer ends."
        else:
            desc = "Normal: finish the level without a time limit."

        desc_txt = key_font.render(desc, True, (220, 220, 220))
        screen.blit(desc_txt, (WINDOW_W // 2 - desc_txt.get_width() // 2, 225))

        # Important condition: this branch protects an alternate state or edge case.
        if my_id == 0 and not my_ready:
            mode_hint = "Player 1: press 1 or 2 to choose mode, then ENTER when ready"
        elif my_id == 0 and my_ready:
            mode_hint = "Mode locked for you. Waiting for partner..."
        else:
            mode_hint = "Player 2: wait for Player 1 to choose the mode"

        mode_hint_txt = key_font.render(mode_hint, True, (255, 235, 160))
        screen.blit(mode_hint_txt, (WINDOW_W // 2 - mode_hint_txt.get_width() // 2, 252))

        # =========================
        # Controls Panel
        # =========================
        controls = [
            "CONTROLS:",
            "ARROWS or ADWS - Move     UP - Jump / Interaction",
            "SPACE  - Shoot    H  - Show AI Hint",
            "L       - Return to Lobby during game",
            "R      - Restart  ESC - Exit after end"

        ]

        y_off = 292
        line_gap = 27

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for line in controls:
            color = (255, 215, 0) if line == "CONTROLS:" else (210, 210, 210)
            txt = key_font.render(line, True, color)
            screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, y_off))
            y_off += line_gap

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for event in pygame.event.get():
            # Important condition: this branch protects an alternate state or edge case.
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Important condition: this branch protects an alternate state or edge case.
            if event.type == pygame.KEYDOWN:
                # Important condition: this branch protects an alternate state or edge case.
                if my_id == 0 and not my_ready:
                    # Important condition: this branch protects an alternate state or edge case.
                    if event.key == pygame.K_1:
                        selected_game_mode = "normal"
                    # Important condition: this branch protects an alternate state or edge case.
                    if event.key == pygame.K_2:
                        selected_game_mode = "speedrun"

                # Important condition: this branch protects an alternate state or edge case.
                if event.key == pygame.K_RETURN and both_connected:
                    my_ready = True

        out_input = InputFrame()
        out_input.ready = my_ready

        
        
        out_input.selected_game_mode = selected_game_mode

        try:
            send_msg(client, out_input)
        except:
            pass

        ready_y = 430
        status_y = 490

        # Important condition: this branch protects an alternate state or edge case.
        if both_connected:
            c1 = (100, 255, 100) if p1_ready else (255, 100, 100)
            c2 = (100, 255, 100) if p2_ready else (255, 100, 100)

            t1 = key_font.render(f"Joseph: {'READY' if p1_ready else 'WAITING'}", True, c1)
            t2 = key_font.render(f"Caesar: {'READY' if p2_ready else 'WAITING'}", True, c2)

            screen.blit(t1, (WINDOW_W // 2 - 220, ready_y))
            screen.blit(t2, (WINDOW_W // 2 + 40, ready_y))

        # Important condition: this branch protects an alternate state or edge case.
        if not both_connected:
            status_txt = info_font.render("Waiting for Player 2 to connect...", True, (255, 100, 100))
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if not my_ready:
                status_txt = info_font.render("PRESS ENTER WHEN READY", True, (255, 255, 100))
            else:
                status_txt = info_font.render("Waiting for partner...", True, (100, 255, 100))

        screen.blit(status_txt, (WINDOW_W // 2 - status_txt.get_width() // 2, status_y))

        pygame.display.flip()
        clock.tick(FPS)


class Camera1P:
    """Camera used by one client to follow its player through the level.
    
    Constructor Args:
        w: Value used to initialize this object.
        h: Value used to initialize this object."""
    def __init__(self, w, h):
        """Execute the __init__ operation.
        
        Args:
            w: Input value required by this function.
            h: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        self.w, self.h = int(w), int(h)
        self.x, self.y = 0.0, 0.0
        self.follow_hz = 5.0
        self.margin_x, self.margin_y = max(150, int(w * 0.25)), max(120, int(h * 0.25))

    def view_rect_world(self):
        """Return the camera viewport rectangle in world coordinates.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt, target_rect, level_w, level_h, look_x, look_y):
        """Execute the update operation.
        
        Args:
            dt: Input value required by this function.
            target_rect: Input value required by this function.
            level_w: Input value required by this function.
            level_h: Input value required by this function.
            look_x: Input value required by this function.
            look_y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        target = self.view_rect_world()
        # Important condition: this branch protects an alternate state or edge case.
        if target_rect.left < target.left + self.margin_x: target.left = target_rect.left - self.margin_x
        # Important condition: this branch protects an alternate state or edge case.
        if target_rect.right > target.right - self.margin_x: target.left = target_rect.right + self.margin_x - self.w
        # Important condition: this branch protects an alternate state or edge case.
        if target_rect.top < target.top + self.margin_y: target.top = target_rect.top - self.margin_y
        # Important condition: this branch protects an alternate state or edge case.
        if target_rect.bottom > target.bottom - self.margin_y: target.top = target_rect.bottom + self.margin_y - self.h
        target.left = int(entities.clamp(target.left + look_x, 0, max(0, level_w - self.w)))
        target.top = int(entities.clamp(target.top + look_y, 0, max(0, level_h - self.h)))
        s = 1.0 - math.exp(-dt * self.follow_hz)
        self.x = entities.lerp(self.x, float(target.left), s)
        self.y = entities.lerp(self.y, float(target.top), s)

    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates.
        
        Args:
            x: Input value required by this function.
            y: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        return int(x - self.x), int(y - self.y)


def draw_lift(surf: pygame.Surface, lf: Lift, camera: Camera1P, gtime: float):
    """Draw one moving platform or hazard lift on the screen.
    
    Args:
        surf: Input value required by this function.
        lf: Input value required by this function.
        camera: Input value required by this function.
        gtime: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    sx, sy = camera.world_to_screen(lf.rect.x, lf.rect.y)
    r = pygame.Rect(sx, sy, lf.rect.w, lf.rect.h)
    # Important condition: this branch protects an alternate state or edge case.
    if getattr(lf, "is_hazard", False):
        pygame.draw.rect(surf, (220, 60, 70), r, border_radius=8)
        pygame.draw.rect(surf, (90, 20, 25), r, 2, border_radius=8)
    else:
        pygame.draw.rect(surf, (120, 135, 160), r, border_radius=8)
        pygame.draw.rect(surf, (50, 60, 75), r, 2, border_radius=8)
    k = (gtime * 2.0) % 1.0
    pygame.draw.rect(surf, (255, 255, 255), (r.x + int(k * (r.w - 24)), r.y + 4, 18, 4), border_radius=2)


def draw_crate(surf: pygame.Surface, c: Crate, camera: Camera1P):
    """Draw one crate at its camera-adjusted screen position.
    
    Args:
        surf: Input value required by this function.
        c: Input value required by this function.
        camera: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    sx, sy = camera.world_to_screen(c.rect.x, c.rect.y)
    r = pygame.Rect(sx, sy, c.rect.w, c.rect.h)
    pygame.draw.rect(surf, (150, 105, 70), r, border_radius=10)
    pygame.draw.rect(surf, (60, 40, 25), r, 3, border_radius=10)
    pygame.draw.line(surf, (80, 55, 35), (r.x + 10, r.y + 10), (r.right - 12, r.bottom - 12), 4)
    pygame.draw.line(surf, (80, 55, 35), (r.x + 10, r.bottom - 12), (r.right - 12, r.y + 10), 4)


def draw_button(surf: pygame.Surface, b: Button, camera: Camera1P):
    """Draw one floor button and its pressed/unpressed state.
    
    Args:
        surf: Input value required by this function.
        b: Input value required by this function.
        camera: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    sx, sy = camera.world_to_screen(b.rect.x, b.rect.y)
    base_r = pygame.Rect(sx + 4, sy + TILE - 10, TILE - 8, 10)
    # Important condition: this branch protects an alternate state or edge case.
    if b.pressed:
        btn_r = pygame.Rect(sx + 8, sy + TILE - 12, TILE - 16, 12)
        color = (100, 30, 30)
    else:
        btn_r = pygame.Rect(sx + 8, sy + TILE - 16, TILE - 16, 16)
        color = (180, 50, 50)
    pygame.draw.rect(surf, (80, 80, 90), base_r, border_radius=4)
    pygame.draw.rect(surf, color, btn_r, border_radius=4)


def draw_respawn_flags(surf: pygame.Surface, players, camera: Camera1P):
    """Draw small flags that mark each player respawn position.
    
    Args:
        surf: Input value required by this function.
        players: Input value required by this function.
        camera: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    flag_colors = [(80, 170, 255), (255, 190, 80)]

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i, p in enumerate(players):
        try:
            rx, ry = getattr(p, "respawn_pos", (p.rect.x, p.rect.y))
            base_x = int(rx + p.w // 2)
            base_y = int(ry + p.h)
            sx, sy = camera.world_to_screen(base_x, base_y)

            
            if sx < -80 or sx > surf.get_width() + 80 or sy < -120 or sy > surf.get_height() + 80:
                continue

            color = flag_colors[i % len(flag_colors)]

            
            pygame.draw.line(surf, (35, 35, 35), (sx, sy), (sx, sy - 44), 4)
            pygame.draw.line(surf, (230, 230, 230), (sx + 1, sy), (sx + 1, sy - 44), 1)

            
            points = [(sx + 3, sy - 43), (sx + 34, sy - 34), (sx + 3, sy - 24)]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (40, 40, 40), points, 2)

            
            pygame.draw.circle(surf, (40, 40, 40), (sx, sy), 6)
            pygame.draw.circle(surf, color, (sx, sy), 4)

        except Exception:
            pass


HEART_IMG = None


def draw_ui(surf, lives, timer_str, font, timer_label="Time"):
    """Draw the player interface, timer, lives, countdown, and game status text.
    
    Args:
        surf: Input value required by this function.
        lives: Input value required by this function.
        timer_str: Input value required by this function.
        font: Input value required by this function.
        timer_label: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    global HEART_IMG
    # Important condition: this branch protects an alternate state or edge case.
    if HEART_IMG is None:
        s = pygame.Surface((8, 8), pygame.SRCALPHA)
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for y, row in enumerate(["..OO..OO.", "OXXOOXXO", "OXXXXXXO", ".OXXXXO.", "..OXXO..", "...OO...", "........"]):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for x, c in enumerate(row):
                # Important condition: this branch protects an alternate state or edge case.
                if c == 'X':
                    s.set_at((x, y), (220, 40, 60))
                elif c == 'O':
                    s.set_at((x, y), (30, 20, 20))
        HEART_IMG = pygame.transform.scale(s, (32, 32))

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for i in range(lives): surf.blit(HEART_IMG, (40 + i * 36, 25))

    txt_time = font.render(f"{timer_label}: {timer_str}", True, (0, 0, 0))
    surf.blit(txt_time, (WINDOW_W - txt_time.get_width() - 30, 25))


def wrap_text(text, font, max_width):
    """Wrap text into lines that fit within a maximum pixel width.
    
    Args:
        text: Input value required by this function.
        font: Input value required by this function.
        max_width: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    words = text.split(" ")
    lines = []
    current_line = ""

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for word in words:
        test_line = current_line + (" " if current_line else "") + word

        # Important condition: this branch protects an alternate state or edge case.
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            # Important condition: this branch protects an alternate state or edge case.
            if current_line:
                lines.append(current_line)
            current_line = word

    # Important condition: this branch protects an alternate state or edge case.
    if current_line:
        lines.append(current_line)

    return lines


def draw_hint_box(surf, text, font):
    """Draw the AI hint overlay box.
    
    Args:
        surf: Input value required by this function.
        text: Input value required by this function.
        font: Input value required by this function.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    # Important condition: this branch protects an alternate state or edge case.
    if not text:
        return

    box_w = min(WINDOW_W - 80, 950)
    x = (WINDOW_W - box_w) // 2
    y = 70

    padding = 20
    title_h = 28
    line_gap = 6
    max_text_width = box_w - padding * 2

    lines = wrap_text(text, font, max_text_width)

    
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] += "..."

    box_h = padding * 2 + title_h + len(lines) * (font.get_height() + line_gap)

    overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    surf.blit(overlay, (x, y))

    pygame.draw.rect(surf, (255, 215, 0), (x, y, box_w, box_h), 3, border_radius=10)

    title = font.render("AI Hint - Press H", True, (255, 215, 0))
    surf.blit(title, (x + padding, y + 12))

    text_y = y + padding + title_h

    # Important loop: iterates through game objects that must be processed every frame or build step.
    for line in lines:
        msg = font.render(line, True, (255, 255, 255))
        surf.blit(msg, (x + padding, text_y))
        text_y += font.get_height() + line_gap


def run_network_game():
    """Start the client, connect to the server, receive state updates, and run the local game loop.
    
    Args:
        None.
    
    Returns:
        The result of the operation, or None when the function performs side effects only."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("JoJo Co-op - Connecting...")
    clock = pygame.time.Clock()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(SERVER_ADDRESS)

        first_msg = recv_msg(client)

        # Important condition: this branch protects an alternate state or edge case.
        if isinstance(first_msg, dict) and first_msg.get("type") == "SERVER_FULL":
            pygame.init()
            screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
            pygame.display.set_caption("Server Full")
            clock = pygame.time.Clock()

            font_big = pygame.font.SysFont("consolas", 54, bold=True)
            font_small = pygame.font.SysFont("consolas", 28, bold=True)
            font_hint = pygame.font.SysFont("consolas", 22, bold=True)

            message = first_msg.get("message", "Server is full. Only 2 players can play.")

            running_full_screen = True
            # Important loop: keeps running until the game, network, or UI state changes.
            while running_full_screen:
                # Important loop: iterates through game objects that must be processed every frame or build step.
                for event in pygame.event.get():
                    # Important condition: this branch protects an alternate state or edge case.
                    if event.type == pygame.QUIT:
                        running_full_screen = False

                    # Important condition: this branch protects an alternate state or edge case.
                    if event.type == pygame.KEYDOWN:
                        running_full_screen = False

                screen.fill((18, 18, 32))

                title = font_big.render("SERVER FULL", True, (255, 90, 90))
                msg = font_small.render(message, True, (255, 255, 255))
                msg2 = font_hint.render("Press any key to exit.", True, (190, 190, 190))

                screen.blit(
                    title,
                    (WINDOW_W // 2 - title.get_width() // 2, 240)
                )

                screen.blit(
                    msg,
                    (WINDOW_W // 2 - msg.get_width() // 2, 325)
                )

                screen.blit(
                    msg2,
                    (WINDOW_W // 2 - msg2.get_width() // 2, 380)
                )

                pygame.display.flip()
                clock.tick(60)

            client.close()
            pygame.quit()
            return

        my_id = first_msg
        assert my_id in (0, 1), "Server must assign player id 0 or 1"
        logger.info("Connected as Player %s", my_id + 1)
    except Exception as e:
        logger.exception("Connection error: %s", e)
        return

    shared_state = {"data": None, "lock": threading.Lock()}

    def receive_loop():
        """Continuously receive server snapshots in a background thread.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important loop: keeps running until the game, network, or UI state changes.
        while True:
            try:
                new_state = recv_msg(client)
                # Important condition: this branch protects an alternate state or edge case.
                if new_state is None: break
                with shared_state["lock"]:
                    shared_state["data"] = new_state
            except:
                break

    threading.Thread(target=receive_loop, daemon=True).start()

    show_lobby_screen(screen, clock, my_id, shared_state, client)

    pygame.display.set_caption(f"JoJo Co-op (Player {my_id + 1})")
    view_w, view_h = int(WINDOW_W / VIEW_SCALE), int(WINDOW_H / VIEW_SCALE)
    view = pygame.Surface((view_w, view_h))

    font_ui = pygame.font.SysFont("consolas", 22, bold=True)
    font_hint = pygame.font.SysFont("consolas", 18, bold=True)
    font_big = pygame.font.SysFont("consolas", 60, bold=True)

    level, crate_spawns, button_spawns, lift_specs, _ = build_level()
    entities.LEVEL_REF = level
    players = [Player("Joseph", 0, 0, "joseph", {}), Player("Caesar", 0, 0, "caesar", {})]
    crates = [Crate(x, y) for x, y in crate_spawns]
    lifts = [Lift(x, t_y, b_y) for x, t_y, b_y in lift_specs]
    buttons = [Button(x, y) for x, y in button_spawns]
    camera = Camera1P(view_w, view_h)

    dialogue = AutoDialogue(SPLIT_DIALOGUE)
    split_triggered = False
    gtime = 0.0
    look_x, look_y = 0.0, 0.0

    cur_projs = []
    lives, game_over, cleared = 3, False, False
    timer_str = "00:00:00"
    elapsed_timer_str = "00:00:00"
    timer_label = "Time"
    game_mode = "normal"
    time_up = False
    countdown = 0.0
    best_time_val = float('inf')
    is_new_record = False

    # AI hint system
    hint_text = ""
    hint_timer = 0.0
    last_game_state = None
    last_game_version = None
    return_to_lobby_sent = False

    def rebuild_local_level_after_restart():
        """Rebuild the client-side level objects after a restart or lobby return.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        nonlocal level, crate_spawns, button_spawns, lift_specs, players, crates, lifts, buttons
        nonlocal cur_projs, split_triggered, dialogue, hint_text, hint_timer

        level, crate_spawns, button_spawns, lift_specs, _ = build_level()
        entities.LEVEL_REF = level
        crates = [Crate(x, y) for x, y in crate_spawns]
        lifts = [Lift(x, t_y, b_y) for x, t_y, b_y in lift_specs]
        buttons = [Button(x, y) for x, y in button_spawns]

        
        for p in players:
            p.just_died = False

        cur_projs = []
        split_triggered = False
        dialogue = AutoDialogue(SPLIT_DIALOGUE)
        hint_text = ""
        hint_timer = 0.0

    running = True
    # Important loop: keeps running until the game, network, or UI state changes.
    while running:
        dt = clock.tick(FPS) / 1000.0
        gtime += dt

        # CLIENT SIDE SHOOT VISUAL TIMER
        
        
        try:
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for _p in players:
                # Important condition: this branch protects an alternate state or edge case.
                if not hasattr(_p, "_shoot_anim_timer"):
                    _p._shoot_anim_timer = 0.0
                # Important condition: this branch protects an alternate state or edge case.
                if not hasattr(_p, "network_shoot_timer"):
                    _p.network_shoot_timer = 0.0

                _p._shoot_anim_timer = max(0.0, _p._shoot_anim_timer - dt)
                _p.network_shoot_timer = max(0.0, _p.network_shoot_timer - dt)
                _p.network_shooting = _p.network_shoot_timer > 0.0
        except Exception:
            pass

        
        try:
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for _p in players:
                # Important condition: this branch protects an alternate state or edge case.
                if hasattr(_p, "_shoot_anim_timer"):
                    _p._shoot_anim_timer = max(0.0, _p._shoot_anim_timer - dt)
        except Exception:
            pass

        jump_p, shoot_p = False, False
        request_return_lobby = False

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for event in pygame.event.get():
            # Important condition: this branch protects an alternate state or edge case.
            if event.type == pygame.QUIT:
                running = False

            # Important condition: this branch protects an alternate state or edge case.
            if event.type == pygame.KEYDOWN:
                # Important condition: this branch protects an alternate state or edge case.
                if event.key == pygame.K_l:
                    request_return_lobby = True

                # Important condition: this branch protects an alternate state or edge case.
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    jump_p = True

                # Important condition: this branch protects an alternate state or edge case.
                if event.key == pygame.K_SPACE:
                    shoot_p = True
                    # FORCE LOCAL SHOOT IMAGE
                    try:
                        players[my_id]._shoot_anim_timer = 0.75
                    except Exception:
                        pass

                # Important condition: this branch protects an alternate state or edge case.
                if event.key == pygame.K_h:
                    with shared_state["lock"]:
                        current_state = shared_state["data"] if shared_state["data"] is not None else last_game_state
                    hint_text = get_ai_hint(current_state, my_id)
                    hint_timer = 5.0

        keys = pygame.key.get_pressed()
        my_in = InputFrame(
            left=keys[pygame.K_LEFT] or keys[pygame.K_a],
            right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
            down=keys[pygame.K_DOWN] or keys[pygame.K_s],
            jump_held=keys[pygame.K_UP] or keys[pygame.K_w],
            jump_pressed=jump_p,
            shoot_held=keys[pygame.K_SPACE],
            shoot_pressed=shoot_p,
            ready=not return_to_lobby_sent
        )

        
        if request_return_lobby:
            my_in.return_to_lobby = True
            my_in.ready = False
            return_to_lobby_sent = True

        # FORCE SHOOT IMAGE AFTER INPUTFRAME
        if shoot_p:
            try:
                players[my_id]._shoot_anim_timer = 0.1
            except Exception:
                pass

        # Important condition: this branch protects an alternate state or edge case.
        if game_over or cleared:
            # Important condition: this branch protects an alternate state or edge case.
            if keys[pygame.K_r]:
                my_in.restart = True
            # Important condition: this branch protects an alternate state or edge case.
            if keys[pygame.K_ESCAPE]:
                running = False

        # Important condition: this branch protects an alternate state or edge case.
        if game_over or cleared:
            # Important condition: this branch protects an alternate state or edge case.
            if keys[pygame.K_l]:
                my_in.return_to_lobby = True
                my_in.ready = False
                return_to_lobby_sent = True

        try:
            send_msg(client, my_in)
        except:
            break

        return_to_lobby_now = False

        with shared_state["lock"]:
            # Important condition: this branch protects an alternate state or edge case.
            if shared_state["data"]:
                s = shared_state["data"]
                last_game_state = s
                
                if not s.get("players_ready", [True, True])[0] and not s.get("players_ready", [True, True])[
                    1] and not s.get("global", {}).get("cleared", False) and not s.get("global", {}).get("game_over",
                                                                                                         False):
                    return_to_lobby_sent = False
                    show_lobby_screen(screen, clock, my_id, shared_state, client)
                    rebuild_local_level_after_restart()
                    continue

                current_game_version = s.get("global", {}).get("game_version", 0)
                # Important condition: this branch protects an alternate state or edge case.
                if last_game_version is None:
                    last_game_version = current_game_version
                elif current_game_version != last_game_version:
                    rebuild_local_level_after_restart()
                    last_game_version = current_game_version

                # Important condition: this branch protects an alternate state or edge case.
                if "timer" in s["global"]:
                    timer_val = s["global"].get("timer", 0.0)
                    game_mode = s["global"].get("game_mode", "normal")
                    time_limit = s["global"].get("time_limit", 300.0)
                    time_up = s["global"].get("time_up", False)

                    entities.GLOBAL_STATE["timer"] = timer_val

                    
                    mins = int(timer_val) // 60
                    secs = int(timer_val) % 60
                    mils = int((timer_val * 100) % 100)
                    elapsed_timer_str = f"{mins:02d}:{secs:02d}:{mils:02d}"

                    
                    if game_mode == "speedrun":
                        time_left = max(0.0, time_limit - timer_val)
                        lmins = int(time_left) // 60
                        lsecs = int(time_left) % 60
                        timer_str = f"{lmins:02d}:{lsecs:02d}"
                        timer_label = "Time Left"
                    else:
                        timer_str = elapsed_timer_str
                        timer_label = "Time"

                # Important condition: this branch protects an alternate state or edge case.
                if "targets_hit" in s:
                    # Important loop: iterates through game objects that must be processed every frame or build step.
                    for tx, ty in s["targets_hit"]:
                        # Important condition: this branch protects an alternate state or edge case.
                        if level.tile_at(tx, ty) == "O":
                            level.set_tile(tx, ty, "o")
                            k = (tx * entities.TILE_DEFAULT, ty * entities.TILE_DEFAULT)
                            # Important condition: this branch protects an alternate state or edge case.
                            if k in entities.TARGET_META:
                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for dx, dy in entities.TARGET_META[k]: level.set_tile(dx, dy, ".")

                # Important loop: iterates through game objects that must be processed every frame or build step.
                for i, p_d in enumerate(s["players"]):
                    players[i].rect.topleft = (int(p_d[0]), int(p_d[1]))
                    players[i]._anim_i, players[i].facing, players[i].just_died = p_d[2], p_d[3], p_d[4]
                    # Important condition: this branch protects an alternate state or edge case.
                    if len(p_d) > 5:
                        players[i].h = p_d[5]
                    # Important condition: this branch protects an alternate state or edge case.
                    if len(p_d) > 7:
                        players[i].respawn_pos = (int(p_d[6]), int(p_d[7]))

                    # Important condition: this branch protects an alternate state or edge case.
                    if len(p_d) >= 9:
                        shoot_timer = float(p_d[8])
                        # Important condition: this branch protects an alternate state or edge case.
                        if shoot_timer > 0.0:
                            players[i].network_shoot_timer = max(getattr(players[i], "network_shoot_timer", 0.0),
                                                                 shoot_timer)
                    players[i].network_shooting = getattr(players[i], "network_shoot_timer", 0.0) > 0.0
                # Important loop: iterates through game objects that must be processed every frame or build step.
                for i, c_p in enumerate(s["crates"]): crates[i].rect.topleft = c_p
                # Important loop: iterates through game objects that must be processed every frame or build step.
                for i, l_p in enumerate(s["lifts"]): lifts[i].rect.topleft = l_p
                # Important loop: iterates through game objects that must be processed every frame or build step.
                for i, b_s in enumerate(s["buttons"]):
                    # Important condition: this branch protects an alternate state or edge case.
                    if buttons[i].pressed != b_s:
                        buttons[i].pressed = b_s
                        # Important condition: this branch protects an alternate state or edge case.
                        if buttons[i].linked_doors:
                            # Important loop: iterates through game objects that must be processed every frame or build step.
                            for tx, ty in buttons[i].linked_doors: level.set_tile(tx, ty, "." if b_s else "#")

                cur_projs = s["projectiles"]
                lives = s["global"]["lives"]
                game_over = s["global"]["game_over"]
                cleared = s["global"]["cleared"]

                countdown = s["global"].get("countdown", 0.0)
                best_time_val = s["global"].get("best_time", float('inf'))
                is_new_record = s["global"].get("is_new_record", False)

                
                return_to_lobby_now = s["global"].get("in_lobby", False)

                shared_state["data"] = None

        # Important condition: this branch protects an alternate state or edge case.
        if return_to_lobby_now:
            rebuild_local_level_after_restart()
            game_over = False
            cleared = False
            time_up = False
            countdown = 0.0
            last_game_version = None
            show_lobby_screen(screen, clock, my_id, shared_state, client)
            return_to_lobby_sent = False
            continue

        # Important condition: this branch protects an alternate state or edge case.
        if not split_triggered and (players[0].rect.x > 440 * TILE or players[1].rect.x > 440 * TILE):
            dialogue.trigger()
            split_triggered = True

        
        if countdown <= 0 and not game_over and not cleared:
            update_level_mechanics(dt, level)

        camera.update(dt, players[my_id].rect, level.width_px, level.height_px, look_x, look_y)
        themes.draw_bg_procedural(view, gtime, camera.x, level.theme)

        vr = camera.view_rect_world()
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for ty in range(int(vr.top // TILE - 1), int(vr.bottom // TILE + 2)):
            # Important loop: iterates through game objects that must be processed every frame or build step.
            for tx in range(int(vr.left // TILE - 1), int(vr.right // TILE + 2)):
                ch = level.tile_at(tx, ty)
                # Important condition: this branch protects an alternate state or edge case.
                if ch not in (".", "L"):
                    sx, sy = camera.world_to_screen(tx * TILE, ty * TILE)
                    themes.draw_tile(view, ch, sx, sy, gtime, level.theme)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for lf in lifts:
            draw_lift(view, lf, camera, gtime)
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for c in crates:
            draw_crate(view, c, camera)
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for b in buttons:
            draw_button(view, b, camera)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for proj in cur_projs:
            
            
            
            try:
                px = proj[0]
                py = proj[1]

                # Important condition: this branch protects an alternate state or edge case.
                if len(proj) >= 5:
                    pw = proj[2]
                    ph = proj[3]
                    pkind = proj[4]
                else:
                    pkind = proj[2] if len(proj) >= 3 else "bottlecap"
                    # Important condition: this branch protects an alternate state or edge case.
                    if pkind == "bubble":
                        pw, ph = 24, 24
                    else:
                        pw, ph = 18, 18
            except Exception:
                continue

            psx, psy = camera.world_to_screen(px, py)

            # Important condition: this branch protects an alternate state or edge case.
            if pkind == "bubble":
                
                cx = psx + pw // 2
                cy = psy + ph // 2
                pygame.draw.circle(view, (175, 235, 255), (cx, cy), 13)
                pygame.draw.circle(view, (70, 150, 235), (cx, cy), 13, 3)
                pygame.draw.circle(view, (255, 255, 255), (cx - 5, cy - 5), 4)
                pygame.draw.circle(view, (220, 245, 255), (cx + 4, cy + 4), 3, 1)
            else:
                
                cx = psx + pw // 2
                cy = psy + ph // 2
                pygame.draw.circle(view, (220, 25, 35), (cx, cy), 10)
                pygame.draw.circle(view, (110, 0, 10), (cx, cy), 10, 3)
                pygame.draw.circle(view, (255, 175, 175), (cx - 4, cy - 4), 3)
                pygame.draw.line(view, (255, 80, 80), (cx - 20, cy), (cx - 9, cy), 3)
                pygame.draw.line(view, (255, 140, 140), (cx - 17, cy - 5), (cx - 8, cy - 2), 2)

        draw_respawn_flags(view, players, camera)
        # Important loop: iterates through game objects that must be processed every frame or build step.
        for p in players: p.draw(view, camera)

        tint = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        tint.fill((48, 26, 76, 26))
        view.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        pygame.transform.smoothscale(view, (WINDOW_W, WINDOW_H), screen)

        draw_ui(screen, lives, timer_str, font_ui, timer_label)
        dialogue.update_and_draw(dt, screen, font_ui)

        # Important condition: this branch protects an alternate state or edge case.
        if hint_timer > 0:
            hint_timer -= dt
            draw_hint_box(screen, hint_text, font_hint)

        
        if countdown > 0:
            count_int = int(countdown)
            text = str(count_int) if count_int > 0 else "GO!"
            color = (255, 215, 0) if count_int > 0 else (100, 255, 100)

            ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 100))
            screen.blit(ov, (0, 0))

            txt_surf = font_big.render(text, True, color)
            screen.blit(txt_surf, (WINDOW_W // 2 - txt_surf.get_width() // 2, WINDOW_H // 2 - 50))

        
        if cleared:
            ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 190))
            screen.blit(ov, (0, 0))

            txt_main = font_big.render("LEVEL CLEARED!", True, (100, 255, 100))
            screen.blit(txt_main, (WINDOW_W // 2 - txt_main.get_width() // 2, WINDOW_H // 2 - 120))

            
            if is_new_record:
                rec_txt = font_big.render("NEW RECORD!!!", True, (255, 215, 0))
                screen.blit(rec_txt, (WINDOW_W // 2 - rec_txt.get_width() // 2, WINDOW_H // 2 - 40))
            else:
                # Important condition: this branch protects an alternate state or edge case.
                if best_time_val != float('inf'):
                    bmins, bsecs = int(best_time_val) // 60, int(best_time_val) % 60
                    bmils = int((best_time_val * 100) % 100)
                    b_str = f"Best Time: {bmins:02d}:{bsecs:02d}:{bmils:02d}"
                    b_txt = font_ui.render(b_str, True, (200, 200, 200))
                    screen.blit(b_txt, (WINDOW_W // 2 - b_txt.get_width() // 2, WINDOW_H // 2 - 40))

            t2 = font_ui.render(f"Your Time: {elapsed_timer_str}", True, (255, 255, 255))
            t3 = font_ui.render("Press 'R' to Play Again", True, (255, 255, 100))
            t4 = font_ui.render("Press 'L' to Return to Lobby and Change Mode", True, (180, 220, 255))

            screen.blit(t2, (WINDOW_W // 2 - t2.get_width() // 2, WINDOW_H // 2 + 20))
            screen.blit(t3, (WINDOW_W // 2 - t3.get_width() // 2, WINDOW_H // 2 + 70))
            screen.blit(t4, (WINDOW_W // 2 - t4.get_width() // 2, WINDOW_H // 2 + 105))

        # Important condition: this branch protects an alternate state or edge case.
        if game_over:
            ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            ov.fill((100, 0, 0, 180))
            screen.blit(ov, (0, 0))

            over_msg = "TIME'S UP!" if time_up else "GAME OVER"
            txt_over = font_big.render(over_msg, True, (255, 80, 80))
            t2 = font_ui.render("Press 'R' to Try Again", True, (255, 255, 100))
            t3 = font_ui.render("Press 'L' to Return to Lobby", True, (180, 220, 255))
            t4 = font_ui.render("Press ESC to Quit", True, (200, 200, 200))

            screen.blit(txt_over, (WINDOW_W // 2 - txt_over.get_width() // 2, WINDOW_H // 2 - 100))
            screen.blit(t2, (WINDOW_W // 2 - t2.get_width() // 2, WINDOW_H // 2 - 10))
            screen.blit(t3, (WINDOW_W // 2 - t3.get_width() // 2, WINDOW_H // 2 + 30))
            screen.blit(t4, (WINDOW_W // 2 - t4.get_width() // 2, WINDOW_H // 2 + 70))
        try:
            lobby_msg = font.render("L - Return to Lobby", True, (255, 255, 255))
            screen.blit(lobby_msg, (20, 60))
        except Exception:
            pass

        pygame.display.flip()
    pygame.quit()


# Important condition: this branch protects an alternate state or edge case.
if __name__ == "__main__":
    run_network_game()
