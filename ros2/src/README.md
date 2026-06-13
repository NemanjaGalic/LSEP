# LSEP ROS 2 Workspace — v0.2

Two packages, drop both into your workspace `src/`:

```
src/
├── lsep_msgs/    # typed interfaces (Signal + 3 modalities) — build first
└── lsep_ros2/    # lifecycle node, v2.1 engine, simulated demo, tests
```

```bash
cd ~/lsep_ws
colcon build --packages-select lsep_msgs lsep_ros2
source install/setup.bash
ros2 launch lsep_ros2 lsep_demo.launch.py
ros2 topic echo /lsep/signal     # typed transport (primary)
```

Migration note for v0.1 users: the JSON String on `lsep/state` still works
but is deprecated — switch consumers to `lsep_msgs/Signal` on `lsep/signal`,
then set `publish_json:=false`.
