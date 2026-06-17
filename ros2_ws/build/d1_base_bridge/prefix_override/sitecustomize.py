import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/sunrise/mid360_nav_project/ros2_ws/install/d1_base_bridge'
