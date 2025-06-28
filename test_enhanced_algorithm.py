#!/usr/bin/env python3
"""
测试增强布局算法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_layout import EnhancedLayoutGenerator
from core.optimized_layout import OptimizedLayoutGenerator
from core.regular_layout import RegularLayoutGenerator
from core.maxrects import Rectangle
import time

def test_enhanced_vs_original():
    """对比增强算法与原算法"""
    print("=" * 60)
    print("增强算法 vs 原算法对比测试")
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
    
    # 1. 测试规则布局（基准）
    print("\n1. 规则布局算法（基准）:")
    regular_gen = RegularLayoutGenerator(config)
    start_time = time.time()
    regular_layout = regular_gen.generate_layout(boundary, obstacles)
    regular_time = time.time() - start_time
    
    print(f"   结果: {len(regular_layout)} 个台球桌")
    print(f"   用时: {regular_time:.2f} 秒")
    
    # 2. 测试原优化算法
    print("\n2. 原优化算法:")
    opt_gen = OptimizedLayoutGenerator(config)
    start_time = time.time()
    opt_layout = opt_gen.generate_layout(boundary, obstacles)
    opt_time = time.time() - start_time
    
    print(f"   结果: {len(opt_layout)} 个台球桌")
    print(f"   用时: {opt_time:.2f} 秒")
    print(f"   vs基准: +{len(opt_layout) - len(regular_layout)} 个")
    
    # 3. 测试增强算法
    print("\n3. 增强算法:")
    enhanced_gen = EnhancedLayoutGenerator(config)
    start_time = time.time()
    enhanced_layout = enhanced_gen.generate_layout(boundary, obstacles)
    enhanced_time = time.time() - start_time
    
    print(f"   结果: {len(enhanced_layout)} 个台球桌")
    print(f"   用时: {enhanced_time:.2f} 秒")
    print(f"   vs基准: +{len(enhanced_layout) - len(regular_layout)} 个")
    print(f"   vs原优化: +{len(enhanced_layout) - len(opt_layout)} 个")
    
    # 4. 分析最佳布局
    best_layout = enhanced_layout if len(enhanced_layout) >= len(opt_layout) else opt_layout
    best_name = "增强算法" if len(enhanced_layout) >= len(opt_layout) else "原优化算法"
    
    print(f"\n4. 最佳布局分析 ({best_name}):")
    if best_layout:
        print("   台球桌位置:")
        for i, table in enumerate(best_layout):
            orientation = "横向" if table.rotation == 0 else "纵向"
            print(f"     台球桌{i+1}: ({table.x:.0f}, {table.y:.0f}) - {orientation}")
        
        # 分析布局质量
        horizontal_count = sum(1 for t in best_layout if t.rotation == 0)
        vertical_count = sum(1 for t in best_layout if t.rotation == 90)
        print(f"\n   布局统计:")
        print(f"     横向: {horizontal_count} 个")
        print(f"     纵向: {vertical_count} 个")
        
        # 检查规则性
        x_positions = sorted(set(t.x for t in best_layout))
        y_positions = sorted(set(t.y for t in best_layout))
        print(f"     X位置数: {len(x_positions)}")
        print(f"     Y位置数: {len(y_positions)}")
        
        # 计算空间利用率
        table_area = len(best_layout) * 2.85 * 1.55  # 平方米
        field_area = 10 * 15  # 平方米
        utilization = (table_area / field_area) * 100
        print(f"     空间利用率: {utilization:.1f}%")
    
    return regular_layout, opt_layout, enhanced_layout

def test_multiple_scenarios():
    """测试多种场景"""
    print("\n" + "=" * 60)
    print("多场景测试")
    print("=" * 60)
    
    scenarios = [
        {
            'name': '小场地无障碍',
            'boundary': [[0, 0], [8000, 0], [8000, 12000], [0, 12000]],
            'obstacles': []
        },
        {
            'name': '中场地单障碍',
            'boundary': [[0, 0], [10000, 0], [10000, 15000], [0, 15000]],
            'obstacles': [Rectangle(5000, 7500, 600, 600)]
        },
        {
            'name': '大场地多障碍',
            'boundary': [[0, 0], [15000, 0], [15000, 20000], [0, 20000]],
            'obstacles': [
                Rectangle(3000, 5000, 500, 500),
                Rectangle(7500, 10000, 400, 400),
                Rectangle(12000, 15000, 600, 600)
            ]
        }
    ]
    
    config = {
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550
    }
    
    results = []
    
    for scenario in scenarios:
        print(f"\n场景: {scenario['name']}")
        print("-" * 30)
        
        # 测试增强算法
        enhanced_gen = EnhancedLayoutGenerator(config)
        enhanced_layout = enhanced_gen.generate_layout(scenario['boundary'], scenario['obstacles'])
        
        # 测试原算法
        opt_gen = OptimizedLayoutGenerator(config)
        opt_layout = opt_gen.generate_layout(scenario['boundary'], scenario['obstacles'])
        
        improvement = len(enhanced_layout) - len(opt_layout)
        
        print(f"原算法: {len(opt_layout)} 个台球桌")
        print(f"增强算法: {len(enhanced_layout)} 个台球桌")
        print(f"改进: {improvement:+d} 个")
        
        results.append({
            'scenario': scenario['name'],
            'original': len(opt_layout),
            'enhanced': len(enhanced_layout),
            'improvement': improvement
        })
    
    # 总结
    print(f"\n总结:")
    total_improvement = sum(r['improvement'] for r in results)
    avg_improvement = total_improvement / len(results)
    print(f"平均改进: {avg_improvement:.1f} 个台球桌")
    print(f"总体改进: {total_improvement} 个台球桌")
    
    return results

if __name__ == "__main__":
    # 主要对比测试
    regular, original, enhanced = test_enhanced_vs_original()
    
    # 多场景测试
    scenario_results = test_multiple_scenarios()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)