#!/bin/bash

echo "安装台球桌自动布局系统依赖"
echo "=========================="

# 使用pip3安装基本依赖
echo "安装基本依赖包..."
pip3 install flask flask-cors numpy

echo ""
echo "基本依赖安装完成！"
echo ""
echo "注意：完整功能需要安装以下包："
echo "- scipy (科学计算)"
echo "- shapely (几何处理)"
echo "- opencv-python (图像处理)"
echo "- rtree (空间索引)"
echo ""
echo "可以运行以下命令安装完整依赖："
echo "pip3 install -r requirements.txt"
echo ""
echo "现在可以运行: python3 app.py 启动应用"