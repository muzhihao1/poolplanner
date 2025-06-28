#!/usr/bin/env python3
"""
简单启动脚本
"""

import subprocess
import sys
import os

print("台球桌自动布局系统")
print("==================")
print()

# 检查Python版本
print(f"Python版本: {sys.version}")
print()

# 检查是否安装了必要的包
try:
    import flask
    print("✓ Flask 已安装")
except ImportError:
    print("✗ Flask 未安装")
    print("请先运行: pip install flask flask-cors")
    sys.exit(1)

try:
    import numpy
    print("✓ NumPy 已安装")
except ImportError:
    print("✗ NumPy 未安装")
    print("请先运行: pip install numpy")
    sys.exit(1)

print()
print("启动服务器...")
print("访问地址: http://localhost:8080")
print("按 Ctrl+C 停止服务器")
print()

# 启动Flask应用
try:
    subprocess.run([sys.executable, "app.py"], check=True)
except KeyboardInterrupt:
    print("\n服务器已停止")
except Exception as e:
    print(f"启动失败: {e}")