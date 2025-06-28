#!/bin/bash

echo "安装台球桌自动布局系统依赖"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 在WebContainer环境中，只能使用标准库
echo "注意：当前环境仅支持Python标准库"
echo "以下依赖包在WebContainer中不可用："
echo "- Flask (Web框架)"
echo "- flask-cors (跨域支持)"
echo "- numpy (数值计算)"
echo "- scipy (科学计算)"
echo "- shapely (几何处理)"
echo "- opencv-python (图像处理)"
echo "- rtree (空间索引)"
echo ""
echo "建议在本地环境中运行完整功能版本"
echo "或使用简化版本进行测试"
echo ""
echo "现在可以运行: python3 simple_app.py 启动简化版应用"