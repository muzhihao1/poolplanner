"""
测试1000平米大场地布局
"""

from core.large_field_layout import LargeFieldLayoutGenerator
from core.optimized_layout import OptimizedLayoutGenerator
from core.maxrects import Rectangle
import math

# 配置
config = {
    'wall_distance': 1600,
    'table_distance': 1400,
    'table_width': 2850,
    'table_height': 1550
}

print("=" * 60)
print("1000平米场地布局测试")
print("=" * 60)

# 测试不同形状的1000平米场地

# 场景1: 正方形场地 (31.6m × 31.6m ≈ 1000平米)
print("\n场景1: 正方形场地")
side_length = math.sqrt(1000) * 1000  # 转换为毫米
boundary1 = [
    [0, 0], 
    [side_length, 0], 
    [side_length, side_length], 
    [0, side_length]
]

generator = LargeFieldLayoutGenerator(config)
layout1 = generator.generate_layout(boundary1, [])
print(f"\n正方形场地可放置: {len(layout1)} 个台球桌")

# 场景2: 长方形场地 (40m × 25m = 1000平米)
print("\n\n场景2: 长方形场地 (40m × 25m)")
boundary2 = [
    [0, 0], 
    [40000, 0], 
    [40000, 25000], 
    [0, 25000]
]

layout2 = generator.generate_layout(boundary2, [])
print(f"\n长方形场地可放置: {len(layout2)} 个台球桌")

# 场景3: 带障碍物的场地 (35m × 28.5m ≈ 1000平米，4个柱子)
print("\n\n场景3: 带障碍物的场地 (35m × 28.5m，4个柱子)")
boundary3 = [
    [0, 0], 
    [35000, 0], 
    [35000, 28500], 
    [0, 28500]
]

# 4个结构柱
obstacles = [
    Rectangle(10000, 8000, 600, 600),   # 左上
    Rectangle(25000, 8000, 600, 600),   # 右上
    Rectangle(10000, 20000, 600, 600),  # 左下
    Rectangle(25000, 20000, 600, 600),  # 右下
]

layout3 = generator.generate_layout(boundary3, obstacles)
print(f"\n带障碍物场地可放置: {len(layout3)} 个台球桌")

# 对比普通算法
print("\n\n对比测试：使用普通优化算法处理1000平米场地")
print("-" * 40)
normal_generator = OptimizedLayoutGenerator(config)

# 测试正方形场地
print("正方形场地（普通算法）...")
import time
start_time = time.time()
normal_layout1 = normal_generator.generate_layout(boundary1, [])
end_time = time.time()
print(f"普通算法: {len(normal_layout1)} 个台球桌, 耗时: {end_time - start_time:.1f}秒")

# 测试大场地算法
print("\n正方形场地（大场地算法）...")
start_time = time.time()
large_layout1 = generator.generate_layout(boundary1, [])
end_time = time.time()
print(f"大场地算法: {len(large_layout1)} 个台球桌, 耗时: {end_time - start_time:.1f}秒")

# 建议
print("\n\n布局建议:")
print("1. 对于1000平米的场地，建议使用长方形布局（如40m×25m）")
print("2. 预计可放置100-120个台球桌")
print("3. 建议在场地中适当设置休息区和通道")
print("4. 考虑分区管理，每个区域20-30张台球桌")