#!/bin/bash

echo "安装台球桌自动布局系统依赖"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "安装依赖包..."
pip3 install -r requirements.txt

echo ""
echo "依赖安装完成！"
echo ""
echo "现在可以运行: python3 app.py 启动应用"
echo "或者运行: ./run.sh 使用启动脚本"