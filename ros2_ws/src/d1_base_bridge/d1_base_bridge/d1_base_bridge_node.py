#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
d1_base_bridge_node.py

功能：
1. 订阅标准 ROS2 导航速度话题 /cmd_vel，类型 geometry_msgs/msg/Twist
2. 限速、死区、异常值过滤
3. 发布到底盘 SDK 速度话题 /d15020024/command/cmd_twist
4. 默认输出类型为 geometry_msgs/msg/TwistStamped，匹配 D1 控制器
5. watchdog 超时自动持续发布零速度
6. 节点退出时自动发布一次零速度

后续预留：
1. 接入 Nav2 controller_server 输出的 /cmd_vel
2. 增加 /odom 发布
3. 增加 odom -> base_link TF
4. 接入 AMCL 发布 map -> odom
5. 和 MID360 的 base_link -> livox_frame 静态 TF 联动
"""

import math
from typing import Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from std_msgs.msg import String


class D1BaseBridge(Node):
    def __init__(self):
        super().__init__('d1_base_bridge')

        self.declare_parameter('input_cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('output_cmd_twist_topic', '/d15020024/command/cmd_twist')
        self.declare_parameter('status_topic', '/d1_base_bridge/status')

        self.declare_parameter('output_msg_type', 'twist_stamped')
        self.declare_parameter('output_frame_id', 'base_link')

        self.declare_parameter('max_linear_x', 0.08)
        self.declare_parameter('max_linear_y', 0.00)
        self.declare_parameter('max_angular_z', 0.20)

        self.declare_parameter('linear_deadband', 0.005)
        self.declare_parameter('angular_deadband', 0.005)

        self.declare_parameter('watchdog_timeout_sec', 0.5)
        self.declare_parameter('watchdog_publish_rate', 20.0)

        self.input_cmd_vel_topic = self.get_parameter('input_cmd_vel_topic').value
        self.output_cmd_twist_topic = self.get_parameter('output_cmd_twist_topic').value
        self.status_topic = self.get_parameter('status_topic').value

        self.output_msg_type = str(self.get_parameter('output_msg_type').value).strip().lower()
        self.output_frame_id = str(self.get_parameter('output_frame_id').value).strip()

        self.max_linear_x = float(self.get_parameter('max_linear_x').value)
        self.max_linear_y = float(self.get_parameter('max_linear_y').value)
        self.max_angular_z = float(self.get_parameter('max_angular_z').value)

        self.linear_deadband = float(self.get_parameter('linear_deadband').value)
        self.angular_deadband = float(self.get_parameter('angular_deadband').value)

        self.watchdog_timeout_sec = float(self.get_parameter('watchdog_timeout_sec').value)
        self.watchdog_publish_rate = float(self.get_parameter('watchdog_publish_rate').value)

        if self.output_msg_type not in ['twist_stamped', 'twist']:
            self.get_logger().warn(
                f'Invalid output_msg_type={self.output_msg_type}, force set to twist_stamped'
            )
            self.output_msg_type = 'twist_stamped'

        if self.watchdog_publish_rate <= 0.0:
            self.get_logger().warn('watchdog_publish_rate <= 0, force set to 20.0 Hz')
            self.watchdog_publish_rate = 20.0

        self.cmd_sub = self.create_subscription(
            Twist,
            self.input_cmd_vel_topic,
            self.cmd_vel_callback,
            10
        )

        if self.output_msg_type == 'twist_stamped':
            self.cmd_pub = self.create_publisher(
                TwistStamped,
                self.output_cmd_twist_topic,
                10
            )
        else:
            self.cmd_pub = self.create_publisher(
                Twist,
                self.output_cmd_twist_topic,
                10
            )

        self.status_pub = self.create_publisher(
            String,
            self.status_topic,
            10
        )

        self.last_cmd_time = self.get_clock().now()
        self.received_cmd_once = False

        timer_period = 1.0 / self.watchdog_publish_rate
        self.watchdog_timer = self.create_timer(timer_period, self.watchdog_callback)

        self.get_logger().info('d1_base_bridge started.')
        self.get_logger().info(f'Subscribe : {self.input_cmd_vel_topic} [geometry_msgs/msg/Twist]')
        self.get_logger().info(
            f'Publish   : {self.output_cmd_twist_topic} '
            f'[{self.output_msg_type}]'
        )
        self.get_logger().info(f'Status    : {self.status_topic}')
        self.get_logger().info(f'Frame ID  : {self.output_frame_id}')
        self.get_logger().info(
            'Limits    : '
            f'max_linear_x={self.max_linear_x:.3f}, '
            f'max_linear_y={self.max_linear_y:.3f}, '
            f'max_angular_z={self.max_angular_z:.3f}'
        )
        self.get_logger().info(
            'Deadband  : '
            f'linear_deadband={self.linear_deadband:.4f}, '
            f'angular_deadband={self.angular_deadband:.4f}'
        )
        self.get_logger().info(
            'Watchdog  : '
            f'timeout={self.watchdog_timeout_sec:.3f}s, '
            f'publish_rate={self.watchdog_publish_rate:.1f}Hz'
        )

        self.publish_status('d1_base_bridge started')

    def safe_float(self, value: Optional[float]) -> float:
        try:
            if value is None:
                return 0.0
            value = float(value)
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return value
        except Exception:
            return 0.0

    def clamp(self, value: float, limit_abs: float) -> float:
        limit_abs = abs(float(limit_abs))
        if limit_abs <= 0.0:
            return 0.0
        return max(-limit_abs, min(limit_abs, value))

    def apply_deadband(self, value: float, deadband: float) -> float:
        if abs(value) < abs(deadband):
            return 0.0
        return value

    def make_zero_twist(self) -> Twist:
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0
        return msg

    def filter_cmd(self, msg: Twist) -> Twist:
        out = Twist()

        linear_x = self.safe_float(msg.linear.x)
        linear_y = self.safe_float(msg.linear.y)
        angular_z = self.safe_float(msg.angular.z)

        linear_x = self.apply_deadband(linear_x, self.linear_deadband)
        linear_y = self.apply_deadband(linear_y, self.linear_deadband)
        angular_z = self.apply_deadband(angular_z, self.angular_deadband)

        out.linear.x = self.clamp(linear_x, self.max_linear_x)

        if self.max_linear_y <= 0.0:
            out.linear.y = 0.0
        else:
            out.linear.y = self.clamp(linear_y, self.max_linear_y)

        out.linear.z = 0.0
        out.angular.x = 0.0
        out.angular.y = 0.0
        out.angular.z = self.clamp(angular_z, self.max_angular_z)

        return out

    def to_output_msg(self, twist: Twist):
        if self.output_msg_type == 'twist_stamped':
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.output_frame_id
            msg.twist = twist
            return msg

        return twist

    def cmd_vel_callback(self, msg: Twist):
        safe_cmd = self.filter_cmd(msg)
        self.last_cmd_time = self.get_clock().now()
        self.received_cmd_once = True
        self.cmd_pub.publish(self.to_output_msg(safe_cmd))

    def watchdog_callback(self):
        now = self.get_clock().now()
        dt = (now - self.last_cmd_time).nanoseconds / 1e9

        if (not self.received_cmd_once) or dt > self.watchdog_timeout_sec:
            zero_cmd = self.make_zero_twist()
            self.cmd_pub.publish(self.to_output_msg(zero_cmd))

    def publish_status(self, text: str):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)

    def stop_robot(self):
        zero_cmd = self.make_zero_twist()
        self.cmd_pub.publish(self.to_output_msg(zero_cmd))
        self.publish_status('d1_base_bridge stopped, zero velocity published')
        self.get_logger().warn('Published zero velocity before shutdown.')


def main(args=None):
    rclpy.init(args=args)
    node = D1BaseBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().warn('KeyboardInterrupt received.')
    except Exception as e:
        node.get_logger().error(f'Unexpected error: {e}')
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
