#!/bin/bash

echo "台球桌自动布局系统启动脚本"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

echo ""
echo "注意：WebContainer环境限制"
echo "- 无法安装第三方Python包"
echo "- 仅支持Python标准库"
echo ""

# 检查是否存在简化版本
if [ -f "simple_app.py" ]; then
    echo "启动简化版应用..."
    echo "应用将运行在: http://localhost:8080"
    echo "按 Ctrl+C 停止服务器"
    python3 simple_app.py
else
    echo "未找到简化版应用文件"
    echo "请确保 simple_app.py 文件存在"
    echo ""
    echo "或者在支持pip的环境中运行："
    echo "pip3 install -r requirements.txt"
    echo "python3 app.py"
fi