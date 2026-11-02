"""RViz marker colors per LSEP state — no ROS imports, unit-testable.

Source: LSEP specification, Section 9.1 "Color Coding" (RGB 0-255) and
Section 7.3.1 for the INTEGRITY sweep. Colors are not unique per state in
the spec: AWARENESS and INTENT are both Bright White, CRITICAL and THREAT
are both red; they differ in pattern, not in color.
"""

# Spec 9.1, RGB 0-255. INTEGRITY is "Multicolor / Cycling", see below.
SPEC_RGB_255 = {
    'IDLE':      (240, 240, 240),   # Soft White
    'AWARENESS': (255, 255, 255),   # Bright White
    'INTENT':    (255, 255, 255),   # Bright White
    'CARE':      (255, 165, 0),     # Amber
    'CRITICAL':  (255, 0, 0),       # Red
    'THREAT':    (255, 0, 0),       # Bright Red
    'MED_CONF':  (0, 255, 255),     # Cyan
    'LOW_CONF':  (255, 255, 0),     # Yellow
}

# Spec 7.3.1: "Multicolor Blue -> Green -> Cyan -> White", one complete
# cycle per 2.0 seconds. The spec names the colors without RGB values;
# blue and green are rendered as sRGB primaries here.
INTEGRITY_CYCLE_RGB_255 = (
    (0, 0, 255),       # Blue
    (0, 255, 0),       # Green
    (0, 255, 255),     # Cyan
    (255, 255, 255),   # White
)
INTEGRITY_CYCLE_PERIOD_S = 2.0


def _unit(rgb):
    return tuple(c / 255.0 for c in rgb)


STATE_COLORS = {state: _unit(rgb) for state, rgb in SPEC_RGB_255.items()}


def marker_color(state: str, now: float):
    """Return (r, g, b) in 0.0-1.0 for `state` at time `now` [s]."""
    if state == 'INTEGRITY':
        steps = len(INTEGRITY_CYCLE_RGB_255)
        phase = (now % INTEGRITY_CYCLE_PERIOD_S) / INTEGRITY_CYCLE_PERIOD_S
        return _unit(INTEGRITY_CYCLE_RGB_255[int(phase * steps) % steps])
    return STATE_COLORS.get(state, (1.0, 1.0, 1.0))
