"""
简化版应用 - 用于测试
"""

from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    """首页"""
    # 直接返回HTML内容，避免文件路径问题
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>台球桌自动布局系统</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .status { 
            background: #e8f5e9; 
            padding: 15px; 
            border-radius: 5px;
            margin: 20px 0;
        }
        .link {
            display: inline-block;
            margin: 10px 0;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .link:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎱 台球桌自动布局系统</h1>
        <div class="status">
            <h2>✅ 系统运行正常！</h2>
            <p>Flask服务器已成功启动。</p>
        </div>
        
        <h3>功能说明：</h3>
        <ul>
            <li>自动计算台球桌最优布局</li>
            <li>支持自定义场地形状和障碍物</li>
            <li>可视化展示布局结果</li>
            <li>提供详细的空间利用率统计</li>
        </ul>
        
        <h3>API端点：</h3>
        <ul>
            <li><a href="/api/health" class="link">健康检查</a></li>
            <li><a href="/api/layout/test" class="link">测试布局优化</a></li>
        </ul>
        
        <h3>完整界面：</h3>
        <p>要使用完整的可视化界面，请访问 <a href="/full" class="link">完整应用</a></p>
        
        <p style="margin-top: 30px; color: #666;">
            提示：如果看到这个页面，说明基本的Flask服务已经工作正常。
        </p>
    </div>
</body>
</html>
    '''

@app.route('/full')
def full_app():
    """完整应用"""
    try:
        return send_from_directory('static', 'index.html')
    except:
        return "找不到static/index.html文件", 404

@app.route('/api/health')
def health():
    """健康检查"""
    return {'status': 'ok', 'message': '服务运行正常'}

@app.route('/api/layout/test')
def test_layout():
    """测试布局"""
    return {
        'success': True,
        'message': 'API工作正常',
        'test_data': {
            'tables': 5,
            'area': '150m²',
            'utilization': '20%'
        }
    }

if __name__ == '__main__':
    print("\n" + "="*50)
    print("台球桌自动布局系统 - 简化版")
    print("="*50)
    print("\n访问地址: http://localhost:8888")
    print("\n按 Ctrl+C 停止服务器\n")
    
    # 尝试多个端口
    ports = [8888, 8080, 5001, 3000, 9000]
    for port in ports:
        try:
            app.run(debug=True, port=port, host='127.0.0.1')
            break
        except OSError:
            print(f"端口 {port} 被占用，尝试下一个...")
            continue