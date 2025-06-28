"""
分析底部空间是否可以再放置台球桌
"""

from core.maxrects import Rectangle, BilliardTable
from core.constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon

# 根据截图估算的台球桌位置
existing_tables = [
    BilliardTable(4300, 2600, 2850, 1550, 0),    # 台球桌1
    BilliardTable(11000, 2800, 2850, 1550, 90),  # 台球桌2 (纵向)
    BilliardTable(9000, 6000, 1550, 2850, 90),   # 台球桌3 (纵向)
    BilliardTable(2300, 6500, 2850, 1550, 0),    # 台球桌4
    BilliardTable(5800, 7000, 1550, 2850, 90),   # 台球桌5 (纵向)
    BilliardTable(11500, 8500, 1550, 2850, 90),  # 台球桌6 (纵向)
]

# 障碍物位置
obstacles = [
    Rectangle(3500, 5000, 1000, 1000),    # 左侧障碍物
    Rectangle(10000, 6500, 1500, 1500),   # 右侧障碍物
]

# 场地边界 17.7m x ?m (根据截图推测高度约13m)
boundary = [[0, 0], [17700, 0], [17700, 13000], [0, 13000]]

# 设置参数
config = {
    'wall_distance': 1200,    # 使用较宽松的间距
    'table_distance': 1200,
    'table_width': 2850,
    'table_height': 1550
}

# 创建约束求解器
constraint_solver = ConstraintSolver()
constraint_solver.add_constraint(
    DistanceConstraint(config['wall_distance'], config['table_distance'], config['wall_distance'])
)

# 创建验证上下文
boundary_polygon = Polygon(boundary)
context = {
    'boundary': boundary,
    'boundary_polygon': boundary_polygon,
    'obstacles': obstacles
}

print("分析底部空间...")
print("=" * 60)

# 计算每个台球桌到底部墙壁的距离
print("\n现有台球桌到底部墙壁的距离：")
for i, table in enumerate(existing_tables):
    if table.rotation == 0:
        bottom_y = table.y + table.height
    else:
        bottom_y = table.y + table.width
    
    dist_to_bottom = 13000 - bottom_y
    print(f"台球桌{i+1}: 距底部 {dist_to_bottom:.0f}mm ({dist_to_bottom/1000:.2f}m)")

# 测试在底部是否可以放置新的台球桌
print("\n\n测试底部可放置位置：")
test_positions = [
    # 底部左侧
    (2000, 10500, 0, "底部左侧横向"),
    (2000, 10000, 0, "底部左侧横向(上移)"),
    (2000, 10500, 90, "底部左侧纵向"),
    
    # 底部中间
    (6000, 10500, 0, "底部中间横向"),
    (6000, 10000, 0, "底部中间横向(上移)"),
    (7000, 10500, 0, "底部中间横向(右移)"),
    
    # 底部右侧
    (12000, 10500, 0, "底部右侧横向"),
    (13000, 10000, 0, "底部右侧横向(右移)"),
    (14000, 10500, 90, "底部右侧纵向"),
]

successful_positions = []

for x, y, rotation, desc in test_positions:
    table = BilliardTable(x, y, config['table_width'], config['table_height'], rotation)
    
    # 检查边界
    if rotation == 0:
        width, height = config['table_width'], config['table_height']
    else:
        width, height = config['table_height'], config['table_width']
    
    if x + width > 17700 - config['wall_distance'] or y + height > 13000 - config['wall_distance']:
        print(f"× {desc} at ({x}, {y}) - 超出边界")
        continue
    
    # 验证约束
    temp_layout = existing_tables + [table]
    valid, violations = constraint_solver.validate_layout(temp_layout, context)
    
    if valid:
        print(f"✓ {desc} at ({x}, {y}) - 可以放置!")
        successful_positions.append((x, y, rotation, desc))
    else:
        # 分析冲突原因
        conflict_info = []
        if violations:
            for v in violations:
                if hasattr(v, 'table1_id') and hasattr(v, 'table2_id'):
                    if v.table2_id < len(existing_tables):
                        conflict_info.append(f"与台球桌{v.table2_id+1}距离太近")
                else:
                    conflict_info.append(str(v))
        print(f"× {desc} at ({x}, {y}) - {', '.join(conflict_info[:2])}")

print(f"\n\n总结：")
print(f"底部可以再放置 {len(successful_positions)} 个台球桌")
if successful_positions:
    print("\n建议位置：")
    for x, y, rotation, desc in successful_positions[:3]:  # 只显示前3个
        print(f"- {desc} at ({x:.0f}, {y:.0f})")

# 分析距离标注问题
print("\n\n距离标注分析：")
print("底部的距离标注（1.20m, 1.30m, 1.35m, 1.50m）可能是：")
print("1. 台球桌4到底部墙壁的距离")
print("2. 台球桌5到底部墙壁的距离")
print("3. 但缺少连线，导致不清楚具体对应关系")
print("\n建议修复：")
print("- 确保每个距离标注都有明确的连线")
print("- 避免在同一区域显示过多距离标注")
print("- 优先显示最重要的距离（如最近的墙壁距离）")