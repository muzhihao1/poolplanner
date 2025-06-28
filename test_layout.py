"""
测试布局优化并生成可视化
"""

from core.maxrects import Rectangle
from core.optimized_layout import OptimizedLayoutGenerator
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle as RectPatch

def visualize_layout(boundary, obstacles, tables, title="Layout Visualization"):
    """可视化布局结果"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 15))
    
    # 绘制边界
    boundary_x = [p[0] for p in boundary] + [boundary[0][0]]
    boundary_y = [p[1] for p in boundary] + [boundary[0][1]]
    ax.plot(boundary_x, boundary_y, 'k-', linewidth=2, label='Boundary')
    
    # 绘制障碍物
    for i, obs in enumerate(obstacles):
        rect = RectPatch((obs.x, obs.y), obs.width, obs.height, 
                         linewidth=1, edgecolor='red', facecolor='lightcoral', 
                         label='Obstacle' if i == 0 else '')
        ax.add_patch(rect)
    
    # 绘制台球桌
    for i, table in enumerate(tables):
        # 获取实际尺寸（考虑旋转）
        if table.rotation == 0:
            width, height = table.width, table.height
        else:
            width, height = table.height, table.width
            
        rect = RectPatch((table.x, table.y), width, height,
                         linewidth=1, edgecolor='green', facecolor='lightgreen',
                         label='Table' if i == 0 else '')
        ax.add_patch(rect)
        
        # 添加编号
        center_x = table.x + width / 2
        center_y = table.y + height / 2
        ax.text(center_x, center_y, str(i+1), ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 设置坐标轴
    ax.set_xlim(-500, 10500)
    ax.set_ylim(-500, 15500)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(f"{title} - {len(tables)} tables")
    
    # 添加尺寸标注
    ax.text(5000, -300, f"Field: 10m × 15m", ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('layout_visualization.png', dpi=150)
    print(f"Visualization saved to layout_visualization.png")
    plt.close()

# 设置参数
config = {
    'wall_distance': 1500,
    'table_distance': 1400,
    'table_width': 2850,
    'table_height': 1550
}

boundary = [[0, 0], [10000, 0], [10000, 15000], [0, 15000]]
obstacles = [
    Rectangle(3000, 4000, 1000, 1000),  # First obstacle
    Rectangle(7000, 9000, 1500, 1500)   # Second obstacle
]

# 运行优化
generator = OptimizedLayoutGenerator(config)
layout = generator.generate_layout(boundary, obstacles)

print(f'\nFinal result: {len(layout)} tables')
for i, table in enumerate(layout):
    print(f'Table {i+1}: x={table.x:.0f}, y={table.y:.0f}, rotation={table.rotation}°')

# 生成可视化
visualize_layout(boundary, obstacles, layout, "Optimized Layout")

# 分析未使用的空间
print("\n空间分析:")
print(f"场地总面积: {10 * 15} m²")
print(f"台球桌占用面积: {len(layout) * 2.85 * 1.55:.2f} m²")
print(f"障碍物占用面积: {(1 * 1 + 1.5 * 1.5):.2f} m²")
print(f"空间利用率: {(len(layout) * 2.85 * 1.55) / (10 * 15) * 100:.1f}%")