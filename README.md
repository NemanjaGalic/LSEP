# LSEP — Luminae Signal Expression Protocol

**The open standard for human-robot communication.**

9 states. 3 modalities. 1 grammar.
Physics-based. EU AI Act ready. No demographic profiling.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

340,000 humanoid robots will enter human spaces by 2030. The EU AI Act (Art. 50) demands transparent communication. ISO 13482 requires safety signaling. Yet **no standard exists** for how a robot tells a human:

> "I see you. I'm slowing down. You're safe."

LSEP fills that gap.

---

## What is LSEP?

LSEP is a **multimodal communication grammar** that defines how robots express internal states to humans through coordinated **light**, **sound**, and **motion** signals.

It is **not** a proprietary API. It is an open protocol — like HTTP for robot communication.

### Core States (6)

| State | Signal | Meaning |
|-------|--------|---------|
| `IDLE` | Slow blue pulse | "I'm here, not active" |
| `ACTIVE` | Steady green | "I'm working" |
| `AWARE` | Directional amber | "I see you" |
| `CAUTION` | Pulsing orange + tone | "Please keep distance" |
| `ALERT` | Fast red flash + alarm | "Danger — move away" |
| `YIELD` | Dimming + deceleration | "I'm giving you space" |

### Extended States (3)

| State | Signal | Meaning |
|-------|--------|---------|
| `HANDOFF` | Sequential light sweep | "Taking/giving control" |
| `LEARNING` | Breathing cyan pulse | "I'm adapting" |
| `ERROR` | Amber strobe + diagnostic tone | "Something is wrong" |

---

## Who It's For

- **System Architects** — Drop-in compliance layer. Import the JSON signal definition, map it to your light ring or speaker array, deploy.
- **Safety Officers** — The first pre-certified communication standard for robot deployments. Audit-ready documentation. Every state transition is traceable.
- **Regulators & Insurers** — The protocol the EU AI Act implies but doesn't define. LSEP gives you a measurable benchmark for "did the robot communicate properly?"

---

## Regulatory Alignment

- **EU AI Act** — Article 50 (transparency obligations)
- **ISO 13482** — Safety requirements for personal care robots
- **EU Machinery Regulation 2023/1230** — Safety of machinery

---

## Quick Start

```json
{
  "protocol": "LSEP",
  "version": "1.0",
  "state": "AWARE",
  "modalities": {
    "light": { "color": "#FFB020", "pattern": "directional_pulse", "frequency_hz": 1.2 },
    "sound": { "type": "proximity_tone", "volume_db": 45 },
    "motion": { "speed_modifier": 0.7, "trajectory": "yield_path" }
  }
}
```

---

## Links

- **Website**: [experiencedesigninstitute.ch](https://www.experiencedesigninstitute.ch)
- **Reddit**: [r/robotics](https://reddit.com/r/robotics)

---

## Citation

```bibtex
@misc{galic2026lsep,
  title={LSEP: Luminae Signal Expression Protocol},
  author={Galic, Nemanja},
  year={2026},
  note={Open protocol specification, v1.0}
}
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Making the silence between humans and machines audible.*

**Experience Design Institute** — Zurich, Switzerland
