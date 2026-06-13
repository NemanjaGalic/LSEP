"""LSEP v2.1-draft — Safety Decision Engine.

Changes vs. v2.0 (addresses Issue #1):
  * Time-based de-escalation: a less-severe state must remain stable for
    `dwell_de_escalation_s` before the machine de-escalates. Escalation is
    always immediate. THREAT (< 0.5 s TTC) bypasses everything.
  * Input watchdog: if no fresh sensor input arrives within
    `input_timeout_s`, the *reported* state degrades to LOW_CONF instead of
    latching the last danger state forever.
  * Confidence overlay: MED_CONF / LOW_CONF are reported only while the core
    state is non-critical (IDLE / AWARENESS). Danger states always win.

The protocol defines semantics, not aesthetics — the SIGNALS table below is
a reference rendering, manufacturers may restyle within the semantic bounds.
"""

import time

# Most severe first. Lower index == more severe.
CORE_SEVERITY = ['THREAT', 'CRITICAL', 'CARE', 'INTENT', 'AWARENESS', 'IDLE']

# Upper TTC bound (seconds) per state, ordered most-severe first.
TTC_THRESHOLDS = {
    'THREAT': 0.5,
    'CRITICAL': 1.5,
    'CARE': 3.0,
    'INTENT': 5.0,
    'AWARENESS': 10.0,
}

_BEZIER = [0.4, 0.0, 0.2, 1.0]

SIGNALS = {
    'IDLE': {
        'light': {'pattern': 'breathe', 'frequency_hz': 0.2, 'intensity': 0.2, 'bezier': _BEZIER},
        'sound': {'type': 'none', 'frequency_hz': 0, 'volume_db': 0, 'envelope': 'none'},
        'motion': {'action': 'none', 'speed_modifier': 1.0, 'trajectory': 'free'},
    },
    'AWARENESS': {
        'light': {'pattern': 'pulse', 'frequency_hz': 0.5, 'intensity': 0.4, 'bezier': _BEZIER},
        'sound': {'type': 'presence_tone', 'frequency_hz': 440, 'volume_db': 40, 'envelope': 'adsr'},
        'motion': {'action': 'maintain', 'speed_modifier': 1.0, 'trajectory': 'free'},
    },
    'INTENT': {
        'light': {'pattern': 'pulse', 'frequency_hz': 1.0, 'intensity': 0.6, 'bezier': _BEZIER},
        'sound': {'type': 'intent_tone', 'frequency_hz': 550, 'volume_db': 48, 'envelope': 'adsr'},
        'motion': {'action': 'announce_path', 'speed_modifier': 0.8, 'trajectory': 'planned'},
    },
    'CARE': {
        'light': {'pattern': 'wave', 'frequency_hz': 1.5, 'intensity': 0.8, 'bezier': _BEZIER},
        'sound': {'type': 'proximity_tone', 'frequency_hz': 660, 'volume_db': 55, 'envelope': 'adsr'},
        'motion': {'action': 'decelerate', 'speed_modifier': 0.4, 'trajectory': 'yield_path'},
    },
    'CRITICAL': {
        'light': {'pattern': 'strobe', 'frequency_hz': 3.0, 'intensity': 1.0, 'bezier': _BEZIER},
        'sound': {'type': 'urgent_tone', 'frequency_hz': 880, 'volume_db': 70, 'envelope': 'pulse'},
        'motion': {'action': 'evasive', 'speed_modifier': 0.1, 'trajectory': 'evasive'},
    },
    'THREAT': {
        'light': {'pattern': 'strobe', 'frequency_hz': 6.0, 'intensity': 1.0, 'bezier': _BEZIER},
        'sound': {'type': 'alarm', 'frequency_hz': 1000, 'volume_db': 85, 'envelope': 'continuous'},
        'motion': {'action': 'emergency_stop', 'speed_modifier': 0.0, 'trajectory': 'halt'},
    },
    'MED_CONF': {
        'light': {'pattern': 'wave', 'frequency_hz': 0.8, 'intensity': 0.5, 'bezier': _BEZIER},
        'sound': {'type': 'soft_tone', 'frequency_hz': 500, 'volume_db': 45, 'envelope': 'adsr'},
        'motion': {'action': 'cautious', 'speed_modifier': 0.6, 'trajectory': 'conservative'},
    },
    'LOW_CONF': {
        'light': {'pattern': 'slow_blink', 'frequency_hz': 0.5, 'intensity': 0.7, 'bezier': _BEZIER},
        'sound': {'type': 'degraded_tone', 'frequency_hz': 400, 'volume_db': 50, 'envelope': 'adsr'},
        'motion': {'action': 'creep', 'speed_modifier': 0.3, 'trajectory': 'conservative'},
    },
    'INTEGRITY': {
        'light': {'pattern': 'sweep', 'frequency_hz': 0.3, 'intensity': 0.5, 'bezier': _BEZIER},
        'sound': {'type': 'chime', 'frequency_hz': 520, 'volume_db': 45, 'envelope': 'adsr'},
        'motion': {'action': 'stationary', 'speed_modifier': 0.0, 'trajectory': 'self_test'},
    },
}


class SafetyDecisionEngine:
    """Physics-based state determination with time-aware hysteresis."""

    def __init__(self,
                 dwell_de_escalation_s: float = 1.5,
                 input_timeout_s: float = 0.5,
                 idle_distance_m: float = 10.0,
                 clock=None):
        self.dwell = float(dwell_de_escalation_s)
        self.timeout = float(input_timeout_s)
        self.idle_distance = float(idle_distance_m)
        self._clock = clock or time.monotonic

        self._state = 'IDLE'           # core kinematic state
        self._candidate = None          # pending de-escalation target
        self._candidate_since = None
        self._last_input_time = None
        self._last = {'distance': None, 'velocity': None, 'ttc': None,
                      'confidence': 1.0, 'sensors': []}

    # ------------------------------------------------------------------ api

    @property
    def state(self) -> str:
        """Core kinematic state (ignores confidence overlay)."""
        return self._state

    def update(self, distance_m: float, closing_velocity_ms: float,
               confidence: float = 1.0, sensors=None) -> str:
        """Feed one fresh sensor sample. Returns the *reported* state."""
        now = self._clock()
        self._last_input_time = now

        ttc = None
        if closing_velocity_ms is not None and closing_velocity_ms > 0.0:
            ttc = distance_m / closing_velocity_ms

        self._last = {
            'distance': distance_m,
            'velocity': closing_velocity_ms,
            'ttc': ttc,
            'confidence': confidence,
            'sensors': sensors or ['simulated'],
        }

        raw = self._raw_state(distance_m, closing_velocity_ms)
        self._apply_time_aware_hysteresis(raw, now)
        return self.reported_state()

    def reported_state(self) -> str:
        """Core state + watchdog + confidence overlay."""
        now = self._clock()
        stale = (self._last_input_time is None
                 or now - self._last_input_time > self.timeout)
        if stale:
            # Input stream died — never latch a danger state on dead sensors,
            # never pretend everything is fine either.
            return 'LOW_CONF'

        conf = self._last.get('confidence', 1.0)
        if self._state in ('IDLE', 'AWARENESS'):
            if conf < 0.70:
                return 'LOW_CONF'
            if conf < 0.85:
                return 'MED_CONF'
        return self._state

    def signal(self) -> dict:
        """Full LSEP JSON signal for the current reported state."""
        st = self.reported_state()
        now = self._clock()
        stale = (self._last_input_time is None
                 or now - self._last_input_time > self.timeout)
        ttc = self._last.get('ttc')
        return {
            'protocol': 'LSEP',
            'version': '2.1-draft',
            'state': st,
            'core_state': self._state,
            'ttc_seconds': round(ttc, 3) if ttc is not None else None,
            'distance_m': self._last.get('distance'),
            'closing_velocity_ms': self._last.get('velocity'),
            'modalities': SIGNALS[st],
            'confidence': self._last.get('confidence', 1.0),
            'sensor_fusion': self._last.get('sensors', []),
            'stale_input': stale,
        }

    @staticmethod
    def static_signal(state: str) -> dict:
        """Signal for a fixed state (e.g. INTEGRITY during boot self-check)."""
        return {
            'protocol': 'LSEP',
            'version': '2.1-draft',
            'state': state,
            'core_state': state,
            'ttc_seconds': None,
            'distance_m': None,
            'closing_velocity_ms': None,
            'modalities': SIGNALS[state],
            'confidence': 1.0,
            'sensor_fusion': [],
            'stale_input': False,
        }

    # ------------------------------------------------------------ internals

    def _raw_state(self, d, v) -> str:
        if d is None or v is None:
            return 'IDLE'
        if v <= 0.0:
            return 'IDLE' if d > self.idle_distance else 'AWARENESS'
        ttc = d / v
        for state, threshold in TTC_THRESHOLDS.items():
            if ttc < threshold:
                return state
        return 'IDLE'

    def _apply_time_aware_hysteresis(self, raw: str, now: float) -> None:
        cur_i = CORE_SEVERITY.index(self._state)
        raw_i = CORE_SEVERITY.index(raw)

        if raw_i < cur_i:
            # Escalation: always immediate. THREAT lands here in one step.
            self._state = raw
            self._candidate = None
            self._candidate_since = None
        elif raw_i == cur_i:
            # Stable: cancel any pending de-escalation.
            self._candidate = None
            self._candidate_since = None
        else:
            # De-escalation: require the calmer state to hold for `dwell`.
            if self._candidate != raw:
                self._candidate = raw
                self._candidate_since = now
            elif now - self._candidate_since >= self.dwell:
                self._state = raw
                self._candidate = None
                self._candidate_since = None
