"""
障碍物感知布局算法 - 在有障碍物的情况下最大化台球桌数量
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon, box
from rtree import index


class ObstacleAwareLayoutGenerator:
    """障碍物感知的布局生成器"""
    
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
        生成障碍物感知的优化布局
        
        策略：
        1. 识别可用区域（排除障碍物影响区）
        2. 在每个可用区域内进行密集布局
        3. 优先横向布局，空间不足时考虑纵向
        """
        print("\n障碍物感知布局生成...")
        print(f"场地中有 {len(obstacles)} 个障碍物")
        
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
        
        # 创建空间索引以加速碰撞检测
        obstacle_index = self._create_obstacle_index(obstacles)
        
        layout = []
        
        # 策略1: 行扫描布局（优先横向）
        print("\n阶段1: 行扫描布局（横向优先）")
        layout1 = self._row_scan_layout(boundary, obstacles, context, obstacle_index)
        print(f"  行扫描布局: {len(layout1)} 个台球桌")
        layout = layout1
        
        # 策略2: 区域分割布局
        print("\n阶段2: 区域分割布局")
        layout2 = self._region_based_layout(boundary, obstacles, context)
        print(f"  区域分割布局: {len(layout2)} 个台球桌")
        if len(layout2) > len(layout):
            layout = layout2
        
        # 策略3: 空隙填充
        print("\n阶段3: 空隙填充优化")
        layout3 = self._fill_gaps_smart(layout.copy(), boundary, obstacles, context, obstacle_index)
        print(f"  填充后: {len(layout3)} 个台球桌")
        if len(layout3) > len(layout):
            layout = layout3
        
        # 对结果排序
        if layout:
            layout.sort(key=lambda t: (t.y, t.x))
            print("\n最终布局:")
            for i, table in enumerate(layout):
                orientation = "纵向" if table.rotation == 90 else "横向"
                print(f"  台球桌#{i+1}: ({table.x:.0f}, {table.y:.0f}) - {orientation}")
        
        return layout
    
    def _create_obstacle_index(self, obstacles):
        """创建障碍物的空间索引"""
        idx = index.Index()
        for i, obstacle in enumerate(obstacles):
            # 扩展障碍物边界（加上安全距离）
            left = obstacle.x - self.wall_distance
            bottom = obstacle.y - self.wall_distance
            right = obstacle.x + obstacle.width + self.wall_distance
            top = obstacle.y + obstacle.height + self.wall_distance
            idx.insert(i, (left, bottom, right, top))
        return idx
    
    def _row_scan_layout(self, boundary, obstacles, context, obstacle_index):
        """行扫描布局 - 逐行放置，智能避开障碍物"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 更细粒度的扫描
        scan_step_y = 100  # Y方向扫描步长
        
        # 从上到下扫描
        y = min_y + self.wall_distance
        
        while y + min(self.table_height, self.table_width) <= max_y - self.wall_distance:
            # 尝试横向行
            if y + self.table_height <= max_y - self.wall_distance:
                # 获取这一行的可用区间（横向）
                available_intervals = self._get_available_intervals(
                    y, y + self.table_height, min_x + self.wall_distance, 
                    max_x - self.wall_distance, obstacles
                )
                
                row_placed = False
                for start_x, end_x in available_intervals:
                    interval_width = end_x - start_x
                    
                    # 尝试横向
                    if interval_width >= self.table_width:
                        x = start_x
                        while x + self.table_width <= end_x:
                            table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                            temp_layout = layout + [table]
                            valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                            
                            if valid:
                                layout.append(table)
                                row_placed = True
                                x += self.table_width + self.table_distance
                            else:
                                x += 50
                
                # 如果横向放置了桌子，跳过一个行高
                if row_placed:
                    y += self.table_height + self.table_distance
                    continue
            
            # 尝试纵向行
            if y + self.table_width <= max_y - self.wall_distance:
                # 获取这一行的可用区间（纵向）
                available_intervals = self._get_available_intervals(
                    y, y + self.table_width, min_x + self.wall_distance, 
                    max_x - self.wall_distance, obstacles
                )
                
                row_placed = False
                for start_x, end_x in available_intervals:
                    interval_width = end_x - start_x
                    
                    # 尝试纵向
                    if interval_width >= self.table_height:
                        x = start_x
                        while x + self.table_height <= end_x:
                            table = BilliardTable(x, y, self.table_width, self.table_height, 90)
                            temp_layout = layout + [table]
                            valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                            
                            if valid:
                                layout.append(table)
                                row_placed = True
                                x += self.table_height + self.table_distance
                            else:
                                x += 50
                
                # 如果纵向放置了桌子，跳过相应高度
                if row_placed:
                    y += self.table_width + self.table_distance
                    continue
            
            # 如果都没放置，小步前进
            y += scan_step_y
        
        return layout
    
    def _get_available_intervals(self, y_start, y_end, x_start, x_end, obstacles):
        """获取指定Y范围内的可用X区间"""
        # 收集所有障碍物在这个Y范围内的X投影
        blocked_intervals = []
        
        for obstacle in obstacles:
            # 检查障碍物是否与Y范围重叠
            obs_top = obstacle.y + obstacle.height + self.wall_distance
            obs_bottom = obstacle.y - self.wall_distance
            
            if obs_bottom < y_end and obs_top > y_start:
                # 障碍物影响这个Y范围
                obs_left = obstacle.x - self.wall_distance
                obs_right = obstacle.x + obstacle.width + self.wall_distance
                
                # 限制在有效范围内
                obs_left = max(obs_left, x_start)
                obs_right = min(obs_right, x_end)
                
                if obs_left < obs_right:
                    blocked_intervals.append((obs_left, obs_right))
        
        # 合并重叠的区间
        blocked_intervals.sort()
        merged_blocked = []
        for start, end in blocked_intervals:
            if merged_blocked and start <= merged_blocked[-1][1]:
                merged_blocked[-1] = (merged_blocked[-1][0], max(merged_blocked[-1][1], end))
            else:
                merged_blocked.append((start, end))
        
        # 计算可用区间
        available_intervals = []
        current_x = x_start
        
        for block_start, block_end in merged_blocked:
            if current_x < block_start:
                available_intervals.append((current_x, block_start))
            current_x = max(current_x, block_end)
        
        if current_x < x_end:
            available_intervals.append((current_x, x_end))
        
        return available_intervals
    
    def _region_based_layout(self, boundary, obstacles, context):
        """基于区域分割的布局"""
        layout = []
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 创建初始区域
        regions = [(min_x + self.wall_distance, min_y + self.wall_distance, 
                   max_x - self.wall_distance, max_y - self.wall_distance)]
        
        # 根据障碍物分割区域
        for obstacle in obstacles:
            new_regions = []
            for rx1, ry1, rx2, ry2 in regions:
                # 检查障碍物是否与区域相交
                obs_x1 = obstacle.x - self.wall_distance
                obs_y1 = obstacle.y - self.wall_distance
                obs_x2 = obstacle.x + obstacle.width + self.wall_distance
                obs_y2 = obstacle.y + obstacle.height + self.wall_distance
                
                if obs_x1 < rx2 and obs_x2 > rx1 and obs_y1 < ry2 and obs_y2 > ry1:
                    # 障碍物与区域相交，分割区域
                    # 上方区域
                    if ry1 < obs_y1:
                        new_regions.append((rx1, ry1, rx2, obs_y1))
                    # 下方区域
                    if obs_y2 < ry2:
                        new_regions.append((rx1, obs_y2, rx2, ry2))
                    # 左侧区域
                    if rx1 < obs_x1:
                        new_regions.append((rx1, max(ry1, obs_y1), obs_x1, min(ry2, obs_y2)))
                    # 右侧区域
                    if obs_x2 < rx2:
                        new_regions.append((obs_x2, max(ry1, obs_y1), rx2, min(ry2, obs_y2)))
                else:
                    # 无相交，保留原区域
                    new_regions.append((rx1, ry1, rx2, ry2))
            regions = new_regions
        
        # 在每个区域内进行密集布局
        for rx1, ry1, rx2, ry2 in regions:
            region_width = rx2 - rx1
            region_height = ry2 - ry1
            
            # 只处理足够大的区域
            if region_width >= self.table_height and region_height >= self.table_height:
                # 在区域内进行网格布局
                y = ry1
                while y + self.table_height <= ry2:
                    x = rx1
                    while x + self.table_width <= rx2:
                        table = BilliardTable(x, y, self.table_width, self.table_height, 0)
                        temp_layout = layout + [table]
                        valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                        
                        if valid:
                            layout.append(table)
                            x += self.table_width + self.table_distance
                        else:
                            x += 100
                    y += self.table_height + self.table_distance
        
        return layout
    
    def _fill_gaps_smart(self, layout, boundary, obstacles, context, obstacle_index):
        """智能填充空隙"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 细粒度扫描
        scan_step = 50
        added_count = 0
        
        # 尝试所有可能的位置和方向
        for y in range(int(min_y + self.wall_distance), 
                      int(max_y - self.wall_distance - min(self.table_height, self.table_width)), 
                      scan_step):
            for x in range(int(min_x + self.wall_distance), 
                          int(max_x - self.wall_distance - min(self.table_width, self.table_height)), 
                          scan_step):
                
                # 快速检查是否在障碍物附近
                potential_obstacles = list(obstacle_index.intersection(
                    (x - self.table_width, y - self.table_width, 
                     x + self.table_width * 2, y + self.table_width * 2)
                ))
                
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
                    
                    # 如果附近有障碍物，进行精确检查
                    if potential_obstacles:
                        skip = False
                        for obs_idx in potential_obstacles:
                            obstacle = obstacles[obs_idx]
                            # 计算与障碍物的距离
                            if (x + width + self.wall_distance > obstacle.x and 
                                x < obstacle.x + obstacle.width + self.wall_distance and
                                y + height + self.wall_distance > obstacle.y and 
                                y < obstacle.y + obstacle.height + self.wall_distance):
                                skip = True
                                break
                        if skip:
                            continue
                    
                    table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
                    temp_layout = layout + [table]
                    valid, _ = self.constraint_solver.validate_layout(temp_layout, context)
                    
                    if valid:
                        layout.append(table)
                        added_count += 1
                        break
        
        print(f"  空隙填充: 新增 {added_count} 个台球桌")
        return layout