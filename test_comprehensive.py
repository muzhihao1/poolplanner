#!/usr/bin/env python3
"""
综合测试台球桌布局系统
"""

import requests
import json

# API端点
API_URL = "http://127.0.0.1:8080/api/layout/optimize"

def test_layout(name, test_data):
    """测试单个布局"""
    print(f"\n{'='*60}")
    print(f"测试场景: {name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_URL, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ 布局优化成功!")
                print(f"   放置了 {result['count']} 个台球桌")
                print(f"   空间利用率: {result['stats']['space_utilization']}%")
                print(f"   平均间距: {result['stats']['average_distance']:.0f}mm")
                
                print(f"\n📍 台球桌位置:")
                for i, table in enumerate(result['tables']):
                    print(f"   台球桌 #{i+1}: 位置({table['x']:.0f}, {table['y']:.0f}), " +
                          f"尺寸({table['width']:.0f}x{table['height']:.0f}), " +
                          f"旋转: {table['rotation']}°")
            else:
                print(f"❌ 优化失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

# 测试1: 小型场地（7x10米），无障碍物
test1 = {
    "boundary": [[0, 0], [7000, 0], [7000, 10000], [0, 10000]],
    "obstacles": [],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "use_regular_layout": True
    }
}

# 测试2: 中型场地（10x15米），有2个障碍物
test2 = {
    "boundary": [[0, 0], [10000, 0], [10000, 15000], [0, 15000]],
    "obstacles": [
        {"type": "rectangle", "center": [3000, 5000], "size": [400, 400]},
        {"type": "rectangle", "center": [7000, 10000], "size": [400, 400]}
    ],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "use_regular_layout": True
    }
}

# 测试3: 大型场地（15x20米），多个障碍物
test3 = {
    "boundary": [[0, 0], [15000, 0], [15000, 20000], [0, 20000]],
    "obstacles": [
        {"type": "rectangle", "center": [3000, 5000], "size": [400, 400]},
        {"type": "rectangle", "center": [12000, 5000], "size": [400, 400]},
        {"type": "rectangle", "center": [7500, 10000], "size": [600, 600]},
        {"type": "rectangle", "center": [3000, 15000], "size": [400, 400]},
        {"type": "rectangle", "center": [12000, 15000], "size": [400, 400]}
    ],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "use_regular_layout": True
    }
}

# 测试4: 不规则形状场地（L形）
test4 = {
    "boundary": [
        [0, 0], [10000, 0], [10000, 10000], 
        [5000, 10000], [5000, 15000], [0, 15000]
    ],
    "obstacles": [],
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "use_regular_layout": True
    }
}

# 执行所有测试
test_layout("小型场地（7x10米）无障碍物", test1)
test_layout("中型场地（10x15米）有障碍物", test2)
test_layout("大型场地（15x20米）多障碍物", test3)
test_layout("L形不规则场地", test4)

print(f"\n{'='*60}")
print("测试完成！")
print(f"{'='*60}")