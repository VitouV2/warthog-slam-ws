#!/usr/bin/env python3
"""
Multi-Robot Coordinator Node
Shares sensor data (LaserScan, Odometry) between w200_0001 and a200_0001.
Publishes:
  /shared/w200_0001/scan  - warthog scan visible to husky
  /shared/a200_0001/scan  - husky scan visible to warthog
  /shared/w200_0001/odom  - warthog pose visible to husky
  /shared/a200_0001/odom  - husky pose visible to warthog
  /shared/distance        - distance between the two robots
  /shared/in_range        - True if robots are within communication range
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32, Bool
import math


class MultiRobotCoordinator(Node):

    def __init__(self):
        super().__init__('multi_robot_coordinator')

        # Communication range in meters (set to inf to disable constraint)
        self.declare_parameter('comm_range', 20.0)
        self.comm_range = self.get_parameter('comm_range').value

        self.get_logger().info(f'Communication range: {self.comm_range}m')

        # Store latest poses
        self.w200_odom = None
        self.a200_odom = None

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(LaserScan, '/w200_0001/scan', self.w200_scan_cb, 10)
        self.create_subscription(LaserScan, '/a200_0001/scan', self.a200_scan_cb, 10)
        self.create_subscription(Odometry,  '/w200_0001/odom', self.w200_odom_cb, 10)
        self.create_subscription(Odometry,  '/a200_0001/odom', self.a200_odom_cb, 10)

        # ── Publishers ───────────────────────────────────────────────────────
        self.w200_scan_pub  = self.create_publisher(LaserScan, '/shared/w200_0001/scan', 10)
        self.a200_scan_pub  = self.create_publisher(LaserScan, '/shared/a200_0001/scan', 10)
        self.w200_odom_pub  = self.create_publisher(Odometry,  '/shared/w200_0001/odom', 10)
        self.a200_odom_pub  = self.create_publisher(Odometry,  '/shared/a200_0001/odom', 10)
        self.distance_pub   = self.create_publisher(Float32,   '/shared/distance',        10)
        self.in_range_pub   = self.create_publisher(Bool,      '/shared/in_range',        10)

        # ── Timer: publish shared state at 10Hz ──────────────────────────────
        self.create_timer(0.1, self.publish_shared_state)

        self.get_logger().info('Multi-robot coordinator started!')

    def w200_odom_cb(self, msg):
        self.w200_odom = msg
        if self.in_range():
            self.w200_odom_pub.publish(msg)

    def a200_odom_cb(self, msg):
        self.a200_odom = msg
        if self.in_range():
            self.a200_odom_pub.publish(msg)

    def w200_scan_cb(self, msg):
        if self.in_range():
            self.w200_scan_pub.publish(msg)

    def a200_scan_cb(self, msg):
        if self.in_range():
            self.a200_scan_pub.publish(msg)

    def get_distance(self):
        """Calculate Euclidean distance between the two robots."""
        if self.w200_odom is None or self.a200_odom is None:
            return float('inf')
        w = self.w200_odom.pose.pose.position
        a = self.a200_odom.pose.pose.position
        return math.sqrt((w.x - a.x)**2 + (w.y - a.y)**2)

    def in_range(self):
        """Return True if robots are within communication range."""
        return self.get_distance() <= self.comm_range

    def publish_shared_state(self):
        dist = self.get_distance()
        in_range = dist <= self.comm_range

        # Publish distance
        dist_msg = Float32()
        dist_msg.data = float(dist) if dist != float('inf') else -1.0
        self.distance_pub.publish(dist_msg)

        # Publish in_range flag
        range_msg = Bool()
        range_msg.data = in_range
        self.in_range_pub.publish(range_msg)

        if dist != float('inf'):
            status = 'IN RANGE' if in_range else 'OUT OF RANGE'
            self.get_logger().info(
                f'Distance: {dist:.2f}m | {status} (limit: {self.comm_range}m)',
                throttle_duration_sec=2.0
            )


def main(args=None):
    rclpy.init(args=args)
    node = MultiRobotCoordinator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
