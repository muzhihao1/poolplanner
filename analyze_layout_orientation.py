"""
分析不同摆放方向的容量
"""

# 场地尺寸
field_width = 16300  # 16.3m
field_height = 7530  # 7.53m

# 台球桌尺寸
table_width = 2850   # 2.85m
table_height = 1550  # 1.55m

# 间距要求（根据截图显示的实际间距）
wall_distance = 1600  # 1.6m
table_distance = 1400 # 1.4m

print("场地分析")
print("=" * 50)
print(f"场地尺寸: {field_width/1000:.2f}m × {field_height/1000:.2f}m")
print(f"台球桌尺寸: {table_width/1000:.2f}m × {table_height/1000:.2f}m")
print(f"墙壁距离: {wall_distance/1000:.1f}m")
print(f"台球桌间距: {table_distance/1000:.1f}m")

# 可用空间
usable_width = field_width - 2 * wall_distance
usable_height = field_height - 2 * wall_distance

print(f"\n可用空间: {usable_width/1000:.2f}m × {usable_height/1000:.2f}m")

# 方案1：纵向摆放（当前方案）
print("\n方案1：纵向摆放（台球桌竖着放）")
print("-" * 30)

# 纵向时，台球桌实际占用：1.55m × 2.85m
cols_vertical = int((usable_width + table_distance) / (table_height + table_distance))
rows_vertical = int((usable_height + table_distance) / (table_width + table_distance))

print(f"每行可放: {cols_vertical} 个")
print(f"可放行数: {rows_vertical} 行")
print(f"总计: {cols_vertical * rows_vertical} 个台球桌")

# 验证计算
print(f"\n验证:")
print(f"横向占用: {cols_vertical} × {table_height/1000:.2f}m + {(cols_vertical-1)} × {table_distance/1000:.1f}m = {(cols_vertical * table_height + (cols_vertical-1) * table_distance)/1000:.2f}m")
print(f"纵向占用: {rows_vertical} × {table_width/1000:.2f}m + {(rows_vertical-1)} × {table_distance/1000:.1f}m = {(rows_vertical * table_width + (rows_vertical-1) * table_distance)/1000:.2f}m")

# 方案2：横向摆放（台球桌横着放）
print("\n\n方案2：横向摆放（台球桌横着放）")
print("-" * 30)

# 横向时，台球桌实际占用：2.85m × 1.55m
cols_horizontal = int((usable_width + table_distance) / (table_width + table_distance))
rows_horizontal = int((usable_height + table_distance) / (table_height + table_distance))

print(f"每行可放: {cols_horizontal} 个")
print(f"可放行数: {rows_horizontal} 行")
print(f"总计: {cols_horizontal * rows_horizontal} 个台球桌")

# 验证计算
print(f"\n验证:")
print(f"横向占用: {cols_horizontal} × {table_width/1000:.2f}m + {(cols_horizontal-1)} × {table_distance/1000:.1f}m = {(cols_horizontal * table_width + (cols_horizontal-1) * table_distance)/1000:.2f}m")
print(f"纵向占用: {rows_horizontal} × {table_height/1000:.2f}m + {(rows_horizontal-1)} × {table_distance/1000:.1f}m = {(rows_horizontal * table_height + (rows_horizontal-1) * table_distance)/1000:.2f}m")

# 总结
print("\n" + "=" * 50)
print("结论：")
if cols_vertical * rows_vertical > cols_horizontal * rows_horizontal:
    print(f"✓ 纵向摆放更优，可以放置 {cols_vertical * rows_vertical} 个台球桌")
    print(f"  横向摆放只能放置 {cols_horizontal * rows_horizontal} 个台球桌")
elif cols_horizontal * rows_horizontal > cols_vertical * rows_vertical:
    print(f"✓ 横向摆放更优，可以放置 {cols_horizontal * rows_horizontal} 个台球桌")
    print(f"  纵向摆放只能放置 {cols_vertical * rows_vertical} 个台球桌")
    print(f"  建议改为横向布局，可多放置 {cols_horizontal * rows_horizontal - cols_vertical * rows_vertical} 个台球桌")
else:
    print(f"两种方案效果相同，都可以放置 {cols_vertical * rows_vertical} 个台球桌")

# 混合方案分析
print("\n\n方案3：混合摆放（部分横向、部分纵向）")
print("-" * 30)
print("对于这种长条形场地，混合摆放通常不会比单一方向更优")
print("因为会产生更多的边角浪费空间")

# 空间利用率分析
print("\n\n空间利用率分析：")
print("-" * 30)
table_area = table_width * table_height / 1000000  # 单个台球桌面积（平方米）
field_area = field_width * field_height / 1000000  # 场地总面积

vertical_count = cols_vertical * rows_vertical
horizontal_count = cols_horizontal * rows_horizontal

print(f"场地总面积: {field_area:.2f} m²")
print(f"单个台球桌面积: {table_area:.2f} m²")
print(f"\n纵向摆放:")
print(f"  台球桌总面积: {vertical_count * table_area:.2f} m²")
print(f"  面积利用率: {(vertical_count * table_area / field_area * 100):.1f}%")
print(f"\n横向摆放:")
print(f"  台球桌总面积: {horizontal_count * table_area:.2f} m²")
print(f"  面积利用率: {(horizontal_count * table_area / field_area * 100):.1f}%")