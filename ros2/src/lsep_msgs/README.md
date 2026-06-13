# lsep_msgs

Typed ROS 2 interfaces for **LSEP** (Luminae Signal Expression Protocol).

| Message | Purpose |
|---|---|
| `Signal` | Full LSEP signal: state enum + name, TTC physics, trimodal expression, confidence, watchdog flag |
| `LightModality` | pattern / frequency / intensity / bezier easing |
| `SoundModality` | type / frequency / volume / envelope |
| `MotionModality` | action / speed modifier / trajectory |

Undefined physics values are encoded as `NaN` (e.g. TTC when there is no
closing motion). State is carried twice — as `uint8` enum for machines and
as `state_name` string for humans running `ros2 topic echo`.

License: MIT — © 2026 Nemanja Galic / Experience Design Institute.
