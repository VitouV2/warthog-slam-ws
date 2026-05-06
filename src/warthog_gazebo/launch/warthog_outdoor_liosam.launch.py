from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution, Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([
            FindPackageShare('warthog_description'), 'urdf', 'warthog.urdf.xacro'
        ])]),
        value_type=str
    )

    # Farm outdoor world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution([
            FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
        ])]),
        launch_arguments={
            'gz_args': '-r /home/v2/warthog_ws/src/warthog_gazebo/worlds/outdoor_farm.sdf'
        }.items()
    )

    # Robot state publisher
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot_description}
        ],
        output='screen'
    )

    # Spawn Warthog at clear area near water tank
    spawn_warthog = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'warthog',
            '-topic', '/robot_description',
            '-x', '-30.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen'
    )

    # ROS-Gazebo bridge — using /warthog/lidar/points/points for PointCloud2
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/w200_0001/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/w200_0001/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/warthog/lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/warthog/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        output='screen'
    )

    # Static TF — connect Gazebo sensor frames to URDF frames
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'vlp16_link',
            'warthog/vlp16_link/vlp16_sensor'
        ],
        output='screen'
    )

    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'vlp16_imu_link',
            'warthog/vlp16_imu_link/vlp16_imu_sensor'
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        robot_state_pub,
        spawn_warthog,
        bridge,
        lidar_tf,
        imu_tf,
    ])
