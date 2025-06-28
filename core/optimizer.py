"""
三阶段布局优化算法
结合贪心算法、局部搜索和全局优化
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
import random
from copy import deepcopy
import time

from .maxrects import Rectangle, BilliardTable, MaxRectsAlgorithm
from .constraints import ConstraintSolver, DistanceConstraint, AccessibilityConstraint
from .regular_layout import RegularLayoutGenerator, LayoutMode


class LayoutOptimizer:
    """布局优化器"""
    
    def __init__(self, config: Dict):
        """
        初始化优化器
        
        Args:
            config: 配置参数
                - wall_distance: 与墙壁的最小距离
                - table_distance: 台球桌之间的最小距离
                - table_width: 台球桌宽度
                - table_height: 台球桌高度
                - grid_size: 网格大小（用于搜索）
        """
        self.config = config
        self.wall_distance = config.get('wall_distance', 1500)
        self.table_distance = config.get('table_distance', 1400)
        self.table_width = config.get('table_width', 2850)
        self.table_height = config.get('table_height', 1550)
        self.grid_size = config.get('grid_size', 100)  # 100mm网格
        
        # 约束求解器
        self.constraint_solver = ConstraintSolver()
        self.constraint_solver.add_constraint(
            DistanceConstraint(self.wall_distance, self.table_distance, self.wall_distance)
        )
        self.constraint_solver.add_constraint(AccessibilityConstraint())
    
    def optimize(self, boundary: List[Tuple[float, float]], obstacles: List[Rectangle], 
                 use_regular_layout: bool = True) -> Dict:
        """
        执行三阶段优化
        
        Args:
            boundary: 场地边界点列表
            obstacles: 障碍物列表
            use_regular_layout: 是否使用规则布局算法
        
        Returns:
            优化结果字典
        """
        start_time = time.time()
        
        # 如果使用规则布局算法
        if use_regular_layout:
            # 检查是否需要最大化布局
            optimize_count = self.config.get('optimize_count', False)
            
            if optimize_count:
                print("使用优化布局算法（最大化数量）...")
                from .optimized_layout import OptimizedLayoutGenerator
                optimized_generator = OptimizedLayoutGenerator(self.config)
                final_layout = optimized_generator.generate_layout(boundary, obstacles)
                
                # 应用布局调整器进行后处理
                print("\n应用布局调整器优化边距...")
                from .layout_adjuster import LayoutAdjuster
                adjuster = LayoutAdjuster(self.config)
                final_layout = adjuster.adjust_layout(final_layout, boundary, obstacles)
            else:
                print("使用规则布局算法...")
                regular_generator = RegularLayoutGenerator(self.config)
                # 获取布局模式
                layout_mode_str = self.config.get('layout_mode', 'auto').upper()
                layout_mode = LayoutMode[layout_mode_str] if layout_mode_str in ['HORIZONTAL', 'VERTICAL', 'MIXED', 'AUTO'] else LayoutMode.AUTO
                final_layout = regular_generator.generate_layout(boundary, obstacles, layout_mode)
        else:
            # 第一阶段：贪心放置
            print("第一阶段：贪心放置...")
            initial_layout = self._greedy_placement(boundary, obstacles)
            
            # 第二阶段：局部搜索优化
            print(f"第二阶段：局部搜索优化（初始{len(initial_layout)}个台球桌）...")
            optimized_layout = self._local_search(initial_layout, boundary, obstacles)
            
            # 第2.5阶段：空间填充优化
            print(f"\n第2.5阶段：空间填充优化...")
            optimized_layout = self._fill_gaps(optimized_layout, boundary, obstacles)
            
            # 第三阶段：全局调整
            print(f"第三阶段：全局调整（当前{len(optimized_layout)}个台球桌）...")
            final_layout = self._global_adjustment(optimized_layout, boundary, obstacles)
        
        end_time = time.time()
        
        # 计算统计信息
        stats = self._calculate_stats(final_layout, boundary)
        
        return {
            'tables': final_layout,
            'count': len(final_layout),
            'optimization_time': end_time - start_time,
            'stats': stats,
            'success': True
        }
    
    def _greedy_placement(self, boundary: List[Tuple[float, float]], obstacles: List[Rectangle]) -> List[BilliardTable]:
        """
        第一阶段：贪心放置
        使用MaxRects算法进行初始放置
        """
        print(f"\n=== 第一阶段：贪心放置 ===")
        print(f"墙壁安全距离: {self.wall_distance}mm")
        print(f"台球桌间距离: {self.table_distance}mm")
        print(f"台球桌尺寸: {self.table_width}x{self.table_height}mm")
        
        # 使用MaxRects算法
        maxrects = MaxRectsAlgorithm(boundary, obstacles)
        maxrects.wall_distance = self.wall_distance
        maxrects.table_distance = self.table_distance
        maxrects.table_width = self.table_width
        maxrects.table_height = self.table_height
        
        # 执行优化
        layout = maxrects.optimize_layout()
        print(f"MaxRects算法放置了 {len(layout)} 个台球桌")
        
        # 创建几何处理器以获取boundary_polygon
        from .geometry import GeometryProcessor
        geometry = GeometryProcessor()
        geometry.process_boundary(boundary)
        
        # 验证约束
        context = {
            'boundary': boundary,
            'boundary_polygon': geometry.boundary_polygon,
            'obstacles': obstacles
        }
        valid, violations = self.constraint_solver.validate_layout(layout, context)
        
        if not valid:
            print(f"贪心放置后发现{len(violations)}个约束违反:")
            for v in violations:
                print(f"  - {v.description}")
            layout = self._fix_violations(layout, violations, context)
            print(f"修正后剩余 {len(layout)} 个台球桌")
        else:
            print("所有约束都满足！")
        
        return layout
    
    def _local_search(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]], 
                     obstacles: List[Rectangle]) -> List[BilliardTable]:
        """
        第二阶段：局部搜索优化
        尝试微调每个台球桌的位置和旋转，并压缩布局以腾出空间
        """
        print(f"\n=== 局部搜索优化 ===")
        initial_count = len(layout)
        
        # 创建几何处理器
        from .geometry import GeometryProcessor
        geometry = GeometryProcessor()
        geometry.process_boundary(boundary)
        
        context = {
            'boundary': boundary,
            'boundary_polygon': geometry.boundary_polygon,
            'obstacles': obstacles
        }
        
        improved = True
        max_iterations = 15  # 增加迭代次数
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            print(f"局部搜索迭代 {iteration}")
            
            # 随机打乱顺序以避免局部最优
            indices = list(range(len(layout)))
            random.shuffle(indices)
            
            improvements = 0
            for i in indices:
                table = layout[i]
                best_position = (table.x, table.y, table.rotation)
                best_score = self._calculate_layout_score(layout)
                
                # 尝试更大范围的移动（使用不同步长）
                step_sizes = [50, 100, 200]
                for step in step_sizes:
                    for dx in [-step, 0, step]:
                        for dy in [-step, 0, step]:
                            for rotation in [0, 90]:
                                if dx == 0 and dy == 0 and rotation == table.rotation:
                                    continue
                                
                                # 创建临时台球桌
                                temp_table = BilliardTable(
                                    table.x + dx,
                                    table.y + dy,
                                    self.table_width,
                                    self.table_height,
                                    rotation
                                )
                                
                                # 检查是否满足约束
                                temp_layout = layout[:i] + [temp_table] + layout[i+1:]
                                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                                
                                if valid:
                                    # 计算新布局的得分
                                    score = self._calculate_layout_score(temp_layout)
                                    if score > best_score:
                                        best_position = (temp_table.x, temp_table.y, temp_table.rotation)
                                        best_score = score
                                        improved = True
                
                # 更新到最佳位置
                if best_position != (table.x, table.y, table.rotation):
                    table.x, table.y, table.rotation = best_position
                    improvements += 1
            
            print(f"  改进了 {improvements} 个台球桌位置")
            
            # 每隔几轮尝试压缩布局
            if iteration % 3 == 0:
                print("  尝试压缩布局...")
                layout = self._compress_layout(layout, boundary, obstacles, context)
        
        print(f"局部搜索完成: {initial_count} -> {len(layout)} 个台球桌")
        return layout
    
    def _global_adjustment(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]], 
                          obstacles: List[Rectangle]) -> List[BilliardTable]:
        """
        第三阶段：全局调整
        重新排列部分台球桌以获得更好的整体布局
        """
        context = {
            'boundary': boundary,
            'obstacles': obstacles
        }
        
        best_layout = deepcopy(layout)
        best_count = len(layout)
        
        # 尝试移除一些台球桌并重新放置
        num_attempts = 5
        remove_ratio = 0.2  # 移除20%的台球桌
        
        for attempt in range(num_attempts):
            temp_layout = deepcopy(layout)
            
            # 随机移除一部分台球桌
            num_remove = int(len(temp_layout) * remove_ratio)
            if num_remove > 0:
                indices = random.sample(range(len(temp_layout)), num_remove)
                indices.sort(reverse=True)
                removed_tables = []
                
                for i in indices:
                    removed_tables.append(temp_layout.pop(i))
                
                # 尝试重新放置被移除的台球桌和新的台球桌
                temp_layout = self._refill_layout(temp_layout, boundary, obstacles)
                
                # 如果得到更好的结果，更新最佳布局
                if len(temp_layout) > best_count:
                    best_layout = temp_layout
                    best_count = len(temp_layout)
                    print(f"全局调整改进：{len(layout)} -> {best_count}")
        
        return best_layout
    
    def _fill_gaps(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]], 
                   obstacles: List[Rectangle]) -> List[BilliardTable]:
        """尝试在现有布局的空隙中添加新的台球桌 - 使用更细粒度的搜索"""
        print(f"\n=== 空间填充优化 ===")
        initial_count = len(layout)
        
        # 创建几何处理器
        from .geometry import GeometryProcessor
        geometry = GeometryProcessor()
        geometry.process_boundary(boundary)
        
        context = {
            'boundary': boundary,
            'boundary_polygon': geometry.boundary_polygon,
            'obstacles': obstacles
        }
        
        # 获取边界范围
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 使用更细的网格（50mm）进行多轮搜索
        grid_sizes = [50, 100, 200]  # 逐步增大网格尺寸
        
        for grid in grid_sizes:
            print(f"尝试网格大小: {grid}mm")
            added_in_round = 0
            
            # 生成所有可能的位置
            positions = []
            for x in np.arange(min_x + self.wall_distance, 
                              max_x - self.wall_distance - self.table_width, 
                              grid):
                for y in np.arange(min_y + self.wall_distance, 
                                  max_y - self.wall_distance - self.table_height, 
                                  grid):
                    for rotation in [0, 90]:
                        width = self.table_height if rotation == 90 else self.table_width
                        height = self.table_width if rotation == 90 else self.table_height
                        
                        if x + width <= max_x - self.wall_distance and y + height <= max_y - self.wall_distance:
                            positions.append((x, y, rotation))
            
            # 随机打乱顺序以避免系统性偏差
            random.shuffle(positions)
            
            # 尝试每个位置
            for x, y, rotation in positions:
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                
                # 快速边界检查
                bounds = table.get_bounds()
                if (bounds.x < min_x + self.wall_distance or
                    bounds.y < min_y + self.wall_distance or
                    bounds.x + bounds.width > max_x - self.wall_distance or
                    bounds.y + bounds.height > max_y - self.wall_distance):
                    continue
                
                # 检查是否可以放置
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(table)
                    added_in_round += 1
                    print(f"  添加台球桌 #{len(layout)} at ({x:.0f}, {y:.0f}, {rotation}°)")
            
            print(f"  本轮添加: {added_in_round} 个台球桌")
            
            # 如果这一轮没有添加任何台球桌，尝试下一个网格大小
            if added_in_round == 0 and grid == grid_sizes[-1]:
                print("无法添加更多台球桌")
                break
        
        print(f"空间填充完成: {initial_count} -> {len(layout)} 个台球桌")
        return layout
    
    def _refill_layout(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]], 
                       obstacles: List[Rectangle]) -> List[BilliardTable]:
        """重新填充布局"""
        # 使用改进的MaxRects算法重新填充
        # 这里简化处理，实际应该考虑已有的台球桌作为障碍物
        return self._fill_gaps(layout, boundary, obstacles)
    
    def _fix_violations(self, layout: List[BilliardTable], violations: List, context: Dict) -> List[BilliardTable]:
        """修复约束违反"""
        # 简单策略：移除有冲突的台球桌
        tables_to_remove = set()
        
        for violation in violations:
            for obj in violation.objects:
                if isinstance(obj, BilliardTable):
                    tables_to_remove.add(id(obj))
        
        return [table for table in layout if id(table) not in tables_to_remove]
    
    def _is_better_position(self, new_table: BilliardTable, old_table: BilliardTable, 
                           layout: List[BilliardTable]) -> bool:
        """判断新位置是否更好"""
        # 简单策略：更靠近左下角的位置更好（更紧凑）
        new_score = new_table.x + new_table.y
        old_score = old_table.x + old_table.y
        return new_score < old_score
    
    def _calculate_layout_score(self, layout: List[BilliardTable]) -> float:
        """计算布局得分 - 更高的分数表示更好的布局"""
        if not layout:
            return 0
        
        score = 0
        
        # 1. 台球桌数量（主要因素）
        score += len(layout) * 10000
        
        # 2. 紧凑度（台球桌之间的平均距离）
        total_distance = 0
        count = 0
        for i in range(len(layout)):
            for j in range(i + 1, len(layout)):
                bounds1 = layout[i].get_bounds()
                bounds2 = layout[j].get_bounds()
                total_distance += bounds1.distance_to(bounds2)
                count += 1
        
        if count > 0:
            avg_distance = total_distance / count
            # 距离越小越好（但不能小于最小要求）
            if avg_distance >= self.table_distance:
                score += (5000 - avg_distance) / 100
        
        # 3. 空间利用效率（使用的总面积）
        min_x = min(t.x for t in layout)
        max_x = max(t.x + (t.height if t.rotation == 90 else t.width) for t in layout)
        min_y = min(t.y for t in layout)
        max_y = max(t.y + (t.width if t.rotation == 90 else t.height) for t in layout)
        
        used_area = (max_x - min_x) * (max_y - min_y)
        score -= used_area / 1000000  # 面积越小越好
        
        return score
    
    def _compress_layout(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]], 
                        obstacles: List[Rectangle], context: Dict) -> List[BilliardTable]:
        """压缩布局 - 将台球桌向中心移动以腾出边缘空间"""
        if not layout:
            return layout
        
        # 计算布局中心
        center_x = sum(t.x + (t.height if t.rotation == 90 else t.width) / 2 for t in layout) / len(layout)
        center_y = sum(t.y + (t.width if t.rotation == 90 else t.height) / 2 for t in layout) / len(layout)
        
        compressed = False
        for table in layout:
            # 计算向中心移动的方向
            table_center_x = table.x + (table.height if table.rotation == 90 else table.width) / 2
            table_center_y = table.y + (table.width if table.rotation == 90 else table.height) / 2
            
            dx = center_x - table_center_x
            dy = center_y - table_center_y
            
            # 标准化方向
            distance = np.sqrt(dx**2 + dy**2)
            if distance > 0:
                dx = dx / distance * 50  # 每次移动50mm
                dy = dy / distance * 50
                
                # 尝试移动
                original_pos = (table.x, table.y)
                table.x += dx
                table.y += dy
                
                # 检查约束
                valid, _ = self.constraint_solver.validate_layout(layout, context)
                if not valid:
                    # 恢复原位置
                    table.x, table.y = original_pos
                else:
                    compressed = True
        
        if compressed:
            print("    成功压缩布局")
        
        return layout
    
    def _calculate_stats(self, layout: List[BilliardTable], boundary: List[Tuple[float, float]]) -> Dict:
        """计算统计信息"""
        if not layout:
            return {
                'space_utilization': 0,
                'total_area': 0,
                'used_area': 0,
                'average_distance': 0
            }
        
        # 计算场地总面积（简化为矩形）
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        total_area = (max_x - min_x) * (max_y - min_y)
        
        # 计算台球桌占用面积
        table_area = self.table_width * self.table_height
        used_area = len(layout) * table_area
        
        # 计算空间利用率
        space_utilization = (used_area / total_area) * 100 if total_area > 0 else 0
        
        # 计算平均间距
        distances = []
        for i, table1 in enumerate(layout):
            bounds1 = table1.get_bounds()
            for j, table2 in enumerate(layout[i+1:], i+1):
                bounds2 = table2.get_bounds()
                distances.append(bounds1.distance_to(bounds2))
        
        average_distance = np.mean(distances) if distances else 0
        
        return {
            'space_utilization': round(space_utilization, 2),
            'total_area': round(total_area / 1000000, 2),  # 转换为平方米
            'used_area': round(used_area / 1000000, 2),    # 转换为平方米
            'average_distance': round(average_distance, 0),
            'table_count': len(layout)
        }