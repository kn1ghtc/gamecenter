#!/usr/bin/env python3
import json
from pathlib import Path

# 读取资源目录和角色数据库
catalog = json.load(open('d:/pyproject/gamecenter/streetBattle/assets/resource_catalog.json', 'r', encoding='utf-8'))
chars_db = json.load(open('d:/pyproject/gamecenter/streetBattle/assets/comprehensive_kof_characters.json', 'r', encoding='utf-8'))

# 获取有效角色名单
valid_chars = [name for name, info in catalog.items() if info.get('sketchfab', {}).get('uid')]

print(f'有效角色数量: {len(valid_chars)}')

# 过滤角色数据库，只保留有效角色
filtered_chars = [char for char in chars_db['characters'] if char.get('id') in valid_chars]

# 更新元数据
chars_db['metadata']['total_characters'] = len(filtered_chars)
chars_db['metadata']['description'] = f'Valid downloadable KOF characters ({len(filtered_chars)} total)'
chars_db['metadata']['last_updated'] = '2025-09-26'
chars_db['characters'] = filtered_chars

# 保存更新后的文件
with open('d:/pyproject/gamecenter/streetBattle/assets/comprehensive_kof_characters.json', 'w', encoding='utf-8') as f:
    json.dump(chars_db, f, indent=2, ensure_ascii=False)

print(f'已更新角色数据库：减少到 {len(filtered_chars)} 个有效角色')
print('前10个有效角色：')
for i, char in enumerate(filtered_chars[:10]):
    print(f'  {i+1}. {char["name"]} ({char["id"]})')
if len(filtered_chars) > 10:
    print(f'  ... 还有 {len(filtered_chars) - 10} 个角色')