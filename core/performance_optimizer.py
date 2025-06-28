"""
性能优化器 - 提升算法执行效率
"""

import time
import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

from .maxrects import Rectangle, BilliardTable


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    memory_usage: float
    table_count: int
    iterations: int
    cache_hits: int
    cache_misses: int


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.enable_caching = config.get('enable_caching', True)
        self.enable_parallel = config.get('enable_parallel', True)
        self.max_workers = config.get('max_workers', 4)
    
    def optimize_layout_generation(self, generator_func: Callable, 
                                 boundary: List[Tuple[float, float]], 
                                 obstacles: List[Rectangle]) -> Tuple[List[BilliardTable], PerformanceMetrics]:
        """优化布局生成过程"""
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # 检查缓存
        cache_key = self._generate_cache_key(boundary, obstacles)
        
        if self.enable_caching and cache_key in self.cache:
            self.cache_hits += 1
            layout = self.cache[cache_key]
            execution_time = time.time() - start_time
            
            return layout, PerformanceMetrics(
                execution_time=execution_time,
                memory_usage=0,
                table_count=len(layout),
                iterations=0,
                cache_hits=self.cache_hits,
                cache_misses=self.cache_misses
            )
        
        self.cache_misses += 1
        
        # 执行布局生成
        if self.enable_parallel and self._should_use_parallel(boundary, obstacles):
            layout = self._parallel_layout_generation(generator_func, boundary, obstacles)
        else:
            layout = generator_func(boundary, obstacles)
        
        # 缓存结果
        if self.enable_caching:
            self.cache[cache_key] = layout
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        metrics = PerformanceMetrics(
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            table_count=len(layout),
            iterations=1,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses
        )
        
        return layout, metrics
    
    def _generate_cache_key(self, boundary, obstacles):
        """生成缓存键"""
        # 将边界和障碍物转换为可哈希的字符串
        boundary_str = str(sorted(boundary))
        obstacles_str = str(sorted([(obs.x, obs.y, obs.width, obs.height) for obs in obstacles]))
        config_str = str(sorted(self.config.items()))
        
        return hash(boundary_str + obstacles_str + config_str)
    
    def _should_use_parallel(self, boundary, obstacles):
        """判断是否应该使用并行处理"""
        # 计算场地面积
        area = self._calculate_area(boundary)
        
        # 大场地或多障碍物时使用并行处理
        return area > 200 * 1000000 or len(obstacles) > 2  # 200平米以上或超过2个障碍物
    
    def _parallel_layout_generation(self, generator_func, boundary, obstacles):
        """并行布局生成"""
        
        # 将场地分割为多个区域
        regions = self._split_field_for_parallel(boundary, obstacles)
        
        layouts = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 为每个区域提交任务
            future_to_region = {
                executor.submit(generator_func, region['boundary'], region['obstacles']): region
                for region in regions
            }
            
            # 收集结果
            for future in as_completed(future_to_region):
                try:
                    region_layout = future.result()
                    layouts.extend(region_layout)
                except Exception as e:
                    print(f"并行处理区域时出错: {e}")
        
        return layouts
    
    def _split_field_for_parallel(self, boundary, obstacles):
        """为并行处理分割场地"""
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 简单的四等分
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        
        regions = [
            {  # 左上
                'boundary': [[min_x, min_y], [mid_x, min_y], [mid_x, mid_y], [min_x, mid_y]],
                'obstacles': [obs for obs in obstacles if obs.x < mid_x and obs.y < mid_y]
            },
            {  # 右上
                'boundary': [[mid_x, min_y], [max_x, min_y], [max_x, mid_y], [mid_x, mid_y]],
                'obstacles': [obs for obs in obstacles if obs.x >= mid_x and obs.y < mid_y]
            },
            {  # 左下
                'boundary': [[min_x, mid_y], [mid_x, mid_y], [mid_x, max_y], [min_x, max_y]],
                'obstacles': [obs for obs in obstacles if obs.x < mid_x and obs.y >= mid_y]
            },
            {  # 右下
                'boundary': [[mid_x, mid_y], [max_x, mid_y], [max_x, max_y], [mid_x, max_y]],
                'obstacles': [obs for obs in obstacles if obs.x >= mid_x and obs.y >= mid_y]
            }
        ]
        
        return regions
    
    def _calculate_area(self, boundary):
        """计算多边形面积"""
        if len(boundary) < 3:
            return 0
        
        area = 0
        n = len(boundary)
        for i in range(n):
            j = (i + 1) % n
            area += boundary[i][0] * boundary[j][1]
            area -= boundary[j][0] * boundary[i][1]
        
        return abs(area) / 2
    
    def _get_memory_usage(self):
        """获取内存使用量（简化实现）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0  # 如果没有psutil，返回0
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_stats(self):
        """获取缓存统计"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': round(hit_rate, 2)
        }


def performance_monitor(func):
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(f"[性能] {func.__name__} 执行时间: {execution_time:.2f}秒")
            
            if hasattr(result, '__len__'):
                print(f"[性能] 结果数量: {len(result)}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[性能] {func.__name__} 执行失败，耗时: {execution_time:.2f}秒，错误: {e}")
            raise
    
    return wrapper


def memory_efficient_layout_generation(boundary, obstacles, config):
    """内存高效的布局生成"""
    
    # 使用生成器而不是列表来节省内存
    def generate_positions():
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        wall_distance = config.get('wall_distance', 1500)
        table_distance = config.get('table_distance', 1400)
        table_width = config.get('table_width', 2850)
        table_height = config.get('table_height', 1550)
        
        scan_step = 100
        
        for y in range(int(min_y + wall_distance), 
                      int(max_y - wall_distance - table_height), 
                      scan_step):
            for x in range(int(min_x + wall_distance), 
                          int(max_x - wall_distance - table_width), 
                          scan_step):
                for rotation in [0, 90]:
                    yield (x, y, rotation)
    
    # 批量处理位置以减少内存使用
    layout = []
    batch_size = 100
    batch = []
    
    for position in generate_positions():
        batch.append(position)
        
        if len(batch) >= batch_size:
            # 处理批次
            batch_layout = process_position_batch(batch, boundary, obstacles, config)
            layout.extend(batch_layout)
            batch.clear()
    
    # 处理最后一批
    if batch:
        batch_layout = process_position_batch(batch, boundary, obstacles, config)
        layout.extend(batch_layout)
    
    return layout


def process_position_batch(positions, boundary, obstacles, config):
    """处理位置批次"""
    from .constraints import ConstraintSolver, DistanceConstraint
    from shapely.geometry import Polygon
    
    # 创建约束求解器
    constraint_solver = ConstraintSolver()
    constraint_solver.add_constraint(
        DistanceConstraint(
            config.get('wall_distance', 1500),
            config.get('table_distance', 1400),
            config.get('wall_distance', 1500)
        )
    )
    
    context = {
        'boundary': boundary,
        'boundary_polygon': Polygon(boundary),
        'obstacles': obstacles
    }
    
    layout = []
    
    for x, y, rotation in positions:
        table = BilliardTable(
            x, y, 
            config.get('table_width', 2850), 
            config.get('table_height', 1550), 
            rotation
        )
        
        temp_layout = layout + [table]
        valid, _ = constraint_solver.validate_layout(temp_layout, context)
        
        if valid:
            layout.append(table)
    
    return layout