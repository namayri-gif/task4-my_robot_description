import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    pkg_share = get_package_share_directory('my_robot_description')
    turtlebot3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')

    world_file = os.path.join(
        turtlebot3_gazebo_share,
        'worlds',
        'turtlebot3_world.world'
    )

    xacro_file = os.path.join(
        pkg_share,
        'urdf',
        'robot.urdf.xacro'
    )

    bridge_file = os.path.join(
        pkg_share,
        'config',
        'gz_bridge.yaml'
    )

    # NOTE: no mesh_path arg passed -- current xacro uses a plain
    # <cylinder> for lidar_link, not a <mesh> tag. Add mesh_path back
    # here only if you reintroduce a <mesh> reference in the xacro.
    robot_description = ParameterValue(
        Command(["xacro ", xacro_file]),
        value_type=str
    )

    # Sets GZ_SIM_RESOURCE_PATH for this launch only -- safer than
    # relying on ~/.bashrc, which we found wasn't actually persisting.
    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join([
            os.path.dirname(pkg_share),
            turtlebot3_gazebo_share
        ])
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}'
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True}
        ]
    )

    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        parameters=[{'use_sim_time': True}],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'my_robot',
            '-x', '-2.0',
            '-y', '0.5',
            '-z', '0.2',
        ],
        output='screen'
    )

    # Delay spawn so robot_state_publisher is guaranteed to be
    # publishing /robot_description before 'create' tries to read it
    delayed_spawn = TimerAction(period=3.0, actions=[spawn_robot])

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[
            {'config_file': bridge_file}
        ],
        output='screen'
    )


    return LaunchDescription([
        gazebo_resource_path,
        gazebo,
        robot_state_publisher,
        delayed_spawn,
        bridge,
        joint_state_publisher
    ])