"""
顺序布局算法 - 模拟实际摆放习惯
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class SequentialLayoutGenerator:
    """顺序布局生成器 - 从角落开始顺着摆放"""
    
    def __init__(self, config: Dict):
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
        生成顺序布局 - 有序的行列摆放
        
        策略：
        1. 从左上角开始
        2. 横向摆放，从左到右
        3. 一行满了，移到下一行
        4. 如果最右侧空间不够横放但够竖放，则竖向摆放
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
        
        layout = []
        
        print("开始顺序布局（有序行列模式）...")
        
        # 计算单元格尺寸
        h_cell_width = self.table_width + self.table_distance  # 横向单元格宽度
        h_cell_height = self.table_height + self.table_distance  # 横向单元格高度
        v_cell_width = self.table_height + self.table_distance  # 纵向单元格宽度
        v_cell_height = self.table_width + self.table_distance  # 纵向单元格高度
        
        # 第一阶段：横向行列布局
        print("\n第一阶段：横向行列布局")
        y = min_y + self.wall_distance
        row = 1
        
        while y + self.table_height <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            col = 1
            row_has_tables = False
            
            # 这一行从左到右摆放
            while x + self.table_width <= max_x - self.wall_distance:
                table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(table)
                    print(f"  放置台球桌#{len(layout)} at ({x:.0f}, {y:.0f}) - 第{row}行第{col}列（横向）")
                    row_has_tables = True
                    x += h_cell_width
                    col += 1
                else:
                    # 如果放不下，稍微移动再试
                    x += 100
                    
            # 如果这一行放了桌子，移到下一行
            if row_has_tables:
                y += h_cell_height
                row += 1
            else:
                # 如果整行都没放桌子，小步移动
                y += 200
                
            # 防止无限循环
            if y > max_y - self.wall_distance - self.table_height:
                break
        
        # 第二阶段：检查右侧是否有空间可以竖向摆放
        print("\n第二阶段：检查右侧空间")
        
        # 找出已摆放桌子的最右边界
        if layout:
            rightmost_x = max(t.x + (t.height if t.rotation == 90 else t.width) for t in layout)
            
            # 检查右侧是否有足够空间
            available_width = max_x - self.wall_distance - rightmost_x - self.table_distance
            
            if available_width >= self.table_height:  # 够放纵向桌子
                x = rightmost_x + self.table_distance
                y = min_y + self.wall_distance
                col = 1
                
                print(f"  右侧有{available_width:.0f}mm空间，尝试纵向摆放")
                
                while y + self.table_width <= max_y - self.wall_distance:
                    table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        print(f"  放置台球桌#{len(layout)} at ({x:.0f}, {y:.0f}) - 右侧第{col}个（纵向）")
                        y += v_cell_height
                        col += 1
                    else:
                        y += 100
        
        # 第二遍：尝试在现有布局的空隙中填充
        print(f"\n第二遍：在空隙中填充...")
        before_count = len(layout)
        
        # 更细的扫描步长
        fine_scan_step = 50
        
        x = min_x + self.wall_distance
        while x + min(self.table_width, self.table_height) <= max_x - self.wall_distance:
            y = min_y + self.wall_distance
            while y + min(self.table_width, self.table_height) <= max_y - self.wall_distance:
                # 尝试两种方向
                for rotation in [90, 0]:  # 优先尝试纵向
                    if rotation == 0:
                        width, height = self.table_width, self.table_height
                    else:
                        width, height = self.table_height, self.table_width
                    
                    # 检查边界
                    if x + width > max_x - self.wall_distance:
                        continue
                    if y + height > max_y - self.wall_distance:
                        continue
                    
                    table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        orientation = "横向" if rotation == 0 else "纵向"
                        print(f"  填充台球桌#{len(layout)} at ({x:.0f}, {y:.0f}) - {orientation}")
                        break
                        
                y += fine_scan_step
            x += fine_scan_step
        
        added_count = len(layout) - before_count
        print(f"第二遍额外放置了{added_count}个台球桌")
        
        print(f"\n顺序布局完成：共{len(layout)}个台球桌")
        return layout
    
    def _calculate_skip_distance(self, x, y, width, height, obstacles, violations):
        """计算需要跳过的距离以避开障碍物"""
        # 找到影响当前位置的障碍物
        table_bounds = Rectangle(x, y, width, height)
        
        min_skip = float('inf')
        for obstacle in obstacles:
            # 检查是否在同一列
            if (obstacle.x < x + width + self.wall_distance and 
                obstacle.x + obstacle.width > x - self.wall_distance):
                # 计算需要的y位置
                if obstacle.y > y:  # 障碍物在下方
                    required_y = obstacle.y + obstacle.height + self.wall_distance
                    skip = required_y - y
                    if skip < min_skip:
                        min_skip = skip
        
        return min_skip if min_skip < float('inf') else 0
    
    def _fill_gaps_with_vertical(self, existing_layout, boundary, obstacles, context):
        """在现有布局的空隙中尝试放置纵向台球桌"""
        additional_tables = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 扫描可能的位置
        scan_step = 200
        
        y = min_y + self.wall_distance
        while y + self.table_width <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            while x + self.table_height <= max_x - self.wall_distance:
                # 尝试纵向放置
                table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                temp_layout = existing_layout + additional_tables + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    additional_tables.append(table)
                    print(f"  填充：纵向台球桌 at ({x:.0f}, {y:.0f})")
                    # 跳过已占用的区域
                    x += self.table_height + self.table_distance
                else:
                    x += scan_step
            y += scan_step
        
        return additional_tables