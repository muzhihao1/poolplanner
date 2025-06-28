#!/usr/bin/env python3
"""
测试新的增强API
"""

import requests
import json

# API端点
url = "http://127.0.0.1:8080/api/layout/optimize"

def test_enhanced_api():
    """测试增强API"""
    print("=" * 60)
    print("测试增强布局API")
    print("=" * 60)
    
    # 测试数据 - 10x15米场地，2个障碍物
    test_cases = [
        {
            'name': '增强算法测试',
            'data': {
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
                    "use_enhanced_algorithm": True
                }
            }
        },
        {
            'name': '传统算法对比',
            'data': {
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
                    "use_enhanced_algorithm": False
                }
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print("-" * 30)
        
        try:
            # 发送请求
            response = requests.post(url, json=test_case['data'])
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ 成功！")
                    print(f"   台球桌数量: {result['count']} 个")
                    print(f"   使用算法: {result.get('algorithm', 'unknown')}")
                    print(f"   空间利用率: {result['stats']['space_utilization']}%")
                    print(f"   平均间距: {result['stats']['average_distance']:.0f}mm")
                    
                    print(f"\n   台球桌位置:")
                    for i, table in enumerate(result['tables'][:5]):  # 只显示前5个
                        orientation = "横向" if table['rotation'] == 0 else "纵向"
                        print(f"     #{i+1}: ({table['x']:.0f}, {table['y']:.0f}) - {orientation}")
                    
                    if len(result['tables']) > 5:
                        print(f"     ... 还有 {len(result['tables']) - 5} 个台球桌")
                    
                    results.append({
                        'name': test_case['name'],
                        'count': result['count'],
                        'algorithm': result.get('algorithm', 'unknown'),
                        'utilization': result['stats']['space_utilization']
                    })
                else:
                    print(f"❌ 失败: {result.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器，请确保服务器正在运行")
            return
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
    
    # 对比结果
    if len(results) >= 2:
        print(f"\n" + "=" * 60)
        print("算法对比结果:")
        print("=" * 60)
        
        enhanced_result = next((r for r in results if '增强' in r['name']), None)
        traditional_result = next((r for r in results if '传统' in r['name']), None)
        
        if enhanced_result and traditional_result:
            improvement = enhanced_result['count'] - traditional_result['count']
            print(f"传统算法: {traditional_result['count']} 个台球桌")
            print(f"增强算法: {enhanced_result['count']} 个台球桌")
            print(f"改进效果: {improvement:+d} 个台球桌")
            
            if improvement > 0:
                print(f"✨ 增强算法表现更好！")
            elif improvement == 0:
                print(f"🤝 两种算法效果相同")
            else:
                print(f"⚠️  传统算法在此场景下表现更好")

def test_health_check():
    """测试健康检查"""
    print(f"\n健康检查:")
    try:
        response = requests.get('http://127.0.0.1:8080/api/health')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务器状态: {result['status']}")
            print(f"   版本: {result['version']}")
            print(f"   功能: {', '.join(result['features'])}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except:
        print(f"❌ 无法连接到服务器")

if __name__ == '__main__':
    test_health_check()
    test_enhanced_api()
    
    print(f"\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)