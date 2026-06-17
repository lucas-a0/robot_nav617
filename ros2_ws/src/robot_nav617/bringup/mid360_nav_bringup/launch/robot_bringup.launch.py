import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = get_package_share_directory('mid360_nav_bringup')
    navigation_share = get_package_share_directory('robot_nav617_navigation')
    livox_share = get_package_share_directory('livox_ros_driver2')

    robot_description_path = os.path.join(bringup_share, 'urdf', 'robot.urdf.xacro')
    rviz_config_path = os.path.join(navigation_share, 'config', 'rviz_mid360.rviz')
    nav2_params_path = os.path.join(navigation_share, 'config', 'nav2_params.yaml')
    map_path = os.path.join(navigation_share, 'config', 'map_nav2', 'map.yaml')
    mid360_config_path = os.path.join(livox_share, 'config', 'MID360_config.json')

    use_lidar = LaunchConfiguration('use_lidar')
    use_base_bridge = LaunchConfiguration('use_base_bridge')
    use_nav = LaunchConfiguration('use_nav')
    use_rviz = LaunchConfiguration('use_rviz')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', robot_description_path]),
                value_type=str,
            )
        }],
    )

    lidar_node = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        condition=IfCondition(use_lidar),
        parameters=[{
            'xfer_format': 1,
            'multi_topic': 0,
            'data_src': 0,
            'publish_freq': 10.0,
            'output_data_type': 0,
            'frame_id': 'lidar_link',
            'lvx_file_path': '/home/livox/livox_test.lvx',
            'user_config_path': mid360_config_path,
            'cmdline_input_bd_code': 'livox0000000001',
        }],
    )

    base_bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('d1_base_bridge'),
                'launch',
                'd1_base_bridge.launch.py',
            ])
        ),
        condition=IfCondition(use_base_bridge),
    )

    nav_stack_placeholder = ExecuteProcess(
        cmd=[
            'ros2',
            'launch',
            'nav2_bringup',
            'bringup_launch.py',
            f'params_file:={nav2_params_path}',
            f'map:={map_path}',
        ],
        output='screen',
        condition=IfCondition(use_nav),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(use_rviz),
        arguments=['-d', rviz_config_path],
    )

    static_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_map_to_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
    )

    static_odom_to_base = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_odom_to_base_link',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_lidar', default_value='true'),
        DeclareLaunchArgument('use_base_bridge', default_value='true'),
        DeclareLaunchArgument('use_nav', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        robot_state_publisher,
        static_map_to_odom,
        static_odom_to_base,
        lidar_node,
        base_bridge_launch,
        LogInfo(
            msg='Nav2 placeholder enabled: launching nav2_bringup with navigation/config parameters.',
            condition=IfCondition(use_nav),
        ),
        nav_stack_placeholder,
        rviz_node,
    ])
