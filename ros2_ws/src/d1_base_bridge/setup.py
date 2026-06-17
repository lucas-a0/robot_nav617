from setuptools import setup
import os
from glob import glob

package_name = 'd1_base_bridge'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sunrise',
    maintainer_email='sunrise@example.com',
    description='Bridge standard /cmd_vel to D1 SDK /d15020024/command/cmd_twist with safety limits and watchdog.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'd1_base_bridge = d1_base_bridge.d1_base_bridge_node:main',
        ],
    },
)
