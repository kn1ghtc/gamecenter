"""Multiplayer system for Delta Operation.

Handles dual-player mode with:
- Player 2 instance management
- Dual-camera modes (split-screen or center-locked)
- Shared mission objectives tracking
- Cooperative gameplay mechanics
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import pygame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gamecenter.deltaOperation.core.player import Player
from gamecenter.deltaOperation.utils.camera import Camera


@dataclass
class MultiplayerConfig:
    """Multiplayer configuration settings."""
    
    mode: str = "shared"  # 'shared' (single viewport) or 'split' (split-screen)
    max_distance: float = 800.0  # Max distance between players before forcing proximity
    resurrection_enabled: bool = True  # Allow players to revive each other
    resurrection_time: float = 3.0  # Time to revive (seconds)
    shared_objectives: bool = True  # Both players contribute to mission progress


class MultiplayerManager:
    """Manages dual-player cooperative gameplay.
    
    Features:
    - Player 2 lifecycle (spawn, update, render)
    - Camera tracking for 2 players (center-lock or split-screen)
    - Proximity enforcement (prevent excessive separation)
    - Resurrection system (revive fallen teammate)
    - Shared objective tracking
    """

    def __init__(self, config: MultiplayerConfig = None) -> None:
        self.config = config or MultiplayerConfig()
        
        # Player references
        self.player1: Optional[Player] = None
        self.player2: Optional[Player] = None
        
        # Camera modes
        self.camera_mode = self.config.mode  # 'shared' or 'split'
        
        # Resurrection tracking
        self.p1_resurrecting_p2 = False
        self.p2_resurrecting_p1 = False
        self.resurrection_timer = 0.0

    def initialize_players(self, player1: Player, spawn_x: float, spawn_y: float) -> Player:
        """Initialize Player 2 at spawn location.
        
        Args:
            player1: Existing Player 1 instance
            spawn_x: Player 2 spawn X coordinate
            spawn_y: Player 2 spawn Y coordinate
        
        Returns:
            Player 2 instance
        """
        self.player1 = player1
        self.player2 = Player(spawn_x, spawn_y, player_id=2)
        
        # Copy weapon loadout from Player 1
        if hasattr(player1, 'weapons') and player1.weapons:
            self.player2.weapons = [type(weapon)(self.player2) for weapon in player1.weapons]
            self.player2.current_weapon = self.player2.weapons[0] if self.player2.weapons else None
        
        return self.player2

    def update(self, delta_time: float) -> None:
        """Update multiplayer state (proximity, resurrection).
        
        Args:
            delta_time: Time delta in seconds
        """
        if not self.player1 or not self.player2:
            return
        
        # Enforce proximity limit
        if self.config.max_distance > 0:
            self._enforce_proximity()
        
        # Update resurrection system
        if self.config.resurrection_enabled:
            self._update_resurrection(delta_time)

    def _enforce_proximity(self) -> None:
        """Prevent players from separating beyond max_distance."""
        dx = self.player2.position.x - self.player1.position.x
        dy = self.player2.position.y - self.player1.position.y
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance > self.config.max_distance:
            # Pull slower player toward the other
            ratio = self.config.max_distance / distance
            center_x = (self.player1.position.x + self.player2.position.x) / 2
            center_y = (self.player1.position.y + self.player2.position.y) / 2
            
            # Adjust positions symmetrically
            self.player1.position.x = center_x - (self.player1.position.x - center_x) * ratio
            self.player1.position.y = center_y - (self.player1.position.y - center_y) * ratio
            self.player2.position.x = center_x + (self.player2.position.x - center_x) * ratio
            self.player2.position.y = center_y + (self.player2.position.y - center_y) * ratio

    def _update_resurrection(self, delta_time: float) -> None:
        """Handle player resurrection mechanics.
        
        Args:
            delta_time: Time delta in seconds
        """
        # Check if Player 1 is reviving Player 2
        if self.player2.health <= 0 and self.player1.health > 0:
            distance = self._get_player_distance()
            if distance < 50:  # 50px proximity required for revival
                keys = pygame.key.get_pressed()
                if keys[self.player1.controls.get("action", pygame.K_e)]:
                    if not self.p1_resurrecting_p2:
                        self.p1_resurrecting_p2 = True
                        self.resurrection_timer = 0.0
                    
                    self.resurrection_timer += delta_time
                    if self.resurrection_timer >= self.config.resurrection_time:
                        self._revive_player(self.player2)
                        self.p1_resurrecting_p2 = False
                        self.resurrection_timer = 0.0
                else:
                    self.p1_resurrecting_p2 = False
                    self.resurrection_timer = 0.0
        
        # Check if Player 2 is reviving Player 1
        if self.player1.health <= 0 and self.player2.health > 0:
            distance = self._get_player_distance()
            if distance < 50:
                keys = pygame.key.get_pressed()
                if keys[self.player2.controls.get("action", pygame.K_RSHIFT)]:
                    if not self.p2_resurrecting_p1:
                        self.p2_resurrecting_p1 = True
                        self.resurrection_timer = 0.0
                    
                    self.resurrection_timer += delta_time
                    if self.resurrection_timer >= self.config.resurrection_time:
                        self._revive_player(self.player1)
                        self.p2_resurrecting_p1 = False
                        self.resurrection_timer = 0.0
                else:
                    self.p2_resurrecting_p1 = False
                    self.resurrection_timer = 0.0

    def _revive_player(self, player: Player) -> None:
        """Revive a fallen player.
        
        Args:
            player: Player instance to revive
        """
        player.health = player.max_health * 0.3  # Revive with 30% HP
        from gamecenter.deltaOperation.core.player import PlayerState
        player.state = PlayerState.IDLE

    def _get_player_distance(self) -> float:
        """Calculate distance between players.
        
        Returns:
            Distance in pixels
        """
        if not self.player1 or not self.player2:
            return float('inf')
        
        dx = self.player2.position.x - self.player1.position.x
        dy = self.player2.position.y - self.player1.position.y
        return (dx**2 + dy**2) ** 0.5

    def update_camera(self, camera: Camera) -> None:
        """Update camera to track both players.
        
        In 'shared' mode, camera centers on midpoint between players.
        In 'split' mode (future implementation), uses dual viewports.
        
        Args:
            camera: Camera instance to update
        """
        if not self.player1 or not self.player2:
            return
        
        if self.camera_mode == "shared":
            # Center camera on midpoint
            center_x = (self.player1.position.x + self.player2.position.x) / 2
            center_y = (self.player1.position.y + self.player2.position.y) / 2
            camera.set_target(center_x, center_y)
        
        # Split-screen mode not yet implemented (requires dual render passes)

    def get_resurrection_progress(self) -> Optional[float]:
        """Get current resurrection progress.
        
        Returns:
            Progress ratio (0.0-1.0) or None if not resurrecting
        """
        if self.p1_resurrecting_p2 or self.p2_resurrecting_p1:
            return min(1.0, self.resurrection_timer / self.config.resurrection_time)
        return None

    def is_multiplayer_active(self) -> bool:
        """Check if Player 2 is active.
        
        Returns:
            True if Player 2 exists and alive
        """
        return self.player2 is not None and self.player2.health > 0

    def both_players_dead(self) -> bool:
        """Check mission failure condition.
        
        Returns:
            True if both players are dead
        """
        if not self.player1 or not self.player2:
            return False
        
        return self.player1.health <= 0 and self.player2.health <= 0


__all__ = ["MultiplayerManager", "MultiplayerConfig"]
