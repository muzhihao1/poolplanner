"""
改进的MaxRects算法实现
用于台球桌自动布局优化
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Rectangle:
    """矩形类，表示可用空间或台球桌"""
    x: float
    y: float
    width: float
    height: float
    
    def area(self) -> float:
        """计算矩形面积"""
        return self.width * self.height
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在矩形内"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """检查两个矩形是否相交"""
        return not (self.x + self.width <= other.x or
                   other.x + other.width <= self.x or
                   self.y + self.height <= other.y or
                   other.y + other.height <= self.y)
    
    def distance_to(self, other: 'Rectangle') -> float:
        """计算两个矩形之间的最短距离"""
        # 计算x方向距离
        dx = max(0, max(other.x - (self.x + self.width), self.x - (other.x + other.width)))
        # 计算y方向距离
        dy = max(0, max(other.y - (self.y + self.height), self.y - (other.y + other.height)))
        return np.sqrt(dx**2 + dy**2)


@dataclass
class BilliardTable:
    """台球桌类"""
    x: float
    y: float
    width: float = 2850  # 默认宽度 2850mm
    height: float = 1550  # 默认高度 1550mm
    rotation: int = 0  # 旋转角度，0或90度
    
    def get_bounds(self) -> Rectangle:
        """获取台球桌的边界矩形"""
        if self.rotation == 90:
            return Rectangle(self.x, self.y, self.height, self.width)
        return Rectangle(self.x, self.y, self.width, self.height)
    
    def get_safety_bounds(self, wall_distance: float = 1500, table_distance: float = 1400) -> Rectangle:
        """获取包含安全距离的边界矩形"""
        bounds = self.get_bounds()
        # 对于墙壁，使用wall_distance
        # 这里简化处理，实际使用时需要根据具体情况调整
        safety_margin = wall_distance
        return Rectangle(
            bounds.x - safety_margin,
            bounds.y - safety_margin,
            bounds.width + 2 * safety_margin,
            bounds.height + 2 * safety_margin
        )


class MaxRectsAlgorithm:
    """改进的MaxRects算法实现"""
    
    def __init__(self, boundary: List[Tuple[float, float]], obstacles: List[Rectangle]):
        """
        初始化算法
        
        Args:
            boundary: 场地边界点列表
            obstacles: 障碍物（柱子）列表
        """
        self.boundary = boundary
        self.obstacles = obstacles
        self.free_rectangles: List[Rectangle] = []
        self.placed_tables: List[BilliardTable] = []
        
        # 约束参数
        self.wall_distance = 1500  # 与墙壁的最小距离
        self.table_distance = 1400  # 台球桌之间的最小距离
        self.table_width = 2850
        self.table_height = 1550
        
        # 初始化可用空间
        self._initialize_free_space()
    
    def _initialize_free_space(self):
        """初始化可用空间为整个场地"""
        # 简化处理：假设场地是矩形
        # 实际应用中需要处理多边形场地
        min_x = min(p[0] for p in self.boundary)
        max_x = max(p[0] for p in self.boundary)
        min_y = min(p[1] for p in self.boundary)
        max_y = max(p[1] for p in self.boundary)
        
        # 考虑墙壁安全距离 - 修复：正确计算内缩后的宽度和高度
        safe_min_x = min_x + self.wall_distance
        safe_min_y = min_y + self.wall_distance
        safe_max_x = max_x - self.wall_distance
        safe_max_y = max_y - self.wall_distance
        
        # 确保有足够的空间
        if safe_max_x <= safe_min_x or safe_max_y <= safe_min_y:
            print(f"警告：场地太小，无法满足安全距离要求")
            self.free_rectangles = []
            return
            
        self.free_rectangles = [Rectangle(
            safe_min_x,
            safe_min_y,
            safe_max_x - safe_min_x,  # 宽度
            safe_max_y - safe_min_y   # 高度
        )]
        
        print(f"初始化可用空间: x={safe_min_x:.0f}-{safe_max_x:.0f}, y={safe_min_y:.0f}-{safe_max_y:.0f}")
        
        # 移除障碍物占用的空间
        for obstacle in self.obstacles:
            self._remove_obstacle_space(obstacle)
    
    def _remove_obstacle_space(self, obstacle: Rectangle):
        """从可用空间中移除障碍物及其安全距离"""
        # 扩展障碍物边界以包含安全距离
        expanded_obstacle = Rectangle(
            obstacle.x - self.wall_distance,
            obstacle.y - self.wall_distance,
            obstacle.width + 2 * self.wall_distance,
            obstacle.height + 2 * self.wall_distance
        )
        
        new_free_rectangles = []
        for free_rect in self.free_rectangles:
            if not free_rect.intersects(expanded_obstacle):
                new_free_rectangles.append(free_rect)
            else:
                # 分割矩形
                splits = self._split_rectangle(free_rect, expanded_obstacle)
                new_free_rectangles.extend(splits)
        
        self.free_rectangles = new_free_rectangles
    
    def _split_rectangle(self, rect: Rectangle, obstacle: Rectangle) -> List[Rectangle]:
        """将矩形按障碍物分割"""
        splits = []
        
        # 左侧部分
        if obstacle.x > rect.x:
            splits.append(Rectangle(
                rect.x, rect.y,
                obstacle.x - rect.x, rect.height
            ))
        
        # 右侧部分
        if obstacle.x + obstacle.width < rect.x + rect.width:
            splits.append(Rectangle(
                obstacle.x + obstacle.width, rect.y,
                rect.x + rect.width - obstacle.x - obstacle.width, rect.height
            ))
        
        # 上侧部分
        if obstacle.y > rect.y:
            splits.append(Rectangle(
                rect.x, rect.y,
                rect.width, obstacle.y - rect.y
            ))
        
        # 下侧部分
        if obstacle.y + obstacle.height < rect.y + rect.height:
            splits.append(Rectangle(
                rect.x, obstacle.y + obstacle.height,
                rect.width, rect.y + rect.height - obstacle.y - obstacle.height
            ))
        
        return [s for s in splits if s.width > 0 and s.height > 0]
    
    def find_best_position(self, width: float, height: float) -> Optional[Tuple[float, float, int]]:
        """
        找到最佳放置位置 - 改进版：考虑多个候选位置
        
        Returns:
            (x, y, rotation) 或 None
        """
        candidates = []
        
        for free_rect in self.free_rectangles:
            # 尝试0度旋转
            if free_rect.width >= width and free_rect.height >= height:
                # 尝试多个位置：左下、左上、右下、右上、中心
                positions = [
                    (free_rect.x, free_rect.y),  # 左下
                    (free_rect.x, free_rect.y + free_rect.height - height),  # 左上
                    (free_rect.x + free_rect.width - width, free_rect.y),  # 右下
                    (free_rect.x + free_rect.width - width, free_rect.y + free_rect.height - height),  # 右上
                    (free_rect.x + (free_rect.width - width) / 2, free_rect.y + (free_rect.height - height) / 2)  # 中心
                ]
                
                for x, y in positions:
                    # 确保位置有效
                    if x >= free_rect.x and y >= free_rect.y and x + width <= free_rect.x + free_rect.width and y + height <= free_rect.y + free_rect.height:
                        # 计算评分：优先填充角落和边缘
                        edge_score = min(x - free_rect.x, y - free_rect.y, 
                                       free_rect.x + free_rect.width - x - width,
                                       free_rect.y + free_rect.height - y - height)
                        score = -edge_score  # 负值因为我们想要最小化边缘距离
                        candidates.append((x, y, 0, score))
            
            # 尝试90度旋转
            if free_rect.width >= height and free_rect.height >= width:
                positions = [
                    (free_rect.x, free_rect.y),
                    (free_rect.x, free_rect.y + free_rect.height - width),
                    (free_rect.x + free_rect.width - height, free_rect.y),
                    (free_rect.x + free_rect.width - height, free_rect.y + free_rect.height - width),
                    (free_rect.x + (free_rect.width - height) / 2, free_rect.y + (free_rect.height - width) / 2)
                ]
                
                for x, y in positions:
                    if x >= free_rect.x and y >= free_rect.y and x + height <= free_rect.x + free_rect.width and y + width <= free_rect.y + free_rect.height:
                        edge_score = min(x - free_rect.x, y - free_rect.y,
                                       free_rect.x + free_rect.width - x - height,
                                       free_rect.y + free_rect.height - y - width)
                        score = -edge_score
                        candidates.append((x, y, 90, score))
        
        if not candidates:
            return None
        
        # 选择最佳候选位置
        candidates.sort(key=lambda c: c[3])
        x, y, rotation, _ = candidates[0]
        
        return (x, y, rotation)
    
    def place_table(self, table: BilliardTable) -> bool:
        """
        放置台球桌
        
        Returns:
            是否成功放置
        """
        table_bounds = table.get_bounds()
        
        # 首先检查是否在场地边界内（考虑安全距离）
        min_x = min(p[0] for p in self.boundary)
        max_x = max(p[0] for p in self.boundary)
        min_y = min(p[1] for p in self.boundary)
        max_y = max(p[1] for p in self.boundary)
        
        # 检查台球桌是否太靠近墙壁
        if (table_bounds.x < min_x + self.wall_distance or
            table_bounds.y < min_y + self.wall_distance or
            table_bounds.x + table_bounds.width > max_x - self.wall_distance or
            table_bounds.y + table_bounds.height > max_y - self.wall_distance):
            print(f"拒绝放置：台球桌 ({table_bounds.x:.0f}, {table_bounds.y:.0f}) 太靠近墙壁")
            return False
        
        # 检查是否与已放置的台球桌冲突
        for i, placed in enumerate(self.placed_tables):
            placed_bounds = placed.get_bounds()
            distance = table_bounds.distance_to(placed_bounds)
            if distance < self.table_distance:
                print(f"拒绝放置：与台球桌{i}距离{distance:.0f}mm < {self.table_distance}mm")
                return False
        
        # 检查是否与障碍物冲突
        for j, obstacle in enumerate(self.obstacles):
            distance = table_bounds.distance_to(obstacle)
            if distance < self.wall_distance:
                print(f"拒绝放置：与障碍物{j}距离{distance:.0f}mm < {self.wall_distance}mm")
                return False
        
        # 更新可用空间
        self._update_free_rectangles(table)
        self.placed_tables.append(table)
        print(f"成功放置台球桌 #{len(self.placed_tables)} at ({table.x:.0f}, {table.y:.0f})")
        return True
    
    def _update_free_rectangles(self, table: BilliardTable):
        """放置台球桌后更新可用空间"""
        # 获取台球桌的安全边界（包含与其他台球桌的最小距离）
        safety_bounds = table.get_safety_bounds(self.table_distance, self.table_distance)
        
        new_free_rectangles = []
        for free_rect in self.free_rectangles:
            if not free_rect.intersects(safety_bounds):
                new_free_rectangles.append(free_rect)
            else:
                # 分割矩形
                splits = self._split_rectangle(free_rect, safety_bounds)
                new_free_rectangles.extend(splits)
        
        # 合并相邻的矩形以优化性能（可选）
        self.free_rectangles = self._merge_rectangles(new_free_rectangles)
    
    def _merge_rectangles(self, rectangles: List[Rectangle]) -> List[Rectangle]:
        """合并相邻的矩形（简化版本）"""
        # 这里暂时返回原列表，实际应用中可以实现矩形合并优化
        return rectangles
    
    def optimize_layout(self) -> List[BilliardTable]:
        """
        执行布局优化
        
        Returns:
            放置的台球桌列表
        """
        while True:
            # 找到最佳位置
            position = self.find_best_position(self.table_width, self.table_height)
            if position is None:
                break
            
            x, y, rotation = position
            table = BilliardTable(x, y, self.table_width, self.table_height, rotation)
            
            if not self.place_table(table):
                break
        
        return self.placed_tables