# 台球桌自动布局系统

一个智能的台球桌自动布局优化系统，能够根据场地形状、障碍物位置和安全距离要求，自动计算最优的台球桌摆放方案。

## 功能特点

- 🎯 **智能布局优化** - 自动计算最优布局方案
- 📐 **网格对齐** - 台球桌整齐排列成行列
- 🚧 **障碍物避让** - 自动避开柱子等障碍物
- 📏 **精确距离控制** - 严格遵守安全距离要求
- 🎨 **实时可视化** - 直观展示布局结果和距离标注
- 🔄 **多种布局模式** - 支持横向、纵向和自动优化
- ⚡ **最大化优化** - 可选择最大化台球桌数量模式

## 系统要求

- Python 3.7+
- Flask
- NumPy
- Shapely
- rtree

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/billiard-layout.git
cd billiard-layout

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 启动服务器

```bash
python app.py
```

服务器将在 `http://127.0.0.1:8080` 启动。

### Web界面

打开浏览器访问 `http://127.0.0.1:8080`，你可以：

1. 绘制场地边界
2. 添加障碍物（柱子等）
3. 调整参数（安全距离、台球桌尺寸等）
4. 选择是否最大化台球桌数量
5. 点击"优化布局"查看结果

### API使用

```python
import requests

# API端点
url = "http://127.0.0.1:8080/api/layout/optimize"

# 请求数据
data = {
    "boundary": [[0, 0], [10000, 0], [10000, 15000], [0, 15000]],
    "obstacles": [
        {"type": "rectangle", "center": [5000, 7500], "size": [400, 400]}
    ],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "optimize_count": True  # 启用最大化优化
    }
}

# 发送请求
response = requests.post(url, json=data)
result = response.json()
```

## 配置参数

- `wall_distance`: 台球桌到墙壁的最小距离（默认1500mm）
- `table_distance`: 台球桌之间的最小距离（默认1400mm）
- `table_width`: 台球桌宽度（默认2850mm）
- `table_height`: 台球桌高度（默认1550mm）
- `optimize_count`: 是否最大化台球桌数量（默认True）
- `layout_mode`: 布局模式（auto/horizontal/vertical/mixed）

## 算法说明

### 规则布局算法
- 将台球桌按网格方式整齐排列
- 支持横向、纵向和自动选择最优方向
- 确保所有台球桌对齐且间距一致

### 优化布局算法（最大化数量）
- 使用多种策略组合找到最优解
- 贪心算法优先放置边角位置
- 混合填充算法在空隙中尝试不同方向
- 平均可提升10-20%的台球桌数量

## 性能测试

在各种场地尺寸下的测试结果：

| 场地类型 | 尺寸 | 普通布局 | 优化布局 | 提升 |
|---------|------|---------|---------|------|
| 小场地 | 8x12m | 4 | 4 | +0% |
| 中等场地 | 10x15m | 6 | 7 | +17% |
| 大场地 | 15x20m | 18 | 18 | +0% |
| 有障碍物 | 10x15m | 3 | 4 | +33% |

## 许可证

MIT License
