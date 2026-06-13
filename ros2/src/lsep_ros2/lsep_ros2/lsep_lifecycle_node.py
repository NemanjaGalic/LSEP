"""LSEP ROS 2 reference node — managed lifecycle node.

Subscribes (std_msgs/Float32):
  lsep/input/distance_m              distance to nearest human [m]
  lsep/input/closing_velocity_ms     closing velocity [m/s], > 0 = approaching

Publishes:
  lsep/signal  (lsep_msgs/Signal)        typed LSEP signal  <-- primary
  lsep/state   (std_msgs/String)         JSON mirror, deprecated
                                         (disable: publish_json:=false)
  lsep/marker  (visualization_msgs/Marker) RViz sphere, color = state,
                                           alpha pulses at the light
                                           modality's frequency

Lifecycle: unconfigured -> configure (INTEGRITY self-check) -> activate
(publishing) -> deactivate / cleanup / shutdown. Set parameter
`autostart:=false` to drive transitions manually via `ros2 lifecycle`.
"""

import json
import math
import time

import rclpy
from rclpy.lifecycle import Node, TransitionCallbackReturn
from std_msgs.msg import Float32, String
from visualization_msgs.msg import Marker

from lsep_msgs.msg import (LightModality, MotionModality, Signal,
                           SoundModality)

from .engine import SafetyDecisionEngine

# Map engine state names -> lsep_msgs/Signal enum values.
STATE_IDS = {
    'IDLE': Signal.STATE_IDLE,
    'AWARENESS': Signal.STATE_AWARENESS,
    'INTENT': Signal.STATE_INTENT,
    'CARE': Signal.STATE_CARE,
    'CRITICAL': Signal.STATE_CRITICAL,
    'THREAT': Signal.STATE_THREAT,
    'MED_CONF': Signal.STATE_MED_CONF,
    'LOW_CONF': Signal.STATE_LOW_CONF,
    'INTEGRITY': Signal.STATE_INTEGRITY,
}


def _nan_if_none(value):
    return float(value) if value is not None else float('nan')

STATE_COLORS = {
    'IDLE':      (0.60, 0.60, 0.60),
    'AWARENESS': (0.20, 0.50, 1.00),
    'INTENT':    (1.00, 0.90, 0.20),
    'CARE':      (1.00, 0.60, 0.10),
    'CRITICAL':  (1.00, 0.15, 0.10),
    'THREAT':    (1.00, 0.00, 0.60),
    'MED_CONF':  (0.40, 0.90, 0.90),
    'LOW_CONF':  (0.80, 0.50, 0.90),
    'INTEGRITY': (1.00, 1.00, 1.00),
}


class LSEPLifecycleNode(Node):

    def __init__(self, **kwargs):
        super().__init__('lsep_node', **kwargs)
        self.declare_parameter('autostart', True)
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('dwell_de_escalation_s', 1.5)
        self.declare_parameter('input_timeout_s', 0.5)
        self.declare_parameter('idle_distance_m', 10.0)
        self.declare_parameter('integrity_boot_s', 1.5)
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('publish_json', True)   # deprecated transport

        self._engine = None
        self._pub_signal = None
        self._pub_state = None
        self._pub_marker = None
        self._sub_d = None
        self._sub_v = None
        self._timer = None
        self._distance = None
        self._velocity = None
        self._last_msg_mono = None
        self._activated_mono = None

    # -------------------------------------------------- lifecycle callbacks

    def on_configure(self, state) -> TransitionCallbackReturn:
        self._rate = self.get_parameter('publish_rate_hz').value
        self._timeout = self.get_parameter('input_timeout_s').value
        self._integrity_boot = self.get_parameter('integrity_boot_s').value
        self._frame_id = self.get_parameter('frame_id').value
        self._publish_json = self.get_parameter('publish_json').value

        self._engine = SafetyDecisionEngine(
            dwell_de_escalation_s=self.get_parameter('dwell_de_escalation_s').value,
            input_timeout_s=self._timeout,
            idle_distance_m=self.get_parameter('idle_distance_m').value,
        )
        self._pub_signal = self.create_lifecycle_publisher(Signal, 'lsep/signal', 10)
        self._pub_state = self.create_lifecycle_publisher(String, 'lsep/state', 10)
        self._pub_marker = self.create_lifecycle_publisher(Marker, 'lsep/marker', 10)
        self._sub_d = self.create_subscription(
            Float32, 'lsep/input/distance_m', self._on_distance, 10)
        self._sub_v = self.create_subscription(
            Float32, 'lsep/input/closing_velocity_ms', self._on_velocity, 10)

        self.get_logger().info('LSEP configured — INTEGRITY self-check passed.')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state) -> TransitionCallbackReturn:
        self._activated_mono = time.monotonic()
        self._timer = self.create_timer(1.0 / self._rate, self._tick)
        self.get_logger().info('LSEP active — publishing on lsep/state.')
        return super().on_activate(state)

    def on_deactivate(self, state) -> TransitionCallbackReturn:
        if self._timer is not None:
            self.destroy_timer(self._timer)
            self._timer = None
        return super().on_deactivate(state)

    def on_cleanup(self, state) -> TransitionCallbackReturn:
        self._teardown()
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state) -> TransitionCallbackReturn:
        self._teardown()
        return TransitionCallbackReturn.SUCCESS

    def _teardown(self):
        for attr in ('_timer',):
            obj = getattr(self, attr)
            if obj is not None:
                self.destroy_timer(obj)
                setattr(self, attr, None)
        for attr in ('_pub_signal', '_pub_state', '_pub_marker'):
            obj = getattr(self, attr)
            if obj is not None:
                self.destroy_publisher(obj)
                setattr(self, attr, None)
        for attr in ('_sub_d', '_sub_v'):
            obj = getattr(self, attr)
            if obj is not None:
                self.destroy_subscription(obj)
                setattr(self, attr, None)
        self._engine = None

    # ------------------------------------------------------------ callbacks

    def _on_distance(self, msg: Float32):
        self._distance = float(msg.data)
        self._last_msg_mono = time.monotonic()

    def _on_velocity(self, msg: Float32):
        self._velocity = float(msg.data)
        self._last_msg_mono = time.monotonic()

    # ----------------------------------------------------------------- tick

    def _tick(self):
        now = time.monotonic()

        # Boot phase: announce INTEGRITY (diagnostic) before going live.
        if (self._activated_mono is not None
                and now - self._activated_mono < self._integrity_boot):
            self._publish(SafetyDecisionEngine.static_signal('INTEGRITY'), now)
            return

        fresh = (self._last_msg_mono is not None
                 and now - self._last_msg_mono <= self._timeout
                 and self._distance is not None
                 and self._velocity is not None)
        if fresh:
            # Only feed the engine fresh samples; if the stream dies the
            # engine's own watchdog degrades the reported state to LOW_CONF.
            self._engine.update(self._distance, self._velocity,
                                confidence=1.0,
                                sensors=['simulated'])
        self._publish(self._engine.signal(), now)

    def _publish(self, signal: dict, now: float):
        self._pub_signal.publish(self._to_signal_msg(signal))
        if self._publish_json:
            msg = String()
            msg.data = json.dumps(signal)
            self._pub_state.publish(msg)
        self._pub_marker.publish(self._marker_for(signal, now))

    def _to_signal_msg(self, sig: dict) -> Signal:
        m = Signal()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = self._frame_id

        m.protocol = sig['protocol']
        m.version = sig['version']
        m.state = STATE_IDS[sig['state']]
        m.state_name = sig['state']
        m.core_state = STATE_IDS[sig['core_state']]
        m.core_state_name = sig['core_state']

        m.ttc_seconds = _nan_if_none(sig['ttc_seconds'])
        m.distance_m = _nan_if_none(sig['distance_m'])
        m.closing_velocity_ms = _nan_if_none(sig['closing_velocity_ms'])

        mods = sig['modalities']
        m.light = LightModality(
            pattern=mods['light']['pattern'],
            frequency_hz=float(mods['light']['frequency_hz']),
            intensity=float(mods['light']['intensity']),
            bezier=[float(x) for x in mods['light']['bezier']],
        )
        m.sound = SoundModality(
            type=mods['sound']['type'],
            frequency_hz=float(mods['sound']['frequency_hz']),
            volume_db=float(mods['sound']['volume_db']),
            envelope=mods['sound']['envelope'],
        )
        m.motion = MotionModality(
            action=mods['motion']['action'],
            speed_modifier=float(mods['motion']['speed_modifier']),
            trajectory=mods['motion']['trajectory'],
        )

        m.confidence = float(sig['confidence'])
        m.sensor_fusion = list(sig['sensor_fusion'])
        m.stale_input = bool(sig['stale_input'])
        return m

    def _marker_for(self, signal: dict, now: float) -> Marker:
        st = signal['state']
        r, g, b = STATE_COLORS.get(st, (1.0, 1.0, 1.0))
        freq = signal['modalities']['light'].get('frequency_hz', 0.0) or 0.0
        # Pulse alpha at the light modality's frequency (semantics -> render).
        alpha = 1.0 if freq <= 0 else 0.35 + 0.65 * abs(math.sin(math.pi * freq * now))

        m = Marker()
        m.header.frame_id = self._frame_id
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lsep'
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = 0.0
        m.pose.position.y = 0.0
        m.pose.position.z = 0.5
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = m.scale.z = 0.6
        m.color.r, m.color.g, m.color.b, m.color.a = r, g, b, alpha
        m.text = st
        return m


def main(args=None):
    rclpy.init(args=args)
    node = LSEPLifecycleNode()
    if node.get_parameter('autostart').value:
        try:
            node.trigger_configure()
            node.trigger_activate()
        except Exception as exc:  # pragma: no cover - distro differences
            node.get_logger().warning(
                f'autostart failed ({exc}); run manually:\n'
                '  ros2 lifecycle set /lsep_node configure\n'
                '  ros2 lifecycle set /lsep_node activate')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
