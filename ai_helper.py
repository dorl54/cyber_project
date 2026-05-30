# ========================================
# Submitter: Dor LEVEK
# Date: 28/05/2026
# File: ai_helper.py
# Description: AI hint helper. Reads the current game state and returns a context-aware hint based on the player position.
# ========================================

"""
ai_helper.py

Provides simple, location-based hints for the co-op game.

The client calls this module when the player asks for help:
    hint_text = get_ai_hint(current_state, my_id)

Expected state format:
    state["players"][my_id][0] -> player x position in pixels
    state["players"][my_id][1] -> player y position in pixels

The hint system converts the player x position into a tile index:
    tile_x = x // 48
"""

TILE_SIZE = 48


def _safe_player_pos(state, my_id):
    """
    Safely extracts the selected player's position from the shared game state.

    Parameters:
        state (dict): The latest game state received from the server.
        my_id (int | None): The local player index. Usually 0 for Joseph and 1 for Caesar.

    Returns:
        tuple[float | None, float | None, int | None]:
            x position in pixels, y position in pixels, and x tile index.
            Returns (None, None, None) if the state cannot be read safely.
    """
    try:
        players = state.get("players", [])

        # If the server has not sent players yet, the helper cannot determine a hint location.
        if not players:
            return None, None, None

        # If the caller did not provide an id, default to player 0 so the function still works.
        if my_id is None:
            my_id = 0

        # If the id is outside the valid range, fall back to player 0 instead of crashing.
        if my_id < 0 or my_id >= len(players):
            my_id = 0

        p = players[my_id]
        x = float(p[0])
        y = float(p[1])
        tile_x = int(x // TILE_SIZE)

        return x, y, tile_x
    except Exception:
        # Any malformed or partial network state should fail safely and let the caller show a generic hint.
        return None, None, None


def get_ai_hint(state, my_id=0):
    """
    Returns a gameplay hint based on the current player's location and global game status.

    Parameters:
        state (dict): The latest game state received from the server.
        my_id (int): The local player index. 0 means Joseph, 1 means Caesar.

    Returns:
        str: A short hint that can be displayed in the client UI.
    """
    # If no state has arrived yet, the client should show a temporary message instead of crashing.
    if not state:
        return "No game data yet. Try again in a moment."

    x, y, tile_x = _safe_player_pos(state, my_id)

    # If the player's tile cannot be calculated, the helper cannot choose an area-specific hint.
    if tile_x is None:
        return "I cannot read your position yet. Try again in a moment."

    # Read global game flags first because end-state messages are more important than location hints.
    try:
        global_state = state.get("global", {})
        lives = global_state.get("lives", None)
        game_over = global_state.get("game_over", False)
        cleared = global_state.get("cleared", False)
        time_up = global_state.get("time_up", False)

        # If the level was completed, tell the player which reset/lobby keys are available.
        if cleared:
            return "Level cleared! You can press R to play again or L to return to the lobby."

        # If the game ended, explain whether it ended because of the timer or another failure.
        if game_over:
            if time_up:
                return "Time is up. Press R to retry or L to return to the lobby."
            return "Game over. Press R to retry or L to return to the lobby."

        # If the team has almost no lives left, prioritize a safety warning over area hints.
        if lives is not None and lives <= 1:
            return "You have one life left. Move carefully and use checkpoints before risky jumps."
    except Exception:
        # Global status is optional for hints, so location-based hints can still be returned.
        pass

    # Location-based hints use tile_x ranges. Change only these ranges if hints trigger too early or too late.

    # Start area: teach the basic movement keys.
    if tile_x < 35:
        return "Move right together. Use the arrow keys to move and UP to jump."

    # First platforming area: remind players to jump carefully.
    if 35 <= tile_x < 90:
        return "This is the first platforming area. Stay on solid ground and jump carefully."

    # First checkpoint area: explain that progress is saved around this region.
    if 90 <= tile_x < 150:
        return "You are near the first checkpoint area. If you fall later, you should return close to here."

    # Crate and bunker entrance area: encourage teamwork with objects and buttons.
    if 150 <= tile_x < 230:
        return "Look for crates, buttons, or blocked paths. Some obstacles need teamwork."

    # First target room: give character-specific shooting guidance.
    if 230 <= tile_x < 330:
        if my_id == 0:
            return "Joseph: there is a target nearby. Press SPACE to shoot and open the blocked path."
        else:
            return "Caesar: wait near the path while Joseph or you shoot the target with SPACE."

    # After the first target: guide the players forward once the path should be open.
    if 330 <= tile_x < 420:
        return "The path should open after the target is hit. Keep moving right and stay together."

    # Split-path area: give character-specific cooperation guidance.
    if 420 <= tile_x < 560:
        if my_id == 0:
            return "Split-path area: one player may need to shoot or stand in one place while the other advances."
        else:
            return "Split-path area: coordinate with Joseph. Sometimes one player opens the way for the other."

    # Moving platforms: warn the player to wait for safe timing.
    if 560 <= tile_x < 690:
        return "Moving platforms ahead. Wait for the platform to come close before jumping."

    # Laser and hazard area: emphasize timing.
    if 690 <= tile_x < 820:
        return "Danger zone. Watch the timing of hazards and do not rush."

    # Late-game area before the goal: encourage careful teamwork.
    if 820 <= tile_x < 930:
        return "You are close to the final area. Stay together and avoid unnecessary risks."

    # Final area: both players should reach the goal together.
    if tile_x >= 930:
        return "Final area. Both players should move toward the goal together."

    return "Keep moving right and cooperate with your partner."
