from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    namespace = LaunchConfiguration('namespace', default='warthog')

    # Launch Gazebo Fortress with warehouse world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': '-r warehouse.sdf'   # or your custom world
        }.items()
    )

    # Spawn Warthog with namespace
    spawn_warthog = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'warthog',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.1',
        ],
        namespace=namespace,
        output='screen'
    )

    # Robot State Publisher (namespaced)
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=namespace,
        parameters=[{'use_sim_time': True}],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
        output='screen'
    )

    # ROS-Gazebo Bridge (cmd_vel + odom + clock)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        namespace=namespace,
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/warthog/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/warthog/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/warthog/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        robot_state_pub,
        spawn_warthog,
        bridge,
    ])
