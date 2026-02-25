# LSEP — Luminae Signal Expression Protocol

> The open standard for human-robot communication.

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.0-blue.svg)](https://github.com/NemanjaGalic/LSEP/releases)
[![Website](https://img.shields.io/badge/Website-lsep.org-brightgreen.svg)](https://lsep.org)

**9 states. 3 modalities. 1 grammar. Physics-based. EU AI Act ready. No demographic profiling.**

---

## The Problem

By 2030, the International Federation of Robotics projects **340,000 humanoid robots** will be deployed globally. Yet there is **no open standard** for how these robots communicate their intent and state to humans.

**Regulatory mandates are clear:**
- **EU AI Act (Article 50)** requires transparency in autonomous system decision-making
- **ISO 13482** mandates safety signaling for personal care robots
- **EU Machinery Regulation 2023/1230** demands comprehensible human-machine interaction

Without a standard, each manufacturer invents their own signaling—creating confusion, inconsistency, and safety risks.

> *"I see you. I'm slowing down. You're safe."*

This is what humans need to understand. LSEP makes that possible.

---

## What is LSEP?

LSEP is an **open, multimodal communication protocol** that defines how robots signal their state and intent to humans. Think of it as **HTTP for robot communication**.

### Three Core Modalities

1. **Light** — Visual signals (patterns, intensity, frequency)
2. **Sound** — Auditory signals (tones, frequency, volume, envelope)
3. **Motion** — Behavioral signals (speed, trajectory, deceleration)

State determination is driven by **Time-to-Collision (TTC)** calculations—objective physics, not demographic classification.

---

## Core States (v2.0)

| State | TTC Threshold | Meaning | Human Experience |
|-------|---------------|---------|------------------|
| **IDLE** | ∞ | System dormant, no human detected | Robot is inactive, safe to approach |
| **AWARENESS** | < 10.0s | Human detected, passive observation | Robot sees you, maintaining distance |
| **INTENT** | < 5.0s | Robot planning action in human proximity | Robot is about to move near you |
| **CARE** | < 3.0s | Active safety measures, proximity caution | Robot is slowing down, protecting you |
| **CRITICAL** | < 1.5s | Immediate danger, emergency response | Urgent hazard—evasive action |
| **THREAT** | < 0.5s | Imminent collision, maximum alert | *Collision imminent. Full emergency mode.* |

---

## Extended States (v2.0)

| State | Purpose | Trigger |
|-------|---------|---------| 
| **MED_CONF** | Medium confidence in sensor data | Sensor fusion 70–85% confidence |
| **LOW_CONF** | Low confidence, degraded sensing | Sensor fusion < 70% (fog, occlusion) |
| **INTEGRITY** | System self-check, diagnostic mode | Boot, post-collision, maintenance |

---

## Physics-Based Safety: Time-to-Collision (TTC)

```
TTC = distance / closing_velocity
```

This metric is **independent of demographics**. A child, an elderly person, and a factory worker all trigger the same calculation. **Equal safety for all.**

### Safety Decision Engine

```python
class SafetyDecisionEngine:
    """LSEP v2.0 — Physics-based state determination"""

    THRESHOLDS = {
        'THREAT':    0.5,   # seconds — hysteresis bypass
        'CRITICAL':  1.5,   # seconds
        'CARE':      3.0,   # seconds
        'INTENT':    5.0,   # seconds
        'AWARENESS': 10.0,  # seconds
    }

    def determine_state(self, distance_m, velocity_ms, current_state):
        if velocity_ms <= 0:
            return 'IDLE' if distance_m > 10.0 else 'AWARENESS'

        ttc = distance_m / velocity_ms

        # Hysteresis bypass: TTC < 0.5s overrides everything
        if ttc < self.THRESHOLDS['THREAT']:
            return 'THREAT'

        for state, threshold in self.THRESHOLDS.items():
            if ttc < threshold:
                return self._apply_hysteresis(current_state, state, ttc)

        return 'IDLE'

    def _apply_hysteresis(self, current, target, ttc):
        severity = list(self.THRESHOLDS.keys())
        current_idx = severity.index(current) if current in severity else len(severity)
        target_idx = severity.index(target)
        if target_idx <= current_idx:
            return target  # Escalate immediately
        return current     # Hold current state
```

**THREAT (< 0.5s) bypasses hysteresis entirely.** Physics demands immediate response.

---

## JSON Signal Format (v2.0)

**No hex color codes.** The protocol defines *semantics*, not *aesthetics*.

```json
{
  "protocol": "LSEP",
  "version": "2.0",
  "state": "CARE",
  "ttc_seconds": 2.8,
  "distance_m": 3.2,
  "closing_velocity_ms": 1.14,
  "modalities": {
    "light": {
      "pattern": "wave",
      "frequency_hz": 1.5,
      "intensity": 0.8,
      "bezier": [0.4, 0.0, 0.2, 1.0]
    },
    "sound": {
      "type": "proximity_tone",
      "frequency_hz": 660,
      "volume_db": 55,
      "envelope": "adsr"
    },
    "motion": {
      "action": "decelerate",
      "speed_modifier": 0.4,
      "trajectory": "yield_path"
    }
  },
  "confidence": 0.92,
  "sensor_fusion": ["lidar", "camera", "ultrasonic"]
}
```

---

## Key Differentiators

### 1. Physics-Based Safety
States determined by TTC, not demographics. Every human receives equal safety treatment.

### 2. Bezier Curve Transitions
Smooth state transitions prevent jarring movements that might startle humans.

### 3. Hysteresis Protection
Sensor noise doesn't cause flickering. Escalation is immediate; de-escalation is conservative.

### 4. Trimodal Redundancy
Light + Sound + Motion ensures humans receive the signal even if one modality is compromised.

---

## Regulatory Alignment

| Regulation | Article | Compliance |
|------------|---------|-----------|
| **EU AI Act** | Art. 50 (Transparency) | ✓ Clear, explainable state signals |
| **EU AI Act** | Art. 10 (Non-Discrimination) | ✓ Physics-based, no demographic profiling |
| **ISO 13482** | Safety signaling | ✓ Signal semantics for all states |
| **EU Machinery Reg. 2023/1230** | Human-machine interaction | ✓ Standardized, manufacturer-flexible |

---

## Repository Structure

```
LSEP/
├── README.md
├── LICENSE
├── LSEP_SPECIFICATION_v2.0.md
├── lsep_signals_v2.0.json
├── LSEP_STATE_DIAGRAM.mermaid
└── examples/
    └── safety_decision_engine.py
```

---

## Quick Start

```python
from safety_decision_engine import SafetyDecisionEngine

engine = SafetyDecisionEngine()

def update_state():
    distance = lidar.get_distance_to_nearest_human()
    velocity = calculate_closing_velocity()
    new_state = engine.determine_state(distance, velocity, robot.current_state)
    robot.emit_signals(new_state)
```

---

## Links

- **[Website](https://lsep.org)** — Overview and use cases
- **[Specification](./LSEP_SPECIFICATION_v2.0.md)** — Full technical documentation
- **[Signal Schema](./lsep_signals_v2.0.json)** — JSON signal definitions
- **[State Diagram](./LSEP_STATE_DIAGRAM.mermaid)** — State transition flows
- **[Reference Implementation](./examples/safety_decision_engine.py)** — Python code

---

## Citation

```bibtex
@misc{galic2026lsep,
  title={LSEP: Luminae Signal Expression Protocol},
  author={Galic, Nemanja},
  year={2026},
  note={Open protocol specification, v2.0},
  url={https://github.com/NemanjaGalic/LSEP}
}
```

---

## License

[MIT License](LICENSE). Free for commercial and non-commercial use with attribution.

---

## Contributing

LSEP is an open protocol. We welcome implementation feedback, safety validation studies, regulatory alignment proposals, and multimodal signal research. Open an issue or pull request.

---

<div align="center">

**Making the silence between humans and machines audible.**

*Experience Design Institute — Zurich, Switzerland*

*LSEP v2.0 — Physics-based. Transparent. Equal safety for all.*

</div>
