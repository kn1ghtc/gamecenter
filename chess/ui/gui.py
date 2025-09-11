"""
国际象棋主要用户界面
基于Pygame的图形界面
"""
import pygame
import sys
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config.settings import *
from game.game_state import ChessGameState, GameState, GameMode
from game.pieces import PieceColor
from ai.ai_factory import ai_factory
from ui.board_renderer import ChessBoardRenderer, AnimationManager
from data.database import ChessDatabase
from game.board import ChessBoard

try:
    # 备用直连ML模型（当ai_factory不可用或未实现MEDIUM时）
    from ai.ml_ai import ChessMLAI
except Exception:
    ChessMLAI = None

class ChessUI:
    """国际象棋用户界面"""
    
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🏆 Professional Chess Game")
        self.clock = pygame.time.Clock()

        # 游戏组件
        self.game_state = ChessGameState()
        self.board_renderer = ChessBoardRenderer()
        self.animation_manager = AnimationManager()

        # AI对手（延迟加载）
        self.ai_opponents = {
            'EASY': None,    # BasicAI
            'MEDIUM': None,  # ChessMLAI
            'HARD': None     # GPTChessAI
        }

        # UI组件
        self.fonts = self._init_fonts()
        self.buttons = {}
        self.panels = {}
        self._init_ui_components()

        # 事件处理
        self.game_state.add_observer(self._on_game_event)

        # 资源与状态
        self.sounds = self._load_sounds()
        # 数据库（用于保存对局与训练样本）
        try:
            self.db = ChessDatabase(DATABASE_PATH)
        except Exception:
            # 回退：尝试使用相对路径
            chess_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fallback_db = os.path.join(chess_dir, "data", "chess_games.db")
            os.makedirs(os.path.dirname(fallback_db), exist_ok=True)
            self.db = ChessDatabase(fallback_db)

        # 运行标志
        self.running = True

        # 主菜单与游戏按钮
        # 菜单选择按钮保持原先的大致位置
    
    def _init_fonts(self) -> Dict:
        """初始化字体"""
        return {
            'title': pygame.font.Font(None, 48),
            'large': pygame.font.Font(None, 36),
            'medium': pygame.font.Font(None, 24),
            'small': pygame.font.Font(None, 18)
        }
    

    def _init_ui_components(self):
        # 初始化面板与按钮，确保先有 captured 面板再计算按钮位置
        self.panels = {
            'board': pygame.Rect(30, 30, BOARD_SIZE * SQUARE_SIZE, BOARD_SIZE * SQUARE_SIZE),
            'info': pygame.Rect(BOARD_SIZE * SQUARE_SIZE + 60, 30, 320, 200),
            'moves': pygame.Rect(BOARD_SIZE * SQUARE_SIZE + 60, 250, 320, 200),
            'captured': pygame.Rect(BOARD_SIZE * SQUARE_SIZE + 60, 470, 320, 100)
        }

        # 先清空并设置菜单按钮（主菜单显示用）
        self.buttons = {}
        menu_button_width = 200
        menu_button_x = WINDOW_WIDTH - menu_button_width - 20
        self.buttons['vs_human'] = pygame.Rect(menu_button_x, 120, menu_button_width, 50)
        self.buttons['vs_ai_easy'] = pygame.Rect(menu_button_x, 190, menu_button_width, 50)
        self.buttons['vs_ai_medium'] = pygame.Rect(menu_button_x, 260, menu_button_width, 50)
        self.buttons['vs_ai_hard'] = pygame.Rect(menu_button_x, 330, menu_button_width, 50)

        # 游戏界面按钮：两排布局，放在 captured 面板下方
        button_height = 36
        base_y = self.panels['captured'].bottom + 20
        gap_x = 16
        gap_y = 10

        # 两列宽度计算：按钮不遮挡右侧边距
        total_width = 320  # 与右侧面板统一宽度
        col_width = (total_width - gap_x) // 2
        left_x = self.panels['captured'].x
        right_x = left_x + col_width + gap_x

        # 第一排：New Game | Menu
        self.buttons['new_game'] = pygame.Rect(left_x, base_y, col_width, button_height)
        self.buttons['menu'] = pygame.Rect(right_x, base_y, col_width, button_height)
        # 第二排：Undo | Pause
        row2_y = base_y + button_height + gap_y
        self.buttons['undo'] = pygame.Rect(left_x, row2_y, col_width, button_height)
        self.buttons['pause'] = pygame.Rect(right_x, row2_y, col_width, button_height)
    
    def _load_sounds(self) -> Dict:
        """加载音效（优先加载本地 OGG 文件）"""
        sounds = {}
        sound_dir = os.path.join(PATHS['assets'], "sounds")
        move_path = os.path.join(sound_dir, "move.ogg")
        capture_path = os.path.join(sound_dir, "capture.ogg")
        check_path = os.path.join(sound_dir, "check.ogg")

        try:
            pygame.mixer.init()
            if os.path.exists(move_path):
                sounds['move'] = pygame.mixer.Sound(move_path)
            if os.path.exists(capture_path):
                sounds['capture'] = pygame.mixer.Sound(capture_path)
            if os.path.exists(check_path):
                sounds['check'] = pygame.mixer.Sound(check_path)
        except Exception as e:
            # 声音不是关键路径，失败时静默
            pass

        return sounds
    
    def _on_game_event(self, event: str, data: Dict):
        """处理游戏事件"""
        if event == 'move_made':
            # 播放移动音效
            if 'move' in self.sounds:
                self.sounds['move'].play()
                
            # 添加移动动画
            from_pos = data['from']
            to_pos = data['to']
            piece = self.game_state.board.get_piece_at(to_pos)
            if piece:
                self.animation_manager.add_move_animation(piece, from_pos, to_pos)
        
        elif event == 'game_ended':
            # 保存对局并提示
            try:
                self._save_game_to_db(data)
            except Exception as e:
                print(f"⚠️ 保存对局到数据库失败: {e}")
            self._show_game_over_message(data)
    
    def run(self):
        """主游戏循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._render()
        
        pygame.quit()
        sys.exit()
    
    def _handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self._handle_mouse_click(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)
    
    def _handle_mouse_click(self, pos: tuple):
        """处理鼠标点击"""
        # 检查按钮点击
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(pos):
                self._handle_button_click(button_name)
                return
        
        # 检查棋盘点击
        if self.panels['board'].collidepoint(pos):
            # 转换为棋盘坐标
            board_offset = (self.panels['board'].x, self.panels['board'].y)
            relative_pos = (pos[0] - board_offset[0], pos[1] - board_offset[1])
            board_pos = self.board_renderer.pixel_to_board_position(relative_pos)
            
            if board_pos and self.game_state.state == GameState.PLAYING:
                self.game_state.select_square(board_pos)
    
    def _handle_button_click(self, button_name: str):
        """处理按钮点击"""
        if button_name == 'new_game':
            self.game_state.start_new_game(GameMode.HUMAN_VS_HUMAN)
        
        elif button_name == 'vs_human':
            self.game_state.start_new_game(GameMode.HUMAN_VS_HUMAN)
        
        elif button_name == 'vs_ai_easy':
            self._start_ai_game('EASY')
        
        elif button_name == 'vs_ai_medium':
            self._start_ai_game('MEDIUM')
        
        elif button_name == 'vs_ai_hard':
            self._start_ai_game('HARD')
        
        elif button_name == 'undo':
            self.game_state.undo_move()
        
        elif button_name == 'pause':
            if self.game_state.state == GameState.PLAYING:
                self.game_state.pause_game()
            elif self.game_state.state == GameState.PAUSED:
                self.game_state.resume_game()
        
        elif button_name == 'menu':
            self.game_state.go_to_menu()
    
    def _handle_key_press(self, key):
        """处理键盘按键"""
        if key == pygame.K_ESCAPE:
            if self.game_state.state == GameState.PLAYING:
                self.game_state.go_to_menu()
            else:
                self.running = False
        
        elif key == pygame.K_u:
            self.game_state.undo_move()
        
        elif key == pygame.K_SPACE:
            if self.game_state.state == GameState.PLAYING:
                self.game_state.pause_game()
            elif self.game_state.state == GameState.PAUSED:
                self.game_state.resume_game()
    
    def _update(self, dt: float):
        """更新游戏状态"""
        self.animation_manager.update(dt)
        
        # AI移动处理
        if (self.game_state.state == GameState.PLAYING and 
            not self.game_state.is_human_turn() and 
            not self.animation_manager.is_animating()):
            self._make_ai_move()
    
    def _make_ai_move(self):
        """执行AI移动"""
        current_player = self.game_state.board.current_player
        ai_level = self.game_state.ai_level
        
        # 延迟加载AI实例
        if ai_level not in self.ai_opponents or self.ai_opponents[ai_level] is None:
            print(f"🤖 加载{ai_level}级AI...")
            ai = ai_factory.create_ai(ai_level)
            if ai:
                self.ai_opponents[ai_level] = ai
                print(f"✅ {ai_level}级AI加载成功")
            else:
                print(f"❌ {ai_level}级AI加载失败")
                return
        
        ai = self.ai_opponents[ai_level]
        if ai:
            print(f"🧠 {ai_level}级AI思考中...")
            move = ai.get_best_move(self.game_state.board, current_player)
            
            if move:
                from_pos, to_pos = move
                print(f"🎯 AI选择移动: {from_pos} -> {to_pos}")
                self.game_state.attempt_move(from_pos, to_pos)
            else:
                print("⚠️ AI未能生成有效移动")
    
    def _start_ai_game(self, difficulty: str):
        """开始AI对战游戏"""
        print(f"🎮 开始与{difficulty}级AI对战...")
        
        # 预加载AI（显示加载进度）
        if difficulty not in self.ai_opponents or self.ai_opponents[difficulty] is None:
            print(f"🔄 正在加载{difficulty}级AI...")
            ai = None
            try:
                # 优先通过工厂创建
                ai = ai_factory.create_ai(difficulty)
            except Exception as e:
                print(f"⚠️ AI工厂创建失败: {e}")
                ai = None

            # MEDIUM 使用训练好的ML模型作为回退
            if (ai is None or not hasattr(ai, 'get_best_move')) and difficulty == 'MEDIUM' and ChessMLAI:
                try:
                    model_path = AI_LEVELS['MEDIUM'].get('model_path')
                    print(f"📦 直接加载ML模型: {model_path}")
                    ai = ChessMLAI(model_path)
                except Exception as e:
                    print(f"⚠️ ML模型加载失败: {e}")
                    ai = None
            if ai:
                self.ai_opponents[difficulty] = ai
                print(f"✅ {difficulty}级AI加载完成")
            else:
                print(f"❌ {difficulty}级AI加载失败，使用备用AI")
                # 如果高级AI失败，使用基础AI作为备用
                backup_ai = ai_factory.create_ai('EASY')
                if backup_ai:
                    self.ai_opponents[difficulty] = backup_ai
                    print("✅ 备用AI加载成功")
        
        # 开始游戏
        self.game_state.start_new_game(GameMode.HUMAN_VS_AI, difficulty)

    # --- 数据与持久化 ---
    def _save_game_to_db(self, data: Dict):
        """保存当前对局到数据库（用于后续训练）"""
        end_time_dt = datetime.now()
        game_info = self.game_state.get_game_info()
        duration_sec = float(game_info.get('game_time', 0.0) or 0.0)
        start_time_dt = end_time_dt - timedelta(seconds=duration_sec)

        # 结果映射
        result = data.get('result', 'draw')
        if result not in ('white_wins', 'black_wins', 'draw'):
            # 兼容其他标记
            if result in ('white', 'White'):
                result = 'white_wins'
            elif result in ('black', 'Black'):
                result = 'black_wins'
            else:
                result = 'draw'

        total_moves = len(self.game_state.board.move_history)
        final_position = self._encode_board_simple_fen()

        # 玩家信息（尽量推断）
        mode = self.game_state.mode
        ai_level = self.game_state.ai_level if mode == GameMode.HUMAN_VS_AI else None
        white_type = 'human'
        black_type = 'human'
        if mode == GameMode.HUMAN_VS_AI:
            # 简化：默认白方为人类、黑方为AI（具体方位可根据项目需求调整）
            white_type = 'human'
            black_type = 'ai'

        game_data = {
            'start_time': start_time_dt.isoformat(timespec='seconds'),
            'end_time': end_time_dt.isoformat(timespec='seconds'),
            'white_player': 'Human' if white_type == 'human' else f"AI-{ai_level or ''}",
            'black_player': 'Human' if black_type == 'human' else f"AI-{ai_level or ''}",
            'white_type': white_type,
            'black_type': black_type,
            'ai_level': ai_level,
            'result': result,
            'total_moves': total_moves,
            'game_duration': duration_sec,
            'pgn': '',  # 可后续替换为真实PGN
            'final_position': final_position
        }

        game_id = self.db.save_game(game_data)

        # 使用临时棋盘回放每一步，以获取 position_after（简化FEN）
        temp_board = ChessBoard()

        # 保存每一步（尽力填充字段）
        for idx, mv in enumerate(self.game_state.board.move_history, start=1):
            try:
                if isinstance(mv, dict):
                    from_pos = mv.get('from')
                    to_pos = mv.get('to')
                    notation = mv.get('notation', None)
                    player_color = mv.get('player') or ( 'white' if idx % 2 == 1 else 'black')
                else:
                    # 对象形式的兼容
                    from_pos = getattr(mv, 'from_pos', None)
                    to_pos = getattr(mv, 'to_pos', None)
                    notation = getattr(mv, 'notation', None)
                    player_color = getattr(mv, 'player_color', ('white' if idx % 2 == 1 else 'black'))

                from_sq = self._board_pos_to_square(from_pos) if from_pos else ''
                to_sq = self._board_pos_to_square(to_pos) if to_pos else ''

                # 终局棋盘获取到达后的棋子类型（尽力而为）
                piece = self.game_state.board.get_piece_at(to_pos) if to_pos else None
                piece_type = piece.piece_type.name if piece else ''

                # 在临时棋盘上回放一步并记录该步后的简化FEN
                position_after_simple = ''
                try:
                    if from_pos and to_pos:
                        temp_board.make_move(from_pos, to_pos)
                        position_after_simple = self._encode_board_simple_fen_from_board(temp_board)
                except Exception:
                    position_after_simple = ''

                self.db.save_move(game_id, {
                    'move_number': idx,
                    'player_color': player_color,
                    'from_square': from_sq,
                    'to_square': to_sq,
                    'piece_type': piece_type,
                    'captured_piece': None,
                    'special_move': None,
                    'notation': notation or f"{from_sq}-{to_sq}",
                    'evaluation': None,
                    'think_time': None,
                    'position_after': position_after_simple
                })
            except Exception as e:
                print(f"⚠️ 保存移动失败（第{idx}步）: {e}")

    def _board_pos_to_square(self, pos):
        """将(行,列)坐标转换为代数记谱（a1..h8），假设(0,0)=a8"""
        try:
            row, col = pos
            file_char = chr(ord('a') + col)
            rank_char = str(8 - row)
            return f"{file_char}{rank_char}"
        except Exception:
            return ''

    def _encode_board_simple_fen(self) -> str:
        """生成简化FEN风格的棋盘编码（与训练侧兼容）"""
        pieces_list = []
        try:
            for row in range(8):
                for col in range(8):
                    piece = self.game_state.board.get_piece_at((row, col))
                    if piece:
                        color = 'W' if piece.color.name == 'WHITE' else 'B'
                        piece_type = piece.piece_type.name[0]
                        pieces_list.append(f"{row}{col}{color}{piece_type}")
        except Exception:
            pass
        return ';'.join(pieces_list)

    def _encode_board_simple_fen_from_board(self, board: ChessBoard) -> str:
        """基于给定棋盘生成简化FEN"""
        pieces_list = []
        try:
            for row in range(8):
                for col in range(8):
                    piece = board.get_piece_at((row, col))
                    if piece:
                        color = 'W' if piece.color.name == 'WHITE' else 'B'
                        piece_type = piece.piece_type.name[0]
                        pieces_list.append(f"{row}{col}{color}{piece_type}")
        except Exception:
            pass
        return ';'.join(pieces_list)
    
    def _render(self):
        """渲染画面"""
        self.screen.fill(COLORS['BACKGROUND'])
        
        if self.game_state.state == GameState.MENU:
            self._render_menu()
        else:
            self._render_game()
        
        pygame.display.flip()
    
    def _render_menu(self):
        """渲染主菜单"""
        # 标题
        title = self.fonts['title'].render("🏆 Professional Chess", True, COLORS['TEXT'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # 副标题
        subtitle = self.fonts['medium'].render("Choose your game mode", True, COLORS['TEXT'])
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # 菜单按钮（移除New Game，这应该只在游戏界面显示）
        menu_buttons = [
            ('vs_human', "Human vs Human"),
            ('vs_ai_easy', "vs AI (Easy)"),
            ('vs_ai_medium', "vs AI (Medium)"),
            ('vs_ai_hard', "vs AI (Hard)")
        ]
        
        for button_name, text in menu_buttons:
            if button_name in self.buttons:
                self._draw_button(self.buttons[button_name], text, self.fonts['medium'])
    
    def _render_game(self):
        """渲染游戏界面"""
        # 渲染棋盘
        board_offset = (self.panels['board'].x, self.panels['board'].y)
        self.board_renderer.render_board(self.screen, board_offset)
        
        # 渲染高亮和提示
        if self.game_state.highlighted_squares:
            self.board_renderer.render_highlights(self.screen, 
                                                 self.game_state.highlighted_squares, 
                                                 board_offset)
        
        if self.game_state.move_hints:
            self.board_renderer.render_move_hints(self.screen, 
                                                 self.game_state.move_hints, 
                                                 board_offset)
        
        # 渲染上一步移动
        if self.game_state.board.move_history:
            last_move = self.game_state.board.move_history[-1]
            self.board_renderer.render_last_move(self.screen, last_move, board_offset)
        
        # 渲染将军警告
        current_player = self.game_state.board.current_player
        if self.game_state.board.is_in_check(current_player):
            king_pos = self.game_state.board.get_king_position(current_player)
            if king_pos:
                self.board_renderer.render_check_warning(self.screen, king_pos, board_offset)
        
        # 渲染棋子（不在动画中的）
        pieces_to_render = {}
        animated_pieces = {anim['piece'] for anim in self.animation_manager.animations if anim['type'] == 'move'}
        
        for pos, piece in self.game_state.board.pieces.items():
            if piece not in animated_pieces:
                pieces_to_render[pos] = piece
        
        self.board_renderer.render_pieces(self.screen, pieces_to_render, board_offset)
        
        # 渲染动画
        self.animation_manager.render_animations(self.screen, self.board_renderer, board_offset)
        
        # 渲染UI面板
        self._render_game_info()
        self._render_move_history()
        self._render_captured_pieces()
        self._render_game_buttons()
    
    def _render_game_info(self):
        """渲染游戏信息面板"""
        panel = self.panels['info']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        y_offset = panel.y + 10
        
        # 当前玩家
        current_player_info = self.game_state.get_current_player_info()
        text = f"Current: {current_player_info['name']}"
        if current_player_info['in_check']:
            text += " (IN CHECK!)"
        
        rendered_text = self.fonts['medium'].render(text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 30
        
        # 游戏模式
        mode_text = f"Mode: {self.game_state.mode.value}"
        rendered_text = self.fonts['small'].render(mode_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 25
        
        # AI难度
        if self.game_state.mode == GameMode.HUMAN_VS_AI:
            ai_text = f"AI Level: {self.game_state.ai_level}"
            rendered_text = self.fonts['small'].render(ai_text, True, COLORS['TEXT'])
            self.screen.blit(rendered_text, (panel.x + 10, y_offset))
            y_offset += 25
        
        # 移动计数
        move_count = len(self.game_state.board.move_history)
        move_text = f"Moves: {move_count}"
        rendered_text = self.fonts['small'].render(move_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
        y_offset += 25
        
        # 游戏时间
        game_info = self.game_state.get_game_info()
        time_text = f"Time: {int(game_info['game_time'] // 60):02d}:{int(game_info['game_time'] % 60):02d}"
        rendered_text = self.fonts['small'].render(time_text, True, COLORS['TEXT'])
        self.screen.blit(rendered_text, (panel.x + 10, y_offset))
    
    def _render_move_history(self):
        """渲染移动历史"""
        panel = self.panels['moves']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        # 标题
        title = self.fonts['medium'].render("Move History", True, COLORS['TEXT'])
        self.screen.blit(title, (panel.x + 10, panel.y + 10))
        
        # 显示最近的移动
        y_offset = panel.y + 40
        moves = self.game_state.board.move_history[-8:]  # 显示最近8步
        
        for i, move in enumerate(moves):
            move_num = len(self.game_state.board.move_history) - len(moves) + i + 1
            notation = getattr(move, 'notation', f"{move['from']} -> {move['to']}")
            text = f"{move_num}. {notation}"
            
            rendered_text = self.fonts['small'].render(text, True, COLORS['TEXT'])
            self.screen.blit(rendered_text, (panel.x + 10, y_offset))
            y_offset += 20
            
            if y_offset > panel.bottom - 20:
                break
    
    def _render_captured_pieces(self):
        """渲染被吃棋子"""
        panel = self.panels['captured']
        pygame.draw.rect(self.screen, COLORS['UI_PANEL'], panel)
        pygame.draw.rect(self.screen, COLORS['TEXT'], panel, 2)
        
        title = self.fonts['medium'].render("Captured", True, COLORS['TEXT'])
        self.screen.blit(title, (panel.x + 10, panel.y + 10))
        
        # 显示被吃的棋子
        y_offset = panel.y + 35
        
        for color in ['white', 'black']:
            captured = self.game_state.board.captured_pieces[color]
            if captured:
                color_text = f"{color.capitalize()}: "
                # 使用简单文字而不是Unicode符号，避免字体渲染问题
                piece_names = []
                for piece in captured:
                    piece_name = piece.piece_type.name.capitalize()
                    piece_names.append(piece_name)
                
                pieces_text = ", ".join(piece_names)
                text = color_text + pieces_text
                
                rendered_text = self.fonts['small'].render(text, True, COLORS['TEXT'])
                self.screen.blit(rendered_text, (panel.x + 10, y_offset))
                y_offset += 20
    
    def _render_game_buttons(self):
        """渲染游戏按钮"""
        game_buttons = [
            ('new_game', "New Game"),
            ('undo', "Undo"),
            ('pause', "Pause" if self.game_state.state == GameState.PLAYING else "Resume"),
            ('menu', "Menu")
        ]
        
        for button_name, text in game_buttons:
            if button_name in self.buttons:
                self._draw_button(self.buttons[button_name], text, self.fonts['small'])
    
    def _draw_button(self, rect: pygame.Rect, text: str, font: pygame.font.Font, 
                    hover: bool = False):
        """绘制按钮"""
        color = COLORS['BUTTON_HOVER'] if hover else COLORS['BUTTON']
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS['TEXT'], rect, 2)
        
        text_surface = font.render(text, True, COLORS['TEXT'])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _show_game_over_message(self, game_data: Dict):
        """显示游戏结束消息"""
        winner = game_data.get('winner', 'draw')
        
        if winner == 'draw':
            message = "Game Over - Draw!"
        else:
            message = f"Game Over - {winner.capitalize()} Wins!"
        
        # 这里可以实现一个模态对话框
        print(message)  # 临时使用print

def main():
    """主函数"""
    chess_ui = ChessUI()
    chess_ui.run()

if __name__ == "__main__":
    main()
