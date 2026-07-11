"""Launch EL-A3 in Gazebo Sim with the same L7 gripper controller interface."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gui = LaunchConfiguration("gui")
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
        PathJoinSubstitution([FindPackageShare("el_a3_description"), "urdf", "el_a3.urdf.xacro"]),
        " use_gazebo:=true use_mock_hardware:=false",
    ])
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }
    controllers = PathJoinSubstitution(
        [FindPackageShare("el_a3_description"), "config", "el_a3_controllers.yaml"]
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": ["-r ", gui, " empty.sdf"]}.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
        output="screen",
    )
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "el_a3"],
        output="screen",
    )
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "--controller-manager", "/controller_manager", "--param-file", controllers],
        output="screen",
    )
    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager", "/controller_manager", "--param-file", controllers],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="-v 4", description="Gazebo GUI arguments; use -s for server only."),
        gz_sim,
        robot_state_publisher,
        # The Gazebo ROS 2 control system is created when the entity is spawned.
        TimerAction(period=2.0, actions=[spawn_robot]),
        TimerAction(period=6.0, actions=[joint_state_broadcaster, arm_controller, gripper_controller]),
    ])
