# Task 4: Build and Simulate a Differential Drive Robot with LiDAR
## Overview
This project implements a complete mobile robot simulation from scratch using URDF, TF, RViz, and Gazebo (`gz sim`).
The robot is a four-wheel differential drive platform, simulated with a Gazebo `DiffDrive` plugin, publishing odometry on `/odom`, broadcasting a full TF tree, and carrying a LiDAR sensor that publishes `/scan`.
This task covers the complete ROS 2 robot simulation workflow: building a robot from URDF, visualizing it in RViz, simulating it in Gazebo, controlling it via keyboard teleoperation, and adding LiDAR sensing.

---
## What I Learned
How to create robot models using URDF (links, joints, visual/collision/inertial properties)
How `continuous` and `fixed` joints behave differently, and how each is broadcast in TF
How to debug and read a TF tree using `tf2_tools` and `ros2 topic echo`
How to configure a Gazebo `gz::sim::systems::DiffDrive` plugin for a 4-wheel robot using two driven axles
How ROS 2 and `gz sim` are separate transport layers, and why a `ros_gz_bridge` is required to connect topics like `/cmd_vel`, `/odom`, `/tf`, `/scan`, and `/joint_states` between them
How to debug common simulation issues: duplicate nodes, race conditions on spawn, QoS/topic mismatches, and mesh resource path resolution
How to add a LiDAR sensor (mesh + Gazebo `gpu_lidar` plugin) and publish `/scan`

---
## Project Structure
```
my_robot_description/
├── launch/
│   ├── display.launch.py
│   └── gazebo.launch.py
│
├── urdf/
│   └── robot.urdf
│
├── meshes/
│   ├── lidar.STL
│   └── zed.stl
│
├── rviz/
│   └── robot.rviz
│
├── package.xml
└── CMakeLists.txt
```
---
### Robot Description
Links
Link	Geometry	Description
`base_link`	Box	Main chassis
`left_front_wheel_link`	Cylinder	Front-left wheel (driven)
`right_front_wheel_link`	Cylinder	Front-right wheel (driven)
`left_back_wheel_link`	Cylinder	Rear-left wheel
`right_back_wheel_link`	Cylinder	Rear-right wheel
`lidar_link`	Mesh (STL)	LiDAR sensor, mounted on top of chassis
Joints
Joint	Type	Parent → Child
`*_wheel_joint` (×4)	`continuous`	`base_link` → `*_wheel_link`
`lidar_joint`	`fixed`	`base_link` → `lidar_link`

---
### Gazebo Plugins
Plugin	Purpose
`gz::sim::systems::DiffDrive`	Subscribes to `/cmd_vel`, drives the front and rear axles, publishes `/odom` and the `odom → base_link` TF
`gz::sim::systems::JointStatePublisher`	Publishes wheel joint angles for `robot_state_publisher` to broadcast wheel TF
`gz::sim::systems::OdometryPublisher`	Publishes odometry data
`gpu_lidar` sensor (on `lidar_link`)	Simulates the LiDAR, publishes scan data on `/scan`

---
### Topics Used
Topic	Type	Direction	Purpose
`/cmd_vel`	`geometry_msgs/msg/Twist`	ROS 2 → Gazebo	Robot velocity commands
`/odom`	`nav_msgs/msg/Odometry`	Gazebo → ROS 2	Robot pose/velocity estimate
`/tf`, `/tf_static`	`tf2_msgs/msg/TFMessage`	Gazebo → ROS 2	Transform tree
`/joint_states`	`sensor_msgs/msg/JointState`	Gazebo → ROS 2	Wheel joint angles (needed for wheel TF)
`/scan`	`sensor_msgs/msg/LaserScan`	Gazebo → ROS 2	LiDAR scan data
`/clock`	`rosgraph_msgs/msg/Clock`	Gazebo → ROS 2	Simulation time, for `use_sim_time`
All of the above are connected via a `ros_gz_bridge` `parameter_bridge` node defined inline in `gazebo.launch.py`.

---
### Requirements
ROS 2 Jazzy
Gazebo Sim (`gz sim`, Harmonic) via `ros_gz_sim` / `ros_gz_bridge`
`robot_state_publisher`, `joint_state_publisher`
`turtlebot3_gazebo` (for the `turtlebot3_world` world file)
`teleop_twist_keyboard`
`rviz2`

---
## Build
```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_description
source install/setup.bash
```
---
### How to Run
Step 1 — Visualize the robot in RViz (no physics)
```bash
ros2 launch my_robot_description display.launch.py
```
### Verify: robot appears correctly, TF frames are visible, no RViz errors.
Step 2 — Simulate the robot in Gazebo
```bash
ros2 launch my_robot_description gazebo.launch.py
```
This launches `gz sim` with the `turtlebot3_world`, spawns the robot, starts `robot_state_publisher`, and bridges all required topics between Gazebo and ROS 2.
Step 3 — Control the robot with Teleop
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
Key	Action
`i`	Forward
`,`	Backward
`j`	Rotate left
`l`	Rotate right
`k`	Stop
### Step 4 — Verify Odometry
```bash
ros2 topic echo /odom
```
In RViz: set Fixed Frame = odom, add RobotModel, TF, Odometry.
### Step 5 — Verify LiDAR
```bash
ros2 topic list | grep scan
ros2 topic echo /scan --once
```
### Step 6 — Verify the TF Tree
```bash
ros2 run tf2_tools view_frames
```
---
### Expected Final TF Tree
```
odom
 └── base_link (base_footprint)
      ├── lidar_link
      ├── left_front_wheel_link
      ├── right_front_wheel_link
      ├── left_back_wheel_link
      └── right_back_wheel_link
```
---
### Verification
The system was tested using a custom 4-wheel differential drive robot in `gz sim` (Gazebo Harmonic), spawned inside `turtlebot3_world`. The following was verified:
Robot URDF loads with no XML errors, no floating links
Robot displays correctly in RViz with a fully connected TF tree
Robot spawns successfully in Gazebo, stable and above the ground plane
`DiffDrive` plugin correctly subscribes to `/cmd_vel` and drives both axles
Robot moves forward, backward, and rotates left/right via teleop, with wheels rotating correctly
`/odom` updates continuously with correct position and orientation while driving
LiDAR link, mesh reference, and `gpu_lidar` sensor plugin are correctly defined; `/scan` is published on the Gazebo side and successfully bridged to ROS 2
Final TF tree is fully connected: `odom → base_link → {lidar_link, 4× wheel links}`, with no disconnected frames

---
### Known Limitations
1) Visual confirmation of LaserScan data in RViz (Part 12) and full mesh rendering of the LiDAR sensor in the 3D Simulator were affected by a confirmed platform-side rendering issue 
in the simulator's sensor pipeline, acknowledged by course staff during this task. All underlying configuration — URDF mesh/sensor definitions, the `gpu_lidar` plugin, and the `/scan` topic 
bridge — was implemented and verified correct via `ros2 topic list` and `ros2 topic echo`; the remaining issue is a known simulator rendering bug rather than an error in this package.
2) Part 10 was completed but as mentioned in the email, the lidar was not being registered in the URDF. This may be to an issue in my code or due to the software issue mentioned earlier. When the mesh file was replaced with a simple cylinder, the object was realized, making it more likely to be an issue from the mesh file than the code itself.
---
URDF View (VS Code URDF Visualizer):

<img width="247" height="148" alt="Screenshot 2026-06-22 171900" src="https://github.com/user-attachments/assets/11541ddc-a8ba-4db1-8aaf-4b5224d21b9e" />

RViz — Robot Model & TF:
<img width="762" height="518" alt="Screenshot 2026-06-23 123716" src="https://github.com/user-attachments/assets/619ede01-0107-4ed0-ab87-497d0a79c536" />

Gazebo Simulation (robot spawned in turtlebot3_world):
<img width="669" height="378" alt="Screenshot 2026-06-22 171932" src="https://github.com/user-attachments/assets/dd15539c-df5f-459b-a637-2837cb81580e" />

Teleop Terminal:
<img width="937" height="507" alt="Screenshot 2026-06-22 173122" src="https://github.com/user-attachments/assets/c91ef0c4-1e7f-4b8c-89fe-ebf85c4dee88" />

RViz — Odometry (Fixed Frame = odom):
<img width="762" height="518" alt="Screenshot 2026-06-23 123716" src="https://github.com/user-attachments/assets/197a62de-21a3-45f8-8bb5-36f6dd8b38e0" />

URDF View (With Lidar "Cylinder")

<img width="214" height="175" alt="image" src="https://github.com/user-attachments/assets/73379417-0649-455e-8eea-93b1e6eebd47" />

TF Tree (`ros2 run tf2_tools view_frames`):
<img width="1004" height="341" alt="Screenshot 2026-06-23 141514" src="https://github.com/user-attachments/assets/b1838580-8a3e-401d-a9c9-849e77abc1cb" />

Demo Video Link


https://github.com/user-attachments/assets/8d5c92e4-7e56-4d62-8125-c6f9988aa91f



---
