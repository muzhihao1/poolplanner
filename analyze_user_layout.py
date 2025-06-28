"""
分析用户截图中的布局，理解为什么算法没有找到这些位置
"""

from core.maxrects import Rectangle, BilliardTable
from core.constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon

# 根据用户截图中的布局，估算各台球桌的位置（单位：mm）
# 场地：10m x 15m，障碍物1在(3-4m, 4-5m)，障碍物2在(7-8.5m, 9-10.5m)
user_tables = [
    # 上方一排（3个）
    (2200, 1500, 0, "台球桌1"),    # 左上
    (5200, 1500, 0, "台球桌2"),    # 中上
    (8200, 1500, 0, "台球桌3"),    # 右上
    
    # 中间位置
    (5200, 4400, 0, "台球桌4"),    # 中间
    (8500, 5500, 90, "台球桌5"),   # 右侧纵向
    
    # 左侧纵向
    (1500, 7000, 90, "台球桌6"),   # 左侧纵向
    
    # 右侧纵向
    (9500, 8000, 90, "台球桌7"),   # 右侧纵向
    
    # 下方
    (4500, 10000, 0, "台球桌8"),   # 下方中间
    (7500, 12000, 0, "台球桌9"),   # 下方右侧
]

# 设置参数
wall_distance = 1500
table_distance = 1400
table_width = 2850
table_height = 1550

boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
obstacles = [
    Rectangle(3000, 4000, 1000, 1000),  # 障碍物1
    Rectangle(7000, 9000, 1500, 1500)   # 障碍物2
]

# 创建约束求解器
constraint_solver = ConstraintSolver()
constraint_solver.add_constraint(
    DistanceConstraint(wall_distance, table_distance, wall_distance)
)

# 创建验证上下文
boundary_polygon = Polygon(boundary)
context = {
    'boundary': boundary,
    'boundary_polygon': boundary_polygon,
    'obstacles': obstacles
}

print("分析用户布局中的9个台球桌...")
print("=" * 60)

# 验证每个台球桌
valid_count = 0
invalid_count = 0

for i, (x, y, rotation, name) in enumerate(user_tables):
    table = BilliardTable(x, y, table_width, table_height, rotation)
    
    # 单独验证
    valid, violations = constraint_solver.validate_layout([table], context)
    
    print(f"\n{name} at ({x}, {y}) 旋转{rotation}°:")
    
    if valid:
        print("  ✓ 单独放置有效")
        valid_count += 1
    else:
        print("  × 单独放置无效")
        if violations:
            for v in violations:
                print(f"    - {v}")
        invalid_count += 1
    
    # 计算关键距离
    if rotation == 0:
        width, height = table_width, table_height
    else:
        width, height = table_height, table_width
    
    # 墙壁距离
    print(f"  墙壁距离: 左={x}mm, 右={10000-x-width}mm, 上={y}mm, 下={15000-y-height}mm")
    
    # 障碍物距离
    for j, obs in enumerate(obstacles):
        # 简化距离计算
        dx = max(0, max(obs.x - (x + width), x - (obs.x + obs.width)))
        dy = max(0, max(obs.y - (y + height), y - (obs.y + obs.height)))
        dist = (dx*dx + dy*dy)**0.5
        print(f"  距障碍物{j+1}: {dist:.0f}mm")

print(f"\n单独验证结果: {valid_count}个有效, {invalid_count}个无效")

# 验证整体布局
print("\n验证整体布局...")
all_tables = []
for x, y, rotation, name in user_tables:
    all_tables.append(BilliardTable(x, y, table_width, table_height, rotation))

valid, violations = constraint_solver.validate_layout(all_tables, context)

if valid:
    print("✓ 整体布局有效!")
else:
    print("× 整体布局无效")
    print(f"发现 {len(violations)} 个冲突:")
    for v in violations[:10]:  # 只显示前10个
        print(f"  - {v}")

# 分析为什么算法没有找到这个布局
print("\n分析结论:")
print("1. 用户布局中台球桌的间距可能略小于1400mm的要求")
print("2. 算法的扫描步长可能太大，错过了一些可行位置")
print("3. 算法可能过早放弃了某些看似不可行但实际可行的区域")