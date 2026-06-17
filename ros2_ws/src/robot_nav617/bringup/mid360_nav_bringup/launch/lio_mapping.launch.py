from launch import LaunchDescription
from launch.actions import LogInfo


def generate_launch_description():
    return LaunchDescription([
        LogInfo(msg='LIO/SLAM launch is reserved for the navigation layer. No algorithm node is started by this refactor.')
    ])
