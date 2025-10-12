"""五子棋游戏主程序
Gomoku (Five in a Row) - Main Entry Point

现代化五子棋游戏，包含智能AI、优雅UI、完整游戏功能。
"""

from __future__ import annotations

import copy
import json
import os
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional, Tuple

import pygame

# 确保UTF-8编码（Windows环境）
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 绝对导入
from gamecenter.gomoku.ai_engine_manager import create_ai_engine
from gamecenter.gomoku.config.config_manager import get_config_manager
from gamecenter.gomoku.font_manager import get_font_manager
from gamecenter.gomoku.game_logic import Board, GameManager, GameState, Player
from gamecenter.gomoku.ui_manager import UIManager, UISidebarState, PlayerPanelData


_CONFIG = get_config_manager()
_WINDOW_CONFIG = _CONFIG.get_window_config()
_GAMEPLAY_CONFIG = _CONFIG.get_gameplay_config()
_ENGINE_DEFAULTS = _CONFIG.get_engine_defaults()
_DEFAULT_SETTINGS = _CONFIG.get_default_settings()
_SETTINGS_FILENAME = _CONFIG.get_path('settings_file', 'user_settings.json')
_SAVE_DIR = _CONFIG.get_path('save_dir', 'saves')
_SESSION_FILE = _CONFIG.get_path('session_file', 'saves/last_session.json')
_AUDIO_CONFIG = _CONFIG.get_audio_config()

WINDOW_MIN_WIDTH = _WINDOW_CONFIG.get('min_width', 800)
WINDOW_MIN_HEIGHT = _WINDOW_CONFIG.get('min_height', 700)
WINDOW_DEFAULT_WIDTH = _WINDOW_CONFIG.get('default_width', 1000)
WINDOW_DEFAULT_HEIGHT = _WINDOW_CONFIG.get('default_height', 900)
MAX_UNDO_COUNT = _GAMEPLAY_CONFIG.get('max_undo_count', 3)
AI_DEFAULT_DIFFICULTY = _ENGINE_DEFAULTS.get('difficulty', 'medium')
AI_ENGINE_TYPE = _ENGINE_DEFAULTS.get('type', 'auto')
AI_TIME_LIMIT = _ENGINE_DEFAULTS.get('time_limit', _GAMEPLAY_CONFIG.get('ai_time_limit', 5.0))
DEFAULT_VOLUME = _AUDIO_CONFIG.get('default_volume', 0.7)


@dataclass
class PlayerRuntimeState:
    """Runtime information tracked for each player."""

    name: str
    is_ai: bool
    score: int = 0
    last_move: Optional[Tuple[int, int]] = None
    last_move_time: Optional[float] = None
    total_time: float = 0.0
    thinking: bool = False
    thinking_duration: float = 0.0

    def reset_round(self) -> None:
        """Clear per-round data while preserving cumulative score."""
        self.last_move = None
        self.last_move_time = None
        self.thinking = False
        self.thinking_duration = 0.0


class GomokuGame:
    """五子棋游戏主类"""
    
    def __init__(
        self,
        *,
        save_dir_override: Optional[Path] = None,
        session_path_override: Optional[Path] = None,
        settings_path_override: Optional[Path] = None,
    ):
        """初始化游戏"""
        pygame.init()
        self.save_dir = Path(save_dir_override) if save_dir_override else Path(__file__).parent / _SAVE_DIR
        self.session_path = Path(session_path_override) if session_path_override else Path(__file__).parent / _SESSION_FILE
        self.settings_path = Path(settings_path_override) if settings_path_override else Path(__file__).parent / _SETTINGS_FILENAME
        
        # 加载设置
        self.settings = self._load_settings()
        self._normalize_display_settings()

        display_settings = self.settings['display']
        width = display_settings['window_width']
        height = display_settings['window_height']
        self.fullscreen = bool(display_settings.get('fullscreen', False))

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            info = pygame.display.Info()
            width, height = info.current_w, info.current_h
        else:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("五子棋 Gomoku - Modern Edition")
        
        # 创建游戏对象
        max_undo = self.settings['game'].get('max_undo_count', MAX_UNDO_COUNT)
        self.game_manager = GameManager(max_undo=max_undo)
        self.ui_manager = UIManager(width, height)
        
        # AI设置（使用AI引擎管理器）
        difficulty_name = self.settings['game'].get('ai_difficulty', AI_DEFAULT_DIFFICULTY)
        engine_type = self.settings['game'].get('ai_engine_type', AI_ENGINE_TYPE)
        time_limit = self.settings['game'].get('ai_time_limit', AI_TIME_LIMIT)
        self.ai_controller = create_ai_engine(engine_type, difficulty_name, time_limit=time_limit)
        self.ai_thinking = False
        self.ai_player = Player.WHITE  # AI默认执白
        self.game_mode = 'pvc'  # 默认人机对战 'pvp'双人 或 'pvc'人机
        self.player_states: Dict[Player, PlayerRuntimeState] = {
            Player.BLACK: PlayerRuntimeState(name="玩家", is_ai=False),
            Player.WHITE: PlayerRuntimeState(name="AI", is_ai=True),
        }
        self.status_messages: Deque[str] = deque(maxlen=3)
        self.turn_start_time: float = time.time()
        self.ai_think_start: Optional[float] = None
        self.game_result_recorded = False
        self._sync_player_profiles()
        self._log_info("新局初始化完成")

        self._load_saved_session_if_available()
        self._refresh_ui_labels()
        if 'undo' in self.ui_manager.buttons:
            self.ui_manager.buttons['undo'].enabled = self.game_manager.can_undo()
        
        # 时钟
        self.clock = pygame.time.Clock()
        self.running = True
    
    def _load_settings(self) -> dict:
        """加载设置"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
        except Exception:
            return copy.deepcopy(_DEFAULT_SETTINGS)

        defaults = copy.deepcopy(_DEFAULT_SETTINGS)
        for section, value in loaded.items():
            if isinstance(value, dict):
                defaults.setdefault(section, {}).update(value)
            else:
                defaults[section] = value
        return defaults

    def _save_settings(self) -> None:
        """保存当前设置到磁盘"""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w', encoding='utf-8') as fp:
                json.dump(self.settings, fp, indent=2, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover - 仅日志输出
            print(f"保存设置失败: {exc}")
        else:
            try:
                state = self._serialize_runtime_state()
                self._write_state_to_file(state, self.session_path)
            except Exception as exc:  # pragma: no cover - 仅日志输出
                print(f"保存会话状态失败: {exc}")

    def _normalize_display_settings(self) -> None:
        """Ensure window settings use supported defaults and constraints."""
        display = self.settings.setdefault('display', {})

        def _coerce(value: Any, fallback: int) -> int:
            try:
                coerced = int(value)
            except (TypeError, ValueError):
                return fallback
            return coerced

        width = _coerce(display.get('window_width', WINDOW_DEFAULT_WIDTH), WINDOW_DEFAULT_WIDTH)
        height = _coerce(display.get('window_height', WINDOW_DEFAULT_HEIGHT), WINDOW_DEFAULT_HEIGHT)

        # 自动迁移旧版默认值
        if width == 1000 and height == 900:
            width, height = WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT

        width = max(WINDOW_MIN_WIDTH, width)
        height = max(WINDOW_MIN_HEIGHT, height)

        display['window_width'] = width
        display['window_height'] = height
        display['fullscreen'] = bool(display.get('fullscreen', False))

    def _refresh_ui_labels(self) -> None:
        """根据当前设置刷新侧边栏按钮文字。"""
        difficulty_name = self.settings['game'].get('ai_difficulty', AI_DEFAULT_DIFFICULTY)
        difficulty_configs = _CONFIG.get_difficulty_names()
        config = difficulty_configs.get(difficulty_name)
        label = config.display_name if config else difficulty_name.title()
        if 'difficulty' in self.ui_manager.buttons:
            self.ui_manager.buttons['difficulty'].text = f"AI难度: {label}"

        if 'mode' in self.ui_manager.buttons:
            mode_text = "模式: " + ("人机对战" if self.game_mode == 'pvc' else "双人对战")
            self.ui_manager.buttons['mode'].text = mode_text

    def _serialize_runtime_state(self) -> Dict[str, Any]:
        """构建可序列化的运行时状态快照。"""
        current_time = time.time()
        elapsed = max(0.0, current_time - self.turn_start_time) if self.turn_start_time else 0.0

        def _serialize_state(state: PlayerRuntimeState) -> Dict[str, Any]:
            return {
                'name': state.name,
                'is_ai': state.is_ai,
                'score': state.score,
                'last_move': list(state.last_move) if state.last_move else None,
                'last_move_time': state.last_move_time,
                'total_time': state.total_time,
            }

        player_blob = {
            player.name: _serialize_state(state)
            for player, state in self.player_states.items()
        }

        return {
            'version': 1,
            'saved_at': datetime.now(timezone.utc).isoformat(),
            'settings': self.settings,
            'game_mode': self.game_mode,
            'ai_player': self.ai_player.value,
            'player_states': player_blob,
            'status_messages': list(self.status_messages),
            'game_result_recorded': self.game_result_recorded,
            'game_manager': {
                'max_undo': self.game_manager.max_undo,
                'undo_count': self.game_manager.undo_count,
            },
            'timers': {
                'current_turn_elapsed': elapsed,
            },
            'board': self.game_manager.board.to_dict(),
        }

    def _write_state_to_file(self, state: Dict[str, Any], path: Path) -> None:
        """将状态写入目标文件。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(state, fp, indent=2, ensure_ascii=False)

    def _restore_player_states(self, payload: Dict[str, Any]) -> None:
        """从存档数据恢复玩家积分与历史信息。"""
        for player in (Player.BLACK, Player.WHITE):
            data = payload.get(player.name)
            if not isinstance(data, dict):
                continue

            state = self.player_states[player]
            state.name = data.get('name', state.name)
            state.is_ai = bool(data.get('is_ai', state.is_ai))
            state.score = int(data.get('score', state.score))

            last_move = data.get('last_move')
            if isinstance(last_move, (list, tuple)) and len(last_move) == 2:
                state.last_move = (int(last_move[0]), int(last_move[1]))
            else:
                state.last_move = None

            last_move_time = data.get('last_move_time')
            state.last_move_time = float(last_move_time) if last_move_time is not None else None

            total_time = data.get('total_time')
            state.total_time = float(total_time) if total_time is not None else 0.0

            state.thinking = False
            state.thinking_duration = 0.0

    def _load_saved_session_if_available(self) -> None:
        """尝试加载最近一次保存的会话。"""
        if not self.session_path.exists():
            return

        try:
            with open(self.session_path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
        except Exception as exc:  # pragma: no cover - 容错日志
            print(f"加载存档失败: {exc}")
            return

        board_blob = data.get('board')
        if not isinstance(board_blob, dict):
            return

        settings_blob = data.get('settings')
        if isinstance(settings_blob, dict):
            self.settings = settings_blob
            self._normalize_display_settings()

        self.game_mode = data.get('game_mode', self.game_mode)
        self._sync_player_profiles()

        ai_player_value = data.get('ai_player')
        if ai_player_value is not None:
            try:
                self.ai_player = Player(ai_player_value)
            except ValueError:  # pragma: no cover - 容错处理
                pass

        board = Board.from_dict(board_blob)
        manager_blob = data.get('game_manager', {})
        max_undo = int(manager_blob.get('max_undo', self.game_manager.max_undo))
        self.game_manager = GameManager(board, max_undo=max_undo)
        self.game_manager.undo_count = int(manager_blob.get('undo_count', 0))

        player_states_blob = data.get('player_states', {})
        if isinstance(player_states_blob, dict):
            self._restore_player_states(player_states_blob)

        messages = data.get('status_messages')
        if isinstance(messages, list):
            self.status_messages = deque(messages, maxlen=3)
        else:
            self.status_messages = deque(maxlen=3)

        timers = data.get('timers', {})
        elapsed = timers.get('current_turn_elapsed', 0.0)
        try:
            elapsed_float = float(elapsed)
        except (TypeError, ValueError):
            elapsed_float = 0.0
        self.turn_start_time = time.time() - max(0.0, elapsed_float)

        self.game_result_recorded = bool(data.get('game_result_recorded', False))

        difficulty = self.settings['game'].get('ai_difficulty', AI_DEFAULT_DIFFICULTY)
        self.ai_controller.set_difficulty(difficulty)

        self._log_info("已加载上次保存的棋局")
        self.ui_manager.resize(self.screen.get_width(), self.screen.get_height())
        self._refresh_ui_labels()
        if 'undo' in self.ui_manager.buttons:
            self.ui_manager.buttons['undo'].enabled = self.game_manager.can_undo()

    def _log_info(self, message: str) -> None:
        """记录状态信息供侧边栏显示"""
        self.status_messages.appendleft(message)

    def _sync_player_profiles(self) -> None:
        """根据当前模式刷新玩家名称和AI标志"""
        if self.game_mode == 'pvc':
            self.player_states[Player.BLACK].name = "玩家"
            self.player_states[Player.BLACK].is_ai = False
            self.player_states[Player.WHITE].name = "AI"
            self.player_states[Player.WHITE].is_ai = True
            self.ai_player = Player.WHITE
        else:
            self.player_states[Player.BLACK].name = "玩家一"
            self.player_states[Player.BLACK].is_ai = False
            self.player_states[Player.WHITE].name = "玩家二"
            self.player_states[Player.WHITE].is_ai = False
            self.ai_player = Player.WHITE

        for state in self.player_states.values():
            state.thinking = False
            state.thinking_duration = 0.0

    @staticmethod
    def _format_move(move: Optional[Tuple[int, int]]) -> Optional[str]:
        """将落子坐标转换为棋谱表示"""
        if move is None:
            return None
        row, col = move
        col_char = chr(ord('A') + col)
        return f"{col_char}{row + 1}"
    
    def _refresh_last_moves_from_history(self) -> None:
        """根据当前棋谱刷新最近落子信息"""
        latest: Dict[Player, Optional[Tuple[int, int]]] = {
            Player.BLACK: None,
            Player.WHITE: None,
        }
        for move in self.game_manager.board.history:
            latest[move.player] = (move.row, move.col)

        for player, state in self.player_states.items():
            state.last_move = latest[player]
            state.last_move_time = None
            state.thinking = False
            state.thinking_duration = 0.0

    def _build_sidebar_state(self) -> UISidebarState:
        board = self.game_manager.board

        if board.state == GameState.ONGOING:
            turn_label = "当前回合: " + ("黑方" if board.current_player == Player.BLACK else "白方")
            status_type = 'ongoing'
        elif board.state == GameState.BLACK_WIN:
            turn_label = "黑方胜利！"
            status_type = GameState.BLACK_WIN.value
        elif board.state == GameState.WHITE_WIN:
            turn_label = "白方胜利！"
            status_type = GameState.WHITE_WIN.value
        else:
            turn_label = "平局"
            status_type = GameState.DRAW.value

        players_data = []
        for player in (Player.BLACK, Player.WHITE):
            state = self.player_states[player]
            status_line = self._describe_player_status(player, state, board)
            players_data.append(
                PlayerPanelData(
                    name=state.name,
                    player=player,
                    score=state.score,
                    last_move=self._format_move(state.last_move),
                    last_move_time=state.last_move_time,
                    total_time=state.total_time,
                    status_line=status_line,
                    is_active=(board.state == GameState.ONGOING and board.current_player == player),
                    is_ai=state.is_ai,
                    is_thinking=state.thinking,
                    thinking_time=state.thinking_duration,
                )
            )

        info_lines = tuple(self.status_messages)
        mode_label = "模式: " + ("人机对战" if self.game_mode == 'pvc' else "双人对战")

        return UISidebarState(
            game_mode_label=mode_label,
            current_turn_text=turn_label,
            status_type=status_type,
            move_count=len(board.history),
            players=tuple(players_data),
            info_lines=info_lines,
        )

    def _describe_player_status(self, player: Player, state: PlayerRuntimeState, board: Board) -> str:
        """生成玩家状态文本"""
        if board.state != GameState.ONGOING:
            if (board.state == GameState.BLACK_WIN and player == Player.BLACK) or (
                board.state == GameState.WHITE_WIN and player == Player.WHITE
            ):
                return "已获胜"
            if board.state == GameState.DRAW:
                return "本局平局"
            return "对局结束"

        if state.thinking:
            return "思考中..."

        if board.current_player == player:
            return "等待落子" if not state.is_ai else "等待AI选择"

        return "等待对手"

    def _check_game_conclusion(self) -> None:
        """检测并记录胜负结果"""
        board = self.game_manager.board
        if board.state == GameState.ONGOING or self.game_result_recorded:
            return

        if board.state == GameState.BLACK_WIN:
            self.player_states[Player.BLACK].score += 1
            self._log_info(f"{self.player_states[Player.BLACK].name} 获胜")
        elif board.state == GameState.WHITE_WIN:
            self.player_states[Player.WHITE].score += 1
            self._log_info(f"{self.player_states[Player.WHITE].name} 获胜")
        else:
            self._log_info("本局为平局")

        for state in self.player_states.values():
            state.thinking = False
            state.thinking_duration = 0.0

        self.game_result_recorded = True

    def _reset_scores(self) -> None:
        for state in self.player_states.values():
            state.score = 0

    def _log_ai_stats(self, engine_name: str, stats: Dict[str, float]) -> None:
        parts = []
        nodes = stats.get('nodes_searched')
        if nodes is not None:
            parts.append(f"{int(nodes)} 节点")
        search_time = stats.get('search_time')
        if search_time:
            parts.append(f"{search_time:.3f} 秒")
        nps = stats.get('nodes_per_second')
        if nps:
            parts.append(f"{int(nps)} nps")
        tt_rate = stats.get('tt_hit_rate')
        if tt_rate:
            parts.append(f"TT命中率 {tt_rate:.1%}")
        message_detail = "，".join(parts) if parts else "无统计"
        console_message = f"[{engine_name}] AI搜索: {message_detail}"
        print(console_message)
        self._log_info(console_message)

    @staticmethod
    def _select_fallback_move(board: Board, ai_player: Player) -> Optional[Tuple[int, int]]:
        """当主搜索失败时选择一个安全的备用落点"""
        # 优先考虑当前已落子附近的位置
        neighbors = board.get_empty_neighbors(distance=1)
        if neighbors:
            # 简单评分：偏好连续棋子更多的位置
            best_move = None
            best_score = -1
            for row, col in neighbors:
                score = 0
                for dr, dc in Board.DIRECTIONS:
                    r, c = row + dr, col + dc
                    if board.is_valid_pos(r, c) and board.get_stone(r, c) == ai_player:
                        score += 1
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
            if best_move:
                return best_move

        # 若附近没有合适位置，退化为选择任意可用空位
        for r in range(board.size):
            for c in range(board.size):
                if board.is_empty(r, c):
                    return (r, c)
        return None
    
    def handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.VIDEORESIZE:
                # 窗口大小调整
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.ui_manager.resize(event.w, event.h)
                self.settings['display']['window_width'] = event.w
                self.settings['display']['window_height'] = event.h
                self.settings['display']['fullscreen'] = False
                self.fullscreen = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)
            
            elif event.type == pygame.MOUSEMOTION:
                self.ui_manager.handle_mouse_motion(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self._handle_mouse_click(event.pos)
            
            # 按钮事件处理
            for button_name, button in self.ui_manager.buttons.items():
                if button.handle_event(event):
                    self._handle_button_click(button_name)
    
    def _handle_key_press(self, key: int) -> None:
        """处理按键"""
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_F11:
            # 全屏切换
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                width = self.settings['display']['window_width']
                height = self.settings['display']['window_height']
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            self.settings['display']['fullscreen'] = self.fullscreen
            
            # 更新布局
            info = pygame.display.Info()
            self.ui_manager.resize(info.current_w, info.current_h)
        
        elif key == pygame.K_u:
            # 悔棋
            self._handle_undo()
        
        elif key == pygame.K_r:
            # 重新开始
            self._handle_new_game()
        
        elif key == pygame.K_F4:
            # 字体调试
            font_mgr = get_font_manager()
            font_mgr.toggle_debug()
    
    def _handle_mouse_click(self, pos: tuple) -> None:
        """处理鼠标点击"""
        board = self.game_manager.board
        if self.ai_thinking:
            return  # AI思考中，禁止落子

        if self.game_mode == 'pvc' and board.current_player == self.ai_player:
            # 人机对战且轮到AI时，阻止玩家代替AI落子
            return
        
        board_pos = self.ui_manager.handle_click(pos)
        if board_pos:
            row, col = board_pos
            self._place_stone(row, col)
    
    def _place_stone(self, row: int, col: int,
                     duration_override: Optional[float] = None,
                     think_time: Optional[float] = None) -> None:
        """放置棋子"""
        board = self.game_manager.board
        
        # 检查游戏状态
        if board.state != GameState.ONGOING:
            return
        
        # 落子
        if self.game_manager.place_stone(row, col):
            move_player = board.history[-1].player
            duration = duration_override if duration_override is not None else max(0.0, time.time() - self.turn_start_time)
            self._record_move(move_player, row, col, duration_override if duration_override is not None else duration, think_time)
            # 添加动画
            self.ui_manager.add_stone_animation(row, col)
            
            # 检查是否需要AI行动
            if (self.game_mode == 'pvc' and 
                board.state == GameState.ONGOING and
                board.current_player == self.ai_player):
                self.ai_thinking = True
                self.player_states[self.ai_player].thinking = True
                self.player_states[self.ai_player].thinking_duration = 0.0
                self.ai_think_start = time.time()
            else:
                self.ai_thinking = False
                self.player_states[self.ai_player].thinking = False
                self.ai_think_start = None

            self.turn_start_time = time.time()
            self.game_result_recorded = False
    
    def _handle_button_click(self, button_name: str) -> None:
        """处理按钮点击"""
        if button_name == 'new_game':
            self._handle_new_game()
        
        elif button_name == 'undo':
            self._handle_undo()
        
        elif button_name == 'difficulty':
            self._cycle_difficulty()
        
        elif button_name == 'mode':
            self._toggle_game_mode()
        
        elif button_name == 'save':
            self._save_game()
    
    def _handle_new_game(self) -> None:
        """开始新游戏"""
        self.game_manager.reset()
        self.ai_thinking = False
        self.ai_controller.clear_cache()  # 清空缓存
        for state in self.player_states.values():
            state.reset_round()
        self.turn_start_time = time.time()
        self.ai_think_start = None
        self.game_result_recorded = False
        self.status_messages.clear()
        self._log_info("开始新局")
    
    def _handle_undo(self) -> None:
        """悔棋"""
        if not self.game_manager.can_undo():
            return
        
        if self.game_mode == 'pvc':
            # 人机对战：悔棋两步
            success = self.game_manager.undo(count=2)
        else:
            # 双人对战：悔棋一步
            success = self.game_manager.undo(count=1)

        if success:
            self._refresh_last_moves_from_history()
            self.ai_thinking = False
            self.player_states[self.ai_player].thinking = False
            self.ai_think_start = None
            self.turn_start_time = time.time()
            self.game_result_recorded = False
            self._log_info("执行悔棋")
    
    def _cycle_difficulty(self) -> None:
        """切换难度"""
        difficulty_configs = _CONFIG.get_difficulty_names()
        difficulties = list(difficulty_configs.keys()) or ['easy', 'medium', 'hard']
        current = self.settings['game']['ai_difficulty']
        current_idx = difficulties.index(current) if current in difficulties else 1
        next_idx = (current_idx + 1) % len(difficulties)
        new_difficulty = difficulties[next_idx]
        
        self.settings['game']['ai_difficulty'] = new_difficulty
        self.ai_controller.set_difficulty(new_difficulty)
        self._refresh_ui_labels()
    
    def _toggle_game_mode(self) -> None:
        """切换游戏模式（人机/双人）"""
        if self.game_mode == 'pvp':
            self.game_mode = 'pvc'
        else:
            self.game_mode = 'pvp'

        self._sync_player_profiles()
        self._reset_scores()
        for state in self.player_states.values():
            state.reset_round()
        self.ai_thinking = False
        self.ai_think_start = None
        self.turn_start_time = time.time()
        self.game_result_recorded = False
        self.status_messages.clear()
        self._refresh_ui_labels()
        mode_desc = "人机对战" if self.game_mode == 'pvc' else "双人对战"
        self._log_info(f"切换为{mode_desc}")
    
    def _save_game(self) -> None:
        """保存游戏"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gomoku_save_{timestamp}.json"
        filepath = self.save_dir / filename

        state = self._serialize_runtime_state()

        try:
            self._write_state_to_file(state, filepath)
            self._write_state_to_file(state, self.session_path)
            self._log_info("棋局已保存")
            print(f"游戏已保存: {filepath}")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def update(self) -> None:
        """更新游戏逻辑"""
        dt = self.clock.get_time()
        
        # 更新UI动画
        self.ui_manager.update(dt)
        
        # AI思考流程
        if self.ai_thinking and self.game_mode == 'pvc':
            board = self.game_manager.board
            # 立即清除思考标志，避免在同一帧内重复触发
            self.ai_thinking = False

            if board.state == GameState.ONGOING:
                if self.ai_think_start is not None:
                    elapsed = time.time() - self.ai_think_start
                    self.player_states[self.ai_player].thinking_duration = max(0.0, elapsed)

                best_move = self.ai_controller.find_best_move(board, self.ai_player)
                fallback_used = False

                if best_move is None:
                    fallback_move = self._select_fallback_move(board, self.ai_player)
                    if fallback_move:
                        best_move = fallback_move
                        fallback_used = True
                        self._log_info("AI 使用备用策略落子")

                if best_move:
                    stats = self.ai_controller.get_stats()
                    engine_name = self.ai_controller.get_engine_name()
                    search_time = stats.get('search_time')
                    row, col = best_move
                    self._place_stone(row, col, duration_override=search_time, think_time=search_time)
                    if not fallback_used:
                        self._log_ai_stats(engine_name, stats)
                else:
                    self._log_info("AI 未找到可落子位置")

            self.player_states[self.ai_player].thinking = False
            self.ai_think_start = None

        self._check_game_conclusion()

        # 更新悔棋按钮状态
        self.ui_manager.buttons['undo'].enabled = self.game_manager.can_undo()

    def _record_move(self, player: Player, row: int, col: int,
                     duration: Optional[float], think_time: Optional[float] = None) -> None:
        """更新玩家落子信息与时间统计"""
        state = self.player_states[player]
        state.last_move = (row, col)
        state.last_move_time = duration if duration is not None else None
        if duration is not None:
            state.total_time += duration
        state.thinking = False
        state.thinking_duration = think_time or 0.0

        move_text = self._format_move((row, col)) or "--"
        if duration is not None:
            self._log_info(f"{state.name} 落子 {move_text} (耗时 {duration:.2f}s)")
        else:
            self._log_info(f"{state.name} 落子 {move_text}")

    def draw(self) -> None:
        """绘制画面"""
        sidebar_state = self._build_sidebar_state()
        self.ui_manager.draw(self.screen, self.game_manager.board, sidebar_state)
        
        # 绘制字体调试信息
        font_mgr = get_font_manager()
        if font_mgr.debug_mode:
            debug_info = font_mgr.get_debug_info()
            debug_surf = font_mgr.render_text(debug_info, 12, (255, 255, 0))
            self.screen.blit(debug_surf, (10, 10))
        
        pygame.display.flip()
    
    def run(self) -> None:
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        
        # 退出时保存设置
        self._save_settings()
        pygame.quit()


def main() -> None:
    """主函数"""
    print("🎮 启动五子棋游戏...")
    print("=" * 50)
    print("操作说明:")
    print("  鼠标左键: 落子")
    print("  U键: 悔棋")
    print("  R键: 重新开始")
    print("  F11: 全屏切换")
    print("  ESC: 退出游戏")
    print("  F4: 字体调试信息")
    print("=" * 50)
    
    try:
        game = GomokuGame()
        game.run()
    except Exception as e:
        print(f"❌ 游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


def run_game() -> None:
    """包导入接口"""
    main()


if __name__ == "__main__":
    main()
