"""
下载高质量国际象棋棋子图像
从GitHub Kadagaden/chess-pieces 仓库下载 Kaneo 风格的 SVG 棋子
"""

import requests
import os
from pathlib import Path
import cairosvg

def download_piece_images():
    """下载并转换棋子图像"""
    
    # GitHub原始文件URL基础路径
    base_url = "https://raw.githubusercontent.com/Kadagaden/chess-pieces/master/chess_kaneo/"
    
    # 棋子映射 - GitHub文件名到我们的命名约定
    piece_mappings = {
        # 白棋子
        'wK.svg': 'white_king.png',
        'wQ.svg': 'white_queen.png', 
        'wR.svg': 'white_rook.png',
        'wB.svg': 'white_bishop.png',
        'wN.svg': 'white_knight.png',
        'wP.svg': 'white_pawn.png',
        
        # 黑棋子
        'bK.svg': 'black_king.png',
        'bQ.svg': 'black_queen.png',
        'bR.svg': 'black_rook.png', 
        'bB.svg': 'black_bishop.png',
        'bN.svg': 'black_knight.png',
        'bP.svg': 'black_pawn.png'
    }
    
    # 创建pieces目录
    pieces_dir = Path(__file__).parent / "pieces"
    pieces_dir.mkdir(exist_ok=True)
    
    print("🏆 开始下载高质量国际象棋棋子...")
    
    for svg_name, png_name in piece_mappings.items():
        try:
            # 下载SVG文件
            svg_url = base_url + svg_name
            print(f"📥 下载 {svg_name}...")
            
            response = requests.get(svg_url)
            response.raise_for_status()
            
            # 转换SVG到PNG (60x60像素)
            png_path = pieces_dir / png_name
            cairosvg.svg2png(
                bytestring=response.content,
                write_to=str(png_path),
                output_width=60,
                output_height=60
            )
            
            print(f"✅ 成功保存 {png_name}")
            
        except Exception as e:
            print(f"❌ 下载 {svg_name} 失败: {e}")
    
    print("🎉 棋子下载完成!")

if __name__ == "__main__":
    download_piece_images()
