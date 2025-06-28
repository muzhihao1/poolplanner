"""
使用实际的布局算法测试不同方向的布局
"""

from core.maxrects import Rectangle
from core.optimized_layout import OptimizedLayoutGenerator
from core.regular_layout import RegularLayoutGenerator

# 场地参数
boundary = [[0, 0], [16300, 0], [16300, 7530], [0, 7530]]
obstacles = []  # 无障碍物

# 测试不同的间距配置
configs = [
    {
        'name': '标准间距 (1600/1400)',
        'wall_distance': 1600,
        'table_distance': 1400,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '紧凑间距 (1200/1200)',
        'wall_distance': 1200,
        'table_distance': 1200,
        'table_width': 2850,
        'table_height': 1550
    },
    {
        'name': '最小间距 (1000/1000)',
        'wall_distance': 1000,
        'table_distance': 1000,
        'table_width': 2850,
        'table_height': 1550
    }
]

print("实际布局算法测试")
print("=" * 60)
print(f"场地: {16.3}m × {7.53}m")
print()

for config in configs:
    print(f"\n{config['name']}:")
    print("-" * 40)
    
    # 测试规则布局（会自动选择最优方向）
    regular_gen = RegularLayoutGenerator(config)
    regular_layout = regular_gen.generate_layout(boundary, obstacles)
    
    print(f"规则布局（自动选择）: {len(regular_layout)} 个台球桌")
    
    # 分析布局方向
    if regular_layout:
        first_table = regular_layout[0]
        if first_table.rotation == 0:
            print("  选择了：横向布局")
        else:
            print("  选择了：纵向布局")
    
    # 测试优化布局
    opt_gen = OptimizedLayoutGenerator(config)
    # 只运行关键策略以加快速度
    
    # 横向布局
    horizontal_layout = opt_gen._try_single_orientation_layout(
        boundary, obstacles, 
        {'boundary': boundary, 'boundary_polygon': None, 'obstacles': obstacles}, 
        0
    )
    print(f"  强制横向: {len(horizontal_layout)} 个")
    
    # 纵向布局
    vertical_layout = opt_gen._try_single_orientation_layout(
        boundary, obstacles,
        {'boundary': boundary, 'boundary_polygon': None, 'obstacles': obstacles},
        90
    )
    print(f"  强制纵向: {len(vertical_layout)} 个")
    
    # 显示布局细节
    if len(horizontal_layout) > 0:
        print(f"\n  横向布局详情:")
        for i, table in enumerate(horizontal_layout[:5]):  # 只显示前5个
            print(f"    台球桌{i+1}: ({table.x:.0f}, {table.y:.0f})")
    
    if len(vertical_layout) > 0:
        print(f"\n  纵向布局详情:")
        for i, table in enumerate(vertical_layout[:5]):  # 只显示前5个
            print(f"    台球桌{i+1}: ({table.x:.0f}, {table.y:.0f})")

# 特殊测试：两排布局的可能性
print("\n\n特殊分析：是否可能放置两排？")
print("-" * 40)

# 检查是否能放两排横向
config = configs[0]  # 使用标准间距
# 两排横向需要的高度: 2 * 1550 + 1400 + 2 * 1600 = 7700mm
required_height_horizontal = 2 * config['table_height'] + config['table_distance'] + 2 * config['wall_distance']
print(f"两排横向需要高度: {required_height_horizontal}mm")
print(f"实际可用高度: {7530}mm")
if required_height_horizontal <= 7530:
    print("✓ 理论上可以放置两排横向台球桌")
else:
    print("× 高度不足，无法放置两排横向台球桌")

# 两排纵向需要的高度: 2 * 2850 + 1400 + 2 * 1600 = 10300mm  
required_height_vertical = 2 * config['table_width'] + config['table_distance'] + 2 * config['wall_distance']
print(f"\n两排纵向需要高度: {required_height_vertical}mm")
print(f"实际可用高度: {7530}mm")
if required_height_vertical <= 7530:
    print("✓ 理论上可以放置两排纵向台球桌")
else:
    print("× 高度不足，无法放置两排纵向台球桌")