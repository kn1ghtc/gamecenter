import sys
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ENEMY_CONFIG

print(f"AI_DECISION_FREQUENCY in ENEMY_CONFIG: {ENEMY_CONFIG.get('AI_DECISION_FREQUENCY', 'NOT FOUND')}")
print(f"Full ENEMY_CONFIG: {ENEMY_CONFIG}")
