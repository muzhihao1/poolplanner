#!/usr/bin/env python3
"""
调试布局问题 - 为什么只使用单列
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import LayoutOptimizer, Rectangle

def test_layout():
    """测试10x15米场地的布局"""
    # 配置
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550,
        'grid_size': 100,
        'use_regular_layout': True,
        'layout_mode': 'auto'
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
        Rectangle(3000 - 200, 5000 - 200, 400, 400),  # 第一个柱子
        Rectangle(7000 - 200, 10000 - 200, 400, 400)  # 第二个柱子
    ]
    
    print("场地配置:")
    print(f"  场地尺寸: 10m x 15m")
    print(f"  障碍物1: 中心({3000}, {5000}), 尺寸 400x400")
    print(f"  障碍物2: 中心({7000}, {10000}), 尺寸 400x400")
    print(f"  墙壁距离: {config['wall_distance']}mm")
    print(f"  台球桌间距: {config['table_distance']}mm")
    print(f"  台球桌尺寸: {config['table_width']}x{config['table_height']}mm")
    
    # 计算可用空间
    usable_width = 10000 - 2 * 1500  # 7000mm
    usable_height = 15000 - 2 * 1500  # 12000mm
    print(f"\n可用空间: {usable_width}mm x {usable_height}mm")
    
    # 理论最大数量（不考虑障碍物）
    cols_max = int((usable_width + 1400) / (2850 + 1400))
    rows_max = int((usable_height + 1400) / (1550 + 1400))
    print(f"理论最大布局: {cols_max}列 x {rows_max}行 = {cols_max * rows_max}个台球桌")
    
    # 创建优化器
    optimizer = LayoutOptimizer(config)
    
    # 执行优化
    result = optimizer.optimize(boundary, obstacles, use_regular_layout=True)
    
    print(f"\n实际布局结果: {result['count']}个台球桌")
    print("\n台球桌位置:")
    for i, table in enumerate(result['tables']):
        print(f"  台球桌{i+1}: 位置({table.x:.0f}, {table.y:.0f}), 旋转{table.rotation}度")
    
    # 分析为什么没有使用更多列
    print("\n分析:")
    print("检查第二列的可能位置...")
    x_col2 = 1500 + 2850 + 1400  # 第二列的x坐标
    print(f"第二列x坐标: {x_col2}")
    
    # 检查第二列是否会与障碍物冲突
    for obs_idx, obs in enumerate(obstacles):
        obs_left = obs.x
        obs_right = obs.x + obs.width
        table_right = x_col2 + 2850
        
        print(f"\n障碍物{obs_idx+1}:")
        print(f"  障碍物范围: x=[{obs_left}, {obs_right}]")
        print(f"  第二列台球桌范围: x=[{x_col2}, {table_right}]")
        
        # 检查是否重叠
        if table_right + 1500 > obs_left and x_col2 - 1500 < obs_right:
            print(f"  -> 会与障碍物冲突（需要1500mm安全距离）")
        else:
            print(f"  -> 不会冲突")

if __name__ == "__main__":
    test_layout()