#!/bin/bash
# 小羊吃草生态模拟游戏启动脚本

echo "🐑 启动小羊吃草生态模拟游戏..."

# 检查Python环境
if command -v /usr/local/bin/python &> /dev/null; then
    PYTHON_CMD="/usr/local/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ 未找到Python环境，请确保已安装Python 3.7+"
    exit 1
fi

# 检查pygame是否安装
$PYTHON_CMD -c "import pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ pygame未安装，正在安装..."
    $PYTHON_CMD -m pip install pygame
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到游戏目录并运行
cd "$SCRIPT_DIR"
echo "🚀 启动游戏..."
$PYTHON_CMD main.py

echo "👋 游戏结束"
