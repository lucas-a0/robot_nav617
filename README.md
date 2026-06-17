# mid360_nav_project

ROS 2 Humble 庭院机器人项目。当前阶段重点是工程结构重构和统一启动入口整理，为后续接入 SLAM、Nav2、视觉、语音和行为决策打基础。

项目目标硬件：

- 地平线 RDK S100
- Livox MID360 LiDAR
- RealSense D415 或 USB 摄像头
- STM32 底盘控制器，通过 `d1_base_bridge` 与 ROS 2 通信

当前已经整理好的核心能力：

- MID360 雷达驱动包归档到传感器层
- D1/STM32 底盘桥接包归档到控制层
- 新增统一 bringup 入口
- 新增导航配置包，用于集中管理 Nav2、SLAM、RViz、地图配置
- 建立标准 TF 骨架

## 工程结构

```text
mid360_nav_project/
├── docs/                         # 网络、驱动、LIO、Nav2、调试文档
├── prompts/                      # 阶段性生成提示词记录
├── ros2_ws/
│   └── src/
│       └── robot_nav617/
│           ├── bringup/
│           │   └── mid360_nav_bringup/
│           │       ├── launch/
│           │       │   ├── robot_bringup.launch.py
│           │       │   ├── all_bringup.launch.py
│           │       │   ├── mid360_driver.launch.py
│           │       │   ├── mid360_rviz.launch.py
│           │       │   ├── nav2_navigation.launch.py
│           │       │   └── lio_mapping.launch.py
│           │       └── urdf/
│           │           └── robot.urdf.xacro
│           ├── navigation/
│           │   ├── package.xml
│           │   ├── CMakeLists.txt
│           │   └── config/
│           │       ├── nav2_params.yaml
│           │       ├── costmap_params.yaml
│           │       ├── lio_mid360.yaml
│           │       ├── rviz_mid360.rviz
│           │       ├── map_nav2/
│           │       ├── pcd/
│           │       └── grid/
│           ├── sensors/
│           │   └── lidar/
│           │       ├── livox_ros_driver2/
│           │       └── livox_interfaces/
│           ├── control/
│           │   └── base_bridge/
│           │       └── d1_base_bridge/
│           ├── perception/        # 视觉/感知算法预留
│           ├── voice/             # 语音模块预留
│           ├── behavior_tree/     # 行为决策层预留
│           ├── config/            # 全局配置预留
│           ├── launch/            # 顶层 launch 转发入口
│           └── scripts/           # 工具脚本
└── bags/                          # rosbag 数据预留
```

## ROS 2 包

当前 `colcon` 可识别的包：

```text
d1_base_bridge            control/base_bridge/d1_base_bridge
livox_interfaces          sensors/lidar/livox_interfaces
livox_ros_driver2         sensors/lidar/livox_ros_driver2
mid360_nav_bringup        bringup/mid360_nav_bringup
robot_nav617_navigation   navigation
```

模块职责：

- `mid360_nav_bringup`：机器人总启动入口，负责组合雷达、底盘桥接、RViz、Nav2 占位和 TF 框架。
- `robot_nav617_navigation`：集中安装导航相关配置、地图、RViz 配置和 SLAM 参数。
- `livox_ros_driver2`：Livox MID360 ROS 2 驱动，保持上游驱动内部代码不变。
- `livox_interfaces`：Livox 自定义消息接口。
- `d1_base_bridge`：将标准 `/cmd_vel` 转换到底盘控制器使用的话题。

## 构建

进入 ROS 2 workspace：

```bash
cd ~/mid360_nav_project/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

也可以使用脚本：

```bash
cd ~/mid360_nav_project
bash ros2_ws/src/robot_nav617/scripts/build_ws.sh
```

注意：`livox_ros_driver2` 依赖 Livox SDK、PCL、APR 等系统依赖。若只验证重构后的包装层，可先构建：

```bash
colcon build --symlink-install --packages-select robot_nav617_navigation mid360_nav_bringup d1_base_bridge
```

如果移动目录后旧 `build/` 缓存报出旧路径相关 CMake 错误，可以清理对应包的旧缓存后重新构建。

## 统一启动

主启动入口：

```bash
ros2 launch mid360_nav_bringup robot_bringup.launch.py
```

启动参数：

```text
use_lidar:=true          # 启动 MID360 雷达
use_base_bridge:=true    # 启动 d1_base_bridge
use_nav:=false           # Nav2 占位入口，默认关闭
use_rviz:=true           # 启动 RViz
```

示例：

```bash
# 默认：雷达 + 底盘桥接 + RViz + TF 框架
ros2 launch mid360_nav_bringup robot_bringup.launch.py

# 只启动雷达和 TF，不启动底盘桥接和 RViz
ros2 launch mid360_nav_bringup robot_bringup.launch.py use_base_bridge:=false use_rviz:=false

# 启动 Nav2 占位入口
ros2 launch mid360_nav_bringup robot_bringup.launch.py use_nav:=true
```

兼容入口：

```bash
ros2 launch mid360_nav_bringup all_bringup.launch.py
ros2 launch mid360_nav_bringup mid360_driver.launch.py
ros2 launch mid360_nav_bringup mid360_rviz.launch.py
ros2 launch mid360_nav_bringup nav2_navigation.launch.py
ros2 launch mid360_nav_bringup lio_mapping.launch.py
```

## TF 框架

当前只建立固定 TF 框架，不包含定位、里程计或 SLAM 算法：

```text
map
└── odom
    └── base_link
        ├── lidar_link
        ├── camera_link
        └── imu_link
```

实现位置：

```text
ros2_ws/src/robot_nav617/bringup/mid360_nav_bringup/urdf/robot.urdf.xacro
ros2_ws/src/robot_nav617/bringup/mid360_nav_bringup/launch/robot_bringup.launch.py
```

当前 `map -> odom` 和 `odom -> base_link` 使用静态 TF 占位。后续接入 SLAM/定位和底盘里程计后，应由对应算法节点发布这些变换。

## 底盘桥接

`d1_base_bridge` 输入标准速度指令：

```text
/cmd_vel
```

输出到底盘控制器：

```text
/d15020024/command/cmd_twist
```

配置文件：

```text
ros2_ws/src/robot_nav617/control/base_bridge/d1_base_bridge/config/d1_base_bridge.yaml
```

默认参数偏保守，限制线速度和角速度，适合初次联调：

```text
max_linear_x: 0.08
max_linear_y: 0.00
max_angular_z: 0.20
watchdog_timeout_sec: 0.5
```

## 雷达驱动

MID360 驱动位于：

```text
ros2_ws/src/robot_nav617/sensors/lidar/livox_ros_driver2
```

统一启动入口会启动：

```text
package: livox_ros_driver2
executable: livox_ros_driver2_node
node name: livox_lidar_publisher
frame_id: lidar_link
config: livox_ros_driver2/config/MID360_config.json
```

MID360 网络配置和驱动调试说明见：

```text
docs/01_mid360_network.md
docs/02_livox_driver.md
```

## 导航配置

导航相关资源统一放在：

```text
ros2_ws/src/robot_nav617/navigation/config/
```

包含：

```text
nav2_params.yaml          # Nav2 参数占位
costmap_params.yaml       # costmap 参数占位
lio_mid360.yaml           # LIO/SLAM 参数占位
rviz_mid360.rviz          # RViz 配置占位
map_nav2/map.yaml         # 2D 栅格地图
map_nav2/map.pgm
pcd/map.pcd               # 点云地图
pcd/patches/
grid/
```

## 当前状态

已完成：

- 工程目录按 `bringup / navigation / sensors / control / perception / voice / behavior_tree` 分层。
- `livox_ros_driver2` 和 `livox_interfaces` 归入 `sensors/lidar`。
- `d1_base_bridge` 归入 `control/base_bridge`。
- 地图、RViz、Nav2、LIO 配置归入 `navigation/config`。
- 新增 `robot_nav617_navigation` 配置包。
- 新增 `robot_bringup.launch.py` 一键入口。
- 建立 `map / odom / base_link / lidar_link / camera_link / imu_link` TF 骨架。

待完善：

- 填写 `nav2_params.yaml`、`costmap_params.yaml`、`lio_mid360.yaml`。
- 补齐 `rviz_mid360.rviz` 显示配置。
- 用真实里程计或 EKF 替换静态 `odom -> base_link`。
- 用 SLAM/定位节点替换静态 `map -> odom`。
- 接入 RealSense D415 或 USB 摄像头驱动。
- 接入语音模块和行为树。

## 常用检查命令

```bash
# 查看包识别结果
colcon list --base-paths ros2_ws/src

# 查看启动参数
ros2 launch mid360_nav_bringup robot_bringup.launch.py --show-args

# 查看 TF
ros2 run tf2_tools view_frames

# 查看话题
ros2 topic list

# 查看底盘桥接状态
ros2 topic echo /d1_base_bridge/status
```
