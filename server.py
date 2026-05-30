# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: server.py
# Description: Server-side game code. Manages networking, player state, game logic, synchronization, checkpoints, and game modes.
# ========================================

import os, socket, threading, pickle, time, pygame, struct, logging
from pathlib import Path
from level import build_level, TILE
import entities
from entities import Player, Crate, Lift, Button, ProjectileManager, InputFrame, update_level_mechanics

# =========================
# File logging
# =========================
# Logs are written only to logs/jojo_game.log and are not printed to the Run console.
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE_PATH = LOGS_DIR / "jojo_game.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(filename=str(LOG_FILE_PATH), level=logging.INFO, format=LOG_FORMAT, encoding="utf-8")
logger = logging.getLogger("jojo.server")







# =========================
# Communication constants
# =========================
# Every value used by the socket protocol and server socket setup is stored in a named constant.
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5555
SERVER_BIND_ADDRESS = (SERVER_HOST, SERVER_PORT)
SERVER_LISTEN_BACKLOG = 2
MAX_CONNECTED_PLAYERS = 2

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

# =========================
# Game Modes
# =========================


GAME_MODE_NORMAL = "normal"
GAME_MODE_SPEEDRUN = "speedrun"



DEFAULT_GAME_MODE = GAME_MODE_NORMAL


TIME_LIMIT = 300.0  # 5 minutes

# =========================
# Fixed Checkpoints
# =========================



CHECKPOINTS = [
    {"trigger_tile_x": 90,  "name": "Ice Stairs"},
    {"trigger_tile_x": 200, "name": "Bunker Entrance"},
    {"trigger_tile_x": 285, "name": "Target Room"},
    {"trigger_tile_x": 360, "name": "Split Path"},
    {"trigger_tile_x": 520, "name": "Moving Platforms"},
    {"trigger_tile_x": 700, "name": "Laser Zone"},
    {"trigger_tile_x": 850, "name": "Final Area"},
]


class GameServer:
    """Authoritative multiplayer server that owns the game state and networking.
    
    Constructor Args:
        None."""
    def return_to_lobby(self):
        """Return both players to the lobby and reset the match state.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        try:
            self.phase = "lobby"
        except Exception:
            pass
        try:
            self.game_phase = "lobby"
        except Exception:
            pass
        try:
            self.ready = [False, False]
        except Exception:
            pass
        try:
            self.players_ready = [False, False]
        except Exception:
            pass
        try:
            self.ready_players = [False, False]
        except Exception:
            pass
        try:
            self.game_over = False
            self.cleared = False
            self.winner = None
        except Exception:
            pass
        try:
            self.reset_game(return_to_lobby=True)
        except Exception:
            try:
                self.reset_level()
            except Exception:
                pass

    def __init__(self):
        """Execute the __init__ operation.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_mode((1, 1))

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(SERVER_BIND_ADDRESS)
        except socket.error as e:
            logger.info(f"[ERROR] Could not bind port: {e}")
            return

        self.server.listen(SERVER_LISTEN_BACKLOG)
        logger.info("JoJo Server Started on %s", SERVER_PORT)

        self.lock = threading.Lock()
        self.inputs = [InputFrame(), InputFrame()]
        self.connected_players = 0
        self.best_time = float('inf')  
        self.game_mode = DEFAULT_GAME_MODE
        self.game_version = 0

        self.reset_game(first_boot=True)

    def reset_game(self, first_boot=False, return_to_lobby=False):
        
        """Reset all server-side game objects, timers, players, and level state.
        
        Args:
            first_boot: Input value required by this function.
            return_to_lobby: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if not first_boot:
            self.game_version += 1

        
        if hasattr(self, "inputs"):
            self.inputs = [InputFrame(), InputFrame()]

        
        self.level, self.crate_spawns, button_spawns, lift_specs, self.goal_tiles = build_level()
        entities.LEVEL_REF = self.level
        entities.GLOBAL_STATE["timer"] = 0.0

        self.players = [
            Player("Joseph", self.level.spawn1_px[0], self.level.spawn1_px[1], "joseph", {}),
            Player("Caesar", self.level.spawn2_px[0], self.level.spawn2_px[1], "caesar", {})
        ]
        self.shoot_net_timers = [0.0, 0.0]
        self.shoot_broadcast_timers = [0.0, 0.0]

        self.crates = [Crate(x, y) for x, y in self.crate_spawns]
        self.lifts = [Lift(x, t_y, b_y) for x, t_y, b_y in lift_specs]
        self.buttons = [Button(x, y) for x, y in button_spawns]
        self.projs = ProjectileManager()

        self.lives = 3
        self.game_over = False
        self.cleared = False
        self.time_up = False
        self.GRAVITY = 2200.0
        self.countdown = 3.99  

        # Important condition: this branch protects an alternate state or edge case.
        if first_boot or return_to_lobby:
            self.players_ready = [False, False]
        else:
            self.players_ready = [True, True]

        self.is_new_record = False

        
        for p in self.players:
            p.checkpoint_index = -1
            p.checkpoint_pos = (p.rect.x, p.rect.y)
            p.respawn_pos = p.checkpoint_pos

    def update_fixed_checkpoints(self, player):
        """Update a player checkpoint after crossing predefined progress markers.
        
        Args:
            player: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if getattr(player, "just_died", False):
            return

        
        if not getattr(player, "on_ground", False):
            return

        current_tile_x = int(player.rect.centerx // TILE)
        current_index = getattr(player, "checkpoint_index", -1)

        # Important loop: iterates through game objects that must be processed every frame or build step.
        for idx, cp in enumerate(CHECKPOINTS):
            # Important condition: this branch protects an alternate state or edge case.
            if idx <= current_index:
                continue

            # Important condition: this branch protects an alternate state or edge case.
            if current_tile_x >= cp["trigger_tile_x"]:
                
                player.checkpoint_index = idx
                player.checkpoint_pos = (player.rect.x, player.rect.y)
                player.respawn_pos = player.checkpoint_pos

    def sync_respawn_to_checkpoint(self, player):
        """Keep a player respawn position synchronized with the saved checkpoint.
        
        Args:
            player: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        # Important condition: this branch protects an alternate state or edge case.
        if hasattr(player, "checkpoint_pos"):
            player.respawn_pos = player.checkpoint_pos

    def main_logic(self):
        """Run the authoritative server-side game simulation loop.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        clock = pygame.time.Clock()
        logger.info("Main logic thread started")

        # Important loop: keeps running until the game, network, or UI state changes.
        while True:
            dt = clock.tick(60) / 1000.0
            # Important condition: this branch protects an alternate state or edge case.
            if dt > 0.1: dt = 0.1

            with self.lock:
                
                if getattr(self.inputs[0], "return_to_lobby", False) or getattr(self.inputs[1], "return_to_lobby", False):
                    self.reset_game(return_to_lobby=True)
                    continue

                
                if self.game_over or self.cleared:
                    return_lobby = getattr(self.inputs[0], "return_to_lobby", False) or getattr(self.inputs[1], "return_to_lobby", False)
                    # Important condition: this branch protects an alternate state or edge case.
                    if return_lobby:
                        self.reset_game(return_to_lobby=True)
                    elif self.inputs[0].restart or self.inputs[1].restart:
                        self.reset_game()

                elif not self.cleared and not self.game_over:
                    
                    if self.connected_players == MAX_CONNECTED_PLAYERS:

                        
                        if self.players_ready[0] and self.players_ready[1]:

                            
                            if self.countdown > 0:
                                self.countdown -= dt
                            else:
                                
                                
                                update_level_mechanics(dt, self.level)

                                
                                if self.game_mode == GAME_MODE_SPEEDRUN and entities.GLOBAL_STATE["timer"] >= TIME_LIMIT:
                                    self.game_over = True
                                    self.time_up = True
                                    continue

                                # SHOOT BROADCAST TIMER DECAY
                                if not hasattr(self, "shoot_broadcast_timers"):
                                    self.shoot_broadcast_timers = [0.0, 0.0]
                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for _si in range(len(self.shoot_broadcast_timers)):
                                    self.shoot_broadcast_timers[_si] = max(0.0, self.shoot_broadcast_timers[_si] - dt)

                                # Important condition: this branch protects an alternate state or edge case.
                                if hasattr(entities, 'update_new_mechanics'):
                                    entities.update_new_mechanics(dt, self.players, self.inputs)

                                proj_rects = [pygame.Rect(pj.x, pj.y, pj.w, pj.h) for pj in self.projs.items]
                                pressers = [c.rect for c in self.crates] + proj_rects
                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for b in self.buttons:
                                    b.update(self.players[0].rect, self.players[1].rect, pressers)

                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for lf in self.lifts:
                                    dy = lf.update(dt)
                                    # Important condition: this branch protects an alternate state or edge case.
                                    if dy != 0.0 or lf.last_dx != 0.0:
                                        lf.carry_riders(dy, self.players, self.crates)

                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for i, p in enumerate(self.players):
                                    p.update(dt, self.inputs[i], self.GRAVITY, self.level, self.crates, self.lifts,
                                             self.projs)

                                    
                                    
                                    self.update_fixed_checkpoints(p)
                                    self.sync_respawn_to_checkpoint(p)

                                    # Important condition: this branch protects an alternate state or edge case.
                                    if p.rect.y > (self.level.height_tiles + 5) * TILE:
                                        p.just_died = True
                                    self.inputs[i].jump_pressed = False
                                    self.inputs[i].shoot_pressed = False

                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for p in self.players:
                                    # Important condition: this branch protects an alternate state or edge case.
                                    if p.just_died:
                                        self.lives -= 1
                                        # Important condition: this branch protects an alternate state or edge case.
                                        if self.lives <= 0:
                                            self.game_over = True
                                        else:
                                            self.sync_respawn_to_checkpoint(p)
                                            p.x, p.y = p.respawn_pos
                                            p.rect.x, p.rect.y = int(p.x), int(p.y)
                                            p.vx, p.vy = 0.0, 0.0
                                            p.just_died = False

                                # Important loop: iterates through game objects that must be processed every frame or build step.
                                for c in self.crates:
                                    c.update(dt, self.GRAVITY, self.level, self.crates, self.lifts)
                                self.projs.update(dt, self.level, self.crates, self.lifts, self.players)

                                
                                goal_rs = [pygame.Rect(tx * TILE, ty * TILE, TILE, TILE) for tx, ty in self.goal_tiles]
                                # Important condition: this branch protects an alternate state or edge case.
                                if not self.cleared:
                                    p1_in = any(self.players[0].rect.colliderect(g) for g in goal_rs)
                                    p2_in = any(self.players[1].rect.colliderect(g) for g in goal_rs)
                                    # Important condition: this branch protects an alternate state or edge case.
                                    if p1_in and p2_in:
                                        self.cleared = True
                                        
                                        current_time = entities.GLOBAL_STATE["timer"]
                                        # Important condition: this branch protects an alternate state or edge case.
                                        if current_time < self.best_time:
                                            self.best_time = current_time
                                            self.is_new_record = True

    def handle_client(self, conn, p_id):
        """Handle one connected player: receive input, update shared input state, and send game snapshots.
        
        Args:
            conn: Input value required by this function.
            p_id: Input value required by this function.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        assert p_id in (0, 1), "Player id must be 0 or 1"
        assert conn is not None, "Client connection must exist"
        logger.info("Handling Player %s", p_id)
        try:
            send_msg(conn, p_id)

            # Important loop: keeps running until the game, network, or UI state changes.
            while True:
                client_input = recv_msg(conn)
                # Important condition: this branch protects an alternate state or edge case.
                if client_input is None: break

                with self.lock:
                    self.inputs[p_id].left = client_input.left
                    self.inputs[p_id].right = client_input.right
                    self.inputs[p_id].down = client_input.down
                    self.inputs[p_id].jump_held = client_input.jump_held
                    self.inputs[p_id].shoot_held = client_input.shoot_held

                    # Important condition: this branch protects an alternate state or edge case.
                    if client_input.jump_pressed: self.inputs[p_id].jump_pressed = True
                    # Important condition: this branch protects an alternate state or edge case.
                    if getattr(client_input, "return_lobby", False):
                        self.return_to_lobby()
                        continue

                    # Important condition: this branch protects an alternate state or edge case.
                    if client_input.shoot_pressed:
                        self.inputs[p_id].shoot_pressed = True
                        # SHOOT BROADCAST EVENT SET
                        if not hasattr(self, "shoot_broadcast_timers"):
                            self.shoot_broadcast_timers = [0.0, 0.0]
                        self.shoot_broadcast_timers[p_id] = 0.4

                    # Important condition: this branch protects an alternate state or edge case.
                    if hasattr(client_input, 'restart'):
                        self.inputs[p_id].restart = client_input.restart

                    
                    self.inputs[p_id].return_to_lobby = getattr(client_input, 'return_to_lobby', False)

                    # Important condition: this branch protects an alternate state or edge case.
                    if hasattr(client_input, 'ready'):
                        self.players_ready[p_id] = client_input.ready

                    
                    if p_id == 0 and hasattr(client_input, 'selected_game_mode'):
                        requested_mode = client_input.selected_game_mode
                        # Important condition: this branch protects an alternate state or edge case.
                        if requested_mode in (GAME_MODE_NORMAL, GAME_MODE_SPEEDRUN):
                            
                            if not (self.players_ready[0] and self.players_ready[1]):
                                self.game_mode = requested_mode

                    targets_hit = []
                    # Important loop: iterates through game objects that must be processed every frame or build step.
                    for k in entities.TARGET_META:
                        tx, ty = k[0] // entities.TILE_DEFAULT, k[1] // entities.TILE_DEFAULT
                        # Important condition: this branch protects an alternate state or edge case.
                        if self.level.tile_at(tx, ty) == "o":
                            targets_hit.append((tx, ty))

                    state = {
                        "players": [(p.x, p.y, getattr(p, '_anim_i', 0), getattr(p, 'facing', 1),
                                     getattr(p, 'just_died', False), getattr(p, 'h', 48),
                                     getattr(p, 'respawn_pos', (p.x, p.y))[0],
                                     getattr(p, 'respawn_pos', (p.x, p.y))[1],
                                     self.shoot_broadcast_timers[i] if hasattr(self, "shoot_broadcast_timers") and i < len(self.shoot_broadcast_timers) else 0.0)
                                    for i, p in enumerate(self.players)],
                        "crates": [(c.x, c.y) for c in self.crates],
                        "lifts": [(l.rect.x, l.rect.y) for l in self.lifts],
                        "buttons": [b.pressed for b in self.buttons],
                        "projectiles": [(pj.x, pj.y, pj.w, pj.h, pj.kind) for pj in self.projs.items],
                        "targets_hit": targets_hit,
                        "global": {
                            "lives": self.lives,
                            "game_over": self.game_over,
                            "cleared": self.cleared,
                            "timer": entities.GLOBAL_STATE["timer"],
                            "game_mode": self.game_mode,
                            "time_limit": TIME_LIMIT,
                            "time_up": self.time_up,
                            "players_connected": self.connected_players,
                            "countdown": self.countdown,
                            "players_ready": self.players_ready,
                            "best_time": self.best_time,
                            "is_new_record": getattr(self, 'is_new_record', False),
                            "game_version": self.game_version,
                            "in_lobby": not (self.players_ready[0] and self.players_ready[1])
                        }
                    }
                send_msg(conn, state)
        except Exception as e:
            logger.exception("Player %s disconnected: %s", p_id, e)
        finally:
            conn.close()

    def run(self):
        """Accept client connections and start one handler thread per player.
        
        Args:
            None.
        
        Returns:
            The result of the operation, or None when the function performs side effects only."""
        threading.Thread(target=self.main_logic, daemon=True).start()
        logger.info("Waiting for players to connect")

        # Important loop: keeps running until the game, network, or UI state changes.
        while True:
            conn, addr = self.server.accept()
            assert conn is not None, "Accepted connection must not be None"

            with self.lock:
                # Important condition: this branch protects an alternate state or edge case.
                if self.connected_players >= 2:
                    logger.warning("Rejected extra client from %s because the server is full", addr)

                    try:
                        send_msg(conn, {
                            "type": "SERVER_FULL",
                            "message": "Server is full. Only 2 players can play."
                        })
                    except Exception as e:
                        logger.exception("Could not send SERVER_FULL message: %s", e)

                    conn.close()
                    continue

                p_id = self.connected_players
                self.connected_players += 1

            logger.info("Player %s connected from %s", p_id, addr)

            threading.Thread(
                target=self.handle_client,
                args=(conn, p_id),
                daemon=True
            ).start()

            # Important condition: this branch protects an alternate state or edge case.
            if self.connected_players == MAX_CONNECTED_PLAYERS:
                logger.info("Both players connected; game physics unlocked")


# Important condition: this branch protects an alternate state or edge case.
if __name__ == "__main__":
    server = GameServer()
    server.run()
