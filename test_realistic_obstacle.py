"""
基于实际截图的障碍物布局测试
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

# 场地边界 (看起来像是一个更大的场地)
boundary = [[0, 0], [16000, 0], [16000, 12000], [0, 12000]]

# 障碍物（两个小障碍物在中间区域）
obstacles = [
    Rectangle(7800, 3000, 400, 400),  # 上方中间
    Rectangle(7800, 8000, 400, 400)   # 下方中间
]

print("测试更真实的障碍物布局")
print("场地: 16m × 12m")
print(f"障碍物: {len(obstacles)} 个")

# 生成布局
generator = OptimizedLayoutGenerator(config)
layout = generator.generate_layout(boundary, obstacles)

print(f"\n最终生成了 {len(layout)} 个台球桌")

# 分析布局分布
horizontal = sum(1 for t in layout if t.rotation == 0)
vertical = sum(1 for t in layout if t.rotation == 90)
print(f"横向: {horizontal} 个")
print(f"纵向: {vertical} 个")

# 按区域分析
top_area = [t for t in layout if t.y < 3000]
middle_area = [t for t in layout if 3000 <= t.y < 8000]
bottom_area = [t for t in layout if t.y >= 8000]

print(f"\n区域分布:")
print(f"上方区域: {len(top_area)} 个")
print(f"中间区域: {len(middle_area)} 个")
print(f"下方区域: {len(bottom_area)} 个")