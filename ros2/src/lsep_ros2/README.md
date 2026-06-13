# lsep_ros2 — LSEP Reference Implementation for ROS 2

> Managed lifecycle node implementing the **Luminae Signal Expression
> Protocol (LSEP) v2.1-draft**. Physics-based (TTC) state machine,
> time-aware hysteresis, trimodal signal output, RViz visualization,
> simulated demo. No Gazebo required for the first run.

Spec & protocol: https://github.com/NemanjaGalic/LSEP · https://lsep.org

## What's new vs. the v2.0 spec snippet

This implementation resolves the de-escalation blind spot (Issue #1):

* **Time-based decay** — a calmer state must hold for
  `dwell_de_escalation_s` (default 1.5 s) before the machine de-escalates.
  Escalation stays immediate; THREAT (< 0.5 s TTC) bypasses everything.
* **Input watchdog** — if the sensor stream dies for longer than
  `input_timeout_s` (default 0.5 s), the *reported* state degrades to
  `LOW_CONF` instead of latching the last danger state on dead sensors.
  The core state is preserved internally for forensics and fast recovery.
* **Confidence overlay** — `MED_CONF` / `LOW_CONF` are only reported while
  the core state is calm (IDLE/AWARENESS). Danger states always win.

## Quick start (ROS 2 Humble or newer)

```bash
# 1. Drop BOTH packages into your workspace
mkdir -p ~/lsep_ws/src && cp -r lsep_msgs lsep_ros2 ~/lsep_ws/src/

# 2. Build (colcon resolves the order: lsep_msgs first)
cd ~/lsep_ws
colcon build --packages-select lsep_msgs lsep_ros2
source install/setup.bash

# 3. Run the demo (LSEP node + simulated human, auto-activates)
ros2 launch lsep_ros2 lsep_demo.launch.py
```

Watch the protocol live:

```bash
ros2 topic echo /lsep/signal
```

You will see the full state ladder as the simulated human approaches,
lingers at 0.4 m, and retreats:

```
INTEGRITY → IDLE → AWARENESS → INTENT → CARE → CRITICAL → THREAT
          → (1.5 s dwell) → AWARENESS → IDLE → …
```

### RViz

Add a `Marker` display on topic `/lsep/marker` (fixed frame `map`).
The sphere's color encodes the state; its alpha pulses at the light
modality's `frequency_hz` — semantics rendered, not hardcoded aesthetics.

### Unit tests (no ROS required)

```bash
python3 -m pytest test/test_engine.py -v   # 9 tests, all green
```

## Interface

| Direction | Topic | Type | Meaning |
|---|---|---|---|
| sub | `lsep/input/distance_m` | `std_msgs/Float32` | Distance to nearest human [m] |
| sub | `lsep/input/closing_velocity_ms` | `std_msgs/Float32` | Closing velocity [m/s], > 0 = approaching |
| pub | `lsep/signal` | `lsep_msgs/Signal` | **Primary**: typed LSEP signal (10 Hz) |
| pub | `lsep/state` | `std_msgs/String` | JSON mirror — deprecated, disable with `publish_json:=false` |
| pub | `lsep/marker` | `visualization_msgs/Marker` | RViz rendering of the light modality |

### Parameters

| Name | Default | Description |
|---|---|---|
| `autostart` | `true` | Self-configure + activate on launch. Set `false` to drive transitions via `ros2 lifecycle set /lsep_node …` |
| `publish_rate_hz` | `10.0` | Signal publish rate |
| `dwell_de_escalation_s` | `1.5` | Time a calmer state must hold before de-escalation |
| `input_timeout_s` | `0.5` | Watchdog: stale input ⇒ reported `LOW_CONF` |
| `idle_distance_m` | `10.0` | Stationary humans beyond this ⇒ IDLE, inside ⇒ AWARENESS |
| `integrity_boot_s` | `1.5` | Duration of the INTEGRITY self-check broadcast after activation |
| `frame_id` | `map` | TF frame for the RViz marker |
| `publish_json` | `true` | Also publish the deprecated JSON-in-String mirror on `lsep/state` |

## Lifecycle

```
unconfigured ──configure──▶ inactive ──activate──▶ active (publishing)
      ▲                        │  ▲                    │
      └──────cleanup───────────┘  └────deactivate──────┘
```

`on_configure` runs the INTEGRITY self-check and creates all interfaces;
`on_activate` starts the 10 Hz publishing timer. Deactivating stops
publishing without tearing down state — exactly what a safety supervisor
needs for orchestrated bring-up.

## Changelog

* **0.2.0** — typed transport via `lsep_msgs/Signal` on `lsep/signal`
  (state enum + `state_name`, NaN for undefined physics). JSON-in-String
  on `lsep/state` kept as deprecated mirror behind `publish_json`.
* **0.1.0** — initial lifecycle node, v2.1 engine (dwell de-escalation +
  input watchdog), simulated human, RViz marker, 9 unit tests.

## Roadmap

1. ~~**Custom messages** (`lsep_msgs/Signal`)~~ — done in 0.2.0.
2. **Gazebo demo world** — TurtleBot-class robot + walking actor, LSEP
   light ring rendered on the robot model.
3. **2D TTC / Time-to-Intercept** — replace the 1D placeholder with
   trajectory-predictive computation (Issue: TTC realism).
4. **Perception study** — empirical validation that humans intuitively
   decode the signal vocabulary (EDI core evidence).

## License

MIT — © 2026 Nemanja Galic / Experience Design Institute, Bern.
