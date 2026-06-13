from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lsep_ros2',
            executable='lsep_node',
            name='lsep_node',
            output='screen',
            parameters=[{
                'autostart': True,
                'publish_rate_hz': 10.0,
                'dwell_de_escalation_s': 1.5,
                'input_timeout_s': 0.5,
            }],
        ),
        Node(
            package='lsep_ros2',
            executable='simulated_human',
            name='simulated_human',
            output='screen',
        ),
    ])
