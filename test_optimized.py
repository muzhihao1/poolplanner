#!/usr/bin/env python3
"""
测试优化布局算法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import LayoutOptimizer, Rectangle

def test_optimized_layout():
    """测试优化布局"""
    # 配置
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550,
        'grid_size': 100,
        'use_regular_layout': True,
        'optimize_count': True  # 启用优化
    }
    
    # 10m x 15m 的矩形场地
    boundary = [
        [0, 0],
        [10000, 0],
        [10000, 15000],
        [0, 15000]
    ]
    
    # 两个柱子
    obstacles = [
        Rectangle(2800, 4800, 400, 400),  # 第一个柱子
        Rectangle(6800, 9800, 400, 400)   # 第二个柱子
    ]
    
    print("=== 测试优化布局算法 ===")
    print(f"场地: 10m x 15m")
    print(f"障碍物: 2个")
    print(f"目标: 最大化台球桌数量")
    print()
    
    # 创建优化器
    optimizer = LayoutOptimizer(config)
    
    # 执行优化
    result = optimizer.optimize(boundary, obstacles, use_regular_layout=True)
    
    print(f"\n优化结果: {result['count']}个台球桌")
    print("\n台球桌位置:")
    for i, table in enumerate(result['tables']):
        rotation_str = "横向" if table.rotation == 0 else "纵向"
        print(f"  台球桌{i+1}: ({table.x:.0f}, {table.y:.0f}) - {rotation_str}")

if __name__ == "__main__":
    test_optimized_layout()