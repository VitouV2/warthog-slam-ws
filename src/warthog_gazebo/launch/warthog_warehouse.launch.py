from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    # Declare namespace argument
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='w200_0001',
        description='Namespace for the Warthog robot'
    )
    namespace = LaunchConfiguration('namespace')

    # Load URDF from warthog_description
    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([
                FindPackageShare('warthog_description'),
                'urdf', 'warthog.urdf.xacro'
            ]),
            ' is_sim:=true'
        ]),
        value_type=str
    )

    # Launch Gazebo Fortress with warehouse world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': '-r /opt/ros/humble/share/clearpath_gz/worlds/warehouse.sdf'
        }.items()
    )
    
    # Robot State Publisher (NO namespace - so gz_ros2_control can find it)
    robot_state_pub = Node(
    	package='robot_state_publisher',
    	executable='robot_state_publisher',
    	parameters=[
    		{'use_sim_time': True},
        	{'robot_description': robot_description}
    	],
    	remappings=[
        	('/tf', 'tf'),
        	('/tf_static', 'tf_static')
    	],
    	output='screen'
    )
    
    # Spawn using global /robot_description topic
    spawn_warthog = Node(
   	package='ros_gz_sim',
    	executable='create',
    	arguments=[
    		'-name', 'warthog',
        	'-topic', '/robot_description',
        	'-x', '0.0',
        	'-y', '0.0',
        	'-z', '0.1',
    	],
    	output='screen'
    )

    # ROS-Gazebo Bridge (cmd_vel + odom + clock)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/w200_0001/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/w200_0001/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/w200_0001/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )

    return LaunchDescription([
        namespace_arg,
        gz_sim,
        robot_state_pub,
        spawn_warthog,
        bridge,
    ])
