#!/usr/bin/env python3
"""
详细调试网格布局
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import Rectangle, BilliardTable
from core.regular_layout import RegularLayoutGenerator

def test_grid_placement():
    """测试网格放置逻辑"""
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550
    }
    
    boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
    obstacles = [
        Rectangle(2800, 4800, 400, 400),  # 第一个柱子
        Rectangle(6800, 9800, 400, 400)   # 第二个柱子
    ]
    
    generator = RegularLayoutGenerator(config)
    
    # 手动测试能否在第二列放置台球桌
    print("测试第二列的可行位置:")
    
    x_col2 = 1500 + 2850 + 1400  # 5750
    table_width = 2850
    table_height = 1550
    
    # 测试第二列的各个y位置
    y_positions = [1500, 4450, 6750, 9700, 12650]
    
    for y in y_positions:
        if y + table_height > 13500:
            print(f"\ny={y}: 超出边界")
            continue
            
        table = BilliardTable(x_col2, y, table_width, table_height, 0)
        table_bounds = table.get_bounds()
        
        print(f"\ny={y}:")
        print(f"  台球桌范围: ({table_bounds.x}, {table_bounds.y}) - ({table_bounds.x + table_bounds.width}, {table_bounds.y + table_bounds.height})")
        
        # 检查与障碍物的距离
        valid = True
        for i, obs in enumerate(obstacles):
            dist = table_bounds.distance_to(obs)
            print(f"  距离障碍物{i+1}: {dist:.0f}mm", end="")
            if dist < 1500:
                print(" -> 冲突!")
                valid = False
            else:
                print(" -> OK")
        
        if valid:
            print(f"  -> 可以放置!")
    
    # 运行实际的布局算法看看结果
    print("\n\n运行规则布局算法:")
    layout = generator._generate_regular_grid(boundary, obstacles, 0)
    
    print(f"\n布局结果: {len(layout)}个台球桌")
    for i, table in enumerate(layout):
        print(f"  台球桌{i+1}: ({table.x}, {table.y})")

if __name__ == "__main__":
    test_grid_placement()