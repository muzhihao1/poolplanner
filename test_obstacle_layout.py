"""
测试障碍物布局
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

# 场地边界 (10.46m x 9.94m)
boundary = [[0, 0], [10460, 0], [10460, 9940], [0, 9940]]

# 障碍物（从截图推测）
# 上方中间有一个障碍物，下方中间有一个障碍物
obstacles = [
    Rectangle(5000, 2000, 400, 400),  # 上方障碍物
    Rectangle(5000, 6500, 400, 400)   # 下方障碍物
]

# 生成布局
generator = OptimizedLayoutGenerator(config)
layout = generator.generate_layout(boundary, obstacles)

print(f"\n生成了 {len(layout)} 个台球桌")
for i, table in enumerate(layout):
    print(f"台球桌 {i+1}: ({table.x}, {table.y}) - {'横向' if table.rotation == 0 else '纵向'}")