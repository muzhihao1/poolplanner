#!/usr/bin/env python3
"""
测试规则布局算法（无障碍物）
"""

import requests
import json

# API端点
API_URL = "http://127.0.0.1:8080/api/layout/optimize"

# 测试数据：10m x 15m 的矩形场地，无障碍物
test_data = {
    "boundary": [
        [0, 0],
        [10000, 0],
        [10000, 15000],
        [0, 15000]
    ],
    "obstacles": [],  # 无障碍物
    "config": {
        "wall_distance": 1500,
        "table_distance": 1400,
        "table_width": 2850,
        "table_height": 1550,
        "grid_size": 100,
        "use_regular_layout": True
    }
}

try:
    # 发送请求
    response = requests.post(API_URL, json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ 布局优化成功!")
            print(f"   放置了 {result['count']} 个台球桌")
            print(f"   优化用时: {result['optimization_time']:.2f} 秒")
            print(f"\n📊 统计信息:")
            for key, value in result['stats'].items():
                print(f"   {key}: {value}")
            
            print(f"\n📍 台球桌位置 (前10个):")
            for i, table in enumerate(result['tables'][:10]):
                print(f"   台球桌 #{i+1}: 位置({table['x']:.0f}, {table['y']:.0f}), " +
                      f"尺寸({table['width']:.0f}x{table['height']:.0f}), 旋转: {table['rotation']}°")
        else:
            print(f"❌ 优化失败: {result.get('error', '未知错误')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务器，请确保服务器正在运行")
except Exception as e:
    print(f"❌ 错误: {str(e)}")