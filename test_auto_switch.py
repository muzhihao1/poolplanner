"""
测试自动切换算法功能
"""

from core.optimized_layout import OptimizedLayoutGenerator
from core.maxrects import Rectangle

# 配置
config = {
    'wall_distance': 1600,
    'table_distance': 1400,
    'table_width': 2850,
    'table_height': 1550
}

print("测试自动算法切换功能")
print("=" * 60)

generator = OptimizedLayoutGenerator(config)

# 测试1: 小场地 (10m × 10m = 100平米)
print("\n测试1: 小场地 (10m × 10m = 100平米)")
small_boundary = [[0, 0], [10000, 0], [10000, 10000], [0, 10000]]
layout1 = generator.generate_layout(small_boundary, [])
print(f"结果: {len(layout1)} 个台球桌")

# 测试2: 中等场地 (20m × 15m = 300平米)
print("\n\n测试2: 中等场地 (20m × 15m = 300平米)")
medium_boundary = [[0, 0], [20000, 0], [20000, 15000], [0, 15000]]
layout2 = generator.generate_layout(medium_boundary, [])
print(f"结果: {len(layout2)} 个台球桌")

# 测试3: 大场地 (30m × 20m = 600平米)
print("\n\n测试3: 大场地 (30m × 20m = 600平米)")
large_boundary = [[0, 0], [30000, 0], [30000, 20000], [0, 20000]]
layout3 = generator.generate_layout(large_boundary, [])
print(f"结果: {len(layout3)} 个台球桌")

# 测试4: 超大场地 (50m × 30m = 1500平米)
print("\n\n测试4: 超大场地 (50m × 30m = 1500平米)")
xlarge_boundary = [[0, 0], [50000, 0], [50000, 30000], [0, 30000]]
layout4 = generator.generate_layout(xlarge_boundary, [])
print(f"结果: {len(layout4)} 个台球桌")

print("\n\n总结:")
print("- 100平米场地: 适合放置10-15个台球桌")
print("- 300平米场地: 适合放置30-40个台球桌")
print("- 600平米场地: 适合放置60-80个台球桌（使用大场地算法）")
print("- 1500平米场地: 适合放置150-200个台球桌（使用大场地算法）")