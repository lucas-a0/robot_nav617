#!/bin/bash
set -e

PROJECT_DIR=$HOME/mid360_nav_project
WS_DIR=$PROJECT_DIR/ros2_ws

source /opt/ros/humble/setup.bash

cd $WS_DIR

echo "=== 开始编译 ROS2 工作空间 ==="
colcon build --symlink-install

echo "=== 编译完成 ==="
echo "请执行："
echo "source $WS_DIR/install/setup.bash"
