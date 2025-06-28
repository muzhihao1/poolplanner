"""
测试布局优化并生成文本可视化
"""

from core.maxrects import Rectangle
from core.optimized_layout import OptimizedLayoutGenerator

def text_visualize_layout(boundary, obstacles, tables):
    """生成文本可视化"""
    # 创建网格 (缩小比例 1:100)
    width = 100  # 10000mm -> 100 chars
    height = 150  # 15000mm -> 150 chars
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # 标记边界
    for i in range(width):
        grid[0][i] = '-'
        grid[height-1][i] = '-'
    for i in range(height):
        grid[i][0] = '|'
        grid[i][width-1] = '|'
    
    # 标记障碍物
    for obs in obstacles:
        x1 = int(obs.x / 100)
        y1 = int(obs.y / 100)
        x2 = int((obs.x + obs.width) / 100)
        y2 = int((obs.y + obs.height) / 100)
        
        for y in range(y1, min(y2, height)):
            for x in range(x1, min(x2, width)):
                if 0 <= y < height and 0 <= x < width:
                    grid[height - 1 - y][x] = '#'
    
    # 标记台球桌
    for i, table in enumerate(tables):
        if table.rotation == 0:
            w, h = table.width, table.height
        else:
            w, h = table.height, table.width
            
        x1 = int(table.x / 100)
        y1 = int(table.y / 100)
        x2 = int((table.x + w) / 100)
        y2 = int((table.y + h) / 100)
        
        for y in range(y1, min(y2, height)):
            for x in range(x1, min(x2, width)):
                if 0 <= y < height and 0 <= x < width:
                    grid[height - 1 - y][x] = str(i + 1)
    
    # 打印网格
    print("\n布局可视化 (1:100比例):")
    print("  " + "".join(str(i % 10) for i in range(0, width, 10)))
    for i, row in enumerate(grid):
        if i % 10 == 0:
            print(f"{150-i:3d} {''.join(row)}")
        else:
            print(f"    {''.join(row)}")
    
    # 打印图例
    print("\n图例:")
    print("- : 边界")
    print("# : 障碍物")
    print("1-9 : 台球桌编号")

# 设置参数
config = {
    'wall_distance': 1500,
    'table_distance': 1400,
    'table_width': 2850,
    'table_height': 1550
}

boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
obstacles = [
    Rectangle(3000, 4000, 1000, 1000),  # 第一个障碍物 (3-4m, 4-5m)
    Rectangle(7000, 9000, 1500, 1500)   # 第二个障碍物 (7-8.5m, 9-10.5m)
]

# 运行优化
print("正在运行布局优化...")
generator = OptimizedLayoutGenerator(config)
layout = generator.generate_layout(boundary, obstacles)

print(f'\n最终结果: {len(layout)} 个台球桌')
print("\n台球桌详细位置:")
for i, table in enumerate(layout):
    orientation = "横向" if table.rotation == 0 else "纵向"
    print(f"台球桌 {i+1}: 位置({table.x:.0f}, {table.y:.0f}), {orientation}")
    
    # 计算距离
    # 左墙距离
    left_dist = table.x
    # 右墙距离
    if table.rotation == 0:
        right_dist = 10000 - (table.x + table.width)
    else:
        right_dist = 10000 - (table.x + table.height)
    # 上墙距离
    top_dist = table.y
    # 下墙距离
    if table.rotation == 0:
        bottom_dist = 15000 - (table.y + table.height)
    else:
        bottom_dist = 15000 - (table.y + table.width)
    
    print(f"  距离: 左={left_dist:.0f}, 右={right_dist:.0f}, 上={top_dist:.0f}, 下={bottom_dist:.0f}")

# 生成文本可视化
text_visualize_layout(boundary, obstacles, layout)

# 分析空间利用
print("\n空间利用分析:")
total_area = 10 * 15
table_area = len(layout) * 2.85 * 1.55
obstacle_area = (1 * 1 + 1.5 * 1.5)
print(f"场地总面积: {total_area} m²")
print(f"台球桌占用: {table_area:.2f} m² ({table_area/total_area*100:.1f}%)")
print(f"障碍物占用: {obstacle_area:.2f} m² ({obstacle_area/total_area*100:.1f}%)")
print(f"有效利用率: {table_area/(total_area-obstacle_area)*100:.1f}%")

# 检查是否有明显的空余空间
print("\n潜在改进:")
if len(layout) < 5:
    print("- 当前只放置了4个台球桌，理论上应该能放置5-6个")
    print("- 建议检查:")
    print("  1. 左上角区域 (0-3m, 0-4m)")
    print("  2. 右侧区域 (7-10m, 0-9m)")
    print("  3. 底部区域 (0-10m, 10.5-15m)")
else:
    print("- 已达到较好的空间利用率")