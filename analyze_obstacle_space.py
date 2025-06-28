"""
分析有障碍物时的可用空间
"""

# 场地尺寸
field_width = 10460  # 10.46m
field_height = 9940  # 9.94m

# 台球桌尺寸
table_width = 2850   # 2.85m
table_height = 1550  # 1.55m

# 间距要求
wall_distance = 1600  # 1.6m
table_distance = 1400 # 1.4m

# 障碍物（假设在中间位置）
obstacle_width = 400
obstacle_height = 400
obstacle1_x = (field_width - obstacle_width) / 2  # 中心X
obstacle1_y = 2000  # 上方
obstacle2_x = (field_width - obstacle_width) / 2  # 中心X
obstacle2_y = 6500  # 下方

print("场地分析（有障碍物）")
print("=" * 50)
print(f"场地尺寸: {field_width/1000:.2f}m × {field_height/1000:.2f}m")
print(f"障碍物1位置: ({obstacle1_x/1000:.2f}m, {obstacle1_y/1000:.2f}m)")
print(f"障碍物2位置: ({obstacle2_x/1000:.2f}m, {obstacle2_y/1000:.2f}m)")

# 计算障碍物影响区域
obs1_left = obstacle1_x - wall_distance
obs1_right = obstacle1_x + obstacle_width + wall_distance
obs1_top = obstacle1_y - wall_distance
obs1_bottom = obstacle1_y + obstacle_height + wall_distance

obs2_left = obstacle2_x - wall_distance
obs2_right = obstacle2_x + obstacle_width + wall_distance
obs2_top = obstacle2_y - wall_distance
obs2_bottom = obstacle2_y + obstacle_height + wall_distance

print(f"\n障碍物1影响区域: X[{obs1_left/1000:.2f}m - {obs1_right/1000:.2f}m], Y[{obs1_top/1000:.2f}m - {obs1_bottom/1000:.2f}m]")
print(f"障碍物2影响区域: X[{obs2_left/1000:.2f}m - {obs2_right/1000:.2f}m], Y[{obs2_top/1000:.2f}m - {obs2_bottom/1000:.2f}m]")

# 分析可用区域
print("\n可用区域分析:")
print("-" * 30)

# 上方区域（墙到障碍物1）
top_area_height = obs1_top - wall_distance
print(f"\n1. 上方区域:")
print(f"   高度: {top_area_height/1000:.2f}m")
if top_area_height >= table_height:
    print(f"   ✓ 可以横向放置台球桌")
    # 计算能放多少个
    available_width = field_width - 2 * wall_distance
    num_tables_h = int((available_width + table_distance) / (table_width + table_distance))
    print(f"   可放置: {num_tables_h} 个横向台球桌")

# 中间区域（障碍物1和障碍物2之间）
middle_area_height = obs2_top - obs1_bottom
print(f"\n2. 中间区域:")
print(f"   高度: {middle_area_height/1000:.2f}m")
print(f"   左侧宽度: {obs1_left/1000:.2f}m")
print(f"   右侧宽度: {(field_width - obs1_right)/1000:.2f}m")

# 左侧
left_width = obs1_left - wall_distance
if left_width >= table_height:
    print(f"   ✓ 左侧可以纵向放置台球桌")
    num_tables_v = int((middle_area_height + table_distance) / (table_width + table_distance))
    print(f"   左侧可放置: {num_tables_v} 个纵向台球桌")

# 右侧
right_width = field_width - wall_distance - obs1_right
if right_width >= table_height:
    print(f"   ✓ 右侧可以纵向放置台球桌")
    num_tables_v = int((middle_area_height + table_distance) / (table_width + table_distance))
    print(f"   右侧可放置: {num_tables_v} 个纵向台球桌")

# 下方区域（障碍物2到墙）
bottom_area_height = field_height - wall_distance - obs2_bottom
print(f"\n3. 下方区域:")
print(f"   高度: {bottom_area_height/1000:.2f}m")
if bottom_area_height >= table_height:
    print(f"   ✓ 可以横向放置台球桌")
    # 计算能放多少个
    available_width = field_width - 2 * wall_distance
    num_tables_h = int((available_width + table_distance) / (table_width + table_distance))
    print(f"   可放置: {num_tables_h} 个横向台球桌")

# 总结
print("\n" + "=" * 50)
print("优化建议:")
print("1. 上方区域：放置1-2行横向台球桌")
print("2. 中间区域：左右两侧各放置纵向台球桌")  
print("3. 下方区域：放置1行横向台球桌")
print("预计总数：6-8个台球桌")