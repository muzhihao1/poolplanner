"""
约束满足系统
处理台球桌布局的各种约束条件
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from rtree import index
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

from .maxrects import Rectangle, BilliardTable


@dataclass
class ConstraintViolation:
    """约束违反信息"""
    constraint_type: str
    description: str
    severity: str  # 'error', 'warning'
    objects: List[any]  # 相关对象


class Constraint(ABC):
    """约束基类"""
    
    @abstractmethod
    def check(self, layout: List[BilliardTable], context: Dict) -> Tuple[bool, Optional[ConstraintViolation]]:
        """检查约束是否满足"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取约束名称"""
        pass


class DistanceConstraint(Constraint):
    """距离约束"""
    
    def __init__(self, wall_distance: float = 1500, table_distance: float = 1400, obstacle_distance: float = 1500):
        self.wall_distance = wall_distance
        self.table_distance = table_distance
        self.obstacle_distance = obstacle_distance
    
    def get_name(self) -> str:
        return "距离约束"
    
    def check(self, layout: List[BilliardTable], context: Dict) -> Tuple[bool, Optional[ConstraintViolation]]:
        """检查所有距离约束"""
        # 检查台球桌之间的距离
        for i, table1 in enumerate(layout):
            bounds1 = table1.get_bounds()
            for j, table2 in enumerate(layout[i+1:], i+1):
                bounds2 = table2.get_bounds()
                distance = bounds1.distance_to(bounds2)
                if distance < self.table_distance:
                    return False, ConstraintViolation(
                        constraint_type="table_distance",
                        description=f"台球桌{i}和{j}之间距离{distance:.0f}mm小于要求的{self.table_distance}mm",
                        severity="error",
                        objects=[table1, table2]
                    )
        
        # 检查与墙壁的距离
        # 如果没有boundary_polygon，尝试创建
        boundary_polygon = context.get('boundary_polygon')
        if not boundary_polygon and 'boundary' in context:
            try:
                boundary_polygon = Polygon(context['boundary'])
                context['boundary_polygon'] = boundary_polygon
            except:
                pass
                
        if boundary_polygon:
            for i, table in enumerate(layout):
                bounds = table.get_bounds()
                # 创建台球桌的多边形
                table_poly = Polygon([
                    (bounds.x, bounds.y),
                    (bounds.x + bounds.width, bounds.y),
                    (bounds.x + bounds.width, bounds.y + bounds.height),
                    (bounds.x, bounds.y + bounds.height)
                ])
                
                # 计算到边界的距离
                distance = boundary_polygon.boundary.distance(table_poly)
                if distance < self.wall_distance:
                    return False, ConstraintViolation(
                        constraint_type="wall_distance",
                        description=f"台球桌{i}距离墙壁{distance:.0f}mm小于要求的{self.wall_distance}mm",
                        severity="error",
                        objects=[table]
                    )
        else:
            # 使用简单的矩形边界检查
            if 'boundary' in context:
                boundary = context['boundary']
                min_x = min(p[0] for p in boundary)
                max_x = max(p[0] for p in boundary)
                min_y = min(p[1] for p in boundary)
                max_y = max(p[1] for p in boundary)
                
                for i, table in enumerate(layout):
                    bounds = table.get_bounds()
                    # 检查到各边的距离
                    dist_left = bounds.x - min_x
                    dist_right = max_x - (bounds.x + bounds.width)
                    dist_top = bounds.y - min_y
                    dist_bottom = max_y - (bounds.y + bounds.height)
                    
                    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                    if min_dist < self.wall_distance:
                        return False, ConstraintViolation(
                            constraint_type="wall_distance",
                            description=f"台球桌{i}距离墙壁{min_dist:.0f}mm小于要求的{self.wall_distance}mm",
                            severity="error",
                            objects=[table]
                        )
        
        # 检查与障碍物的距离
        obstacles = context.get('obstacles', [])
        for i, table in enumerate(layout):
            bounds = table.get_bounds()
            for j, obstacle in enumerate(obstacles):
                distance = bounds.distance_to(obstacle)
                if distance < self.obstacle_distance:
                    return False, ConstraintViolation(
                        constraint_type="obstacle_distance",
                        description=f"台球桌{i}距离障碍物{j}太近：{distance:.0f}mm",
                        severity="error",
                        objects=[table, obstacle]
                    )
        
        return True, None


class AccessibilityConstraint(Constraint):
    """可达性约束"""
    
    def __init__(self, min_passage_width: float = 1000):
        self.min_passage_width = min_passage_width
    
    def get_name(self) -> str:
        return "可达性约束"
    
    def check(self, layout: List[BilliardTable], context: Dict) -> Tuple[bool, Optional[ConstraintViolation]]:
        """检查所有台球桌是否可达"""
        # 简化版本：检查是否有足够的通道
        # 实际应用中应该使用路径规划算法
        return True, None


class SpatialIndex:
    """空间索引，用于加速空间查询"""
    
    def __init__(self):
        # 创建R-tree索引
        self.idx = index.Index()
        self.objects = {}
        self._counter = 0
    
    def insert(self, obj: any, bounds: Rectangle) -> int:
        """插入对象"""
        obj_id = self._counter
        self._counter += 1
        
        # R-tree使用(minx, miny, maxx, maxy)格式
        self.idx.insert(obj_id, (
            bounds.x, bounds.y,
            bounds.x + bounds.width,
            bounds.y + bounds.height
        ))
        self.objects[obj_id] = (obj, bounds)
        return obj_id
    
    def query_intersects(self, bounds: Rectangle) -> List[Tuple[int, any, Rectangle]]:
        """查询与给定边界相交的对象"""
        results = []
        for obj_id in self.idx.intersection((
            bounds.x, bounds.y,
            bounds.x + bounds.width,
            bounds.y + bounds.height
        )):
            obj, obj_bounds = self.objects[obj_id]
            results.append((obj_id, obj, obj_bounds))
        return results
    
    def query_nearest(self, x: float, y: float, num_results: int = 1) -> List[Tuple[int, any, Rectangle, float]]:
        """查询最近的对象"""
        results = []
        for obj_id in self.idx.nearest((x, y, x, y), num_results):
            obj, bounds = self.objects[obj_id]
            # 计算到边界的距离
            distance = self._point_to_rectangle_distance(x, y, bounds)
            results.append((obj_id, obj, bounds, distance))
        return results
    
    def _point_to_rectangle_distance(self, x: float, y: float, rect: Rectangle) -> float:
        """计算点到矩形的距离"""
        # 如果点在矩形内，距离为0
        if rect.contains_point(x, y):
            return 0.0
        
        # 计算到矩形边界的最短距离
        dx = max(rect.x - x, 0, x - (rect.x + rect.width))
        dy = max(rect.y - y, 0, y - (rect.y + rect.height))
        return np.sqrt(dx**2 + dy**2)
    
    def remove(self, obj_id: int):
        """移除对象"""
        if obj_id in self.objects:
            _, bounds = self.objects[obj_id]
            self.idx.delete(obj_id, (
                bounds.x, bounds.y,
                bounds.x + bounds.width,
                bounds.y + bounds.height
            ))
            del self.objects[obj_id]
    
    def clear(self):
        """清空索引"""
        self.idx = index.Index()
        self.objects.clear()
        self._counter = 0


class ConstraintSolver:
    """约束求解器"""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.spatial_index = SpatialIndex()
    
    def add_constraint(self, constraint: Constraint):
        """添加约束"""
        self.constraints.append(constraint)
    
    def validate_layout(self, layout: List[BilliardTable], context: Dict) -> Tuple[bool, List[ConstraintViolation]]:
        """验证布局是否满足所有约束"""
        violations = []
        
        # 构建空间索引以加速查询
        self.spatial_index.clear()
        for table in layout:
            bounds = table.get_bounds()
            self.spatial_index.insert(table, bounds)
        
        # 检查所有约束
        for constraint in self.constraints:
            satisfied, violation = constraint.check(layout, context)
            if not satisfied and violation:
                violations.append(violation)
        
        return len(violations) == 0, violations
    
    def find_conflicts(self, table: BilliardTable, layout: List[BilliardTable], context: Dict) -> List[ConstraintViolation]:
        """查找单个台球桌的约束冲突"""
        violations = []
        
        # 临时添加到布局中进行检查
        temp_layout = layout + [table]
        
        for constraint in self.constraints:
            satisfied, violation = constraint.check(temp_layout, context)
            if not satisfied and violation:
                violations.append(violation)
        
        return violations
    
    def suggest_position(self, table: BilliardTable, layout: List[BilliardTable], context: Dict) -> Optional[Tuple[float, float]]:
        """建议一个满足约束的位置"""
        # 使用网格搜索找到合适的位置
        boundary = context.get('boundary', [])
        if not boundary:
            return None
        
        min_x = min(p[0] for p in boundary)
        max_x = max(p[0] for p in boundary)
        min_y = min(p[1] for p in boundary)
        max_y = max(p[1] for p in boundary)
        
        # 网格步长
        step = 100  # 100mm
        
        for x in np.arange(min_x, max_x - table.width, step):
            for y in np.arange(min_y, max_y - table.height, step):
                table.x = x
                table.y = y
                conflicts = self.find_conflicts(table, layout, context)
                if not conflicts:
                    return (x, y)
        
        return None