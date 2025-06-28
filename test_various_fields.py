#!/usr/bin/env python3
"""
测试不同场地尺寸的优化布局
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import LayoutOptimizer, Rectangle

def test_field(name, width, height, obstacles=[]):
    """测试单个场地"""
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550,
        'grid_size': 100,
        'use_regular_layout': True,
        'optimize_count': True
    }
    
    boundary = [
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ]
    
    optimizer = LayoutOptimizer(config)
    
    # 测试普通布局
    config['optimize_count'] = False
    result_regular = optimizer.optimize(boundary, obstacles, use_regular_layout=True)
    
    # 测试优化布局
    config['optimize_count'] = True
    optimizer.config = config
    result_optimized = optimizer.optimize(boundary, obstacles, use_regular_layout=True)
    
    print(f"\n{name} ({width/1000:.0f}m x {height/1000:.0f}m):")
    print(f"  普通布局: {result_regular['count']}个台球桌")
    print(f"  优化布局: {result_optimized['count']}个台球桌")
    print(f"  提升: +{result_optimized['count'] - result_regular['count']}个 ({(result_optimized['count'] - result_regular['count'])/result_regular['count']*100:.0f}%)")
    
    return result_optimized['count'] - result_regular['count']

def main():
    print("=== 测试不同场地尺寸的布局优化效果 ===")
    
    improvements = []
    
    # 测试1: 小场地 (8x12m)
    improvements.append(test_field("小场地", 8000, 12000))
    
    # 测试2: 中等场地 (10x15m) 无障碍物
    improvements.append(test_field("中等场地(无障碍)", 10000, 15000))
    
    # 测试3: 中等场地 (10x15m) 有障碍物
    obstacles = [
        Rectangle(2800, 4800, 400, 400),
        Rectangle(6800, 9800, 400, 400)
    ]
    improvements.append(test_field("中等场地(有障碍)", 10000, 15000, obstacles))
    
    # 测试4: 大场地 (15x20m)
    improvements.append(test_field("大场地", 15000, 20000))
    
    # 测试5: 大场地 (15x20m) 多障碍物
    obstacles = [
        Rectangle(3000, 3000, 500, 500),
        Rectangle(7500, 5000, 400, 400),
        Rectangle(12000, 8000, 600, 600),
        Rectangle(5000, 15000, 500, 500)
    ]
    improvements.append(test_field("大场地(多障碍)", 15000, 20000, obstacles))
    
    # 测试6: 长条形场地 (6x20m)
    improvements.append(test_field("长条形场地", 6000, 20000))
    
    # 测试7: 方形场地 (12x12m)
    improvements.append(test_field("方形场地", 12000, 12000))
    
    # 测试8: L形场地（模拟）- 用矩形+障碍物模拟
    obstacles = [
        Rectangle(8000, 0, 7000, 8000)  # 遮挡右上角
    ]
    improvements.append(test_field("L形场地", 15000, 15000, obstacles))
    
    print("\n=== 总结 ===")
    avg_improvement = sum(improvements) / len(improvements)
    print(f"平均提升: {avg_improvement:.1f}个台球桌")
    print(f"最大提升: {max(improvements)}个台球桌")
    print(f"最小提升: {min(improvements)}个台球桌")

if __name__ == "__main__":
    main()