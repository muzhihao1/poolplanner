#!/usr/bin/env python3
"""
测试精确位置
"""

# 场地参数
field_width = 10000
field_height = 15000
wall_distance = 1500
table_distance = 1400
table_width = 2850
table_height = 1550

# 可用空间
usable_start_x = wall_distance  # 1500
usable_end_x = field_width - wall_distance  # 8500
usable_width = usable_end_x - usable_start_x  # 7000

print(f"场地宽度: {field_width}")
print(f"墙壁距离: {wall_distance}")
print(f"可用空间: {usable_start_x} 到 {usable_end_x} (宽度: {usable_width})")
print(f"台球桌宽度: {table_width}")
print(f"台球桌间距: {table_distance}")

print("\n列位置计算:")
x = usable_start_x
col = 1
while x + table_width <= usable_end_x:
    print(f"第{col}列: x = {x} 到 {x + table_width}")
    x = x + table_width + table_distance
    col += 1
    
print(f"\n下一列起始位置: x = {x}")
if x + table_width > usable_end_x:
    print(f"第{col}列无法放置 (需要到 {x + table_width}, 但边界是 {usable_end_x})")
    
# 但是，让我们检查是否第二列实际可以放置
col2_start = usable_start_x + table_width + table_distance
col2_end = col2_start + table_width
print(f"\n第2列精确检查:")
print(f"起始: {col2_start}, 结束: {col2_end}")
print(f"是否符合边界? {col2_end <= usable_end_x}")