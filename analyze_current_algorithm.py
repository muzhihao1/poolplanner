#!/usr/bin/env python3
"""
分析当前算法的问题并制定优化方案
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.optimized_layout import OptimizedLayoutGenerator
from core.regular_layout import RegularLayoutGenerator
from core.maxrects import Rectangle
import time

def analyze_current_algorithm():
    """分析当前算法的问题"""
    print("=" * 60)
    print("当前算法问题分析")
    print("=" * 60)
    
    # 测试场地：10m x 15m，2个障碍物
    boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
    obstacles = [
        Rectangle(2800, 4800, 400, 400),  # 障碍物1
        Rectangle(6800, 9800, 400, 400)   # 障碍物2
    ]
    
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550
    }
    
    print(f"测试场地: 10m x 15m")
    print(f"障碍物: 2个")
    print(f"约束: 墙距{config['wall_distance']}mm, 桌距{config['table_distance']}mm")
    
    # 1. 测试规则布局
    print("\n1. 规则布局算法测试:")
    regular_gen = RegularLayoutGenerator(config)
    start_time = time.time()
    regular_layout = regular_gen.generate_layout(boundary, obstacles)
    regular_time = time.time() - start_time
    
    print(f"   结果: {len(regular_layout)} 个台球桌")
    print(f"   用时: {regular_time:.2f} 秒")
    
    # 分析规则布局的问题
    if regular_layout:
        print("   布局分析:")
        horizontal_count = sum(1 for t in regular_layout if t.rotation == 0)
        vertical_count = sum(1 for t in regular_layout if t.rotation == 90)
        print(f"     横向: {horizontal_count} 个")
        print(f"     纵向: {vertical_count} 个")
        
        # 检查是否形成规则网格
        x_positions = sorted(set(t.x for t in regular_layout))
        y_positions = sorted(set(t.y for t in regular_layout))
        print(f"     X位置数: {len(x_positions)} (理想应该是列数)")
        print(f"     Y位置数: {len(y_positions)} (理想应该是行数)")
        
        # 检查间距一致性
        if len(x_positions) > 1:
            x_gaps = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            print(f"     X间距: {x_gaps} (应该一致)")
        if len(y_positions) > 1:
            y_gaps = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
            print(f"     Y间距: {y_gaps} (应该一致)")
    
    # 2. 测试优化布局
    print("\n2. 优化布局算法测试:")
    opt_gen = OptimizedLayoutGenerator(config)
    start_time = time.time()
    opt_layout = opt_gen.generate_layout(boundary, obstacles)
    opt_time = time.time() - start_time
    
    print(f"   结果: {len(opt_layout)} 个台球桌")
    print(f"   用时: {opt_time:.2f} 秒")
    print(f"   提升: +{len(opt_layout) - len(regular_layout)} 个")
    
    # 分析优化布局的问题
    if opt_layout:
        print("   布局分析:")
        horizontal_count = sum(1 for t in opt_layout if t.rotation == 0)
        vertical_count = sum(1 for t in opt_layout if t.rotation == 90)
        print(f"     横向: {horizontal_count} 个")
        print(f"     纵向: {vertical_count} 个")
        
        # 检查布局的整齐度
        x_positions = sorted(set(t.x for t in opt_layout))
        y_positions = sorted(set(t.y for t in opt_layout))
        print(f"     X位置数: {len(x_positions)}")
        print(f"     Y位置数: {len(y_positions)}")
        
        # 检查是否有孤立的台球桌
        isolated_count = 0
        for table in opt_layout:
            neighbors = 0
            for other in opt_layout:
                if table != other:
                    dx = abs(table.x - other.x)
                    dy = abs(table.y - other.y)
                    if (dx < 5000 and dy < 5000):  # 在5m范围内
                        neighbors += 1
            if neighbors < 2:
                isolated_count += 1
        print(f"     孤立台球桌: {isolated_count} 个")
    
    # 3. 问题总结
    print("\n3. 发现的问题:")
    problems = []
    
    if len(regular_layout) < 4:
        problems.append("规则布局数量偏少，可能存在空间浪费")
    
    if len(opt_layout) - len(regular_layout) < 2:
        problems.append("优化算法提升有限，需要更强的搜索策略")
    
    if opt_layout:
        # 检查布局是否过于分散
        x_span = max(t.x for t in opt_layout) - min(t.x for t in opt_layout)
        y_span = max(t.y for t in opt_layout) - min(t.y for t in opt_layout)
        if x_span > 8000 or y_span > 12000:
            problems.append("布局过于分散，不够紧凑")
    
    for i, problem in enumerate(problems, 1):
        print(f"   {i}. {problem}")
    
    return regular_layout, opt_layout, problems

def identify_optimization_targets():
    """确定优化目标"""
    print("\n4. 优化目标:")
    targets = [
        "提高台球桌数量（目标：6-8个）",
        "保持布局整齐（规则网格排列）",
        "减少孤立台球桌",
        "提高空间利用率",
        "优化算法性能"
    ]
    
    for i, target in enumerate(targets, 1):
        print(f"   {i}. {target}")
    
    return targets

if __name__ == "__main__":
    regular_layout, opt_layout, problems = analyze_current_algorithm()
    targets = identify_optimization_targets()
    
    print("\n" + "=" * 60)
    print("分析完成，准备开始优化...")
    print("=" * 60)