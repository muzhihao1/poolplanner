"""
几何处理模块
处理场地边界、障碍物和各种几何计算
"""

import numpy as np
from typing import List, Tuple, Optional, Union, Dict
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union, triangulate
from shapely.validation import make_valid
import cv2

from .maxrects import Rectangle


class GeometryProcessor:
    """几何处理器"""
    
    def __init__(self):
        self.boundary_polygon: Optional[Polygon] = None
        self.obstacle_polygons: List[Polygon] = []
        self.valid_area: Optional[Polygon] = None
    
    def process_boundary(self, points: List[Tuple[float, float]]) -> Polygon:
        """
        处理场地边界点，创建多边形
        
        Args:
            points: 边界点列表
            
        Returns:
            边界多边形
        """
        if len(points) < 3:
            raise ValueError("边界点至少需要3个")
        
        # 确保点按逆时针顺序排列
        polygon = Polygon(points)
        if not polygon.is_valid:
            polygon = make_valid(polygon)
        
        # 如果是顺时针，反转
        if polygon.exterior.is_ccw == False:
            points = list(reversed(points))
            polygon = Polygon(points)
        
        self.boundary_polygon = polygon
        return polygon
    
    def add_obstacle(self, center: Tuple[float, float], size: Tuple[float, float]) -> Polygon:
        """
        添加矩形障碍物（如柱子）
        
        Args:
            center: 中心点坐标
            size: (宽度, 高度)
            
        Returns:
            障碍物多边形
        """
        half_width = size[0] / 2
        half_height = size[1] / 2
        
        points = [
            (center[0] - half_width, center[1] - half_height),
            (center[0] + half_width, center[1] - half_height),
            (center[0] + half_width, center[1] + half_height),
            (center[0] - half_width, center[1] + half_height)
        ]
        
        obstacle = Polygon(points)
        self.obstacle_polygons.append(obstacle)
        return obstacle
    
    def add_circular_obstacle(self, center: Tuple[float, float], radius: float) -> Polygon:
        """
        添加圆形障碍物
        
        Args:
            center: 中心点坐标
            radius: 半径
            
        Returns:
            障碍物多边形
        """
        point = Point(center)
        obstacle = point.buffer(radius)
        self.obstacle_polygons.append(obstacle)
        return obstacle
    
    def calculate_valid_area(self, safety_margin: float = 1500) -> Polygon:
        """
        计算有效放置区域（考虑安全距离）
        
        Args:
            safety_margin: 安全边距
            
        Returns:
            有效区域多边形
        """
        if not self.boundary_polygon:
            raise ValueError("边界多边形未设置")
        
        # 向内收缩边界
        valid_area = self.boundary_polygon.buffer(-safety_margin)
        
        # 移除障碍物区域（包括安全边距）
        for obstacle in self.obstacle_polygons:
            expanded_obstacle = obstacle.buffer(safety_margin)
            valid_area = valid_area.difference(expanded_obstacle)
        
        # 确保结果是有效的
        if not valid_area.is_valid:
            valid_area = make_valid(valid_area)
        
        self.valid_area = valid_area
        return valid_area
    
    def point_in_valid_area(self, x: float, y: float) -> bool:
        """检查点是否在有效区域内"""
        if not self.valid_area:
            return False
        
        point = Point(x, y)
        return self.valid_area.contains(point)
    
    def rectangle_in_valid_area(self, rect: Rectangle) -> bool:
        """检查矩形是否完全在有效区域内"""
        if not self.valid_area:
            return False
        
        # 创建矩形多边形
        rect_poly = Polygon([
            (rect.x, rect.y),
            (rect.x + rect.width, rect.y),
            (rect.x + rect.width, rect.y + rect.height),
            (rect.x, rect.y + rect.height)
        ])
        
        return self.valid_area.contains(rect_poly)
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        获取场地的边界框
        
        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not self.boundary_polygon:
            return (0, 0, 0, 0)
        
        bounds = self.boundary_polygon.bounds
        return bounds
    
    def create_grid_points(self, grid_size: float = 100) -> List[Tuple[float, float]]:
        """
        创建网格点用于搜索
        
        Args:
            grid_size: 网格大小（mm）
            
        Returns:
            有效的网格点列表
        """
        if not self.valid_area:
            return []
        
        min_x, min_y, max_x, max_y = self.valid_area.bounds
        
        points = []
        for x in np.arange(min_x, max_x, grid_size):
            for y in np.arange(min_y, max_y, grid_size):
                if self.point_in_valid_area(x, y):
                    points.append((x, y))
        
        return points
    
    def distance_to_boundary(self, x: float, y: float) -> float:
        """计算点到边界的最短距离"""
        if not self.boundary_polygon:
            return float('inf')
        
        point = Point(x, y)
        return self.boundary_polygon.boundary.distance(point)
    
    def distance_to_obstacles(self, x: float, y: float) -> float:
        """计算点到最近障碍物的距离"""
        if not self.obstacle_polygons:
            return float('inf')
        
        point = Point(x, y)
        min_distance = float('inf')
        
        for obstacle in self.obstacle_polygons:
            distance = obstacle.distance(point)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def visualize(self, image_size: Tuple[int, int] = (800, 600)) -> np.ndarray:
        """
        可视化场地布局
        
        Args:
            image_size: 图像大小
            
        Returns:
            图像数组
        """
        # 创建白色背景
        image = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8) * 255
        
        if not self.boundary_polygon:
            return image
        
        # 获取边界框和缩放因子
        min_x, min_y, max_x, max_y = self.boundary_polygon.bounds
        scale_x = (image_size[0] - 40) / (max_x - min_x)
        scale_y = (image_size[1] - 40) / (max_y - min_y)
        scale = min(scale_x, scale_y)
        
        # 转换坐标函数
        def transform_point(x, y):
            px = int((x - min_x) * scale + 20)
            py = int(image_size[1] - ((y - min_y) * scale + 20))
            return (px, py)
        
        # 绘制有效区域
        if self.valid_area:
            if isinstance(self.valid_area, Polygon):
                coords = list(self.valid_area.exterior.coords)
                points = np.array([transform_point(x, y) for x, y in coords], np.int32)
                cv2.fillPoly(image, [points], (240, 240, 240))
            elif isinstance(self.valid_area, MultiPolygon):
                for poly in self.valid_area.geoms:
                    coords = list(poly.exterior.coords)
                    points = np.array([transform_point(x, y) for x, y in coords], np.int32)
                    cv2.fillPoly(image, [points], (240, 240, 240))
        
        # 绘制边界
        coords = list(self.boundary_polygon.exterior.coords)
        points = np.array([transform_point(x, y) for x, y in coords], np.int32)
        cv2.polylines(image, [points], True, (0, 0, 0), 2)
        
        # 绘制障碍物
        for obstacle in self.obstacle_polygons:
            coords = list(obstacle.exterior.coords)
            points = np.array([transform_point(x, y) for x, y in coords], np.int32)
            cv2.fillPoly(image, [points], (100, 100, 100))
            cv2.polylines(image, [points], True, (0, 0, 0), 2)
        
        return image
    
    def export_to_dict(self) -> Dict:
        """导出几何数据为字典格式"""
        data = {
            'boundary': list(self.boundary_polygon.exterior.coords) if self.boundary_polygon else [],
            'obstacles': []
        }
        
        for obstacle in self.obstacle_polygons:
            bounds = obstacle.bounds
            data['obstacles'].append({
                'type': 'rectangle',
                'bounds': bounds,
                'center': ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2),
                'size': (bounds[2] - bounds[0], bounds[3] - bounds[1])
            })
        
        return data


def parse_image_boundary(image_path: str, scale: float = 1.0) -> List[Tuple[float, float]]:
    """
    从图像中解析场地边界
    
    Args:
        image_path: 图像路径
        scale: 比例尺（像素到毫米的转换）
        
    Returns:
        边界点列表
    """
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 二值化
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        raise ValueError("未找到轮廓")
    
    # 找到最大的轮廓（假设是场地边界）
    largest_contour = max(contours, key=cv2.contourArea)
    
    # 简化轮廓
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # 转换为点列表
    points = []
    for point in approx:
        x = point[0][0] * scale
        y = point[0][1] * scale
        points.append((x, y))
    
    return points