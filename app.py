"""
Flask后端应用
提供台球桌自动布局API服务
"""

import os
import sys
from typing import Dict, List, Tuple
import traceback
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from core import (
    LayoutOptimizer, GeometryProcessor, Rectangle,
    BilliardTable, parse_image_boundary
)

# 获取当前目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载配置文件
config_path = os.path.join(BASE_DIR, 'config.json')
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        APP_CONFIG = json.load(f)
else:
    APP_CONFIG = {
        "default_config": {
            "wall_distance": 1500,
            "table_distance": 1400,
            "table_width": 2850,
            "table_height": 1550,
            "grid_size": 100,
            "use_regular_layout": True
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8080,
            "debug": True
        }
    }

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # 启用跨域支持

# 配置
app.config['MAX_CONTENT_LENGTH'] = APP_CONFIG.get('api', {}).get('max_upload_size', 16 * 1024 * 1024)


@app.route('/')
def index():
    """首页"""
    # 检查文件是否存在
    index_path = os.path.join(BASE_DIR, 'static', 'index.html')
    if not os.path.exists(index_path):
        return f"错误：找不到文件 {index_path}", 404
    return send_from_directory('static', 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })


@app.route('/api/layout/optimize', methods=['POST'])
def optimize_layout():
    """
    优化台球桌布局
    
    请求体:
    {
        "boundary": [[x1, y1], [x2, y2], ...],  # 场地边界点
        "obstacles": [  # 障碍物列表
            {
                "type": "rectangle",
                "center": [x, y],
                "size": [width, height]
            },
            ...
        ],
        "config": {  # 配置参数
            "wall_distance": 1500,
            "table_distance": 1400,
            "table_width": 2850,
            "table_height": 1550,
            "grid_size": 100,
            "use_regular_layout": true  # 是否使用规则布局算法
        }
    }
    """
    try:
        data = request.get_json()
        
        # 验证输入
        if not data or 'boundary' not in data:
            return jsonify({
                'success': False,
                'error': '缺少boundary参数'
            }), 400
        
        boundary = data['boundary']
        obstacles_data = data.get('obstacles', [])
        config = data.get('config', {})
        
        # 设置默认配置
        default_config = {
            'wall_distance': 1500,
            'table_distance': 1400,
            'table_width': 2850,
            'table_height': 1550,
            'grid_size': 100
        }
        default_config.update(config)
        
        # 创建几何处理器
        geometry = GeometryProcessor()
        geometry.process_boundary(boundary)
        
        # 添加障碍物
        obstacles = []
        for obs in obstacles_data:
            if obs['type'] == 'rectangle':
                center = obs['center']
                size = obs['size']
                geometry.add_obstacle(center, size)
                # 创建Rectangle对象
                obstacles.append(Rectangle(
                    center[0] - size[0]/2,
                    center[1] - size[1]/2,
                    size[0],
                    size[1]
                ))
            elif obs['type'] == 'circle':
                center = obs['center']
                radius = obs['radius']
                geometry.add_circular_obstacle(center, radius)
                # 简化为矩形
                obstacles.append(Rectangle(
                    center[0] - radius,
                    center[1] - radius,
                    radius * 2,
                    radius * 2
                ))
        
        # 计算有效区域
        geometry.calculate_valid_area(default_config['wall_distance'])
        
        # 创建优化器
        optimizer = LayoutOptimizer(default_config)
        
        # 执行优化
        use_regular_layout = default_config.get('use_regular_layout', True)  # 默认使用规则布局
        result = optimizer.optimize(boundary, obstacles, use_regular_layout=use_regular_layout)
        
        # 转换结果格式
        tables_data = []
        for table in result['tables']:
            tables_data.append({
                'x': float(table.x),
                'y': float(table.y),
                'width': float(table.width),
                'height': float(table.height),
                'rotation': float(table.rotation)
            })
        
        # 确保所有数值都是Python原生类型
        stats_data = {}
        if 'stats' in result:
            for key, value in result['stats'].items():
                if hasattr(value, 'item'):  # numpy类型
                    stats_data[key] = value.item()
                else:
                    stats_data[key] = value
        
        return jsonify({
            'success': True,
            'tables': tables_data,
            'count': int(result['count']),
            'stats': stats_data,
            'optimization_time': float(result['optimization_time'])
        })
        
    except Exception as e:
        print(f"Error in optimize_layout: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/layout/validate', methods=['POST'])
def validate_layout():
    """
    验证布局是否满足约束
    
    请求体:
    {
        "boundary": [[x1, y1], [x2, y2], ...],
        "obstacles": [...],
        "tables": [
            {"x": x, "y": y, "width": w, "height": h, "rotation": r},
            ...
        ],
        "config": {...}
    }
    """
    try:
        data = request.get_json()
        
        boundary = data['boundary']
        obstacles_data = data.get('obstacles', [])
        tables_data = data.get('tables', [])
        config = data.get('config', {})
        
        # 创建约束求解器
        from core import ConstraintSolver, DistanceConstraint
        
        solver = ConstraintSolver()
        solver.add_constraint(DistanceConstraint(
            config.get('wall_distance', 1500),
            config.get('table_distance', 1400),
            config.get('obstacle_distance', 1500)
        ))
        
        # 创建台球桌对象
        tables = []
        for t in tables_data:
            table = BilliardTable(
                t['x'], t['y'],
                t.get('width', 2850),
                t.get('height', 1550),
                t.get('rotation', 0)
            )
            tables.append(table)
        
        # 创建障碍物
        obstacles = []
        for obs in obstacles_data:
            if obs['type'] == 'rectangle':
                center = obs['center']
                size = obs['size']
                obstacles.append(Rectangle(
                    center[0] - size[0]/2,
                    center[1] - size[1]/2,
                    size[0],
                    size[1]
                ))
        
        # 验证布局
        context = {
            'boundary': boundary,
            'obstacles': obstacles
        }
        
        valid, violations = solver.validate_layout(tables, context)
        
        # 格式化违反信息
        violations_data = []
        for v in violations:
            violations_data.append({
                'type': v.constraint_type,
                'description': v.description,
                'severity': v.severity
            })
        
        return jsonify({
            'success': True,
            'valid': valid,
            'violations': violations_data
        })
        
    except Exception as e:
        print(f"Error in validate_layout: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/layout/test', methods=['GET'])
def test_layout():
    """测试布局优化（使用示例数据）"""
    try:
        # 创建一个10m x 15m的矩形场地
        boundary = [
            [0, 0],
            [10000, 0],
            [10000, 15000],
            [0, 15000]
        ]
        
        # 添加两个柱子
        obstacles = [
            {
                'type': 'rectangle',
                'center': [3000, 5000],
                'size': [400, 400]
            },
            {
                'type': 'rectangle',
                'center': [7000, 10000],
                'size': [400, 400]
            }
        ]
        
        # 默认配置
        config = {
            'wall_distance': 1500,
            'table_distance': 1400,
            'table_width': 2850,
            'table_height': 1550,
            'grid_size': 200
        }
        
        # 创建请求数据
        test_data = {
            'boundary': boundary,
            'obstacles': obstacles,
            'config': config
        }
        
        # 调用优化函数
        with app.test_request_context(json=test_data):
            response = optimize_layout()
            return response
            
    except Exception as e:
        print(f"Error in test_layout: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # 开发模式运行
    app.run(debug=True, host='127.0.0.1', port=8080)