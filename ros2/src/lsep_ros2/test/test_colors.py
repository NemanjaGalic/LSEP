"""Unit tests for the RViz color table (spec Section 9.1 and 7.3.1).

Run without ROS:  python3 -m pytest test/test_colors.py -v
"""

from pathlib import Path

import pytest

from lsep_ros2.colors import (INTEGRITY_CYCLE_PERIOD_S, STATE_COLORS,
                              marker_color)
from lsep_ros2.engine import SIGNALS

# LSEP specification, Section 9.1 "Color Coding", RGB 0-255.
SPEC_9_1 = {
    'IDLE':      (240, 240, 240),
    'AWARENESS': (255, 255, 255),
    'INTENT':    (255, 255, 255),
    'CARE':      (255, 165, 0),
    'CRITICAL':  (255, 0, 0),
    'THREAT':    (255, 0, 0),
    'MED_CONF':  (0, 255, 255),
    'LOW_CONF':  (255, 255, 0),
}


def _rgb255(color):
    return tuple(round(c * 255) for c in color)


def test_state_colors_match_spec_table():
    for state, rgb in SPEC_9_1.items():
        assert _rgb255(STATE_COLORS[state]) == rgb, state
        assert _rgb255(marker_color(state, 0.0)) == rgb, state


def test_every_engine_state_has_a_color():
    for state in SIGNALS:
        r, g, b = marker_color(state, 0.3)
        assert all(0.0 <= c <= 1.0 for c in (r, g, b)), state
    assert set(SIGNALS) == set(SPEC_9_1) | {'INTEGRITY'}


def test_integrity_sweeps_blue_green_cyan_white_in_two_seconds():
    assert INTEGRITY_CYCLE_PERIOD_S == pytest.approx(2.0)
    seen = [_rgb255(marker_color('INTEGRITY', t))
            for t in (0.25, 0.75, 1.25, 1.75)]
    assert seen == [(0, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 255)]
    assert marker_color('INTEGRITY', 2.25) == marker_color('INTEGRITY', 0.25)


def test_node_uses_the_shared_color_table():
    node = (Path(__file__).resolve().parents[1]
            / 'lsep_ros2' / 'lsep_lifecycle_node.py').read_text()
    assert 'STATE_COLORS = {' not in node
    assert 'marker_color(st, now)' in node
