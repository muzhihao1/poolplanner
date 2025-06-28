"""
优化布局算法 - 最大化台球桌数量
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class OptimizedLayoutGenerator:
    """优化布局生成器 - 通过灵活放置最大化台球桌数量"""
    
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
        生成优化布局，最大化台球桌数量
        
        策略：
        1. 先尝试规则网格布局
        2. 然后在空隙中尝试放置额外的台球桌
        3. 尝试不同的方向组合
        """
        # 计算场地面积
        area = self._calculate_area(boundary)
        
        # 如果面积超过500平米，使用大场地算法
        if area > 500 * 1000000:  # 500平米 = 500,000,000平方毫米
            print(f"\n检测到大场地 ({area/1000000:.0f}平米)，使用大场地优化算法...")
            from .large_field_layout import LargeFieldLayoutGenerator
            large_gen = LargeFieldLayoutGenerator(self.config)
            return large_gen.generate_layout(boundary, obstacles)
        
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
        
        best_layout = []
        
        # 策略1: 纯横向布局
        print("尝试横向布局...")
        layout1 = self._try_single_orientation_layout(
            boundary, obstacles, context, rotation=0
        )
        print(f"横向布局结果: {len(layout1)}个台球桌")
        if len(layout1) > len(best_layout):
            best_layout = layout1
        
        # 策略2: 纯纵向布局
        print("\n尝试纵向布局...")
        layout2 = self._try_single_orientation_layout(
            boundary, obstacles, context, rotation=90
        )
        print(f"纵向布局结果: {len(layout2)}个台球桌")
        if len(layout2) > len(best_layout):
            best_layout = layout2
        
        # 策略3: 混合布局 - 在已有布局基础上填充
        print("\n尝试混合填充布局...")
        layout3 = self._try_mixed_fill_layout(boundary, obstacles, context)
        print(f"混合布局结果: {len(layout3)}个台球桌")
        if len(layout3) > len(best_layout):
            best_layout = layout3
        
        # 策略4: 贪心算法 - 尝试所有可能的位置
        print("\n尝试贪心算法...")
        layout4 = self._try_greedy_layout(boundary, obstacles, context)
        print(f"贪心算法结果: {len(layout4)}个台球桌")
        if len(layout4) > len(best_layout):
            best_layout = layout4
        
        # 策略5: 多遍优化 - 在最佳布局基础上继续填充
        print("\n尝试多遍优化...")
        layout5 = self._multi_pass_optimization(best_layout.copy(), boundary, obstacles, context)
        print(f"多遍优化结果: {len(layout5)}个台球桌")
        if len(layout5) > len(best_layout):
            best_layout = layout5
        
        # 策略6: 顺序布局 - 模拟人工摆放
        print("\n尝试顺序布局...")
        from .sequential_layout import SequentialLayoutGenerator
        seq_generator = SequentialLayoutGenerator(self.config)
        layout6 = seq_generator.generate_layout(boundary, obstacles)
        print(f"顺序布局结果: {len(layout6)}个台球桌")
        if len(layout6) > len(best_layout):
            best_layout = layout6
        
        # 策略7: 穷举搜索 - 更彻底的搜索
        print("\n尝试穷举搜索...")
        from .exhaustive_layout import ExhaustiveLayoutGenerator
        exh_generator = ExhaustiveLayoutGenerator(self.config)
        layout7 = exh_generator.generate_layout(boundary, obstacles)
        print(f"穷举搜索结果: {len(layout7)}个台球桌")
        if len(layout7) > len(best_layout):
            best_layout = layout7
        
        # 对最终结果按位置排序，确保编号顺序合理（从上到下，从左到右）
        if best_layout:
            best_layout.sort(key=lambda t: (t.y, t.x))
            print("\n调整后的台球桌顺序:")
            for i, table in enumerate(best_layout):
                orientation = "纵向" if table.rotation == 90 else "横向"
                print(f"  台球桌#{i+1}: ({table.x:.0f}, {table.y:.0f}) - {orientation}")
        
        # 如果有障碍物，使用专门的障碍物感知算法
        if obstacles:
            print("\n检测到障碍物，使用障碍物感知布局...")
            from .obstacle_aware_layout import ObstacleAwareLayoutGenerator
            obstacle_gen = ObstacleAwareLayoutGenerator(self.config)
            layout_obstacle = obstacle_gen.generate_layout(boundary, obstacles)
            print(f"障碍物感知布局结果: {len(layout_obstacle)}个台球桌")
            if len(layout_obstacle) > len(best_layout):
                best_layout = layout_obstacle
        
        print(f"\n优化布局完成: {len(best_layout)}个台球桌")
        return best_layout
    
    def _try_single_orientation_layout(self, boundary, obstacles, context, rotation):
        """尝试单一方向的布局"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 确定台球桌尺寸
        if rotation == 0:
            table_w = self.table_width
            table_h = self.table_height
        else:
            table_w = self.table_height
            table_h = self.table_width
        
        # 网格步长
        step_x = table_w + self.table_distance
        step_y = table_h + self.table_distance
        
        # 从左上角开始放置
        y = min_y + self.wall_distance
        while y + table_h <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            while x + table_w <= max_x - self.wall_distance:
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                
                # 验证约束
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(table)
                
                x += step_x
            y += step_y
        
        return layout
    
    def _try_mixed_fill_layout(self, boundary, obstacles, context):
        """混合填充布局 - 先放横向，再在空隙填充纵向"""
        # 先获取横向布局
        layout = self._try_single_orientation_layout(boundary, obstacles, context, 0)
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 尝试在空隙中放置纵向台球桌
        # 扫描所有可能的位置
        scan_step = 100  # 更细的扫描步长用于填充空隙
        
        y = min_y + self.wall_distance
        while y + self.table_width <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            while x + self.table_height <= max_x - self.wall_distance:
                # 尝试放置纵向台球桌
                table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                
                temp_layout = layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(table)
                    # 跳过这个台球桌占用的区域
                    x += self.table_height + self.table_distance
                else:
                    x += scan_step
            y += scan_step
        
        return layout
    
    def _try_greedy_layout(self, boundary, obstacles, context):
        """贪心算法 - 扫描所有位置，优先放置不会阻挡其他位置的台球桌"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 候选位置列表
        candidates = []
        
        # 生成所有可能的候选位置（横向和纵向）
        scan_step = 50  # 使用更细的扫描步长以找到更多位置
        
        # 横向候选
        y = min_y + self.wall_distance
        while y + self.table_height <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            while x + self.table_width <= max_x - self.wall_distance:
                table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                valid, violations = self.constraint_solver.validate_layout([table], context)
                if valid:
                    candidates.append(table)
                x += scan_step
            y += scan_step
        
        # 纵向候选
        y = min_y + self.wall_distance
        while y + self.table_width <= max_y - self.wall_distance:
            x = min_x + self.wall_distance
            while x + self.table_height <= max_x - self.wall_distance:
                table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                valid, violations = self.constraint_solver.validate_layout([table], context)
                if valid:
                    candidates.append(table)
                x += scan_step
            y += scan_step
        
        print(f"找到{len(candidates)}个候选位置")
        
        # 优化贪心选择：使用更快的算法
        # 改进的排序策略：优先从左上角开始，按行列顺序
        def position_score(table):
            # 按照从左到右，从上到下的顺序
            # 这样更符合实际摆放习惯
            return table.y * 10000 + table.x
        
        candidates.sort(key=position_score)
        
        # 简化的贪心选择
        while candidates:
            # 选择第一个有效的候选
            placed = False
            for i, candidate in enumerate(candidates):
                temp_layout = layout + [candidate]
                valid, violations = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    layout.append(candidate)
                    placed = True
                    print(f"  放置台球桌#{len(layout)} at ({candidate.x:.0f}, {candidate.y:.0f}), 方向:{candidate.rotation}°")
                    
                    # 移除不再有效的候选
                    new_candidates = []
                    for j, other in enumerate(candidates):
                        if i != j:
                            temp_layout2 = layout + [other]
                            valid2, _ = self.constraint_solver.validate_layout(temp_layout2, context)
                            if valid2:
                                new_candidates.append(other)
                    candidates = new_candidates
                    break
            
            if not placed:
                break
        
        return layout
    
    def _multi_pass_optimization(self, initial_layout, boundary, obstacles, context):
        """多遍优化 - 在现有布局基础上寻找空隙并填充"""
        layout = initial_layout.copy()
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 首先识别空隙区域
        print("  识别空隙区域...")
        gaps = self._find_gaps(layout, boundary, obstacles)
        print(f"  找到{len(gaps)}个潜在空隙")
        
        # 进行多次扫描，每次使用不同的策略
        for pass_num in range(3):
            print(f"  第{pass_num + 1}遍扫描...")
            added_count = 0
            
            # 使用更细的步长扫描
            scan_step = 25 if pass_num == 2 else 50
            
            # 尝试横向放置
            y = min_y + self.wall_distance
            while y + self.table_height <= max_y - self.wall_distance:
                x = min_x + self.wall_distance
                while x + self.table_width <= max_x - self.wall_distance:
                    table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        added_count += 1
                        # 跳过已占用的区域
                        x += self.table_width + self.table_distance
                    else:
                        x += scan_step
                y += scan_step
            
            # 尝试纵向放置
            y = min_y + self.wall_distance
            while y + self.table_width <= max_y - self.wall_distance:
                x = min_x + self.wall_distance
                while x + self.table_height <= max_x - self.wall_distance:
                    table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        added_count += 1
                        # 跳过已占用的区域
                        x += self.table_height + self.table_distance
                    else:
                        x += scan_step
                y += scan_step
            
            print(f"    第{pass_num + 1}遍新增: {added_count}个台球桌")
            
            # 如果这一遍没有新增，提前结束
            if added_count == 0:
                break
        
        return layout
    
    def _find_gaps(self, layout, boundary, obstacles):
        """识别布局中的空隙"""
        gaps = []
        
        if not layout:
            return gaps
        
        # 按y坐标排序现有的台球桌
        sorted_tables = sorted(layout, key=lambda t: t.y)
        
        # 检查每两个台球桌之间的垂直空隙
        for i in range(len(sorted_tables) - 1):
            table1 = sorted_tables[i]
            table2 = sorted_tables[i + 1]
            bounds1 = table1.get_bounds()
            bounds2 = table2.get_bounds()
            
            # 计算垂直间隙
            gap_y = bounds2.y - (bounds1.y + bounds1.height)
            
            # 如果间隙足够大（能放下一张桌子+间距）
            if gap_y >= self.table_height + 2 * self.table_distance:
                gaps.append({
                    'y_start': bounds1.y + bounds1.height + self.table_distance,
                    'y_end': bounds2.y - self.table_distance,
                    'type': 'vertical'
                })
        
        return gaps
    
    def _calculate_area(self, boundary):
        """计算多边形面积（使用鞋带公式）"""
        n = len(boundary)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += boundary[i][0] * boundary[j][1]
            area -= boundary[j][0] * boundary[i][1]
        return abs(area) / 2.0