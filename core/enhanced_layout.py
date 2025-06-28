"""
增强布局算法 - 专注于最大化数量和合理性
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import copy

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


@dataclass
class LayoutScore:
    """布局评分"""
    table_count: int
    regularity: float  # 规则性评分 (0-1)
    compactness: float  # 紧凑性评分 (0-1)
    total_score: float  # 总评分


class EnhancedLayoutGenerator:
    """增强布局生成器 - 最大化数量 + 合理布局"""
    
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
        生成增强布局
        
        策略：
        1. 智能网格布局（优先）
        2. 空隙填充优化
        3. 布局质量评估和调整
        """
        print("\n=== 增强布局算法 ===")
        
        # 创建验证上下文
        boundary_polygon = Polygon(boundary)
        context = {
            'boundary': boundary,
            'boundary_polygon': boundary_polygon,
            'obstacles': obstacles
        }
        
        best_layout = []
        best_score = LayoutScore(0, 0, 0, 0)
        
        # 策略1: 智能网格布局
        print("策略1: 智能网格布局")
        grid_layouts = self._generate_smart_grid_layouts(boundary, obstacles, context)
        
        for layout in grid_layouts:
            score = self._evaluate_layout(layout, boundary)
            print(f"  网格布局: {score.table_count}个桌子, 评分: {score.total_score:.2f}")
            if score.total_score > best_score.total_score:
                best_layout = layout
                best_score = score
        
        # 策略2: 在最佳网格基础上进行空隙填充
        print("\n策略2: 空隙填充优化")
        filled_layout = self._intelligent_gap_filling(best_layout.copy(), boundary, obstacles, context)
        filled_score = self._evaluate_layout(filled_layout, boundary)
        print(f"  填充后: {filled_score.table_count}个桌子, 评分: {filled_score.total_score:.2f}")
        
        if filled_score.total_score > best_score.total_score:
            best_layout = filled_layout
            best_score = filled_score
        
        # 策略3: 布局微调优化
        print("\n策略3: 布局微调")
        adjusted_layout = self._fine_tune_layout(best_layout.copy(), boundary, obstacles, context)
        adjusted_score = self._evaluate_layout(adjusted_layout, boundary)
        print(f"  微调后: {adjusted_score.table_count}个桌子, 评分: {adjusted_score.total_score:.2f}")
        
        if adjusted_score.total_score > best_score.total_score:
            best_layout = adjusted_layout
            best_score = adjusted_score
        
        print(f"\n最终结果: {best_score.table_count}个台球桌")
        print(f"布局质量: 规则性{best_score.regularity:.2f}, 紧凑性{best_score.compactness:.2f}")
        
        return best_layout
    
    def _generate_smart_grid_layouts(self, boundary, obstacles, context):
        """生成多种智能网格布局"""
        layouts = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 方案1: 纯横向网格
        layout1 = self._create_grid_layout(boundary, obstacles, context, rotation=0)
        if layout1:
            layouts.append(layout1)
        
        # 方案2: 纯纵向网格
        layout2 = self._create_grid_layout(boundary, obstacles, context, rotation=90)
        if layout2:
            layouts.append(layout2)
        
        # 方案3: 混合网格（上下分区）
        layout3 = self._create_mixed_grid_layout(boundary, obstacles, context)
        if layout3:
            layouts.append(layout3)
        
        # 方案4: 障碍物适应性网格
        layout4 = self._create_obstacle_adaptive_grid(boundary, obstacles, context)
        if layout4:
            layouts.append(layout4)
        
        return layouts
    
    def _create_grid_layout(self, boundary, obstacles, context, rotation=0):
        """创建规则网格布局"""
        layout = []
        
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
        
        start_x = min_x + self.wall_distance
        start_y = min_y + self.wall_distance
        
        # 计算可能的行列数
        max_cols = int((max_x - min_x - 2 * self.wall_distance + self.table_distance) / cell_w)
        max_rows = int((max_y - min_y - 2 * self.wall_distance + self.table_distance) / cell_h)
        
        # 居中对齐
        total_width = max_cols * cell_w - self.table_distance
        total_height = max_rows * cell_h - self.table_distance
        
        offset_x = (max_x - min_x - 2 * self.wall_distance - total_width) / 2
        offset_y = (max_y - min_y - 2 * self.wall_distance - total_height) / 2
        
        start_x += offset_x
        start_y += offset_y
        
        # 放置台球桌
        for row in range(max_rows):
            for col in range(max_cols):
                x = start_x + col * cell_w
                y = start_y + row * cell_h
                
                # 检查边界
                if x + table_w > max_x - self.wall_distance:
                    continue
                if y + table_h > max_y - self.wall_distance:
                    continue
                
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                
                # 检查约束
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(table)
        
        return layout
    
    def _create_mixed_grid_layout(self, boundary, obstacles, context):
        """创建混合网格布局（上下分区）"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        mid_y = (min_y + max_y) / 2
        
        # 上半部分用横向
        upper_boundary = [[min_x, min_y], [max_x, min_y], [max_x, mid_y], [min_x, mid_y]]
        upper_obstacles = [obs for obs in obstacles if obs.y + obs.height/2 < mid_y]
        upper_context = {
            'boundary': upper_boundary,
            'boundary_polygon': Polygon(upper_boundary),
            'obstacles': upper_obstacles
        }
        upper_layout = self._create_grid_layout(upper_boundary, upper_obstacles, upper_context, 0)
        
        # 下半部分用纵向
        lower_boundary = [[min_x, mid_y], [max_x, mid_y], [max_x, max_y], [min_x, max_y]]
        lower_obstacles = [obs for obs in obstacles if obs.y + obs.height/2 >= mid_y]
        lower_context = {
            'boundary': lower_boundary,
            'boundary_polygon': Polygon(lower_boundary),
            'obstacles': lower_obstacles
        }
        lower_layout = self._create_grid_layout(lower_boundary, lower_obstacles, lower_context, 90)
        
        # 合并布局
        combined_layout = (upper_layout or []) + (lower_layout or [])
        
        # 验证整体布局
        if combined_layout:
            valid, _ = self.constraint_solver.validate_layout(combined_layout, context)
            if valid:
                return combined_layout
        
        return []
    
    def _create_obstacle_adaptive_grid(self, boundary, obstacles, context):
        """创建障碍物适应性网格"""
        if not obstacles:
            return self._create_grid_layout(boundary, obstacles, context, 0)
        
        layout = []
        
        # 根据障碍物位置分割空间
        regions = self._split_space_by_obstacles(boundary, obstacles)
        
        for region in regions:
            # 在每个区域内创建最优网格
            region_layout = self._optimize_region_layout(region, obstacles, context)
            layout.extend(region_layout)
        
        return layout
    
    def _split_space_by_obstacles(self, boundary, obstacles):
        """根据障碍物分割空间"""
        # 简化实现：创建矩形区域
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        regions = []
        
        # 基本策略：为每个主要区域创建一个矩形
        if obstacles:
            # 上方区域
            top_y = min(obs.y for obs in obstacles) - self.wall_distance
            if top_y > min_y + self.wall_distance + self.table_height:
                regions.append([[min_x, min_y], [max_x, min_y], [max_x, top_y], [min_x, top_y]])
            
            # 下方区域
            bottom_y = max(obs.y + obs.height for obs in obstacles) + self.wall_distance
            if bottom_y < max_y - self.wall_distance - self.table_height:
                regions.append([[min_x, bottom_y], [max_x, bottom_y], [max_x, max_y], [min_x, max_y]])
            
            # 左右区域可以类似处理
        
        if not regions:
            regions = [boundary]
        
        return regions
    
    def _optimize_region_layout(self, region, obstacles, context):
        """优化区域内的布局"""
        # 在区域内尝试最佳方向
        region_context = {
            'boundary': region,
            'boundary_polygon': Polygon(region),
            'obstacles': obstacles
        }
        
        layout_h = self._create_grid_layout(region, obstacles, region_context, 0)
        layout_v = self._create_grid_layout(region, obstacles, region_context, 90)
        
        if len(layout_h) >= len(layout_v):
            return layout_h
        else:
            return layout_v
    
    def _intelligent_gap_filling(self, layout, boundary, obstacles, context):
        """智能空隙填充"""
        if not layout:
            return layout
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 使用更细的扫描步长
        scan_step = 100
        added_count = 0
        
        # 优先尝试与现有台球桌对齐的位置
        existing_x = sorted(set(t.x for t in layout))
        existing_y = sorted(set(t.y for t in layout))
        
        # 扩展对齐位置
        aligned_positions = []
        
        # X方向对齐
        for x in existing_x:
            for rotation in [0, 90]:
                width = self.table_height if rotation == 90 else self.table_width
                # 向左扩展
                new_x = x - width - self.table_distance
                if new_x >= min_x + self.wall_distance:
                    aligned_positions.extend([(new_x, y, rotation) for y in existing_y])
                # 向右扩展
                new_x = x + (self.table_width if rotation == 0 else self.table_height) + self.table_distance
                if new_x + width <= max_x - self.wall_distance:
                    aligned_positions.extend([(new_x, y, rotation) for y in existing_y])
        
        # Y方向对齐
        for y in existing_y:
            for rotation in [0, 90]:
                height = self.table_width if rotation == 90 else self.table_height
                # 向上扩展
                new_y = y - height - self.table_distance
                if new_y >= min_y + self.wall_distance:
                    aligned_positions.extend([(x, new_y, rotation) for x in existing_x])
                # 向下扩展
                new_y = y + (self.table_height if rotation == 0 else self.table_width) + self.table_distance
                if new_y + height <= max_y - self.wall_distance:
                    aligned_positions.extend([(x, new_y, rotation) for x in existing_x])
        
        # 尝试对齐位置
        for x, y, rotation in aligned_positions:
            table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
            temp_layout = layout + [table]
            valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
            
            if valid:
                layout.append(table)
                added_count += 1
        
        print(f"  对齐填充: 新增 {added_count} 个台球桌")
        
        # 如果对齐填充效果不好，进行自由填充
        if added_count < 2:
            free_added = 0
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
                            free_added += 1
                            break
            
            print(f"  自由填充: 新增 {free_added} 个台球桌")
        
        return layout
    
    def _fine_tune_layout(self, layout, boundary, obstacles, context):
        """布局微调"""
        if not layout:
            return layout
        
        # 尝试微调位置以提高整齐度
        improved = True
        iterations = 0
        max_iterations = 5
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i, table in enumerate(layout):
                # 尝试微调位置（±50mm）
                for dx in [-50, 0, 50]:
                    for dy in [-50, 0, 50]:
                        if dx == 0 and dy == 0:
                            continue
                        
                        original_pos = (table.x, table.y)
                        table.x += dx
                        table.y += dy
                        
                        # 检查约束
                        valid, _ = self.constraint_solver.validate_layout(layout, context)
                        
                        if valid:
                            # 检查是否提高了整齐度
                            new_score = self._evaluate_layout(layout, boundary)
                            table.x, table.y = original_pos
                            old_score = self._evaluate_layout(layout, boundary)
                            
                            if new_score.regularity > old_score.regularity:
                                table.x += dx
                                table.y += dy
                                improved = True
                                break
                            else:
                                table.x, table.y = original_pos
                        else:
                            table.x, table.y = original_pos
                    
                    if improved:
                        break
        
        return layout
    
    def _evaluate_layout(self, layout, boundary):
        """评估布局质量"""
        if not layout:
            return LayoutScore(0, 0, 0, 0)
        
        table_count = len(layout)
        
        # 计算规则性评分
        regularity = self._calculate_regularity(layout)
        
        # 计算紧凑性评分
        compactness = self._calculate_compactness(layout, boundary)
        
        # 总评分：数量权重70%，质量权重30%
        total_score = table_count * 0.7 + (regularity + compactness) * 0.15 * table_count
        
        return LayoutScore(table_count, regularity, compactness, total_score)
    
    def _calculate_regularity(self, layout):
        """计算布局规则性"""
        if len(layout) < 2:
            return 1.0
        
        # 检查X和Y位置的对齐程度
        x_positions = [t.x for t in layout]
        y_positions = [t.y for t in layout]
        
        # 计算位置的聚类程度
        x_clusters = self._count_position_clusters(x_positions, tolerance=100)
        y_clusters = self._count_position_clusters(y_positions, tolerance=100)
        
        # 理想情况下，X和Y位置应该形成较少的聚类
        x_regularity = min(1.0, len(x_clusters) / len(layout))
        y_regularity = min(1.0, len(y_clusters) / len(layout))
        
        return (x_regularity + y_regularity) / 2
    
    def _count_position_clusters(self, positions, tolerance=100):
        """计算位置聚类数量"""
        if not positions:
            return []
        
        clusters = []
        sorted_pos = sorted(positions)
        
        current_cluster = [sorted_pos[0]]
        
        for pos in sorted_pos[1:]:
            if pos - current_cluster[-1] <= tolerance:
                current_cluster.append(pos)
            else:
                clusters.append(current_cluster)
                current_cluster = [pos]
        
        clusters.append(current_cluster)
        return clusters
    
    def _calculate_compactness(self, layout, boundary):
        """计算布局紧凑性"""
        if len(layout) < 2:
            return 1.0
        
        # 计算布局的边界框
        min_x = min(t.x for t in layout)
        max_x = max(t.x + (t.height if t.rotation == 90 else t.width) for t in layout)
        min_y = min(t.y for t in layout)
        max_y = max(t.y + (t.width if t.rotation == 90 else t.height) for t in layout)
        
        layout_area = (max_x - min_x) * (max_y - min_y)
        
        # 计算台球桌总面积
        table_area = len(layout) * self.table_width * self.table_height
        
        # 紧凑性 = 台球桌面积 / 布局边界框面积
        if layout_area > 0:
            compactness = min(1.0, table_area / layout_area)
        else:
            compactness = 1.0
        
        return compactness