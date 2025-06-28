"""
分析空余空间，找出可以放置更多台球桌的位置
"""

from core.maxrects import Rectangle, BilliardTable
from core.constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon

# 设置参数
wall_distance = 1500
table_distance = 1400
table_width = 2850
table_height = 1550

boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
obstacles = [
    Rectangle(3000, 4000, 1000, 1000),  # 第一个障碍物
    Rectangle(7000, 9000, 1500, 1500)   # 第二个障碍物  
]

# 当前布局（来自优化结果）
current_tables = [
    BilliardTable(5200, 1500, table_width, table_height, 0),   # 台球桌1
    BilliardTable(5500, 4450, table_width, table_height, 0),   # 台球桌2
    BilliardTable(1500, 6500, table_width, table_height, 90),  # 台球桌3
    BilliardTable(3950, 10450, table_width, table_height, 90)  # 台球桌4
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

print("当前布局分析:")
print(f"已放置 {len(current_tables)} 个台球桌\n")

# 分析潜在位置
potential_positions = [
    # 左上角区域
    (1500, 1500, 0, "左上角横向"),
    (1500, 1500, 90, "左上角纵向"),
    
    # 右侧区域（障碍物1右侧）
    (6000, 4000, 0, "障碍物1右侧横向"),
    (6000, 4000, 90, "障碍物1右侧纵向"),
    
    # 底部区域
    (1500, 12000, 0, "底部左侧横向"),
    (1500, 12000, 90, "底部左侧纵向"),
    (7000, 12000, 0, "底部右侧横向"),
    (7000, 12000, 90, "底部右侧纵向"),
    
    # 左侧区域
    (1500, 3000, 0, "左侧中部横向"),
    (1500, 3000, 90, "左侧中部纵向"),
    
    # 右上角
    (7500, 1500, 0, "右上角横向"),
    (7500, 1500, 90, "右上角纵向"),
]

print("测试潜在位置:")
successful_positions = []

for x, y, rotation, description in potential_positions:
    # 创建测试台球桌
    test_table = BilliardTable(x, y, table_width, table_height, rotation)
    
    # 检查是否超出边界
    if rotation == 0:
        width, height = table_width, table_height
    else:
        width, height = table_height, table_width
    
    if x + width > 10000 - wall_distance or y + height > 15000 - wall_distance:
        print(f"× {description} at ({x}, {y}) - 超出边界")
        continue
    
    # 验证约束
    temp_layout = current_tables + [test_table]
    valid, violations = constraint_solver.validate_layout(temp_layout, context)
    
    if valid:
        print(f"✓ {description} at ({x}, {y}) - 可以放置!")
        successful_positions.append((x, y, rotation, description))
    else:
        # 分析冲突原因
        if violations:
            conflict_info = []
            for v in violations:
                if hasattr(v, 'table1_id') and hasattr(v, 'table2_id'):
                    if v.table2_id < len(current_tables):
                        conflict_info.append(f"与台球桌{v.table2_id+1}冲突")
                    else:
                        conflict_info.append("与障碍物冲突")
            print(f"× {description} at ({x}, {y}) - {', '.join(conflict_info)}")
        else:
            print(f"× {description} at ({x}, {y}) - 约束冲突")

print(f"\n总结:")
print(f"当前已放置: {len(current_tables)} 个台球桌")
print(f"找到额外可放置位置: {len(successful_positions)} 个")
print(f"理论最大数量: {len(current_tables) + len(successful_positions)} 个台球桌")

if successful_positions:
    print("\n建议添加的台球桌:")
    for i, (x, y, rotation, desc) in enumerate(successful_positions):
        print(f"{i+1}. {desc} at ({x}, {y})")