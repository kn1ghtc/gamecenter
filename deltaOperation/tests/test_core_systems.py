"""
核心系统快速验证测试
测试物理引擎、玩家、武器系统的基本功能
"""

import os
import sys

# Windows UTF-8编码
os.system("chcp 65001 >nul 2>&1")

# 设置无头模式环境变量
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

# 初始化pygame
pygame.init()
pygame.mixer.init()

from gamecenter.deltaOperation.core import (
    PhysicsEngine, Player, WeaponFactory, WeaponType
)
from gamecenter.deltaOperation import config


def test_physics_engine():
    """测试物理引擎"""
    print("测试物理引擎...")
    
    engine = PhysicsEngine()
    assert engine.gravity == config.PLAYER_CONFIG["gravity"]
    assert engine.max_fall_speed == config.PLAYER_CONFIG["max_fall_speed"]
    
    # 测试AABB碰撞
    from gamecenter.deltaOperation.core.physics import AABB
    box1 = AABB(0, 0, 10, 10)
    box2 = AABB(5, 5, 10, 10)
    box3 = AABB(20, 20, 10, 10)
    
    assert box1.overlaps(box2), "应该检测到重叠"
    assert not box1.overlaps(box3), "不应该检测到重叠"
    
    collision = engine.check_aabb_collision(box1, box2)
    assert collision.collided, "应该检测到碰撞"
    
    print("✓ 物理引擎测试通过")


def test_player():
    """测试玩家系统"""
    print("测试玩家系统...")
    
    player = Player(100, 100, player_id=1)
    
    # 测试初始状态
    assert player.health == config.PLAYER_CONFIG["health"]
    assert player.is_alive()
    assert player.player_id == 1
    
    # 测试伤害
    initial_health = player.health
    player.take_damage(10)
    assert player.health == initial_health - 10
    
    # 测试治疗
    player.heal(5)
    assert player.health == initial_health - 5
    
    # 测试死亡
    player.take_damage(1000)
    assert not player.is_alive()
    
    # 测试序列化
    player2 = Player(200, 200, player_id=2)
    player_data = player2.to_dict()
    assert player_data["player_id"] == 2
    assert player_data["position"]["x"] == 200
    assert player_data["position"]["y"] == 200
    
    print("✓ 玩家系统测试通过")


def test_weapon():
    """测试武器系统"""
    print("测试武器系统...")
    
    # 测试工厂创建
    pistol = WeaponFactory.create_pistol()
    assert pistol.weapon_type == WeaponType.PISTOL
    assert pistol.current_ammo > 0
    
    rifle = WeaponFactory.create_rifle()
    assert rifle.weapon_type == WeaponType.RIFLE
    
    # 测试射击
    import pygame
    direction = pygame.math.Vector2(1, 0)
    bullet = pistol.shoot((100, 100), direction, owner_id=1)
    
    if bullet:  # 可能因为射速限制无法射击
        assert bullet.damage == pistol.damage
        assert bullet.owner_id == 1
    
    # 测试弹药
    initial_ammo = pistol.current_ammo
    for _ in range(initial_ammo):
        pistol.shoot((100, 100), direction)
        pistol.last_shot_time = 0  # 重置射击时间以立即射击
    
    assert pistol.current_ammo == 0, "子弹应该全部打完"
    assert not pistol.can_shoot(), "弹药耗尽后不能射击"
    
    # 测试换弹
    assert pistol.can_reload(), "应该可以换弹"
    pistol.start_reload()
    assert pistol.is_reloading, "应该正在换弹"
    pistol.reload()  # 强制完成换弹
    assert pistol.current_ammo > 0, "换弹后应该有子弹"
    
    # 测试序列化
    weapon_data = pistol.to_dict()
    assert weapon_data["weapon_type"] == "pistol"
    
    print("✓ 武器系统测试通过")


def test_integration():
    """集成测试 - 玩家持有武器射击"""
    print("测试集成系统...")
    
    # 创建玩家和物理引擎
    player = Player(100, 100)
    physics_engine = PhysicsEngine()
    
    # 给玩家添加武器
    pistol = WeaponFactory.create_pistol()
    player.add_weapon(pistol)
    
    assert player.current_weapon is not None, "玩家应该装备了武器"
    assert player.current_weapon.weapon_type == WeaponType.PISTOL
    
    # 模拟更新循环
    delta_time = 0.016  # 60 FPS
    
    # 更新玩家(不射击)
    player.update(delta_time, physics_engine)
    
    # 模拟射击
    player.is_shooting = True
    player.update(delta_time, physics_engine)
    
    # 检查子弹
    bullets = player.current_weapon.get_active_bullets()
    print(f"  发射了 {len(bullets)} 颗子弹")
    
    # 更新子弹
    player.current_weapon.update_bullets(delta_time, physics_engine)
    
    print("✓ 集成测试通过")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("三角洲行动 - 核心系统验证测试")
    print("=" * 50)
    
    try:
        test_physics_engine()
        test_player()
        test_weapon()
        test_integration()
        
        print("=" * 50)
        print("✓ 所有核心系统测试通过!")
        print("=" * 50)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
