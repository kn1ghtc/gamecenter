"""
Game State Management System for StreetBattle
Handles game flow, round management, win conditions, and timing
"""

from enum import Enum
from panda3d.core import ClockObject
import time


class GameState(Enum):
    """Game state enumeration"""
    MENU = "menu"
    CHARACTER_SELECT = "character_select"
    LOADING = "loading"
    ROUND_START = "round_start"
    FIGHTING = "fighting"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"
    PAUSED = "paused"


class RoundResult(Enum):
    """Round end result types"""
    KO = "ko"              # One player health reaches 0
    TIME_UP = "time_up"    # Time limit reached
    DRAW = "draw"          # Both players have same health when time up
    FORFEIT = "forfeit"    # Player disconnects or quits


class GameStateManager:
    """Manages game flow, timing, and win conditions"""
    
    def __init__(self, base):
        self.base = base
        self.current_state = GameState.LOADING
        self.previous_state = None
        
        # Round management
        self.current_round = 1
        self.max_rounds = 3  # Best of 3
        self.round_time_limit = 120.0  # 120 seconds per round
        self.round_start_time = 0.0
        self.round_elapsed_time = 0.0
        
        # Win tracking
        self.player_wins = [0, 0]  # [P1 wins, P2 wins]
        self.current_round_winner = None
        self.game_winner = None
        
        # State timing
        self.state_enter_time = 0.0
        self.round_start_delay = 3.0  # 3 seconds before fight starts
        self.round_end_delay = 3.0    # 3 seconds to show results
        
        # Callbacks
        self.on_state_change = None
        self.on_round_start = None
        self.on_round_end = None
        self.on_game_end = None
        
        print("GameStateManager initialized")
    
    def get_current_time(self):
        """Get current game time"""
        try:
            return ClockObject.getGlobalClock().getFrameTime()
        except:
            return time.time()
    
    def change_state(self, new_state):
        """Change game state with proper callbacks"""
        if new_state == self.current_state:
            return
        
        print(f"State change: {self.current_state.value} -> {new_state.value}")
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_enter_time = self.get_current_time()
        
        # Handle state entry actions
        if new_state == GameState.ROUND_START:
            self._enter_round_start()
        elif new_state == GameState.FIGHTING:
            self._enter_fighting()
        elif new_state == GameState.ROUND_END:
            self._enter_round_end()
        elif new_state == GameState.GAME_OVER:
            self._enter_game_over()
        
        # Trigger callback
        if self.on_state_change:
            self.on_state_change(new_state, self.previous_state)
    
    def update(self, players=None):
        """Update game state logic every frame"""
        current_time = self.get_current_time()
        state_duration = current_time - self.state_enter_time
        
        if self.current_state == GameState.ROUND_START:
            # Wait for round start delay, then begin fighting
            if state_duration >= self.round_start_delay:
                self.change_state(GameState.FIGHTING)
        
        elif self.current_state == GameState.FIGHTING:
            # Update round timer
            self.round_elapsed_time = current_time - self.round_start_time
            
            # Check win conditions
            if players and len(players) >= 2:
                winner_idx = self._check_win_conditions(players)
                if winner_idx is not None:
                    self.current_round_winner = winner_idx
                    self.change_state(GameState.ROUND_END)
        
        elif self.current_state == GameState.ROUND_END:
            # Wait for round end delay, then start next round or end game
            if state_duration >= self.round_end_delay:
                if self._is_game_over():
                    self.change_state(GameState.GAME_OVER)
                else:
                    self._start_next_round()
    
    def _enter_round_start(self):
        """Handle round start state entry"""
        print(f"Starting Round {self.current_round}")
        self.round_start_time = self.get_current_time() + self.round_start_delay
        self.round_elapsed_time = 0.0
        
        if self.on_round_start:
            self.on_round_start(self.current_round)
    
    def _enter_fighting(self):
        """Handle fighting state entry"""
        print("Fight begins!")
        self.round_start_time = self.get_current_time()
    
    def _enter_round_end(self):
        """Handle round end state entry"""
        if self.current_round_winner is not None:
            self.player_wins[self.current_round_winner] += 1
            print(f"Round {self.current_round} winner: Player {self.current_round_winner + 1}")
            print(f"Score: P1={self.player_wins[0]} P2={self.player_wins[1]}")
        
        if self.on_round_end:
            self.on_round_end(self.current_round_winner, self._get_round_result())
    
    def _enter_game_over(self):
        """Handle game over state entry"""
        # Determine overall game winner
        if self.player_wins[0] > self.player_wins[1]:
            self.game_winner = 0
        elif self.player_wins[1] > self.player_wins[0]:
            self.game_winner = 1
        else:
            self.game_winner = None  # Draw (shouldn't happen in best of 3)
        
        print(f"Game Over! Winner: Player {self.game_winner + 1 if self.game_winner is not None else 'Draw'}")
        
        if self.on_game_end:
            self.on_game_end(self.game_winner)
    
    def _check_win_conditions(self, players):
        """Check if round should end, return winner index or None"""
        p0, p1 = players[0], players[1]
        
        # Check for KO (health <= 0)
        if p0.health <= 0 and p1.health <= 0:
            # Both KO'd simultaneously - whoever has more health wins
            return 1 if p1.health > p0.health else 0
        elif p0.health <= 0:
            return 1  # P2 wins
        elif p1.health <= 0:
            return 0  # P1 wins
        
        # Check for time up
        remaining_time = self.get_remaining_time()
        if remaining_time <= 0:
            # Time up - whoever has more health wins
            if p0.health > p1.health:
                return 0  # P1 wins
            elif p1.health > p0.health:
                return 1  # P2 wins
            else:
                # Draw - could implement sudden death or judge decision
                return 0  # For now, P1 wins draws
        
        return None  # Continue fighting
    
    def _get_round_result(self):
        """Get the result type for the current round"""
        remaining_time = self.get_remaining_time()
        if remaining_time <= 0:
            return RoundResult.TIME_UP
        else:
            return RoundResult.KO
    
    def _is_game_over(self):
        """Check if the overall game should end"""
        # Game ends when someone wins 2 rounds (best of 3)
        return max(self.player_wins) >= 2
    
    def _start_next_round(self):
        """Start the next round"""
        self.current_round += 1
        self.current_round_winner = None
        self.change_state(GameState.ROUND_START)
    
    def get_remaining_time(self):
        """Get remaining time in current round"""
        if self.current_state != GameState.FIGHTING:
            return self.round_time_limit
        
        elapsed = self.get_current_time() - self.round_start_time
        return max(0.0, self.round_time_limit - elapsed)
    
    def get_round_progress(self):
        """Get round progress as percentage (0-1)"""
        if self.current_state != GameState.FIGHTING:
            return 0.0
        
        elapsed = self.get_current_time() - self.round_start_time
        return min(1.0, elapsed / self.round_time_limit)
    
    def get_game_info(self):
        """Get current game information for UI"""
        return {
            'state': self.current_state.value,
            'round': self.current_round,
            'max_rounds': self.max_rounds,
            'remaining_time': self.get_remaining_time(),
            'player_wins': self.player_wins.copy(),
            'game_winner': self.game_winner,
            'round_winner': self.current_round_winner
        }
    
    def reset_game(self):
        """Reset game state for new game"""
        self.current_round = 1
        self.player_wins = [0, 0]
        self.current_round_winner = None
        self.game_winner = None
        self.round_elapsed_time = 0.0
        self.change_state(GameState.ROUND_START)
        print("Game reset")
    
    def pause_game(self):
        """Pause the game"""
        if self.current_state == GameState.FIGHTING:
            self.change_state(GameState.PAUSED)
    
    def resume_game(self):
        """Resume paused game"""
        if self.current_state == GameState.PAUSED:
            # Adjust round start time to account for pause duration
            pause_duration = self.get_current_time() - self.state_enter_time
            self.round_start_time += pause_duration
            self.change_state(GameState.FIGHTING)
    
    def force_round_end(self, winner_idx=None):
        """Force round to end (for testing or special conditions)"""
        self.current_round_winner = winner_idx
        self.change_state(GameState.ROUND_END)
    
    def is_fighting(self):
        """Check if currently in fighting state"""
        return self.current_state == GameState.FIGHTING
    
    def is_game_active(self):
        """Check if game is actively running (not menu/loading)"""
        return self.current_state in [
            GameState.ROUND_START,
            GameState.FIGHTING,
            GameState.ROUND_END
        ]