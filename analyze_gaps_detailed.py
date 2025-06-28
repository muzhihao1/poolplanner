"""
详细分析空余空间
"""

from core.maxrects import Rectangle, BilliardTable
from core.constraints import ConstraintSolver, DistanceConstraint
from shapely.geometry import Polygon

def check_distance(table1, table2, min_distance):
    """检查两个台球桌之间的距离"""
    # 获取实际边界
    bounds1 = table1.get_bounds()
    bounds2 = table2.get_bounds()
    
    # 计算矩形之间的最短距离
    dx = max(0, max(bounds2.x - (bounds1.x + bounds1.width), bounds1.x - (bounds2.x + bounds2.width)))
    dy = max(0, max(bounds2.y - (bounds1.y + bounds1.height), bounds1.y - (bounds2.y + bounds2.height)))
    
    distance = (dx * dx + dy * dy) ** 0.5
    return distance >= min_distance, distance

def check_obstacle_distance(table, obstacle, min_distance):
    """检查台球桌与障碍物的距离"""
    bounds = table.get_bounds()
    
    dx = max(0, max(obstacle.x - (bounds.x + bounds.width), bounds.x - (obstacle.x + obstacle.width)))
    dy = max(0, max(obstacle.y - (bounds.y + bounds.height), bounds.y - (obstacle.y + obstacle.height)))
    
    distance = (dx * dx + dy * dy) ** 0.5
    return distance >= min_distance, distance

# 设置参数
wall_distance = 1500
table_distance = 1400
table_width = 2850
table_height = 1550

obstacles = [
    Rectangle(3000, 4000, 1000, 1000),
    Rectangle(7000, 9000, 1500, 1500)
]

current_tables = [
    BilliardTable(5200, 1500, table_width, table_height, 0),
    BilliardTable(5500, 4450, table_width, table_height, 0),
    BilliardTable(1500, 6500, table_width, table_height, 90),
    BilliardTable(3950, 10450, table_width, table_height, 90)
]

print("详细空间分析\n")

# 测试一些明显的空位
test_positions = [
    # 左上角
    (1500, 1500, 0, "左上角横向"),
    (1500, 1500, 90, "左上角纵向"),
    
    # 障碍物1下方
    (3000, 5500, 0, "障碍物1下方横向"),
    (3000, 5500, 90, "障碍物1下方纵向"),
    
    # 右侧区域
    (6500, 6000, 0, "右侧中部横向"),
    (6500, 6000, 90, "右侧中部纵向"),
    
    # 底部
    (1500, 11000, 0, "底部左侧横向"),
    (6000, 11000, 0, "底部右侧横向"),
]

for x, y, rotation, desc in test_positions:
    print(f"\n测试位置: {desc} at ({x}, {y})")
    
    # 创建测试台球桌
    test_table = BilliardTable(x, y, table_width, table_height, rotation)
    
    # 获取实际尺寸
    if rotation == 0:
        width, height = table_width, table_height
    else:
        width, height = table_height, table_width
    
    # 检查墙壁距离
    wall_ok = True
    if x < wall_distance:
        print(f"  × 距左墙 {x}mm < {wall_distance}mm")
        wall_ok = False
    if y < wall_distance:
        print(f"  × 距上墙 {y}mm < {wall_distance}mm")
        wall_ok = False
    if x + width > 10000 - wall_distance:
        print(f"  × 距右墙 {10000 - (x + width)}mm < {wall_distance}mm")
        wall_ok = False
    if y + height > 15000 - wall_distance:
        print(f"  × 距下墙 {15000 - (y + height)}mm < {wall_distance}mm")
        wall_ok = False
    
    if wall_ok:
        print(f"  ✓ 墙壁距离满足")
    
    # 检查与现有台球桌的距离
    table_ok = True
    for i, table in enumerate(current_tables):
        ok, dist = check_distance(test_table, table, table_distance)
        if not ok:
            print(f"  × 距台球桌{i+1} {dist:.0f}mm < {table_distance}mm")
            table_ok = False
    
    if table_ok and wall_ok:
        print(f"  ✓ 与现有台球桌距离满足")
    
    # 检查与障碍物的距离
    obstacle_ok = True
    for i, obs in enumerate(obstacles):
        ok, dist = check_obstacle_distance(test_table, obs, wall_distance)
        if not ok:
            print(f"  × 距障碍物{i+1} {dist:.0f}mm < {wall_distance}mm")
            obstacle_ok = False
    
    if obstacle_ok and wall_ok and table_ok:
        print(f"  ✓ 与障碍物距离满足")
    
    if wall_ok and table_ok and obstacle_ok:
        print(f"  ✅ 此位置可以放置!")

# 分析为什么只能放4个台球桌
print("\n\n空间利用分析:")
print(f"场地尺寸: 10m × 15m")
print(f"障碍物1: 位于(3-4m, 4-5m)")
print(f"障碍物2: 位于(7-8.5m, 9-10.5m)")
print(f"\n当前布局:")
print(f"台球桌1: (5.2m, 1.5m) 横向 - 右上区域")
print(f"台球桌2: (5.5m, 4.45m) 横向 - 右中区域")
print(f"台球桌3: (1.5m, 6.5m) 纵向 - 左中区域")
print(f"台球桌4: (3.95m, 10.45m) 纵向 - 中下区域")

print(f"\n未利用的主要区域:")
print(f"1. 左上角 (0-3m, 0-4m) - 被障碍物1阻挡")
print(f"2. 左下角 (0-3m, 11-15m) - 空间不足")
print(f"3. 右下角 (7-10m, 10.5-15m) - 被障碍物2阻挡")