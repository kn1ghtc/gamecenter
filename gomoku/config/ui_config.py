"""UI配置
UI configuration for Gomoku.
"""

# 布局配置
LAYOUT = {
    'board_margin': 40,      # 棋盘边距
    'ui_panel_width': 250,   # 右侧UI面板宽度
    'button_width': 200,     # 按钮宽度
    'button_height': 50,     # 按钮高度
    'button_spacing': 15,    # 按钮间距
    'panel_padding': 20,     # 面板内边距
}

# 字体配置
FONTS = {
    'title': 32,           # 标题字体大小
    'large': 24,           # 大号字体
    'normal': 18,          # 普通字体
    'small': 14,           # 小号字体
    'button': 20,          # 按钮字体
}

# 动画配置
ANIMATION = {
    'stone_drop_duration': 200,    # 落子动画时长（毫秒）
    'stone_scale_start': 0.3,      # 落子初始缩放
    'winning_line_blink': 500,     # 获胜线闪烁间隔（毫秒）
    'button_hover_duration': 150,  # 按钮悬停动画时长
}

# 渲染配置
RENDERING = {
    'antialias': True,              # 抗锯齿
    'stone_3d_effect': True,        # 棋子3D效果
    'board_wood_texture': True,     # 棋盘木纹纹理
    'shadow_enabled': True,         # 棋子阴影
    'shadow_offset': 3,             # 阴影偏移（像素）
}

# 交互配置
INTERACTION = {
    'hover_preview': True,          # 悬停预览
    'click_feedback': True,         # 点击反馈
    'sound_enabled': True,          # 音效开关
    'show_coordinates': False,      # 显示坐标
    'show_last_move': True,         # 显示最后一步标记
}
