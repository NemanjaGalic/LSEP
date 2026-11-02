"""Keep the pattern list in LightModality.msg in step with the engine.

Run without ROS:  python3 -m pytest test/test_msg_comment.py -v
"""

from pathlib import Path

from lsep_ros2.engine import SIGNALS

MSG = (Path(__file__).resolve().parents[2]
       / 'lsep_msgs' / 'msg' / 'LightModality.msg')

# 'none' is the documented value for "no light signal"; the engine never sends it.
NOT_SENT_BY_ENGINE = {'none'}


def _documented_patterns():
    for line in MSG.read_text().splitlines():
        if line.startswith('string pattern'):
            comment = line.split('#', 1)[1]
            return {name.strip() for name in comment.split('|')}
    raise AssertionError('no "string pattern" field in LightModality.msg')


def _engine_patterns():
    return {mods['light']['pattern'] for mods in SIGNALS.values()}


def test_every_engine_pattern_is_documented():
    assert _engine_patterns() <= _documented_patterns()


def test_no_documented_pattern_is_stale():
    assert _documented_patterns() - _engine_patterns() == NOT_SENT_BY_ENGINE


def test_fields_unchanged():
    fields = [line.split('#')[0].split() for line in MSG.read_text().splitlines()
              if line.strip() and not line.startswith('#')]
    assert fields == [['string', 'pattern'], ['float32', 'frequency_hz'],
                      ['float32', 'intensity'], ['float32[4]', 'bezier']]
