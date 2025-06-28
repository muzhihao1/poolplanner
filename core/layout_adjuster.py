"""
布局调整器 - 在保持台球桌数量的前提下，调整位置使布局更平衡
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
import copy

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class LayoutAdjuster:
    """布局调整器 - 优化已有布局的位置分布"""
    
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
    
    def adjust_layout(self, tables: List[BilliardTable], boundary: List[Tuple[float, float]], 
                     obstacles: List[Rectangle]) -> List[BilliardTable]:
        """
        调整布局，使其更平衡
        
        策略：
        1. 计算当前布局的边距
        2. 如果边距差异过大，尝试整体平移
        3. 确保所有约束仍然满足
        """
        if not tables:
            return tables
            
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
        
        # 计算当前布局的边界
        layout_bounds = self._calculate_layout_bounds(tables)
        
        # 计算到墙壁的距离
        left_margin = layout_bounds['min_x'] - min_x
        right_margin = max_x - layout_bounds['max_x']
        top_margin = layout_bounds['min_y'] - min_y
        bottom_margin = max_y - layout_bounds['max_y']
        
        print(f"\n当前边距:")
        print(f"  左: {left_margin:.0f}mm, 右: {right_margin:.0f}mm")
        print(f"  上: {top_margin:.0f}mm, 下: {bottom_margin:.0f}mm")
        
        # 计算理想的平移量，使边距更均衡
        ideal_x_shift = (right_margin - left_margin) / 2
        ideal_y_shift = (bottom_margin - top_margin) / 2
        
        print(f"\n理想平移量:")
        print(f"  X方向: {ideal_x_shift:.0f}mm")
        print(f"  Y方向: {ideal_y_shift:.0f}mm")
        
        # 逐步尝试平移，确保满足约束
        best_layout = copy.deepcopy(tables)
        best_score = self._calculate_balance_score(tables, boundary)
        
        # 尝试不同的平移比例
        for ratio in [1.0, 0.8, 0.6, 0.4, 0.2]:
            x_shift = ideal_x_shift * ratio
            y_shift = ideal_y_shift * ratio
            
            # 创建平移后的布局
            adjusted_tables = []
            for table in tables:
                new_table = BilliardTable(
                    table.x + x_shift,
                    table.y + y_shift,
                    table.width,
                    table.height,
                    table.rotation
                )
                adjusted_tables.append(new_table)
            
            # 验证约束
            valid, violations = self.constraint_solver.validate_layout(adjusted_tables, context)
            
            if valid:
                score = self._calculate_balance_score(adjusted_tables, boundary)
                if score < best_score:
                    best_layout = adjusted_tables
                    best_score = score
                    print(f"  找到更好的布局 (平移比例: {ratio:.0%})")
        
        # 进一步微调：修正间距违规
        final_layout = self._fix_spacing_violations(best_layout, context)
        
        return final_layout
    
    def _calculate_layout_bounds(self, tables):
        """计算布局的边界"""
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for table in tables:
            bounds = table.get_bounds()
            min_x = min(min_x, bounds.x)
            max_x = max(max_x, bounds.x + bounds.width)
            min_y = min(min_y, bounds.y)
            max_y = max(max_y, bounds.y + bounds.height)
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y
        }
    
    def _calculate_balance_score(self, tables, boundary):
        """计算布局平衡度得分（越小越好）"""
        bounds = self._calculate_layout_bounds(tables)
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        left_margin = bounds['min_x'] - min_x
        right_margin = max_x - bounds['max_x']
        top_margin = bounds['min_y'] - min_y
        bottom_margin = max_y - bounds['max_y']
        
        # 边距差异的平方和
        x_imbalance = (left_margin - right_margin) ** 2
        y_imbalance = (top_margin - bottom_margin) ** 2
        
        return x_imbalance + y_imbalance
    
    def _fix_spacing_violations(self, tables, context):
        """修正间距违规问题"""
        adjusted_tables = copy.deepcopy(tables)
        
        # 多次迭代修正，直到所有间距都满足要求
        max_iterations = 10
        for iteration in range(max_iterations):
            violations_fixed = False
            
            # 检查并修正台球桌间距
            for i in range(len(adjusted_tables)):
                for j in range(i + 1, len(adjusted_tables)):
                    table1 = adjusted_tables[i]
                    table2 = adjusted_tables[j]
                    
                    # 计算实际距离
                    bounds1 = table1.get_bounds()
                    bounds2 = table2.get_bounds()
                    
                    # 计算矩形之间的最短距离
                    if bounds1.x + bounds1.width < bounds2.x:
                        # table1 在 table2 左边
                        dx = bounds2.x - (bounds1.x + bounds1.width)
                    elif bounds2.x + bounds2.width < bounds1.x:
                        # table2 在 table1 左边
                        dx = bounds1.x - (bounds2.x + bounds2.width)
                    else:
                        # 水平方向重叠
                        dx = 0
                    
                    if bounds1.y + bounds1.height < bounds2.y:
                        # table1 在 table2 上边
                        dy = bounds2.y - (bounds1.y + bounds1.height)
                    elif bounds2.y + bounds2.height < bounds1.y:
                        # table2 在 table1 上边
                        dy = bounds1.y - (bounds2.y + bounds2.height)
                    else:
                        # 垂直方向重叠
                        dy = 0
                    
                    # 如果只有一个方向有距离，就使用那个距离（垂直或水平）
                    if dx > 0 and dy == 0:
                        distance = dx
                    elif dy > 0 and dx == 0:
                        distance = dy
                    elif dx > 0 and dy > 0:
                        # 两个方向都有距离，使用较小的那个（因为我们要的是最短距离）
                        distance = min(dx, dy)
                    else:
                        distance = 0
                    
                    # 如果距离小于要求，稍微调整位置
                    if distance < self.table_distance - 10 and distance > 0:  # 留10mm容差
                        # 计算需要的调整量
                        shortage = self.table_distance - distance
                        
                        print(f"  修正间距: 台球桌{i+1}和{j+1}之间距离{distance:.0f}mm < {self.table_distance}mm")
                        
                        # 确定调整方向
                        if dx > 0 and (dy == 0 or dx <= dy):  # 主要是水平方向
                            adjust_x = shortage + 20  # 额外增加20mm确保满足要求
                            if bounds1.x < bounds2.x:
                                # table1在左，稍微左移table1，右移table2
                                adjusted_tables[i].x -= adjust_x / 2
                                adjusted_tables[j].x += adjust_x / 2
                            else:
                                # table2在左，稍微左移table2，右移table1
                                adjusted_tables[j].x -= adjust_x / 2
                                adjusted_tables[i].x += adjust_x / 2
                            violations_fixed = True
                        elif dy > 0:  # 主要是垂直方向
                            adjust_y = shortage + 20  # 额外增加20mm确保满足要求
                            if bounds1.y < bounds2.y:
                                # table1在上，稍微上移table1，下移table2
                                adjusted_tables[i].y -= adjust_y / 2
                                adjusted_tables[j].y += adjust_y / 2
                            else:
                                # table2在上，稍微上移table2，下移table1
                                adjusted_tables[j].y -= adjust_y / 2
                                adjusted_tables[i].y += adjust_y / 2
                            violations_fixed = True
            
            # 如果没有违规需要修正，退出循环
            if not violations_fixed:
                break
            else:
                print(f"  迭代{iteration+1}: 继续修正间距违规...")
        
        # 验证最终布局
        valid, violations = self.constraint_solver.validate_layout(adjusted_tables, context)
        
        if valid:
            print("\n间距修正成功")
            return adjusted_tables
        else:
            print("\n间距修正后仍有违规，返回原布局")
            return tables