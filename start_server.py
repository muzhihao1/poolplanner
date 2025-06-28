#!/usr/bin/env python3
"""
台球桌自动布局系统启动脚本
自动检测可用端口并启动服务器
"""

import socket
import sys
import os
from app import app

def find_free_port(start_port=8080, max_port=8090):
    """查找可用端口"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def main():
    print("=" * 50)
    print("🎱 台球桌自动布局系统")
    print("=" * 50)
    print()
    
    # 检查依赖
    print("📋 检查系统依赖...")
    try:
        import flask
        import numpy
        import scipy
        import shapely
        print("✅ 所有依赖已正确安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: python3 -m pip install -r requirements.txt")
        sys.exit(1)
    
    # 查找可用端口
    print("\n🔍 查找可用端口...")
    port = find_free_port()
    if not port:
        print("❌ 无法找到可用端口 (8080-8090)")
        sys.exit(1)
    
    print(f"✅ 找到可用端口: {port}")
    
    # 检查静态文件
    static_file = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
    if os.path.exists(static_file):
        print("✅ 前端页面文件存在")
    else:
        print("⚠️  前端页面文件不存在，只提供API服务")
    
    print(f"\n🚀 启动服务器...")
    print(f"📍 访问地址: http://127.0.0.1:{port}")
    print(f"📍 API文档: http://127.0.0.1:{port}/api/health")
    print(f"📍 测试接口: http://127.0.0.1:{port}/api/layout/test")
    print("\n按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='127.0.0.1', port=port)
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止，再见！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 