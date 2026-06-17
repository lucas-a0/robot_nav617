#!/bin/bash
set -e

echo "=== 安装 MID360 + ROS2 Humble 导航工程基础依赖 ==="

sudo apt update

sudo apt install -y \
  git \
  wget \
  curl \
  vim \
  tree \
  net-tools \
  iputils-ping \
  dnsutils \
  arp-scan \
  build-essential \
  cmake \
  python3-pip \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  libpcl-dev \
  libeigen3-dev \
  libboost-all-dev

sudo apt install -y \
  ros-humble-rviz2 \
  ros-humble-tf2-tools \
  ros-humble-tf-transformations \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-nav2-bringup \
  ros-humble-navigation2 \
  ros-humble-pcl-ros \
  ros-humble-pcl-conversions

echo "=== 依赖安装完成 ==="
