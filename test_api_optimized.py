#!/usr/bin/env python3
"""测试优化API"""

import requests
import json

# API端点
url = "http://127.0.0.1:8080/api/layout/optimize"

# 测试数据 - 10x15米场地，2个障碍物
data = {
    "boundary": [
        [0, 0],
        [10000, 0],
        [10000, 15000],
        [0, 15000]
    ],
    "obstacles": [
        {
            "type": "rectangle",
            "center": [3000, 5000],
            "size": [400, 400]
        },
        {
            "type": "rectangle", 
            "center": [7000, 10000],
            "size": [400, 400]
        }
    ],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "optimize_count": True
    }
}

# 发送请求
response = requests.post(url, json=data)
result = response.json()

if result['success']:
    print(f"优化成功！放置了 {result['count']} 个台球桌")
    print("\n台球桌位置:")
    for i, table in enumerate(result['tables']):
        rotation = "横向" if table['rotation'] == 0 else "纵向"
        print(f"  台球桌{i+1}: ({table['x']:.0f}, {table['y']:.0f}) - {rotation}")
else:
    print(f"优化失败: {result['error']}")