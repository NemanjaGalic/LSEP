"""Unit tests for SafetyDecisionEngine v2.1-rc1 (time-aware hysteresis).

Run without ROS:  python3 -m pytest test/test_engine.py -v
"""

import py_compile
from pathlib import Path

import pytest

from lsep_ros2.engine import (CRITICAL_SEQUENCE_MS, MAX_FLASHES_PER_SECOND,
                              SIGNALS, SafetyDecisionEngine)


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
    assert sig['version'] == '2.1-rc1'
    assert set(sig['modalities']) == {'light', 'sound', 'motion'}


def test_no_light_signal_exceeds_flash_cap():
    # Spec 6.5.5: at most 2 flashes per second, for every state (issue #15).
    for state, mods in SIGNALS.items():
        hz = mods['light']['frequency_hz']
        assert hz <= MAX_FLASHES_PER_SECOND, f'{state}: {hz} Hz'


def test_critical_is_double_pulse_and_threat_is_steady():
    crit = SIGNALS['CRITICAL']['light']
    assert crit['pattern'] == 'double_pulse'
    assert crit['sequence_ms'] == [100, 150, 100, 650]
    on_phases = len(CRITICAL_SEQUENCE_MS[0::2])
    period_s = sum(CRITICAL_SEQUENCE_MS) / 1000.0
    assert on_phases / period_s == crit['frequency_hz'] == 2.0

    threat = SIGNALS['THREAT']['light']
    assert threat['pattern'] == 'steady_max'
    assert threat['frequency_hz'] == 0.0


def test_published_signal_respects_flash_cap_in_every_core_state():
    # Dynamic sibling of the table check: what the node would publish.
    for d in (12.0, 8.0, 4.0, 2.8, 1.0, 0.3):
        eng, _ = make_engine()
        eng.update(d, 1.0)
        light = eng.signal()['modalities']['light']
        assert light['frequency_hz'] <= MAX_FLASHES_PER_SECOND


def test_legacy_example_compiles():
    example = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / 'examples' / 'safety_decision_engine.py'
        if candidate.is_file():
            example = candidate
            break
    if example is None:
        pytest.skip('examples/ not present in this checkout layout')
    py_compile.compile(str(example), doraise=True)
