"""
核心算法模块
"""

from .maxrects import Rectangle, BilliardTable, MaxRectsAlgorithm
from .constraints import (
    Constraint, DistanceConstraint, AccessibilityConstraint,
    ConstraintSolver, ConstraintViolation, SpatialIndex
)
from .optimizer import LayoutOptimizer
from .geometry import GeometryProcessor, parse_image_boundary
from .regular_layout import RegularLayoutGenerator
from .optimized_layout import OptimizedLayoutGenerator
from .sequential_layout import SequentialLayoutGenerator
from .obstacle_aware_layout import ObstacleAwareLayoutGenerator
from .exhaustive_layout import ExhaustiveLayoutGenerator

__all__ = [
    # MaxRects
    'Rectangle',
    'BilliardTable', 
    'MaxRectsAlgorithm',
    
    # 约束系统
    'Constraint',
    'DistanceConstraint',
    'AccessibilityConstraint',
    'ConstraintSolver',
    'ConstraintViolation',
    'SpatialIndex',
    
    # 优化器
    'LayoutOptimizer',
    
    # 几何处理
    'GeometryProcessor',
    'parse_image_boundary',
    
    # 布局生成器
    'RegularLayoutGenerator',
    'OptimizedLayoutGenerator',
    'SequentialLayoutGenerator',
    'ObstacleAwareLayoutGenerator',
    'ExhaustiveLayoutGenerator'
]