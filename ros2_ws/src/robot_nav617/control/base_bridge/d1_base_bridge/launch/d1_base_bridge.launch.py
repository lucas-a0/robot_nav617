#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('d1_base_bridge')
    config_file = os.path.join(pkg_share, 'config', 'd1_base_bridge.yaml')

    d1_base_bridge_node = Node(
        package='d1_base_bridge',
        executable='d1_base_bridge',
        name='d1_base_bridge',
        output='screen',
        parameters=[config_file],
    )

    return LaunchDescription([
        d1_base_bridge_node
    ])
