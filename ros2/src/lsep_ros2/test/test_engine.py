"""Unit tests for SafetyDecisionEngine v2.1 (time-aware hysteresis).

Run without ROS:  python3 -m pytest test/test_engine.py -v
"""

from lsep_ros2.engine import SafetyDecisionEngine


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def make_engine(**kw):
    clock = FakeClock()
    eng = SafetyDecisionEngine(dwell_de_escalation_s=1.5,
                               input_timeout_s=0.5,
                               clock=clock, **kw)
    return eng, clock


def test_ttc_thresholds_map_to_states():
    eng, clock = make_engine()
    # distance / velocity chosen so TTC hits each band
    cases = [
        (12.0, 1.0, 'IDLE'),        # TTC 12.0  -> beyond AWARENESS band
        (8.0, 1.0, 'AWARENESS'),    # TTC 8.0
        (4.0, 1.0, 'INTENT'),       # TTC 4.0
        (2.8, 1.0, 'CARE'),         # TTC 2.8
        (1.0, 1.0, 'CRITICAL'),     # TTC 1.0
        (0.3, 1.0, 'THREAT'),       # TTC 0.3
    ]
    for d, v, expected in cases:
        eng2, _ = make_engine()
        assert eng2.update(d, v) == expected, f'd={d}, v={v}'


def test_escalation_is_immediate():
    eng, clock = make_engine()
    eng.update(8.0, 1.0)            # AWARENESS
    assert eng.state == 'AWARENESS'
    eng.update(0.3, 1.0)            # straight to THREAT, no dwell
    assert eng.state == 'THREAT'


def test_no_instant_de_escalation():
    eng, clock = make_engine()
    eng.update(0.3, 1.0)            # THREAT
    clock.advance(0.1)
    eng.update(8.0, 1.0)            # calmer reading appears…
    assert eng.state == 'THREAT'    # …but state must hold (dwell not met)


def test_de_escalation_after_dwell():
    eng, clock = make_engine()
    eng.update(0.3, 1.0)            # THREAT
    for _ in range(20):             # 2.0 s of calm readings @ 10 Hz
        clock.advance(0.1)
        eng.update(8.0, 1.0)
    assert eng.state == 'AWARENESS'


def test_dwell_resets_if_danger_returns():
    eng, clock = make_engine()
    eng.update(0.3, 1.0)            # THREAT
    clock.advance(1.0)
    eng.update(8.0, 1.0)            # calm for 1.0 s (dwell is 1.5 s)
    clock.advance(0.2)
    eng.update(0.3, 1.0)            # danger again -> candidate must reset
    clock.advance(1.0)
    eng.update(8.0, 1.0)            # calm again, but only 1.0 s
    assert eng.state == 'THREAT'


def test_stationary_human_is_awareness_not_idle():
    eng, clock = make_engine()
    assert eng.update(3.0, 0.0) == 'AWARENESS'
    eng2, _ = make_engine()
    assert eng2.update(15.0, 0.0) == 'IDLE'


def test_stale_input_reports_low_conf():
    eng, clock = make_engine()
    eng.update(0.3, 1.0)            # THREAT
    clock.advance(2.0)              # input stream dies (> 0.5 s timeout)
    assert eng.reported_state() == 'LOW_CONF'
    assert eng.signal()['stale_input'] is True
    # Core state is preserved for forensics / recovery:
    assert eng.state == 'THREAT'


def test_confidence_overlay_only_in_calm_states():
    eng, clock = make_engine()
    assert eng.update(8.0, 1.0, confidence=0.75) == 'MED_CONF'
    assert eng.update(8.0, 1.0, confidence=0.60) == 'LOW_CONF'
    # Danger states always win over confidence overlays:
    assert eng.update(0.3, 1.0, confidence=0.60) == 'THREAT'


def test_signal_schema_contains_required_fields():
    eng, clock = make_engine()
    eng.update(2.8, 1.0)
    sig = eng.signal()
    for key in ('protocol', 'version', 'state', 'ttc_seconds',
                'distance_m', 'closing_velocity_ms', 'modalities',
                'confidence', 'sensor_fusion'):
        assert key in sig
    assert sig['protocol'] == 'LSEP'
    assert set(sig['modalities']) == {'light', 'sound', 'motion'}
