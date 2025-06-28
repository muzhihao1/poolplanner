"""
测试放松约束条件后的布局效果
"""

from core.maxrects import Rectangle
from core.optimized_layout import OptimizedLayoutGenerator

# 测试不同的约束配置
test_configs = [
    {
        'name': '标准约束 (1500/1400)',
        'wall_distance': 1500,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '稍微放松 (1200/1200)',
        'wall_distance': 1200,
        'table_distance': 1200,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '中等放松 (1000/1000)',
        'wall_distance': 1000,
        'table_distance': 1000,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '大幅放松 (800/800)',
        'wall_distance': 800,
        'table_distance': 800,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '极限放松 (500/500)',
        'wall_distance': 500,
        'table_distance': 500,
        'table_width': 2850,
        'table_height': 1550
    }
]

boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
obstacles = [
    Rectangle(3000, 4000, 1000, 1000),
    Rectangle(7000, 9000, 1500, 1500)
]

print("测试不同约束条件下的布局效果")
print("=" * 60)

for config in test_configs:
    print(f"\n{config['name']}:")
    print(f"  墙壁距离: {config['wall_distance']}mm")
    print(f"  台球桌间距: {config['table_distance']}mm")
    
    generator = OptimizedLayoutGenerator(config)
    
    # 只运行贪心算法以加快测试
    best_layout = []
    
    # 贪心算法
    layout = generator._try_greedy_layout(boundary, obstacles, {
        'boundary': boundary,
        'boundary_polygon': None,
        'obstacles': obstacles
    })
    
    print(f"  结果: {len(layout)} 个台球桌")
    
    if len(layout) >= 9:
        print("  ✓ 达到或超过用户截图中的9个台球桌!")
        break

print("\n结论:")
print("用户截图中的布局可能使用了更宽松的间距约束")
print("建议：")
print("1. 与用户确认实际的间距要求")
print("2. 在界面上提供间距参数的调整选项")
print("3. 显示当前使用的约束参数")