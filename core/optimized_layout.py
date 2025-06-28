"""
优化布局算法 - 最大化台球桌数量
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from .enhanced_layout import EnhancedLayoutGenerator
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
        1. 优先使用增强布局算法（新）
        2. 如果效果不佳，回退到原有策略
        3. 对比选择最佳结果
        """
        # 计算场地面积
        area = self._calculate_area(boundary)
        
        # 如果面积超过500平米，使用大场地算法
        if area > 500 * 1000000:  # 500平米 = 500,000,000平方毫米
            print(f"\n检测到大场地 ({area/1000000:.0f}平米)，使用大场地优化算法...")
            from .large_field_layout import LargeFieldLayoutGenerator
            large_gen = LargeFieldLayoutGenerator(self.config)
            return large_gen.generate_layout(boundary, obstacles)
        
        print(f"\n场地面积: {area/1000000:.1f}平米")
        
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
        best_count = 0
        
        # 策略1: 使用新的增强布局算法
        print("策略1: 增强布局算法")
        enhanced_gen = EnhancedLayoutGenerator(self.config)
        enhanced_layout = enhanced_gen.generate_layout(boundary, obstacles)
        print(f"增强算法结果: {len(enhanced_layout)}个台球桌")
        
        if len(enhanced_layout) > best_count:
            best_layout = enhanced_layout
            best_count = len(enhanced_layout)
        
        # 策略2: 原有的优化策略（作为备选）
        print("\n策略2: 传统优化算法")
        
        # 纯横向布局
        layout_h = self._try_single_orientation_layout(boundary, obstacles, context, rotation=0)
        print(f"横向布局结果: {len(layout_h)}个台球桌")
        if len(layout_h) > best_count:
            best_layout = layout_h
            best_count = len(layout_h)
        
        # 纯纵向布局
        layout_v = self._try_single_orientation_layout(boundary, obstacles, context, rotation=90)
        print(f"纵向布局结果: {len(layout_v)}个台球桌")
        if len(layout_v) > best_count:
            best_layout = layout_v
            best_count = len(layout_v)
        
        # 混合填充布局
        layout_mixed = self._try_mixed_fill_layout(boundary, obstacles, context)
        print(f"混合布局结果: {len(layout_mixed)}个台球桌")
        if len(layout_mixed) > best_count:
            best_layout = layout_mixed
            best_count = len(layout_mixed)
        
        # 策略3: 如果有障碍物，使用专门的障碍物感知算法
        if obstacles:
            print("\n策略3: 障碍物感知布局")
            from .obstacle_aware_layout import ObstacleAwareLayoutGenerator
            obstacle_gen = ObstacleAwareLayoutGenerator(self.config)
            layout_obstacle = obstacle_gen.generate_layout(boundary, obstacles)
            print(f"障碍物感知布局结果: {len(layout_obstacle)}个台球桌")
            if len(layout_obstacle) > best_count:
                best_layout = layout_obstacle
                best_count = len(layout_obstacle)
        
        # 策略4: 最终优化 - 在最佳布局基础上进行微调
        if best_layout:
            print(f"\n策略4: 最终优化（基于{best_count}个台球桌的布局）")
            final_layout = self._final_optimization(best_layout.copy(), boundary, obstacles, context)
            print(f"最终优化结果: {len(final_layout)}个台球桌")
            if len(final_layout) >= best_count:
                best_layout = final_layout
                best_count = len(final_layout)
        
        # 对最终结果按位置排序，确保编号顺序合理
        if best_layout:
            best_layout.sort(key=lambda t: (t.y, t.x))
            print(f"\n最终布局: {len(best_layout)}个台球桌")
            
            # 显示布局统计
            horizontal_count = sum(1 for t in best_layout if t.rotation == 0)
            vertical_count = sum(1 for t in best_layout if t.rotation == 90)
            print(f"  横向: {horizontal_count}个, 纵向: {vertical_count}个")
            
            # 计算空间利用率
            table_area = len(best_layout) * self.table_width * self.table_height / 1000000  # 平方米
            field_area = area / 1000000  # 平方米
            utilization = (table_area / field_area) * 100
            print(f"  空间利用率: {utilization:.1f}%")
        
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
        scan_step = 50  # 更细的扫描步长
        
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
    
    def _final_optimization(self, layout, boundary, obstacles, context):
        """最终优化 - 在现有布局基础上寻找更多空隙"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 使用非常细的扫描步长进行最后的空隙搜索
        scan_step = 25
        added_count = 0
        
        print("  进行精细空隙搜索...")
        
        # 多轮扫描，每轮使用不同的起始点
        for start_offset in [0, scan_step//2]:
            for y in range(int(min_y + self.wall_distance + start_offset), 
                          int(max_y - self.wall_distance - min(self.table_height, self.table_width)), 
                          scan_step):
                for x in range(int(min_x + self.wall_distance + start_offset), 
                              int(max_x - self.wall_distance - min(self.table_width, self.table_height)), 
                              scan_step):
                    
                    # 尝试两种方向
                    for rotation in [0, 90]:
                        if rotation == 0:
                            width, height = self.table_width, self.table_height
                        else:
                            width, height = self.table_height, self.table_width
                        
                        # 边界检查
                        if x + width > max_x - self.wall_distance:
                            continue
                        if y + height > max_y - self.wall_distance:
                            continue
                        
                        table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                        temp_layout = layout + [table]
                        valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                        
                        if valid:
                            layout.append(table)
                            added_count += 1
                            print(f"    发现空隙: 位置({x}, {y}), 方向{rotation}°")
                            break  # 找到一个就跳出方向循环
        
        print(f"  精细搜索新增: {added_count}个台球桌")
        return layout
    
    def _calculate_area(self, boundary):
        """计算多边形面积（使用鞋带公式）"""
        n = len(boundary)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += boundary[i][0] * boundary[j][1]
            area -= boundary[j][0] * boundary[i][1]
        return abs(area) / 2.0