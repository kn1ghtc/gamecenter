#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple 3D Model Generator for Street Battle Game
Creates basic geometric models as character placeholders when GLTF files are missing or corrupted
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    CardMaker, NodePath, PandaNode, GeomNode, Geom, GeomTriangles,
    GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomPoints,
    Vec3, Vec4, TransformState, RenderState, Material, TextureStage,
    Texture, PNMImage, Filename
)
import logging

logger = logging.getLogger(__name__)

class SimpleModelGenerator:
    """生成简单的3D模型作为角色占位符"""
    
    def __init__(self):
        self.materials = {}
        self.textures = {}
        self._initialize_materials()
    
    def _initialize_materials(self):
        """初始化基础材质"""
        # 创建基础材质
        base_material = Material()
        base_material.setAmbient((0.3, 0.3, 0.3, 1.0))
        base_material.setDiffuse((0.8, 0.8, 0.8, 1.0))
        base_material.setSpecular((0.5, 0.5, 0.5, 1.0))
        base_material.setShininess(32.0)
        self.materials['base'] = base_material
        
        # 创建角色颜色材质
        character_colors = {
            'red': (0.8, 0.2, 0.2, 1.0),
            'blue': (0.2, 0.2, 0.8, 1.0),
            'green': (0.2, 0.8, 0.2, 1.0),
            'yellow': (0.8, 0.8, 0.2, 1.0),
            'purple': (0.8, 0.2, 0.8, 1.0),
            'cyan': (0.2, 0.8, 0.8, 1.0),
            'orange': (0.8, 0.5, 0.2, 1.0),
            'white': (0.9, 0.9, 0.9, 1.0)
        }
        
        for color_name, color_value in character_colors.items():
            material = Material()
            material.setAmbient((color_value[0] * 0.3, color_value[1] * 0.3, color_value[2] * 0.3, 1.0))
            material.setDiffuse(color_value)
            material.setSpecular((0.3, 0.3, 0.3, 1.0))
            material.setShininess(16.0)
            self.materials[color_name] = material
    
    def create_simple_texture(self, color: Tuple[float, float, float] = (1.0, 1.0, 1.0), size: int = 64) -> Texture:
        """创建简单的纯色纹理"""
        texture = Texture()
        image = PNMImage(size, size)
        image.fill(color[0], color[1], color[2])
        texture.load(image)
        texture.setMinfilter(Texture.FTLinear)
        texture.setMagfilter(Texture.FTLinear)
        return texture
    
    def create_box_model(self, size: Vec3 = Vec3(1, 1, 2), color: str = 'blue') -> NodePath:
        """创建简单的盒子模型作为角色"""
        # 创建几何体
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('box', format, Geom.UHStatic)
        vdata.setNumRows(24)  # 6面 * 4顶点
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        
        # 定义盒子的6个面
        faces = [
            # 前面 (Z+)
            [(-size.x/2, -size.y/2, size.z/2), (size.x/2, -size.y/2, size.z/2), 
             (size.x/2, size.y/2, size.z/2), (-size.x/2, size.y/2, size.z/2)],
            # 后面 (Z-)
            [(size.x/2, -size.y/2, -size.z/2), (-size.x/2, -size.y/2, -size.z/2), 
             (-size.x/2, size.y/2, -size.z/2), (size.x/2, size.y/2, -size.z/2)],
            # 右面 (X+)
            [(size.x/2, -size.y/2, size.z/2), (size.x/2, -size.y/2, -size.z/2), 
             (size.x/2, size.y/2, -size.z/2), (size.x/2, size.y/2, size.z/2)],
            # 左面 (X-)
            [(-size.x/2, -size.y/2, -size.z/2), (-size.x/2, -size.y/2, size.z/2), 
             (-size.x/2, size.y/2, size.z/2), (-size.x/2, size.y/2, -size.z/2)],
            # 上面 (Y+)
            [(-size.x/2, size.y/2, size.z/2), (size.x/2, size.y/2, size.z/2), 
             (size.x/2, size.y/2, -size.z/2), (-size.x/2, size.y/2, -size.z/2)],
            # 下面 (Y-)
            [(-size.x/2, -size.y/2, -size.z/2), (size.x/2, -size.y/2, -size.z/2), 
             (size.x/2, -size.y/2, size.z/2), (-size.x/2, -size.y/2, size.z/2)]
        ]
        
        normals = [
            (0, 0, 1),   # 前面
            (0, 0, -1),  # 后面
            (1, 0, 0),   # 右面
            (-1, 0, 0),  # 左面
            (0, 1, 0),   # 上面
            (0, -1, 0)   # 下面
        ]
        
        # 添加顶点和法线
        for i, face in enumerate(faces):
            for vertex_pos in face:
                vertex.addData3f(*vertex_pos)
                normal.addData3f(*normals[i])
        
        # 创建几何体和三角形
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        # 为每个面添加三角形
        for i in range(6):
            base = i * 4
            # 第一个三角形
            tris.addVertices(base, base + 1, base + 2)
            # 第二个三角形
            tris.addVertices(base, base + 2, base + 3)
        
        geom.addPrimitive(tris)
        
        # 创建节点
        geom_node = GeomNode('box_character')
        geom_node.addGeom(geom)
        
        model = NodePath(geom_node)
        
        # 应用材质
        if color in self.materials:
            model.setMaterial(self.materials[color])
        else:
            model.setMaterial(self.materials['base'])
        
        return model
    
    def create_cylinder_model(self, radius: float = 0.5, height: float = 2.0, segments: int = 12, color: str = 'red') -> NodePath:
        """创建圆柱体模型作为角色"""
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('cylinder', format, Geom.UHStatic)
        
        # 计算顶点数：顶部圆心1 + 顶部圆周segments + 底部圆心1 + 底部圆周segments + 侧面顶点(segments*2)
        num_vertices = 2 + segments * 4
        vdata.setNumRows(num_vertices)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        
        import math
        
        # 顶部圆心
        vertex.addData3f(0, 0, height/2)
        normal.addData3f(0, 0, 1)
        
        # 顶部圆周
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3f(x, y, height/2)
            normal.addData3f(0, 0, 1)
        
        # 底部圆心
        vertex.addData3f(0, 0, -height/2)
        normal.addData3f(0, 0, -1)
        
        # 底部圆周
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3f(x, y, -height/2)
            normal.addData3f(0, 0, -1)
        
        # 侧面顶部顶点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3f(x, y, height/2)
            normal.addData3f(math.cos(angle), math.sin(angle), 0)
        
        # 侧面底部顶点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3f(x, y, -height/2)
            normal.addData3f(math.cos(angle), math.sin(angle), 0)
        
        # 创建几何体
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        # 顶部三角形
        for i in range(segments):
            next_i = (i + 1) % segments
            tris.addVertices(0, 1 + i, 1 + next_i)
        
        # 底部三角形
        base_bottom = 1 + segments + 1
        for i in range(segments):
            next_i = (i + 1) % segments
            tris.addVertices(1 + segments, base_bottom + next_i, base_bottom + i)
        
        # 侧面三角形
        base_side_top = 1 + segments + 1 + segments
        base_side_bottom = base_side_top + segments
        
        for i in range(segments):
            next_i = (i + 1) % segments
            # 第一个三角形
            tris.addVertices(base_side_top + i, base_side_bottom + i, base_side_top + next_i)
            # 第二个三角形
            tris.addVertices(base_side_top + next_i, base_side_bottom + i, base_side_bottom + next_i)
        
        geom.addPrimitive(tris)
        
        # 创建节点
        geom_node = GeomNode('cylinder_character')
        geom_node.addGeom(geom)
        
        model = NodePath(geom_node)
        
        # 应用材质
        if color in self.materials:
            model.setMaterial(self.materials[color])
        else:
            model.setMaterial(self.materials['base'])
        
        return model
    
    def generate_character_model(self, character_name: str, model_type: str = 'box') -> Optional[NodePath]:
        """为指定角色生成模型"""
        try:
            # 根据角色名称选择颜色
            color_map = {
                'kyo_kusanagi': 'red',
                'iori_yagami': 'purple',
                'terry_bogard': 'blue',
                'mai_shiranui': 'red',
                'king': 'yellow',
                'ryo_sakazaki': 'orange',
                'athena_asamiya': 'purple',
                'leona_heidern': 'green',
                'clark_still': 'green',
                'ralf_jones': 'green'
            }
            
            color = color_map.get(character_name, 'blue')
            
            if model_type == 'box':
                return self.create_box_model(Vec3(0.8, 0.4, 1.8), color)
            elif model_type == 'cylinder':
                return self.create_cylinder_model(0.4, 1.8, 12, color)
            else:
                logger.warning(f"Unknown model type: {model_type}, using box")
                return self.create_box_model(Vec3(0.8, 0.4, 1.8), color)
                
        except Exception as e:
            logger.error(f"Failed to generate model for {character_name}: {e}")
            return None
    
    def save_as_bam(self, model: NodePath, output_path: str) -> bool:
        """将模型保存为BAM文件"""
        try:
            model.writeBamFile(output_path)
            logger.info(f"Model saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model to {output_path}: {e}")
            return False
    
    def create_all_character_models(self, output_dir: str, characters: List[str]) -> Dict[str, str]:
        """为所有角色创建模型"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        results = {}
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'cyan', 'orange', 'white']
        
        for i, character in enumerate(characters):
            try:
                # 交替使用盒子和圆柱体
                model_type = 'box' if i % 2 == 0 else 'cylinder'
                color = colors[i % len(colors)]
                
                if model_type == 'box':
                    model = self.create_box_model(Vec3(0.8, 0.4, 1.8), color)
                else:
                    model = self.create_cylinder_model(0.4, 1.8, 12, color)
                
                output_path = os.path.join(output_dir, f"{character}.bam")
                if self.save_as_bam(model, output_path):
                    results[character] = output_path
                    logger.info(f"Created model for {character}: {model_type} ({color})")
                else:
                    logger.warning(f"Failed to save model for {character}")
                    
            except Exception as e:
                logger.error(f"Error creating model for {character}: {e}")
        
        return results

def main():
    """测试函数"""
    import sys
    
    # 初始化基础的Panda3D环境（用于模型生成）
    from direct.showbase.ShowBase import ShowBase
    
    class ModelGeneratorApp(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.generator = SimpleModelGenerator()
            
            # 测试创建一些模型
            box_model = self.generator.create_box_model(color='red')
            box_model.reparentTo(self.render)
            box_model.setPos(-2, 10, 0)
            
            cylinder_model = self.generator.create_cylinder_model(color='blue')
            cylinder_model.reparentTo(self.render)
            cylinder_model.setPos(2, 10, 0)
            
            # 设置相机
            self.camera.setPos(0, -15, 5)
            self.camera.lookAt(0, 0, 0)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        app = ModelGeneratorApp()
        app.run()

if __name__ == '__main__':
    main()