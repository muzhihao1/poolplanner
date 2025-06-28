#!/usr/bin/env python3
"""
测试改进后的优化算法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import LayoutOptimizer, Rectangle

def test_improved_layout():
    """测试改进后的布局算法"""
    # 配置
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550,
        'grid_size': 100,
        'use_regular_layout': True,
        'optimize_count': True
    }
    
    # 10m x 15m 的矩形场地
    boundary = [
        [0, 0],
        [10000, 0],
        [10000, 15000],
        [0, 15000]
    ]
    
    # 两个柱子（与图片中相同的位置）
    obstacles = [
        Rectangle(2800, 4800, 400, 400),  # 第一个柱子
        Rectangle(6800, 9800, 400, 400)   # 第二个柱子
    ]
    
    print("=== 测试改进后的优化布局算法 ===")
    print(f"场地: 10m x 15m")
    print(f"障碍物: 2个")
    print(f"柱子1: 中心(3000, 5000)")
    print(f"柱子2: 中心(7000, 10000)")
    print()
    
    # 创建优化器
    optimizer = LayoutOptimizer(config)
    
    # 执行优化
    result = optimizer.optimize(boundary, obstacles, use_regular_layout=True)
    
    print(f"\n最终结果: {result['count']}个台球桌")
    print("\n台球桌详细位置:")
    for i, table in enumerate(result['tables']):
        rotation_str = "横向" if table.rotation == 0 else "纵向"
        bounds = table.get_bounds()
        print(f"  台球桌{i+1}:")
        print(f"    位置: ({table.x:.0f}, {table.y:.0f})")
        print(f"    方向: {rotation_str}")
        print(f"    边界: ({bounds.x:.0f}, {bounds.y:.0f}) - ({bounds.x + bounds.width:.0f}, {bounds.y + bounds.height:.0f})")
        
        # 检查与墙的距离
        min_wall_dist = min(
            bounds.x,  # 到左墙
            bounds.y,  # 到上墙
            10000 - (bounds.x + bounds.width),  # 到右墙
            15000 - (bounds.y + bounds.height)  # 到下墙
        )
        print(f"    最近墙距: {min_wall_dist:.0f}mm")
        
        # 检查与障碍物的距离
        for j, obs in enumerate(obstacles):
            dist = bounds.distance_to(obs)
            print(f"    到障碍物{j+1}距离: {dist:.0f}mm")

if __name__ == "__main__":
    test_improved_layout()