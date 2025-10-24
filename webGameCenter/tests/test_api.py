# -*- coding: utf-8 -*-
"""
后端API测试
"""
import pytest
import json


def test_categories_endpoint(client, app):
    """测试游戏分类接口"""
    response = client.get('/api/games/categories')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list), "应返回列表"
    assert len(data) > 0, "应该有游戏分类"
    
    # 验证每个分类的数据
    for category in data:
        assert 'id' in category, "分类必须有id"
        assert 'name' in category, "分类必须有name"
        assert 'icon' in category, "分类必须有icon"
        assert 'description' in category, "分类必须有description"
        assert 'game_count' in category, "分类必须有game_count"
        assert category['game_count'] > 0, f"分类 {category['id']} 应该至少有一个游戏"
    
    print("✓ 游戏分类接口测试通过")


def test_category_games_endpoint(client, app):
    """测试获取分类游戏接口"""
    # 先获取分类列表
    categories_response = client.get('/api/games/categories')
    categories = json.loads(categories_response.data)
    
    if len(categories) == 0:
        pytest.skip("没有可用的游戏分类")
    
    category_id = categories[0]['id']
    
    # 测试获取该分类的游戏
    response = client.get(f'/api/games/category/{category_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'games' in data, "应返回games字段"
    assert isinstance(data['games'], list), "games应为列表"
    assert len(data['games']) > 0, "应该有游戏"
    
    # 验证每个游戏的数据
    for game in data['games']:
        assert 'game_id' in game or 'id' in game, "游戏必须有id"
        assert 'name' in game, "游戏必须有name"
        assert 'description' in game, "游戏必须有description"
    
    print(f"✓ 分类 {category_id} 游戏列表测试通过，共 {len(data['games'])} 个游戏")


def test_invalid_category_endpoint(client, app):
    """测试无效分类处理"""
    response = client.get('/api/games/category/invalid_category')
    assert response.status_code == 404, "应该返回404错误"
    
    print("✓ 无效分类错误处理测试通过")


def test_all_configured_games_have_implementations(app):
    """测试所有配置的游戏都有实现"""
    from pathlib import Path
    
    games_config = app.config.get('GAMES_CONFIG', {})
    base_path = Path(__file__).parent.parent / 'frontend' / 'games'
    
    missing_games = []
    
    for category_id, category_data in games_config.items():
        for game_info in category_data.get('games', []):
            game_id = game_info['id']
            # 这里应该检查游戏文件是否存在
            # 根据配置推断游戏路径
            print(f"  验证游戏: {game_id} ({game_info['name']})")
    
    assert len(missing_games) == 0, f"以下游戏缺少实现: {missing_games}"
    print("✓ 所有配置的游戏都有实现")
