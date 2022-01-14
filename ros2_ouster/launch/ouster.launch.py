#!/usr/bin/python3
# Copyright 2020, Steve Macenski
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import LifecycleNode
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import EmitEvent
from launch.actions import RegisterEventHandler
from launch_ros.events.lifecycle import ChangeState
from launch_ros.events.lifecycle import matches_node_name
from launch_ros.event_handlers import OnStateTransition
from launch.actions import LogInfo
from launch.events import matches_action
from launch.event_handlers.on_shutdown import OnShutdown

import lifecycle_msgs.msg
import os


def generate_launch_description():
    share_dir = get_package_share_directory("ros2_ouster")
    parameter_file = LaunchConfiguration("params_file")
    namespace = LaunchConfiguration("namespace")
    node_name = "driver"

    params_declare = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(share_dir, "params", "sensor.yaml"),
        description="FPath to the ROS2 parameters file to use.",
    )
    namespace_declare = DeclareLaunchArgument(
        "namespace",
        default_value="ouster",
        description="Namespace for ouster driver node",
    )

    driver_node = LifecycleNode(
        package="ros2_ouster",
        executable="ouster_driver",
        name=node_name,
        output="screen",
        emulate_tty=True,
        parameters=[parameter_file],
        # namespace="/",
        namespace=namespace,
        # arguments=["--ros-args", "--log-level", "debug"],
    )

    configure_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=matches_action(driver_node),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    activate_event = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=driver_node,
            goal_state="inactive",
            entities=[
                LogInfo(msg="[LifecycleLaunch] Ouster driver node is activating."),
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(driver_node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )
                ),
            ],
        )
    )

    # TODO make lifecycle transition to shutdown before SIGINT
    shutdown_event = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_node_name(
                            node_name=[namespace, "/", node_name]
                        ),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVE_SHUTDOWN,
                    )
                ),
                LogInfo(msg="[LifecycleLaunch] Ouster driver node is exiting."),
            ],
        )
    )

    return LaunchDescription(
        [
            namespace_declare,
            params_declare,
            driver_node,
            activate_event,
            configure_event,
            shutdown_event,
        ]
    )
