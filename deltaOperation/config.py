import sys
from pathlib import Path
import pygame

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT.parent.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent.parent))

ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
SAVES_DIR = PROJECT_ROOT / "saves"

for d in [ASSETS_DIR, DATA_DIR, SAVES_DIR]:
    d.mkdir(exist_ok=True)

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "三角洲行动 - Delta Force: Shadow Operations"
FPS = 60
TILE_SIZE = 32
VIEWPORT_WIDTH = WINDOW_WIDTH // TILE_SIZE
VIEWPORT_HEIGHT = WINDOW_HEIGHT // TILE_SIZE

PLAYER_CONFIG = {
    "width": 48,
    "height": 64,
    "health": 100,
    "max_health": 100,
    "move_speed": 400,  # 像素/秒 (300→400提升响应速度)
    "jump_force": -18,  # 跳跃力 (-12→-18更有力)
    "gravity": 1.2,     # 重力加速度 (0.8→1.2更快落地)
    "max_fall_speed": 20,  # 最大下落速度 (15→20)
    "air_control": 0.7,  # 空中控制力 (新增，空中移动灵敏度)
    "crouch_speed_mult": 0.4,  # 下蹲速度倍率 (0.5→0.4)
    "acceleration": 2500,  # 加速度 (新增，快速启停)
}

WEAPON_DATABASE = {
    "pistol": {
        "name": "M9 Pistol",
        "damage": 15,
        "fire_rate": 2.5,
        "magazine_size": 15,
        "reload_time": 1.5,
        "bullet_speed": 20,
        "accuracy": 0.9,
        "reserve_ammo": 90
    },
    "rifle": {
        "name": "M4A1",
        "damage": 25,
        "fire_rate": 10,
        "magazine_size": 30,
        "reload_time": 2.0,
        "bullet_speed": 30,
        "accuracy": 0.85,
        "reserve_ammo": 120
    },
    "sniper": {
        "name": "M24",
        "damage": 80,
        "fire_rate": 0.67,
        "magazine_size": 5,
        "reload_time": 3.0,
        "bullet_speed": 50,
        "accuracy": 0.98,
        "reserve_ammo": 20
    },
    "shotgun": {
        "name": "M870",
        "damage": 60,
        "fire_rate": 1.25,
        "magazine_size": 8,
        "reload_time": 2.5,
        "bullet_speed": 15,
        "accuracy": 0.7,
        "reserve_ammo": 32
    }
}

ENEMY_TYPES = {
    "grunt": {"health": 50, "damage": 10, "move_speed": 2},
    "elite": {"health": 100, "damage": 20, "move_speed": 3},
    "boss": {"health": 500, "damage": 40, "move_speed": 1.5}
}

CONTROLS_P1 = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "jump": pygame.K_w,
    "crouch": pygame.K_s,
    "shoot": pygame.K_SPACE,
    "reload": pygame.K_r,
    "interact": pygame.K_e,
    "weapon_next": pygame.K_q,
    "weapon_prev": pygame.K_e,
    "pause": pygame.K_ESCAPE
}

CONTROLS_P2 = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "jump": pygame.K_UP,
    "crouch": pygame.K_DOWN,
    "shoot": pygame.K_RCTRL,
    "reload": pygame.K_PERIOD,
    "interact": pygame.K_COMMA,
    "weapon_next": pygame.K_SLASH,
    "weapon_prev": pygame.K_COMMA,
    "pause": pygame.K_ESCAPE
}
