"""
智能网格布局算法 - 核心网格生成逻辑
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


@dataclass
class GridCell:
    """网格单元"""
    x: float
    y: float
    width: float
    height: float
    occupied: bool = False
    blocked: bool = False  # 被障碍物阻挡


@dataclass
class GridLayout:
    """网格布局"""
    cells: List[List[GridCell]]
    rows: int
    cols: int
    cell_width: float
    cell_height: float
    start_x: float
    start_y: float


class SmartGridGenerator:
    """智能网格生成器"""
    
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
    
    def generate_optimal_grid(self, boundary: List[Tuple[float, float]], 
                            obstacles: List[Rectangle]) -> List[BilliardTable]:
        """生成最优网格布局"""
        
        # 分析场地特征
        field_analysis = self._analyze_field(boundary, obstacles)
        
        # 生成多种网格方案
        grid_options = self._generate_grid_options(boundary, obstacles, field_analysis)
        
        # 评估并选择最佳方案
        best_layout = self._select_best_grid(grid_options, boundary, obstacles)
        
        return best_layout
    
    def _analyze_field(self, boundary, obstacles):
        """分析场地特征"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        field_width = max_x - min_x
        field_height = max_y - min_y
        field_ratio = field_width / field_height
        
        # 分析障碍物分布
        obstacle_density = len(obstacles) / ((field_width * field_height) / 1000000)  # 每平方米障碍物数
        
        # 计算障碍物影响区域
        blocked_area = 0
        for obs in obstacles:
            # 包含安全距离的影响区域
            influence_width = obs.width + 2 * self.wall_distance
            influence_height = obs.height + 2 * self.wall_distance
            blocked_area += influence_width * influence_height
        
        blocked_ratio = blocked_area / (field_width * field_height)
        
        return {
            'width': field_width,
            'height': field_height,
            'ratio': field_ratio,
            'obstacle_count': len(obstacles),
            'obstacle_density': obstacle_density,
            'blocked_ratio': blocked_ratio,
            'is_wide': field_ratio > 1.5,
            'is_tall': field_ratio < 0.67,
            'is_square': 0.8 <= field_ratio <= 1.2
        }
    
    def _generate_grid_options(self, boundary, obstacles, analysis):
        """生成多种网格布局选项"""
        options = []
        
        # 选项1: 标准横向网格
        if not analysis['is_tall']:
            grid_h = self._create_grid_layout(boundary, obstacles, rotation=0)
            if grid_h:
                options.append(('horizontal', grid_h))
        
        # 选项2: 标准纵向网格
        if not analysis['is_wide']:
            grid_v = self._create_grid_layout(boundary, obstacles, rotation=90)
            if grid_v:
                options.append(('vertical', grid_v))
        
        # 选项3: 自适应混合网格
        if analysis['obstacle_count'] > 0:
            grid_mixed = self._create_adaptive_grid(boundary, obstacles, analysis)
            if grid_mixed:
                options.append(('adaptive', grid_mixed))
        
        # 选项4: 密集填充网格
        grid_dense = self._create_dense_grid(boundary, obstacles)
        if grid_dense:
            options.append(('dense', grid_dense))
        
        return options
    
    def _create_grid_layout(self, boundary, obstacles, rotation=0):
        """创建标准网格布局"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 确定台球桌尺寸
        if rotation == 0:
            table_w, table_h = self.table_width, self.table_height
        else:
            table_w, table_h = self.table_height, self.table_width
        
        # 计算网格参数
        cell_w = table_w + self.table_distance
        cell_h = table_h + self.table_distance
        
        # 可用空间
        available_width = max_x - min_x - 2 * self.wall_distance
        available_height = max_y - min_y - 2 * self.wall_distance
        
        # 计算行列数
        cols = int((available_width + self.table_distance) / cell_w)
        rows = int((available_height + self.table_distance) / cell_h)
        
        if cols <= 0 or rows <= 0:
            return []
        
        # 计算起始位置（居中）
        total_grid_width = cols * cell_w - self.table_distance
        total_grid_height = rows * cell_h - self.table_distance
        
        start_x = min_x + self.wall_distance + (available_width - total_grid_width) / 2
        start_y = min_y + self.wall_distance + (available_height - total_grid_height) / 2
        
        # 创建网格
        grid = GridLayout(
            cells=[[GridCell(
                x=start_x + col * cell_w,
                y=start_y + row * cell_h,
                width=table_w,
                height=table_h
            ) for col in range(cols)] for row in range(rows)],
            rows=rows,
            cols=cols,
            cell_width=cell_w,
            cell_height=cell_h,
            start_x=start_x,
            start_y=start_y
        )
        
        # 标记被障碍物阻挡的单元格
        self._mark_blocked_cells(grid, obstacles)
        
        # 生成台球桌布局
        layout = []
        context = {
            'boundary': boundary,
            'boundary_polygon': Polygon(boundary),
            'obstacles': obstacles
        }
        
        for row in range(rows):
            for col in range(cols):
                cell = grid.cells[row][col]
                if not cell.blocked:
                    table = BilliardTable(cell.x, cell.y, self.table_width, self.table_height, rotation)
                    
                    # 验证约束
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        cell.occupied = True
        
        return layout
    
    def _create_adaptive_grid(self, boundary, obstacles, analysis):
        """创建自适应网格（根据障碍物调整）"""
        # 根据障碍物位置分割空间
        regions = self._split_by_obstacles(boundary, obstacles)
        
        layout = []
        context = {
            'boundary': boundary,
            'boundary_polygon': Polygon(boundary),
            'obstacles': obstacles
        }
        
        for region in regions:
            # 为每个区域选择最佳方向
            region_layout = self._optimize_region(region, obstacles, context)
            layout.extend(region_layout)
        
        return layout
    
    def _create_dense_grid(self, boundary, obstacles):
        """创建密集网格（最大化数量）"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        context = {
            'boundary': boundary,
            'boundary_polygon': Polygon(boundary),
            'obstacles': obstacles
        }
        
        # 使用更小的扫描步长
        scan_step = 50
        
        # 优先尝试规则位置
        for rotation in [0, 90]:
            if rotation == 0:
                table_w, table_h = self.table_width, self.table_height
                step_w = self.table_width + self.table_distance
                step_h = self.table_height + self.table_distance
            else:
                table_w, table_h = self.table_height, self.table_width
                step_w = self.table_height + self.table_distance
                step_h = self.table_width + self.table_distance
            
            # 规则网格位置
            y = min_y + self.wall_distance
            while y + table_h <= max_y - self.wall_distance:
                x = min_x + self.wall_distance
                while x + table_w <= max_x - self.wall_distance:
                    table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        x += step_w
                    else:
                        x += scan_step
                y += step_h
        
        # 填充剩余空隙
        for y in range(int(min_y + self.wall_distance), 
                      int(max_y - self.wall_distance - self.table_height), 
                      scan_step):
            for x in range(int(min_x + self.wall_distance), 
                          int(max_x - self.wall_distance - self.table_width), 
                          scan_step):
                for rotation in [0, 90]:
                    width = self.table_height if rotation == 90 else self.table_width
                    height = self.table_width if rotation == 90 else self.table_height
                    
                    if x + width > max_x - self.wall_distance:
                        continue
                    if y + height > max_y - self.wall_distance:
                        continue
                    
                    table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        break
        
        return layout
    
    def _mark_blocked_cells(self, grid, obstacles):
        """标记被障碍物阻挡的网格单元"""
        for row in range(grid.rows):
            for col in range(grid.cols):
                cell = grid.cells[row][col]
                
                # 检查是否与任何障碍物冲突
                cell_rect = Rectangle(cell.x, cell.y, cell.width, cell.height)
                
                for obstacle in obstacles:
                    # 计算距离（包含安全距离）
                    distance = cell_rect.distance_to(obstacle)
                    if distance < self.wall_distance:
                        cell.blocked = True
                        break
    
    def _split_by_obstacles(self, boundary, obstacles):
        """根据障碍物分割空间"""
        if not obstacles:
            return [boundary]
        
        # 简化实现：创建主要区域
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        regions = []
        
        # 根据障碍物位置创建区域
        obstacle_y_positions = sorted(set(obs.y for obs in obstacles))
        
        if obstacle_y_positions:
            # 上方区域
            top_y = min(obstacle_y_positions) - self.wall_distance
            if top_y > min_y + self.wall_distance + self.table_height:
                regions.append([
                    [min_x, min_y], [max_x, min_y], 
                    [max_x, top_y], [min_x, top_y]
                ])
            
            # 下方区域
            bottom_y = max(obs.y + obs.height for obs in obstacles) + self.wall_distance
            if bottom_y < max_y - self.wall_distance - self.table_height:
                regions.append([
                    [min_x, bottom_y], [max_x, bottom_y], 
                    [max_x, max_y], [min_x, max_y]
                ])
        
        if not regions:
            regions = [boundary]
        
        return regions
    
    def _optimize_region(self, region, obstacles, context):
        """优化单个区域的布局"""
        # 计算区域尺寸
        min_x = min(p[0] for p in region)
        max_x = max(p[0] for p in region)
        min_y = min(p[1] for p in region)
        max_y = max(p[1] for p in region)
        
        region_width = max_x - min_x
        region_height = max_y - min_y
        
        # 选择最佳方向
        h_capacity = self._estimate_capacity(region_width, region_height, 0)
        v_capacity = self._estimate_capacity(region_width, region_height, 90)
        
        rotation = 0 if h_capacity >= v_capacity else 90
        
        # 在区域内创建网格
        region_context = {
            'boundary': region,
            'boundary_polygon': Polygon(region),
            'obstacles': obstacles
        }
        
        return self._create_grid_layout(region, obstacles, rotation)
    
    def _estimate_capacity(self, width, height, rotation):
        """估算容量"""
        if rotation == 0:
            table_w, table_h = self.table_width, self.table_height
        else:
            table_w, table_h = self.table_height, self.table_width
        
        cols = int((width - 2 * self.wall_distance + self.table_distance) / (table_w + self.table_distance))
        rows = int((height - 2 * self.wall_distance + self.table_distance) / (table_h + self.table_distance))
        
        return max(0, cols * rows)
    
    def _select_best_grid(self, options, boundary, obstacles):
        """选择最佳网格方案"""
        if not options:
            return []
        
        best_layout = []
        best_score = 0
        
        for option_name, layout in options:
            # 计算评分：数量 + 质量
            count_score = len(layout) * 10
            quality_score = self._calculate_quality_score(layout, boundary)
            total_score = count_score + quality_score
            
            print(f"  {option_name}: {len(layout)}个桌子, 评分: {total_score:.1f}")
            
            if total_score > best_score:
                best_layout = layout
                best_score = total_score
        
        return best_layout
    
    def _calculate_quality_score(self, layout, boundary):
        """计算布局质量评分"""
        if not layout:
            return 0
        
        # 规则性评分
        x_positions = [t.x for t in layout]
        y_positions = [t.y for t in layout]
        
        x_regularity = self._calculate_position_regularity(x_positions)
        y_regularity = self._calculate_position_regularity(y_positions)
        
        regularity_score = (x_regularity + y_regularity) * 5
        
        # 紧凑性评分
        compactness_score = self._calculate_compactness_score(layout, boundary) * 3
        
        return regularity_score + compactness_score
    
    def _calculate_position_regularity(self, positions):
        """计算位置规则性"""
        if len(positions) < 2:
            return 10
        
        # 计算位置间距的一致性
        sorted_pos = sorted(positions)
        gaps = [sorted_pos[i+1] - sorted_pos[i] for i in range(len(sorted_pos)-1)]
        
        if not gaps:
            return 10
        
        # 计算间距的标准差
        mean_gap = sum(gaps) / len(gaps)
        variance = sum((gap - mean_gap) ** 2 for gap in gaps) / len(gaps)
        std_dev = variance ** 0.5
        
        # 标准差越小，规则性越高
        regularity = max(0, 10 - std_dev / 100)
        return regularity
    
    def _calculate_compactness_score(self, layout, boundary):
        """计算紧凑性评分"""
        if not layout:
            return 0
        
        # 计算布局边界框
        min_x = min(t.x for t in layout)
        max_x = max(t.x + (t.height if t.rotation == 90 else t.width) for t in layout)
        min_y = min(t.y for t in layout)
        max_y = max(t.y + (t.width if t.rotation == 90 else t.height) for t in layout)
        
        layout_area = (max_x - min_x) * (max_y - min_y)
        table_area = len(layout) * self.table_width * self.table_height
        
        if layout_area > 0:
            compactness = min(10, (table_area / layout_area) * 10)
        else:
            compactness = 10
        
        return compactness