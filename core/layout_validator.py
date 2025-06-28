"""
布局验证器 - 验证布局的合理性和质量
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from .maxrects import Rectangle, BilliardTable
from .constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon


class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"      # 基本约束验证
    STANDARD = "standard"  # 标准质量验证
    STRICT = "strict"    # 严格质量验证


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, float]


class LayoutValidator:
    """布局验证器"""
    
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
    
    def validate_layout(self, layout: List[BilliardTable], 
                       boundary: List[Tuple[float, float]], 
                       obstacles: List[Rectangle],
                       level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """验证布局"""
        
        issues = []
        suggestions = []
        metrics = {}
        
        # 创建验证上下文
        context = {
            'boundary': boundary,
            'boundary_polygon': Polygon(boundary),
            'obstacles': obstacles
        }
        
        # 1. 基本约束验证
        constraint_valid, constraint_violations = self.constraint_solver.validate_layout(layout, context)
        
        if not constraint_valid:
            for violation in constraint_violations:
                issues.append(f"约束违反: {violation.description}")
        
        # 2. 计算基本指标
        metrics.update(self._calculate_basic_metrics(layout, boundary))
        
        # 3. 根据验证级别进行额外检查
        if level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            self._validate_layout_quality(layout, boundary, issues, suggestions, metrics)
        
        if level == ValidationLevel.STRICT:
            self._validate_strict_requirements(layout, boundary, issues, suggestions, metrics)
        
        # 4. 计算总体评分
        score = self._calculate_overall_score(layout, boundary, issues, metrics)
        
        # 5. 生成改进建议
        if score < 80:
            suggestions.extend(self._generate_improvement_suggestions(layout, boundary, metrics))
        
        return ValidationResult(
            is_valid=constraint_valid and len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    def _calculate_basic_metrics(self, layout, boundary):
        """计算基本指标"""
        metrics = {}
        
        if not layout:
            return {
                'table_count': 0,
                'space_utilization': 0,
                'density': 0,
                'coverage': 0
            }
        
        # 场地面积
        field_area = self._calculate_polygon_area(boundary)
        
        # 台球桌总面积
        table_area = len(layout) * self.table_width * self.table_height
        
        # 空间利用率
        space_utilization = (table_area / field_area) * 100 if field_area > 0 else 0
        
        # 密度（每100平方米台球桌数量）
        density = len(layout) / (field_area / 1000000) * 100 if field_area > 0 else 0
        
        # 覆盖率（布局边界框与场地的比例）
        coverage = self._calculate_coverage(layout, boundary)
        
        metrics.update({
            'table_count': len(layout),
            'field_area_sqm': field_area / 1000000,
            'table_area_sqm': table_area / 1000000,
            'space_utilization': round(space_utilization, 2),
            'density': round(density, 2),
            'coverage': round(coverage, 2)
        })
        
        return metrics
    
    def _validate_layout_quality(self, layout, boundary, issues, suggestions, metrics):
        """验证布局质量"""
        
        # 1. 检查布局规则性
        regularity = self._check_regularity(layout)
        metrics['regularity'] = round(regularity, 2)
        
        if regularity < 0.7:
            issues.append("布局不够规则，台球桌排列不整齐")
            suggestions.append("建议使用网格对齐布局")
        
        # 2. 检查间距一致性
        spacing_consistency = self._check_spacing_consistency(layout)
        metrics['spacing_consistency'] = round(spacing_consistency, 2)
        
        if spacing_consistency < 0.8:
            issues.append("台球桌间距不一致")
            suggestions.append("调整台球桌位置以保持一致的间距")
        
        # 3. 检查方向一致性
        orientation_consistency = self._check_orientation_consistency(layout)
        metrics['orientation_consistency'] = round(orientation_consistency, 2)
        
        if orientation_consistency < 0.6:
            suggestions.append("考虑统一台球桌方向以提高整体美观度")
        
        # 4. 检查空间浪费
        space_efficiency = self._check_space_efficiency(layout, boundary)
        metrics['space_efficiency'] = round(space_efficiency, 2)
        
        if space_efficiency < 0.6:
            issues.append("存在明显的空间浪费")
            suggestions.append("尝试在空隙区域放置更多台球桌")
    
    def _validate_strict_requirements(self, layout, boundary, issues, suggestions, metrics):
        """严格要求验证"""
        
        # 1. 检查最小数量要求
        min_expected = self._estimate_minimum_tables(boundary)
        if len(layout) < min_expected * 0.8:
            issues.append(f"台球桌数量偏少，预期至少{min_expected}个，实际{len(layout)}个")
        
        # 2. 检查孤立台球桌
        isolated_count = self._count_isolated_tables(layout)
        metrics['isolated_tables'] = isolated_count
        
        if isolated_count > 0:
            issues.append(f"存在{isolated_count}个孤立的台球桌")
            suggestions.append("调整布局以减少孤立台球桌")
        
        # 3. 检查通道宽度
        narrow_passages = self._check_passage_width(layout)
        if narrow_passages > 0:
            issues.append(f"存在{narrow_passages}个过窄的通道")
            suggestions.append("确保通道宽度满足人员通行要求")
    
    def _check_regularity(self, layout):
        """检查布局规则性"""
        if len(layout) < 2:
            return 1.0
        
        # 检查X和Y位置的对齐程度
        x_positions = [t.x for t in layout]
        y_positions = [t.y for t in layout]
        
        x_regularity = self._calculate_position_regularity(x_positions)
        y_regularity = self._calculate_position_regularity(y_positions)
        
        return (x_regularity + y_regularity) / 2
    
    def _calculate_position_regularity(self, positions):
        """计算位置规则性"""
        if len(positions) < 2:
            return 1.0
        
        # 检查是否形成规则的网格
        unique_positions = sorted(set(positions))
        
        if len(unique_positions) < 2:
            return 1.0
        
        # 计算间距的一致性
        gaps = [unique_positions[i+1] - unique_positions[i] for i in range(len(unique_positions)-1)]
        
        if not gaps:
            return 1.0
        
        # 计算间距标准差
        mean_gap = sum(gaps) / len(gaps)
        variance = sum((gap - mean_gap) ** 2 for gap in gaps) / len(gaps)
        std_dev = variance ** 0.5
        
        # 标准差越小，规则性越高
        if mean_gap > 0:
            regularity = max(0, 1 - (std_dev / mean_gap))
        else:
            regularity = 1.0
        
        return regularity
    
    def _check_spacing_consistency(self, layout):
        """检查间距一致性"""
        if len(layout) < 2:
            return 1.0
        
        distances = []
        for i, table1 in enumerate(layout):
            bounds1 = table1.get_bounds()
            for j, table2 in enumerate(layout[i+1:], i+1):
                bounds2 = table2.get_bounds()
                distance = bounds1.distance_to(bounds2)
                if distance < self.table_distance * 3:  # 只考虑相邻的台球桌
                    distances.append(distance)
        
        if not distances:
            return 1.0
        
        # 计算距离的一致性
        mean_distance = sum(distances) / len(distances)
        variance = sum((d - mean_distance) ** 2 for d in distances) / len(distances)
        std_dev = variance ** 0.5
        
        if mean_distance > 0:
            consistency = max(0, 1 - (std_dev / mean_distance))
        else:
            consistency = 1.0
        
        return consistency
    
    def _check_orientation_consistency(self, layout):
        """检查方向一致性"""
        if not layout:
            return 1.0
        
        horizontal_count = sum(1 for t in layout if t.rotation == 0)
        vertical_count = sum(1 for t in layout if t.rotation == 90)
        
        total = len(layout)
        dominant_ratio = max(horizontal_count, vertical_count) / total
        
        return dominant_ratio
    
    def _check_space_efficiency(self, layout, boundary):
        """检查空间效率"""
        if not layout:
            return 0
        
        # 计算布局的凸包面积
        layout_area = self._calculate_layout_convex_hull_area(layout)
        field_area = self._calculate_polygon_area(boundary)
        
        if field_area > 0:
            efficiency = min(1.0, layout_area / field_area)
        else:
            efficiency = 0
        
        return efficiency
    
    def _count_isolated_tables(self, layout):
        """计算孤立台球桌数量"""
        isolated_count = 0
        
        for i, table in enumerate(layout):
            neighbors = 0
            bounds = table.get_bounds()
            
            for j, other in enumerate(layout):
                if i != j:
                    other_bounds = other.get_bounds()
                    distance = bounds.distance_to(other_bounds)
                    
                    # 如果距离小于2倍的标准间距，认为是邻居
                    if distance < self.table_distance * 2.5:
                        neighbors += 1
            
            if neighbors < 1:
                isolated_count += 1
        
        return isolated_count
    
    def _check_passage_width(self, layout):
        """检查通道宽度"""
        # 简化实现：检查台球桌之间的最小距离
        narrow_count = 0
        min_passage_width = 1000  # 最小通道宽度1米
        
        for i, table1 in enumerate(layout):
            bounds1 = table1.get_bounds()
            for j, table2 in enumerate(layout[i+1:], i+1):
                bounds2 = table2.get_bounds()
                distance = bounds1.distance_to(bounds2)
                
                if self.table_distance <= distance < min_passage_width:
                    narrow_count += 1
        
        return narrow_count
    
    def _estimate_minimum_tables(self, boundary):
        """估算最小台球桌数量"""
        field_area = self._calculate_polygon_area(boundary)
        
        # 考虑墙壁距离和台球桌间距的理论最大数量
        effective_area = field_area * 0.6  # 考虑通道和边距，有效利用率60%
        table_area = self.table_width * self.table_height
        
        return int(effective_area / table_area)
    
    def _calculate_polygon_area(self, boundary):
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
    
    def _calculate_coverage(self, layout, boundary):
        """计算覆盖率"""
        if not layout:
            return 0
        
        # 计算布局边界框
        min_x = min(t.x for t in layout)
        max_x = max(t.x + (t.height if t.rotation == 90 else t.width) for t in layout)
        min_y = min(t.y for t in layout)
        max_y = max(t.y + (t.width if t.rotation == 90 else t.height) for t in layout)
        
        layout_area = (max_x - min_x) * (max_y - min_y)
        field_area = self._calculate_polygon_area(boundary)
        
        if field_area > 0:
            coverage = min(1.0, layout_area / field_area)
        else:
            coverage = 0
        
        return coverage
    
    def _calculate_layout_convex_hull_area(self, layout):
        """计算布局凸包面积"""
        if not layout:
            return 0
        
        # 收集所有台球桌的角点
        points = []
        for table in layout:
            bounds = table.get_bounds()
            points.extend([
                (bounds.x, bounds.y),
                (bounds.x + bounds.width, bounds.y),
                (bounds.x + bounds.width, bounds.y + bounds.height),
                (bounds.x, bounds.y + bounds.height)
            ])
        
        # 计算凸包（简化实现：使用边界框）
        if points:
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            
            return (max_x - min_x) * (max_y - min_y)
        
        return 0
    
    def _calculate_overall_score(self, layout, boundary, issues, metrics):
        """计算总体评分"""
        if not layout:
            return 0
        
        # 基础分数（基于台球桌数量）
        base_score = min(50, len(layout) * 5)
        
        # 质量分数
        quality_score = 0
        
        if 'space_utilization' in metrics:
            quality_score += min(20, metrics['space_utilization'])
        
        if 'regularity' in metrics:
            quality_score += metrics['regularity'] * 15
        
        if 'spacing_consistency' in metrics:
            quality_score += metrics['spacing_consistency'] * 10
        
        if 'space_efficiency' in metrics:
            quality_score += metrics['space_efficiency'] * 5
        
        # 扣分（基于问题数量）
        penalty = len(issues) * 5
        
        total_score = max(0, base_score + quality_score - penalty)
        
        return min(100, total_score)
    
    def _generate_improvement_suggestions(self, layout, boundary, metrics):
        """生成改进建议"""
        suggestions = []
        
        if metrics.get('space_utilization', 0) < 15:
            suggestions.append("空间利用率较低，建议增加台球桌数量")
        
        if metrics.get('regularity', 1) < 0.7:
            suggestions.append("布局不够规则，建议使用网格对齐")
        
        if metrics.get('spacing_consistency', 1) < 0.8:
            suggestions.append("间距不一致，建议统一台球桌间距")
        
        if metrics.get('isolated_tables', 0) > 0:
            suggestions.append("存在孤立台球桌，建议调整布局使其更紧凑")
        
        return suggestions