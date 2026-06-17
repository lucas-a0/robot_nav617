from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('mid360_nav_bringup'),
                    'launch',
                    'robot_bringup.launch.py',
                ])
            ),
            launch_arguments={
                'use_lidar': 'false',
                'use_base_bridge': 'false',
                'use_nav': 'true',
                'use_rviz': 'false',
            }.items(),
        )
    ])
