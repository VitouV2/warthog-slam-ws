import re
import subprocess
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution, Command
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    warthog_ns = 'w200_0001'
    husky_ns = 'a200_0001'

    # Warthog URDF
    warthog_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([
                FindPackageShare('warthog_description'),
                'urdf',
                'warthog.urdf.xacro'
            ]),
        ]),
        value_type=str
    )

    # Husky URDF - strip ros2_control to avoid hardware plugin crash
    husky_urdf_raw = subprocess.check_output([
        'xacro',
        '/home/v2/warthog_ws/install/husky_description/share/husky_description/urdf/husky.urdf.xacro'
    ]).decode('utf-8')
    husky_urdf = re.sub(r'<ros2_control.*?</ros2_control>', '', husky_urdf_raw, flags=re.DOTALL)

    # Gazebo warehouse world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': '-r /opt/ros/humble/share/clearpath_gz/worlds/warehouse.sdf'
        }.items()
    )

    # Warthog RSP (namespaced)
    warthog_rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=warthog_ns,
        parameters=[
            {'use_sim_time': True},
            {'robot_description': warthog_description},
            {'frame_prefix': warthog_ns + '/'}
        ],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
        output='screen'
    )

    # Spawn warthog
    spawn_warthog = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', warthog_ns,
            '-topic', '/' + warthog_ns + '/robot_description',
            '-x', '-5.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen'
    )

    # Husky RSP (namespaced)
    husky_rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=husky_ns,
        parameters=[
            {'use_sim_time': True},
            {'robot_description': husky_urdf},
            {'frame_prefix': husky_ns + '/'}
        ],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
        output='screen'
    )

    # Spawn husky
    spawn_husky = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', husky_ns,
            '-topic', '/' + husky_ns + '/robot_description',
            '-x', '5.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen'
    )

    # ROS-Gazebo bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # Warthog
            '/' + warthog_ns + '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/' + warthog_ns + '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/' + warthog_ns + '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/warthog/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',  # ← ADD
            '/warthog/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',  
            # Husky
            '/' + husky_ns + '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/' + husky_ns + '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/' + husky_ns + '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # Husky sensors
            '/sensors/lidar_0/scan/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/sensors/lidar_0/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/sensors/imu_0/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        output='screen'
    )

    # Relay LiDAR to a200_0001 namespace
    lidar_relay = Node(
        package='topic_tools',
        executable='relay',
        arguments=[
            '/sensors/lidar_0/scan/points',
            '/' + husky_ns + '/points_raw'
        ],
        output='screen'
    )
    # Relay IMU to a200_0001 namespace (existing)
    imu_relay = Node(
        package='topic_tools',
        executable='relay',
        arguments=[
            '/sensors/imu_0/data',
            '/' + husky_ns + '/imu/data'
        ],
        output='screen'
    )
    # Relay LiDAR to warthog namespace   ← ADD THIS
    warthog_lidar_relay = Node(
        package='topic_tools',
        executable='relay',
        arguments=[
            '/sensors/lidar_0/scan/points',
            '/warthog/lidar/points'
        ],
        output='screen'
    )
    # Relay IMU to warthog namespace   ← ADD THIS
    warthog_imu_relay = Node(
        package='topic_tools',
        executable='relay',
        arguments=[
            '/sensors/imu_0/data',
            '/warthog/imu/data'
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        warthog_rsp,
        spawn_warthog,
        husky_rsp,
        spawn_husky,
        bridge,
        lidar_relay,
        imu_relay,
	warthog_lidar_relay,
	warthog_imu_relay,
    ])
