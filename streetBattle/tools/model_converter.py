#!/usr/bin/env python3
"""
3D Model Format Converter for Panda3D
将通用3D模型格式(.obj/.fbx/.gltf/.dae/.3ds)转换为Panda3D原生.egg格式

Usage:
    python model_converter.py --input model.fbx --output character.egg
    python model_converter.py --batch input_dir/ --output_dir assets/characters/
"""

import os
import sys
import argparse
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelConverter:
    """3D模型格式转换器，支持转换为Panda3D兼容的.egg格式"""
    
    SUPPORTED_INPUT_FORMATS = ['.obj', '.fbx', '.gltf', '.glb', '.dae', '.3ds', '.blend', '.ply']
    PANDA3D_TOOLS = {
        'obj2egg': 'obj2egg',
        'dae2egg': 'dae2egg', 
        'fbx2egg': 'fbx2egg',
        'gltf2egg': 'gltf2egg',
        'x2egg': 'x2egg'
    }
    
    def __init__(self, panda3d_bin_path: Optional[str] = None):
        """
        初始化转换器
        
        Args:
            panda3d_bin_path: Panda3D bin目录路径，如果为None则使用系统PATH
        """
        self.panda3d_bin_path = panda3d_bin_path
        self.validate_panda3d_tools()
        
    def validate_panda3d_tools(self) -> bool:
        """验证Panda3D转换工具是否可用"""
        missing_tools = []
        
        for tool_name in self.PANDA3D_TOOLS.values():
            if not self._check_tool_available(tool_name):
                missing_tools.append(tool_name)
        
        if missing_tools:
            logger.warning(f"Missing Panda3D tools: {missing_tools}")
            logger.info("Will attempt alternative conversion methods")
            return False
        
        logger.info("All Panda3D conversion tools are available")
        return True
        
    def _check_tool_available(self, tool_name: str) -> bool:
        """检查单个工具是否可用"""
        try:
            cmd = [tool_name, '--help'] if not self.panda3d_bin_path else [
                os.path.join(self.panda3d_bin_path, tool_name), '--help'
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def convert_single_model(self, input_path: str, output_path: str, 
                           options: Optional[Dict] = None) -> bool:
        """
        转换单个3D模型文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出.egg文件路径
            options: 转换选项
            
        Returns:
            bool: 转换是否成功
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return False
            
        if input_path.suffix.lower() not in self.SUPPORTED_INPUT_FORMATS:
            logger.error(f"Unsupported input format: {input_path.suffix}")
            return False
            
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据输入格式选择转换工具
        converter_func = self._get_converter_function(input_path.suffix.lower())
        
        if not converter_func:
            logger.error(f"No converter available for format: {input_path.suffix}")
            return False
            
        try:
            success = converter_func(str(input_path), str(output_path), options or {})
            if success:
                logger.info(f"Successfully converted: {input_path} -> {output_path}")
                # 验证输出文件
                if self._validate_egg_file(str(output_path)):
                    return True
                else:
                    logger.warning(f"Generated .egg file failed validation: {output_path}")
                    return False
            else:
                logger.error(f"Conversion failed: {input_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error converting {input_path}: {e}")
            return False
    
    def _get_converter_function(self, file_extension: str):
        """根据文件扩展名获取对应的转换函数"""
        converter_map = {
            '.obj': self._convert_obj_to_egg,
            '.fbx': self._convert_fbx_to_egg,
            '.gltf': self._convert_gltf_to_egg,
            '.glb': self._convert_gltf_to_egg,
            '.dae': self._convert_dae_to_egg,
            '.3ds': self._convert_3ds_to_egg,
            '.blend': self._convert_blend_to_egg,
            '.ply': self._convert_ply_to_egg
        }
        return converter_map.get(file_extension)
    
    def _convert_obj_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """使用obj2egg转换OBJ文件"""
        cmd = ['obj2egg']
        if self.panda3d_bin_path:
            cmd[0] = os.path.join(self.panda3d_bin_path, 'obj2egg')
            
        # 添加常用选项
        cmd.extend([
            '-o', output_path,
            '-cs', 'y-up',  # 坐标系统
            '-f'  # 强制覆盖
        ])
        
        # 添加自定义选项
        if options.get('no_normals'):
            cmd.append('-N')
        if options.get('no_texture'):
            cmd.append('-T')
            
        cmd.append(input_path)
        
        return self._run_conversion_command(cmd)
    
    def _convert_fbx_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """使用fbx2egg转换FBX文件"""
        cmd = ['fbx2egg']
        if self.panda3d_bin_path:
            cmd[0] = os.path.join(self.panda3d_bin_path, 'fbx2egg')
            
        cmd.extend([
            '-o', output_path,
            '-a', 'model,chan',  # 包含模型和动画
            '-p', 'feet',  # 使用feet作为单位
            '-f'  # 强制覆盖
        ])
        
        # 包含动画
        if not options.get('no_animation'):
            cmd.extend(['-a', 'model,chan'])
            
        cmd.append(input_path)
        
        return self._run_conversion_command(cmd)
    
    def _convert_gltf_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """使用gltf2egg转换GLTF/GLB文件"""
        cmd = ['gltf2egg']
        if self.panda3d_bin_path:
            cmd[0] = os.path.join(self.panda3d_bin_path, 'gltf2egg')
            
        cmd.extend([
            '-o', output_path,
            '-cs', 'y-up',
            '-f'
        ])
        
        cmd.append(input_path)
        
        return self._run_conversion_command(cmd)
    
    def _convert_dae_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """使用dae2egg转换Collada文件"""
        cmd = ['dae2egg']
        if self.panda3d_bin_path:
            cmd[0] = os.path.join(self.panda3d_bin_path, 'dae2egg')
            
        cmd.extend([
            '-o', output_path,
            '-cs', 'y-up',
            '-f'
        ])
        
        cmd.append(input_path)
        
        return self._run_conversion_command(cmd)
    
    def _convert_3ds_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """使用x2egg转换3DS文件（通过中间格式）"""
        # 3DS通常需要先转换为其他格式
        logger.warning("3DS format requires intermediate conversion")
        return False
    
    def _convert_blend_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """转换Blender文件（需要Blender）"""
        logger.warning("Blender format requires Blender installation")
        return False
    
    def _convert_ply_to_egg(self, input_path: str, output_path: str, options: Dict) -> bool:
        """转换PLY文件"""
        # PLY可以通过obj2egg转换，需要先转换为OBJ
        temp_obj = input_path.replace('.ply', '_temp.obj')
        
        try:
            # 这里需要实现PLY到OBJ的转换
            # 临时使用obj2egg处理
            return self._convert_obj_to_egg(input_path, output_path, options)
        except Exception as e:
            logger.error(f"PLY conversion error: {e}")
            return False
    
    def _run_conversion_command(self, cmd: List[str]) -> bool:
        """执行转换命令"""
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=os.path.dirname(cmd[-1])  # 在输入文件目录中运行
            )
            
            if result.returncode == 0:
                logger.debug(f"Conversion successful")
                if result.stdout:
                    logger.debug(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"Conversion failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False
    
    def _validate_egg_file(self, egg_path: str) -> bool:
        """验证生成的.egg文件是否有效"""
        try:
            with open(egg_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # 读取前1KB
                
            # 检查基本的egg文件标识
            if '<CoordinateSystem>' in content or '<Group>' in content:
                file_size = os.path.getsize(egg_path)
                if file_size > 100:  # 至少100字节
                    logger.debug(f"Egg file validation passed: {egg_path} ({file_size} bytes)")
                    return True
                else:
                    logger.warning(f"Egg file too small: {file_size} bytes")
                    return False
            else:
                logger.warning("Egg file missing required headers")
                return False
                
        except Exception as e:
            logger.error(f"Error validating egg file {egg_path}: {e}")
            return False
    
    def batch_convert(self, input_dir: str, output_dir: str, 
                     pattern: str = "*", options: Optional[Dict] = None) -> Dict[str, bool]:
        """
        批量转换目录中的模型文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            pattern: 文件匹配模式
            options: 转换选项
            
        Returns:
            Dict[str, bool]: 文件路径到转换结果的映射
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return {}
            
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # 遍历所有支持的格式
        for ext in self.SUPPORTED_INPUT_FORMATS:
            pattern_with_ext = pattern + ext if not pattern.endswith(ext) else pattern
            
            for input_file in input_path.rglob(pattern_with_ext):
                if input_file.is_file():
                    # 构造输出路径
                    relative_path = input_file.relative_to(input_path)
                    output_file = output_path / relative_path.with_suffix('.egg')
                    
                    logger.info(f"Converting: {input_file}")
                    success = self.convert_single_model(
                        str(input_file), 
                        str(output_file), 
                        options
                    )
                    results[str(input_file)] = success
        
        # 打印转换总结
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Batch conversion completed: {successful}/{total} successful")
        
        return results
    
    def create_animation_egg(self, model_egg: str, animation_data: List[Dict]) -> bool:
        """
        为静态模型创建动画.egg文件
        
        Args:
            model_egg: 基础模型.egg文件路径
            animation_data: 动画数据列表
            
        Returns:
            bool: 是否成功创建动画文件
        """
        try:
            # 读取基础模型
            with open(model_egg, 'r', encoding='utf-8') as f:
                model_content = f.read()
            
            # 为每个动画创建简单的循环动画
            for anim_info in animation_data:
                anim_name = anim_info['name']
                anim_duration = anim_info.get('duration', 1.0)
                
                # 创建动画文件
                anim_path = model_egg.replace('.egg', f'_{anim_name}.egg')
                
                # 生成简单的动画内容
                anim_content = self._generate_simple_animation(
                    model_content, anim_name, anim_duration
                )
                
                with open(anim_path, 'w', encoding='utf-8') as f:
                    f.write(anim_content)
                
                logger.info(f"Created animation file: {anim_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating animation files: {e}")
            return False
    
    def _generate_simple_animation(self, model_content: str, anim_name: str, duration: float) -> str:
        """生成简单的动画内容"""
        # 这是一个简化的动画生成器
        # 实际实现可能需要更复杂的逻辑
        
        animation_table = f"""
<Table> "model_morph" {{
  <Bundle> "bundle" {{
    <Table> "<skeleton>" {{
      <Table> "<root>" {{
        <Scalar> fps {{ 24 }}
        <Char*> order {{ "xyzrhp" }}
        <V> contents {{
          // Basic pose keyframes for {anim_name}
          <S$> xfm {{
            <Scalar> 0 {{ 0 0 0 0 0 0 1 1 1 }}
            <Scalar> {duration} {{ 0 0 0 0 0 0 1 1 1 }}
          }}
        }}
      }}
    }}
  }}
}}
"""
        
        # 将动画表格插入到模型内容中
        if '<Group>' in model_content:
            insert_pos = model_content.find('<Group>')
            return model_content[:insert_pos] + animation_table + model_content[insert_pos:]
        else:
            return animation_table + model_content


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='3D Model Format Converter for Panda3D')
    parser.add_argument('--input', '-i', required=True, help='Input model file or directory')
    parser.add_argument('--output', '-o', required=True, help='Output .egg file or directory')
    parser.add_argument('--batch', action='store_true', help='Batch conversion mode')
    parser.add_argument('--pattern', default='*', help='File pattern for batch mode')
    parser.add_argument('--panda3d-bin', help='Path to Panda3D bin directory')
    parser.add_argument('--no-animation', action='store_true', help='Skip animation conversion')
    parser.add_argument('--no-texture', action='store_true', help='Skip texture processing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建转换器
    converter = ModelConverter(args.panda3d_bin)
    
    # 准备转换选项
    options = {
        'no_animation': args.no_animation,
        'no_texture': args.no_texture
    }
    
    if args.batch:
        # 批量转换
        results = converter.batch_convert(args.input, args.output, args.pattern, options)
        
        # 显示结果统计
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"\nConversion completed: {successful}/{total} files converted successfully")
        
        if successful < total:
            print("\nFailed conversions:")
            for file_path, success in results.items():
                if not success:
                    print(f"  - {file_path}")
        
        sys.exit(0 if successful == total else 1)
    else:
        # 单文件转换
        success = converter.convert_single_model(args.input, args.output, options)
        if success:
            print(f"Successfully converted: {args.input} -> {args.output}")
            sys.exit(0)
        else:
            print(f"Failed to convert: {args.input}")
            sys.exit(1)


if __name__ == '__main__':
    main()