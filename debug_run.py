#!/usr/bin/env python3
"""
调试启动脚本
"""

import os
import sys

print("=== 调试信息 ===")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"切换后目录: {os.getcwd()}")

# 检查文件
print("\n=== 文件检查 ===")
files_to_check = ['app.py', 'static/index.html', 'core/__init__.py']
for f in files_to_check:
    exists = os.path.exists(f)
    print(f"{f}: {'✓ 存在' if exists else '✗ 不存在'}")

# 检查依赖
print("\n=== 依赖检查 ===")
dependencies = {
    'flask': 'Flask',
    'flask_cors': 'flask-cors',
    'numpy': 'numpy'
}

missing_deps = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"{name}: ✓ 已安装")
    except ImportError:
        print(f"{name}: ✗ 未安装")
        missing_deps.append(name)

if missing_deps:
    print(f"\n请先安装缺失的依赖: pip3 install {' '.join(missing_deps)}")
    sys.exit(1)

print("\n=== 启动应用 ===")
print("尝试在不同端口启动...")

# 尝试多个端口
ports = [8080, 8888, 5001, 3000]
for port in ports:
    print(f"\n尝试端口 {port}...")
    try:
        # 动态修改app.py中的端口
        from app import app
        print(f"启动服务器: http://localhost:{port}")
        print("按 Ctrl+C 停止")
        app.run(debug=True, port=port, host='127.0.0.1')
        break
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"端口 {port} 已被占用，尝试下一个...")
            continue
        else:
            print(f"错误: {e}")
            break
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        break