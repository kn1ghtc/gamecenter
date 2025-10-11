"""批量更新配置引用脚本"""
import re

files_to_update = [
    'ai_engine_phase2.py',
    'ai_engine_manager.py'
]

for filename in files_to_update:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换Phase2AIController的__init__
        content = re.sub(
            r'def __init__\(self, difficulty: DifficultyLevel = DifficultyLevel\.MEDIUM,\s+time_limit: float = 5\.0\):',
            'def __init__(self, difficulty: str = "medium", time_limit: float = None):',
            content
        )
        
        # 替换set_difficulty
        content = re.sub(
            r'def set_difficulty\(self, difficulty: DifficultyLevel\)',
            'def set_difficulty(self, difficulty: str)',
            content
        )
        
        # 替换difficulty赋值
        if 'phase2' in filename:
            init_replacement = '''def __init__(self, difficulty: str = "medium", time_limit: float = None):
        # 加载难度配置
        self.difficulty_config = get_difficulty_config(difficulty)
        self.difficulty_name = difficulty
        self.time_limit = time_limit if time_limit is not None else self.difficulty_config.time_limit
        
        self.zobrist = ZobristHasher()
        tt_size = self.difficulty_config.transposition_table_size
        self.tt = TranspositionTable(max_size=tt_size, zobrist=self.zobrist)
        self.history_table = HistoryTable()
        self.killer_table = KillerMoveTable(max_depth=20)
        self.nodes_searched = 0
        self.search_time = 0.0
        self.search_start_time = 0.0
        self.current_hash = 0
        self.pv_move = None
        self.null_move_allowed = True
        
        # Phase 2优化配置
        phase2_config = get_config_manager().get_phase2_config()
        self.lmr_config = phase2_config.get('late_move_reduction', {})
        self.nmp_config = phase2_config.get('null_move_pruning', {})
        self.incr_eval_config = phase2_config.get('incremental_evaluation', {})'''
            
            content = re.sub(
                r'def __init__\(self.*?\n.*?self\.null_move_allowed = True',
                init_replacement,
                content,
                flags=re.DOTALL
            )
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ 更新 {filename}')
    
    except Exception as e:
        print(f'❌ 更新 {filename} 失败: {e}')

print('\n完成批量更新')
