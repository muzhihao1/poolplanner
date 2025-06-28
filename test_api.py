"""
API测试脚本
"""

import requests
import json
import time


def test_health():
    """测试健康检查端点"""
    print("测试健康检查...")
    response = requests.get('http://localhost:8080/api/health')
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_optimize():
    """测试布局优化"""
    print("测试布局优化...")
    
    # 测试数据：10m x 15m的场地，带两个柱子
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
            "grid_size": 200
        }
    }
    
    response = requests.post(
        'http://localhost:8080/api/layout/optimize',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"成功！放置了 {result['count']} 个台球桌")
        print(f"优化时间: {result['optimization_time']:.2f} 秒")
        print(f"统计信息: {result['stats']}")
        print(f"前3个台球桌位置:")
        for i, table in enumerate(result['tables'][:3]):
            print(f"  台球桌{i+1}: 位置({table['x']:.0f}, {table['y']:.0f}), 旋转{table['rotation']}度")
    else:
        print(f"失败: {result.get('error')}")
    print()


def test_validate():
    """测试布局验证"""
    print("测试布局验证...")
    
    # 测试数据：一个可能违反约束的布局
    data = {
        "boundary": [
            [0, 0],
            [10000, 0],
            [10000, 10000],
            [0, 10000]
        ],
        "tables": [
            {"x": 100, "y": 100, "width": 2850, "height": 1550, "rotation": 0},  # 太靠近墙壁
            {"x": 5000, "y": 5000, "width": 2850, "height": 1550, "rotation": 0}
        ],
        "config": {
            "wall_distance": 1500,
            "table_distance": 1400
        }
    }
    
    response = requests.post(
        'http://localhost:8080/api/layout/validate',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"验证{'通过' if result['valid'] else '失败'}")
        if not result['valid']:
            print(f"违反约束:")
            for v in result['violations']:
                print(f"  - {v['description']}")
    else:
        print(f"错误: {result.get('error')}")
    print()


def test_test_endpoint():
    """测试示例数据端点"""
    print("测试示例数据端点...")
    response = requests.get('http://localhost:8080/api/layout/test')
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"成功！放置了 {result['count']} 个台球桌")
        print(f"空间利用率: {result['stats']['space_utilization']}%")
    else:
        print(f"失败: {result.get('error')}")


if __name__ == '__main__':
    print("开始API测试...\n")
    
    # 等待服务器启动
    print("请确保Flask服务器正在运行 (python app.py)")
    print("按Enter继续...")
    input()
    
    try:
        test_health()
        test_optimize()
        test_validate()
        test_test_endpoint()
        print("所有测试完成！")
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到服务器。请确保Flask服务器正在运行。")
    except Exception as e:
        print(f"测试失败: {e}")