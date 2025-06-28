"""
规则布局算法
生成整齐排列的台球桌布局
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class LayoutMode(Enum):
    """布局模式"""
    HORIZONTAL = "horizontal"  # 所有台球桌横向
    VERTICAL = "vertical"      # 所有台球桌纵向
    MIXED = "mixed"           # 混合布局
    AUTO = "auto"             # 自动选择最优


@dataclass
class GridPosition:
    """网格位置"""
    row: int
    col: int
    x: float
    y: float
    rotation: int  # 0 或 90


class RegularLayoutGenerator:
    """规则布局生成器"""
    
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
                       obstacles: List[Rectangle], 
                       mode: LayoutMode = LayoutMode.AUTO) -> List[BilliardTable]:
        """
        生成规则布局
        
        Args:
            boundary: 场地边界
            obstacles: 障碍物列表
            mode: 布局模式
            
        Returns:
            台球桌列表
        """
        # 获取有效区域
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 计算可用空间
        usable_width = max_x - min_x - 2 * self.wall_distance
        usable_height = max_y - min_y - 2 * self.wall_distance
        
        if usable_width <= 0 or usable_height <= 0:
            print("场地太小，无法放置台球桌")
            return []
        
        # 根据模式选择布局
        if mode == LayoutMode.AUTO:
            mode = self._choose_best_mode(usable_width, usable_height)
            
        print(f"使用布局模式: {mode.value}")
        
        if mode == LayoutMode.HORIZONTAL:
            return self._generate_horizontal_layout(boundary, obstacles)
        elif mode == LayoutMode.VERTICAL:
            return self._generate_vertical_layout(boundary, obstacles)
        elif mode == LayoutMode.MIXED:
            return self._generate_mixed_layout(boundary, obstacles)
        else:
            return self._generate_auto_layout(boundary, obstacles)
    
    def _choose_best_mode(self, width: float, height: float) -> LayoutMode:
        """选择最佳布局模式"""
        # 对于有障碍物的情况，直接使用AUTO模式测试两种布局
        return LayoutMode.AUTO
    
    def _estimate_count(self, width: float, height: float, rotation: int) -> int:
        """估算能放置的台球桌数量"""
        if rotation == 0:
            table_w = self.table_width
            table_h = self.table_height
        else:
            table_w = self.table_height
            table_h = self.table_width
            
        # 计算行列数
        cols = int((width + self.table_distance) / (table_w + self.table_distance))
        rows = int((height + self.table_distance) / (table_h + self.table_distance))
        
        return cols * rows
    
    def _generate_horizontal_layout(self, boundary: List[Tuple[float, float]], 
                                   obstacles: List[Rectangle]) -> List[BilliardTable]:
        """生成横向布局（所有台球桌横向排列）"""
        return self._generate_regular_grid(boundary, obstacles, rotation=0)
    
    def _generate_vertical_layout(self, boundary: List[Tuple[float, float]], 
                                 obstacles: List[Rectangle]) -> List[BilliardTable]:
        """生成纵向布局（所有台球桌纵向排列）"""
        return self._generate_regular_grid(boundary, obstacles, rotation=90)
    
    def _generate_regular_grid(self, boundary: List[Tuple[float, float]], 
                              obstacles: List[Rectangle], 
                              rotation: int) -> List[BilliardTable]:
        """生成规则网格布局"""
        layout = []
        
        # 获取边界
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 起始位置
        start_x = min_x + self.wall_distance
        start_y = min_y + self.wall_distance
        
        # 台球桌实际占用尺寸
        if rotation == 0:
            table_w = self.table_width
            table_h = self.table_height
        else:
            table_w = self.table_height
            table_h = self.table_width
        
        # 包含间距的占用尺寸
        cell_w = table_w + self.table_distance
        cell_h = table_h + self.table_distance
        
        print(f"网格布局参数:")
        print(f"  场地范围: ({min_x}, {min_y}) - ({max_x}, {max_y})")
        print(f"  可用空间: ({start_x}, {start_y}) - ({max_x - self.wall_distance}, {max_y - self.wall_distance})")
        print(f"  台球桌尺寸: {table_w} x {table_h}")
        print(f"  单元格尺寸: {cell_w} x {cell_h}")
        
        # 计算可能的列数
        available_width = max_x - min_x - 2 * self.wall_distance
        max_cols = int((available_width + self.table_distance) / cell_w)
        print(f"  可用宽度: {available_width}, 最大列数: {max_cols}")
        
        # 创建上下文用于验证
        boundary_polygon = Polygon(boundary)
        context = {
            'boundary': boundary,
            'boundary_polygon': boundary_polygon,
            'obstacles': obstacles
        }
        
        # 按行列放置
        y = start_y
        row = 0
        while y + table_h <= max_y - self.wall_distance:
            x = start_x
            col = 0
            
            while x + table_w <= max_x - self.wall_distance:
                # 创建台球桌
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                
                # 检查是否与障碍物冲突
                valid = True
                table_bounds = table.get_bounds()
                
                # 检查障碍物
                for i, obstacle in enumerate(obstacles):
                    dist = table_bounds.distance_to(obstacle)
                    if dist < self.wall_distance:
                        valid = False
                        break
                
                # 如果没有障碍物冲突，检查完整约束
                if valid:
                    temp_layout = layout + [table]
                    valid, violations = self.constraint_solver.validate_layout(temp_layout, context)
                    if not valid and violations:
                        if isinstance(violations, list) and violations:
                            print(f"    约束验证失败: {violations[0].description}")
                        elif hasattr(violations, 'description'):
                            print(f"    约束验证失败: {violations.description}")
                
                if valid:
                    layout.append(table)
                    print(f"放置台球桌 #{len(layout)} at ({x:.0f}, {y:.0f}) [行{row+1},列{col+1}]")
                else:
                    print(f"  跳过位置 ({x:.0f}, {y:.0f}) [行{row+1},列{col+1}] - 验证失败")
                
                x += cell_w
                col += 1
            
            y += cell_h
            row += 1
        
        print(f"规则网格布局完成：放置了 {len(layout)} 个台球桌")
        return layout
    
    def _generate_mixed_layout(self, boundary: List[Tuple[float, float]], 
                              obstacles: List[Rectangle]) -> List[BilliardTable]:
        """生成混合布局（根据空间自动选择横向或纵向）"""
        # 简单实现：分区域使用不同方向
        # 可以根据障碍物位置智能分区
        layout = []
        
        # 获取边界
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 如果有障碍物在中间，可以分区处理
        if obstacles:
            # 简化：上半部分横向，下半部分纵向
            mid_y = (min_y + max_y) / 2
            
            # 上半部分
            upper_boundary = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, mid_y),
                (min_x, mid_y)
            ]
            upper_obstacles = [obs for obs in obstacles if obs.y + obs.height/2 < mid_y]
            layout.extend(self._generate_regular_grid(upper_boundary, upper_obstacles, 0))
            
            # 下半部分
            lower_boundary = [
                (min_x, mid_y),
                (max_x, mid_y),
                (max_x, max_y),
                (min_x, max_y)
            ]
            lower_obstacles = [obs for obs in obstacles if obs.y + obs.height/2 >= mid_y]
            layout.extend(self._generate_regular_grid(lower_boundary, lower_obstacles, 90))
        else:
            # 没有障碍物，使用自动选择的最佳模式
            return self._generate_auto_layout(boundary, obstacles)
        
        return layout
    
    def _generate_auto_layout(self, boundary: List[Tuple[float, float]], 
                             obstacles: List[Rectangle]) -> List[BilliardTable]:
        """自动选择最优布局"""
        # 尝试两种方向，选择能放置更多台球桌的
        print("\n尝试横向布局...")
        horizontal_layout = self._generate_regular_grid(boundary, obstacles, 0)
        print(f"横向布局结果: {len(horizontal_layout)} 个台球桌")
        
        print("\n尝试纵向布局...")
        vertical_layout = self._generate_regular_grid(boundary, obstacles, 90)
        print(f"纵向布局结果: {len(vertical_layout)} 个台球桌")
        
        if len(horizontal_layout) >= len(vertical_layout):
            print(f"\n最终选择横向布局：{len(horizontal_layout)} 个台球桌")
            return horizontal_layout
        else:
            print(f"\n最终选择纵向布局：{len(vertical_layout)} 个台球桌")
            return vertical_layout