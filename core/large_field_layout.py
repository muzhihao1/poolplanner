"""
大场地布局优化算法 - 专门处理超过500平米的场地
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
import math
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class LargeFieldLayoutGenerator:
    """大场地布局生成器 - 优化处理1000平米级别的场地"""
    
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
        生成大场地优化布局
        
        策略：
        1. 分区域规划 - 将大场地划分为多个区域
        2. 并行处理 - 每个区域独立计算
        3. 智能网格 - 使用自适应网格大小
        """
        print("\n大场地布局生成...")
        
        # 计算场地面积
        area = self._calculate_area(boundary)
        print(f"场地面积: {area/1000000:.1f} 平方米")
        
        # 获取边界
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        field_width = max_x - min_x
        field_height = max_y - min_y
        print(f"场地尺寸: {field_width/1000:.1f}m × {field_height/1000:.1f}m")
        
        # 创建验证上下文
        boundary_polygon = Polygon(boundary)
        context = {
            'boundary': boundary,
            'boundary_polygon': boundary_polygon,
            'obstacles': obstacles
        }
        
        layout = []
        
        # 策略1: 大规模规则网格布局
        print("\n策略1: 大规模网格布局")
        layout1 = self._large_scale_grid_layout(boundary, obstacles, context)
        print(f"  网格布局: {len(layout1)} 个台球桌")
        layout = layout1
        
        # 对于超大场地（>1000平米），跳过其他策略以节省时间
        if area > 1000 * 1000000:
            print("  超大场地，仅使用网格布局以提高效率")
        else:
            # 策略2: 分区域优化
            print("\n策略2: 分区域优化布局")
            layout2 = self._zone_based_layout(boundary, obstacles, context)
            print(f"  分区布局: {len(layout2)} 个台球桌")
            if len(layout2) > len(layout):
                layout = layout2
            
            # 策略3: 智能填充优化（限制在1000平米以下）
            if area < 1000 * 1000000:
                print("\n策略3: 智能填充优化")
                layout3 = self._intelligent_fill(layout.copy(), boundary, obstacles, context)
                print(f"  填充优化后: {len(layout3)} 个台球桌")
                if len(layout3) > len(layout):
                    layout = layout3
        
        # 计算统计信息
        if layout:
            self._print_statistics(layout, area)
        
        return layout
    
    def _calculate_area(self, boundary):
        """计算多边形面积"""
        n = len(boundary)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += boundary[i][0] * boundary[j][1]
            area -= boundary[j][0] * boundary[i][1]
        return abs(area) / 2.0
    
    def _large_scale_grid_layout(self, boundary, obstacles, context):
        """大规模网格布局 - 针对大场地优化"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 计算最优方向
        field_width = max_x - min_x - 2 * self.wall_distance
        field_height = max_y - min_y - 2 * self.wall_distance
        
        # 横向和纵向的容量估算
        h_cols = int((field_width + self.table_distance) / (self.table_width + self.table_distance))
        h_rows = int((field_height + self.table_distance) / (self.table_height + self.table_distance))
        h_capacity = h_cols * h_rows
        
        v_cols = int((field_width + self.table_distance) / (self.table_height + self.table_distance))
        v_rows = int((field_height + self.table_distance) / (self.table_width + self.table_distance))
        v_capacity = v_cols * v_rows
        
        print(f"  横向容量: {h_capacity} ({h_cols}列 × {h_rows}行)")
        print(f"  纵向容量: {v_capacity} ({v_cols}列 × {v_rows}行)")
        
        # 选择最优方向
        if h_capacity >= v_capacity:
            rotation = 0
            cols = h_cols
            rows = h_rows
            cell_width = self.table_width + self.table_distance
            cell_height = self.table_height + self.table_distance
            table_w = self.table_width
            table_h = self.table_height
        else:
            rotation = 90
            cols = v_cols
            rows = v_rows
            cell_width = self.table_height + self.table_distance
            cell_height = self.table_width + self.table_distance
            table_w = self.table_height
            table_h = self.table_width
        
        print(f"  选择{'横向' if rotation == 0 else '纵向'}布局")
        
        # 计算起始位置（居中对齐）
        total_width = cols * cell_width - self.table_distance
        total_height = rows * cell_height - self.table_distance
        start_x = min_x + self.wall_distance + (field_width - total_width) / 2
        start_y = min_y + self.wall_distance + (field_height - total_height) / 2
        
        # 批量放置
        placed = 0
        for row in range(rows):
            y = start_y + row * cell_height
            if y + table_h > max_y - self.wall_distance:
                break
                
            for col in range(cols):
                x = start_x + col * cell_width
                if x + table_w > max_x - self.wall_distance:
                    break
                
                table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                
                # 简化验证（只检查障碍物）
                valid = True
                table_bounds = table.get_bounds()
                for obstacle in obstacles:
                    if table_bounds.distance_to(obstacle) < self.wall_distance:
                        valid = False
                        break
                
                if valid:
                    layout.append(table)
                    placed += 1
                    
                    # 每100个打印一次进度
                    if placed % 100 == 0:
                        print(f"    已放置 {placed} 个台球桌...")
        
        return layout
    
    def _zone_based_layout(self, boundary, obstacles, context):
        """分区域布局 - 将大场地分成多个区域分别优化"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 确定分区大小（每个区域约100-200平米）
        zone_size = 15000  # 15m × 15m = 225平米
        
        # 计算分区数量
        num_zones_x = max(1, int((max_x - min_x) / zone_size) + 1)
        num_zones_y = max(1, int((max_y - min_y) / zone_size) + 1)
        
        print(f"  划分为 {num_zones_x} × {num_zones_y} = {num_zones_x * num_zones_y} 个区域")
        
        # 处理每个区域
        for zone_y in range(num_zones_y):
            for zone_x in range(num_zones_x):
                # 计算区域边界
                zone_min_x = min_x + zone_x * zone_size
                zone_max_x = min(min_x + (zone_x + 1) * zone_size, max_x)
                zone_min_y = min_y + zone_y * zone_size
                zone_max_y = min(min_y + (zone_y + 1) * zone_size, max_y)
                
                # 在区域内进行密集布局
                zone_layout = self._layout_in_zone(
                    zone_min_x, zone_min_y, zone_max_x, zone_max_y,
                    obstacles, context, layout
                )
                
                layout.extend(zone_layout)
                
                if zone_layout:
                    print(f"    区域[{zone_x},{zone_y}]: {len(zone_layout)} 个台球桌")
        
        return layout
    
    def _layout_in_zone(self, min_x, min_y, max_x, max_y, obstacles, context, existing_layout):
        """在指定区域内布局"""
        zone_layout = []
        
        # 考虑边界距离
        start_x = min_x + self.wall_distance if min_x == context['boundary'][0][0] else min_x
        start_y = min_y + self.wall_distance if min_y == context['boundary'][0][1] else min_y
        end_x = max_x - self.wall_distance if max_x == max(p[0] for p in context['boundary']) else max_x
        end_y = max_y - self.wall_distance if max_y == max(p[1] for p in context['boundary']) else max_y
        
        # 快速网格布局
        y = start_y
        while y + self.table_height <= end_y:
            x = start_x
            while x + self.table_width <= end_x:
                table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                
                # 检查约束
                temp_layout = existing_layout + zone_layout + [table]
                valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                
                if valid:
                    zone_layout.append(table)
                    x += self.table_width + self.table_distance
                else:
                    x += 500  # 较大步长跳过
            y += self.table_height + self.table_distance
        
        return zone_layout
    
    def _intelligent_fill(self, layout, boundary, obstacles, context):
        """智能填充 - 在已有布局基础上填充空隙"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 对于大场地，使用更大的扫描步长
        scan_step = 500
        added = 0
        
        # 尝试填充
        for rotation in [0, 90]:
            if rotation == 0:
                width, height = self.table_width, self.table_height
            else:
                width, height = self.table_height, self.table_width
            
            y = min_y + self.wall_distance
            while y + height <= max_y - self.wall_distance:
                x = min_x + self.wall_distance
                while x + width <= max_x - self.wall_distance:
                    table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                    
                    # 快速检查
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        added += 1
                        x += width + self.table_distance
                    else:
                        x += scan_step
                y += scan_step
        
        print(f"  智能填充: 新增 {added} 个台球桌")
        return layout
    
    def _print_statistics(self, layout, total_area):
        """打印统计信息"""
        table_area = self.table_width * self.table_height / 1000000  # 单个台球桌面积（平方米）
        total_table_area = len(layout) * table_area
        utilization = (total_table_area / (total_area / 1000000)) * 100
        
        print(f"\n统计信息:")
        print(f"  台球桌总数: {len(layout)} 个")
        print(f"  台球桌总面积: {total_table_area:.1f} 平方米")
        print(f"  空间利用率: {utilization:.1f}%")
        print(f"  平均每个台球桌占地: {total_area / len(layout) / 1000000:.1f} 平方米")