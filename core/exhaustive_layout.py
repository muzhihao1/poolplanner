"""
穷举布局算法 - 尝试所有可能的位置组合
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import itertools

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class ExhaustiveLayoutGenerator:
    """穷举布局生成器 - 尝试找到最优解"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.wall_distance = config.get('wall_distance', 1500)
        self.table_distance = config.get('table_distance', 1400)
        self.table_width = config.get('table_width', 2850)
        self.table_height = config.get('table_height', 1550)
        
        # 创建约束求解器
        self.constraint_solver = ConstraintSolver()
        self.constraint_solver.add_constraint(
            DistanceConstraint(self.wall_distance, self.table_distance, self.wall_distance)
        )
    
    def generate_layout(self, boundary: List[Tuple[float, float]], 
                       obstacles: List[Rectangle]) -> List[BilliardTable]:
        """
        生成穷举布局
        """
        # 获取边界
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 创建验证上下文
        boundary_polygon = Polygon(boundary)
        context = {
            'boundary': boundary,
            'boundary_polygon': boundary_polygon,
            'obstacles': obstacles
        }
        
        print("开始穷举搜索...")
        
        # 生成所有可能的位置（使用较粗的网格以减少计算量）
        grid_step = 200  # 200mm步长
        positions = []
        
        x = min_x + self.wall_distance
        while x + min(self.table_width, self.table_height) <= max_x - self.wall_distance:
            y = min_y + self.wall_distance
            while y + min(self.table_width, self.table_height) <= max_y - self.wall_distance:
                # 每个位置尝试两种方向
                for rotation in [0, 90]:
                    if rotation == 0:
                        width, height = self.table_width, self.table_height
                    else:
                        width, height = self.table_height, self.table_width
                    
                    # 检查是否在边界内
                    if x + width <= max_x - self.wall_distance and y + height <= max_y - self.wall_distance:
                        positions.append((x, y, rotation))
                
                y += grid_step
            x += grid_step
        
        print(f"生成了 {len(positions)} 个候选位置")
        
        # 首先过滤出所有单独有效的位置
        valid_positions = []
        for x, y, rotation in positions:
            table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
            valid, _ = self.constraint_solver.validate_layout([table], context)
            if valid:
                valid_positions.append((x, y, rotation))
        
        print(f"有 {len(valid_positions)} 个单独有效的位置")
        
        # 使用贪心算法快速找到一个较好的解
        best_layout = self._greedy_search(valid_positions, context)
        print(f"贪心算法找到 {len(best_layout)} 个台球桌")
        
        # 尝试局部改进
        improved_layout = self._local_improvement(best_layout, valid_positions, context)
        if len(improved_layout) > len(best_layout):
            best_layout = improved_layout
            print(f"局部改进后有 {len(best_layout)} 个台球桌")
        
        return best_layout
    
    def _greedy_search(self, positions, context):
        """贪心搜索"""
        layout = []
        remaining_positions = positions.copy()
        
        while remaining_positions:
            best_pos = None
            best_score = -1
            
            # 找到最佳的下一个位置
            for x, y, rotation in remaining_positions:
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    # 计算得分（优先选择角落和边缘位置）
                    score = self._calculate_position_score(x, y, rotation, context)
                    if score > best_score:
                        best_score = score
                        best_pos = (x, y, rotation)
            
            if best_pos:
                x, y, rotation = best_pos
                layout.append(BilliardTable(x, y, self.table_width, self.table_height, rotation))
                # 移除附近的位置以加速搜索
                remaining_positions = [
                    (px, py, pr) for px, py, pr in remaining_positions
                    if abs(px - x) > self.table_distance or abs(py - y) > self.table_distance
                ]
            else:
                break
        
        return layout
    
    def _calculate_position_score(self, x, y, rotation, context):
        """计算位置得分（优先角落和边缘）"""
        boundary = context['boundary']
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 计算到边界的距离
        dist_to_left = x - min_x
        dist_to_right = max_x - x - (self.table_height if rotation == 90 else self.table_width)
        dist_to_top = y - min_y
        dist_to_bottom = max_y - y - (self.table_width if rotation == 90 else self.table_height)
        
        # 越靠近角落和边缘得分越高
        min_dist = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
        score = 10000 - min_dist
        
        # 角落位置额外加分
        if (dist_to_left < 2000 or dist_to_right < 2000) and (dist_to_top < 2000 or dist_to_bottom < 2000):
            score += 5000
        
        return score
    
    def _local_improvement(self, layout, all_positions, context):
        """局部改进 - 尝试添加更多台球桌"""
        improved_layout = layout.copy()
        
        # 尝试在现有布局的基础上添加更多台球桌
        for x, y, rotation in all_positions:
            table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
            temp_layout = improved_layout + [table]
            valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
            
            if valid:
                improved_layout.append(table)
                print(f"  局部改进：添加台球桌 at ({x:.0f}, {y:.0f})")
        
        return improved_layout