#!/bin/bash

echo "台球桌自动布局系统启动脚本"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 启动应用
echo "启动Flask应用..."
echo "应用将运行在: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
python app.py