# LSEP v2.0 Specification Document
## Luminae Signal Expression Protocol — Formal Technical Specification

**Version:** 2.1-rc1 (Candidate)
**Release Date:** February 25, 2026 (v2.0) — Candidate revision July 9, 2026
**Status:** Technical Review — v2.1 Release Candidate
**Classification:** Open Standards

---

## 1. Title & Version Information

### 1.1 Protocol Identification
- **Name:** Luminae Signal Expression Protocol (LSEP)
- **Version:** 2.1-rc1 (Candidate)
- **Previous Version:** 2.0 (February 25, 2026); 1.5 (August 2025)
- **Release Date:** February 25, 2026 (v2.0) — Candidate revision July 9, 2026
- **Document Type:** Formal Technical Specification
- **Intended Audience:** Senior engineering teams (autonomous robotics platforms)

### 1.2 Target Implementations
This specification is designed for deployment on humanoid and mobile robotic platforms requiring transparent, non-discriminatory safety communication with human operators and bystanders.

Target platforms (aspirational compatibility, not endorsements):
- Humanoid platforms (e.g., Tesla Optimus, Figure AI)
- Mobile robotic platforms (e.g., Boston Dynamics)
- Open-source robotics implementations (ROS 2 compatible)

### 1.3 Standards Alignment
- EU AI Act (2024) Articles 10, 50
- ISO 13482:2014 (Personal care robot safety)
- EU Machinery Regulation 2023/1230
- ISO/IEC 22380 (Safety-related artificial intelligence)
- ANSI/RIA R15.06 (Collaborative robot safety)
- WCAG 2.2, SC 2.3.1 "Three Flashes or Below Threshold" (photosensitivity; conservative adaptation — see Section 6.5.5) *(added v2.1-rc1, ADR-003)*
- ISO 9241-391:2016 (Reduction of photosensitive seizures) *(added v2.1-rc1, ADR-003)*
- ITU-R BT.1702-3 (11/2023) (Reduction of photosensitive epileptic seizures) *(added v2.1-rc1, ADR-003)*

---

## 2. Abstract

The Luminae Signal Expression Protocol (LSEP) v2.0 defines a physics-based, non-discriminatory trimodal communication system for autonomous robots to express internal state, safety awareness, and intention through simultaneous light, sound, and motion signals. This protocol ensures transparent human-robot interaction while maintaining full compliance with EU AI Act non-discrimination requirements.

LSEP v2.0 introduces refined Time-to-Collision (TTC) thresholds, enhanced hysteresis mechanisms to prevent signal flickering, and deterministic state transitions based exclusively on kinematic data. The protocol specifies three communication modalities (light, sound, motion) across nine distinct operational states, with formal definitions for each signal parameter and transition rule. All state escalation and de-escalation decisions are grounded in physics-based calculations independent of demographic data.

This specification enables robots to communicate safety state with high fidelity while achieving trimodal redundancy—ensuring that even if one communication channel becomes unavailable (darkness, noise, occlusion), the remaining two channels maintain semantic clarity and safety meaning.

---

## 3. Scope

### 3.1 What This Specification Covers

1. **Signal Modality Definitions:** Complete technical specifications for light patterns, sound frequencies, and motion behaviors across all protocol states
2. **State Machine Architecture:** Nine operational states with rigorous state transition rules based on Time-to-Collision calculations
3. **Physics-Based Safety Logic:** Deterministic algorithms grounded solely in kinematic data (distance, velocity, acceleration)
4. **Temporal Characteristics:** Frequency parameters, envelope specifications, and transition timing for all signals
5. **Redundancy Requirements:** Minimum specifications for trimodal signal design and failure modes
6. **Regulatory Compliance:** Mapping to specific regulatory requirements (EU AI Act, ISO standards)
7. **Implementation Guidelines:** Hardware requirements, sensor fusion approaches, and integration patterns
8. **JSON Schema Reference:** Formal schema for signal transmission and logging
9. **Versioning Protocol:** Change management and backward compatibility specifications

### 3.2 What This Specification Does NOT Cover

1. **Hardware Design:** Specific LED, speaker, or actuator implementations (platforms provide their own)
2. **Sensor Fusion Algorithms:** Detailed distance/velocity estimation methods (platforms implement their own)
3. **Visual Aesthetics:** Color palette choices beyond functional requirements
4. **Natural Language Processing:** Verbal communication protocols (separate specification)
5. **Tactile Modality:** Touch-based feedback (future extension, LSEP v3.0)
6. **Olfactory Signals:** Scent-based communication (not applicable)
7. **Platform-Specific Integration:** SDK implementations (platform-specific documentation)

### 3.3 Applicable Domains

- Warehouse and logistics automation
- Consumer/residential service robotics
- Industrial collaborative robots
- Healthcare and eldercare environments
- Public space autonomous systems
- Emergency response robotics

### 3.4 Explicitly Non-Applicable

- Military or weaponized systems
- Covert surveillance platforms
- Autonomous weapons systems
- Systems designed for human impersonation

---

## 4. Definitions & Terminology

### 4.1 Core Concepts

**State Machine:** A computational model representing the robot's operational condition, transitioning between nine defined states based on sensor inputs and kinematic calculations.

**Time-to-Collision (TTC):** Physics-derived metric calculated as `TTC = distance / closing_velocity` (seconds). Primary determinant for safety state transitions.

**Trimodal Redundancy:** Requirement that each safety state be expressed across three independent communication modalities (light, sound, motion) such that semantic meaning is preserved if one channel fails.

**Closing Velocity:** Rate at which spatial separation between robot and human decreases, calculated from relative velocity components along approach vector.

**Hysteresis:** Temporal buffer applied to state transitions to prevent rapid flickering when TTC calculations fluctuate near threshold boundaries. Escalation is immediate; de-escalation requires sustained readings.

**Signal Envelope:** Amplitude envelope of a signal over time, defined by ADSR parameters (Attack, Decay, Sustain, Release).

**Bezier Transition:** Cubic Bézier curve applied to all signal parameter changes during state transitions, ensuring smooth evolution rather than instantaneous changes.

### 4.2 Safety Terminology

**Immediate Danger:** Any condition where TTC < 0.5 seconds. Triggers automatic escalation to THREAT state, bypassing all standard hysteresis rules.

**Emergency Response Mode:** Triggered when entering CRITICAL or THREAT states. Standard response latency requirements are suspended and maximum signal amplitude is mandated.

**Sensor Degradation:** Condition where sensor confidence falls below defined thresholds, triggering MED_CONF or LOW_CONF states and activating conservative motion behaviors.

**Collision Trajectory:** Predicted path where robot and human occupy same spatial coordinates simultaneously if current velocities and accelerations remain constant.

**Safe Separation Distance:** Minimum distance required such that current TTC exceeds 1.5 seconds at maximum platform velocity.

---

## 5. Protocol Architecture

### 5.1 Overview

LSEP v2.0 is a trimodal state machine that maps internal robot state to synchronized signals across three independent communication channels:

1. **Light Modality:** Visual signals via LED arrays, displays, or dedicated light sources
2. **Sound Modality:** Acoustic signals via speakers or piezoelectric transducers
3. **Motion Modality:** Kinematic signals via actuated movement (head turns, body orientation, movement velocity)

The protocol defines nine operational states organized into two tiers:
- **Core States (6):** Primary safety-critical states
- **Extended States (3):** Secondary diagnostic and confidence states

### 5.2 State Hierarchy

```
LSEP STATE MACHINE (v2.0)
│
├─ CORE SAFETY STATES (6)
│  ├─ IDLE (System dormant, no human detected)
│  ├─ AWARENESS (Human detected, passive observation)
│  ├─ INTENT (Robot planning action near human)
│  ├─ CARE (Active safety measures, proximity caution)
│  ├─ CRITICAL (Immediate danger, emergency response)
│  └─ THREAT (Imminent collision, maximum alert)
│
└─ EXTENDED STATES (3)
   ├─ MED_CONF (Medium confidence in sensor data)
   ├─ LOW_CONF (Low confidence, degraded sensing)
   └─ INTEGRITY (System self-check, diagnostic mode)
```

### 5.3 Modality Independence

Each modality operates independently with identical semantic meaning:

- **Light:** Optimal for line-of-sight communication; primary for spatial information
- **Sound:** Optimal for rapid attention-getting; primary for temporal urgency cues
- **Motion:** Optimal for communicating intent trajectory; primary for kinematic expression

All three carry equal semantic weight and function as a complete redundancy system.

### 5.4 Architecture Principles

1. **Physics-Based Determinism:** State transitions depend exclusively on kinematic data (distance, velocity, acceleration), never on demographic attributes
2. **Signal Clarity:** Each state produces unambiguous, easily distinguishable signals
3. **Fail-Safe Design:** Signal loss in any single modality does not compromise safety semantics
4. **Temporal Responsiveness:** Critical state transitions occur within 200 milliseconds of trigger condition
5. **Energy Efficiency:** Default state (IDLE) minimizes energy consumption
6. **Platform Agnostic:** Signal specifications are hardware-independent

---

## 6. Core State Definitions

### 6.1 IDLE State

**Semantic Meaning:** System dormant, no human detected within operational sensor range. Robot in low-energy monitoring mode.

**Triggering:** No human within 50 meters, system powered on but not actively engaged.

#### 6.1.1 Light Signal

- **Pattern:** Soft breathing pulse
- **Frequency:** 0.3 Hz (3.33 second cycle)
- **Intensity:** 0.15–0.35
- **Color:** Soft white or platform accent
- **Waveform:** Sinusoidal
- **Formula:** Intensity(t) = 0.25 + 0.1 × sin(2π × 0.3 × t)

#### 6.1.2 Sound Signal

- **Pattern:** Silence
- **Volume:** 0 dB
- **Justification:** IDLE represents minimum environmental impact

#### 6.1.3 Motion Signal

- **Action:** Settled posture
- **Behavior:** No active movement; neutral, non-threatening orientation
- **Speed Modifier:** 0.0

#### 6.1.4 Energy Profile

- **LED Power:** 0.5–1.2 watts
- **Speaker Power:** 0 watts
- **Actuator Power:** 0 watts
- **Total:** < 2 watts

---

### 6.2 AWARENESS State

**Semantic Meaning:** Human detected; robot passively observing and acknowledging presence. No active engagement initiated.

**Triggering:** Human within 50m range, TTC 5.0–10.0 seconds, no collision trajectory.

#### 6.2.1 Light Signal

- **Pattern:** Brightening sweep
- **Frequency:** 0.5 Hz (2.0 second cycle)
- **Intensity:** 0.35–0.65
- **Color:** Bright white
- **Formula:** Intensity(t) = 0.50 + 0.15 × sin(2π × 0.5 × t)

#### 6.2.2 Sound Signal

- **Pattern:** Orientation chime
- **Frequency:** 440 Hz (A4 note, international standard)
- **Volume:** 65 dB
- **Duration:** 200 milliseconds
- **ADSR:** Attack 50ms, Decay 100ms, Sustain 50ms, Release 50ms

#### 6.2.3 Motion Signal

- **Action:** Turns toward human
- **Speed:** 0.3 modifier (smooth, deliberate)
- **Trajectory:** Head/body pivot toward detected position
- **Duration:** 1.0–1.5 seconds

---

### 6.3 INTENT State

**Semantic Meaning:** Robot planned action and moving purposefully near/toward human. Active motion with deliberate trajectory communicating intent.

**Triggering:** Human within 15m, robot initiates planned motion, TTC 3.0–5.0 seconds.

#### 6.3.1 Light Signal

- **Pattern:** Steady directional glow
- **Frequency:** None (steady)
- **Intensity:** 0.70
- **Color:** White or platform accent
- **Ramp:** 500ms to steady state

#### 6.3.2 Sound Signal

- **Pattern:** Soft hum
- **Frequency:** 330 Hz (E4 note)
- **Volume:** 60 dB
- **Duration:** Continuous while in state
- **ADSR:** Attack 500ms, Decay 0ms, Sustain 60dB, Release 200ms

#### 6.3.3 Motion Signal

- **Action:** Smooth purposeful movement
- **Speed:** 0.4–0.6 modifier
- **Trajectory:** Follows planned motion vector
- **Velocity Profile:** Ramp over 1.0 second, smooth acceleration

---

### 6.4 CARE State

**Semantic Meaning:** Proximity risk detected; robot implementing active safety measures. Decelerating, yielding path, requesting increased separation distance.

**Triggering:** Human within 2.0m range, TTC 1.5–3.0 seconds, collision trajectory predicted.

#### 6.4.1 Light Signal

- **Pattern:** Amber wave (pulsing warning)
- **Frequency:** 1.5 Hz (0.67 second cycle)
- **Intensity:** 0.50–0.95
- **Color:** Amber/Orange RGB(255, 165, 0)
- **Waveform:** Triangular
- **Formula:** Intensity(t) = 0.725 + 0.225 × triangle_wave(1.5 × t)

#### 6.4.2 Sound Signal

- **Pattern:** Low proximity tone
- **Frequency:** 660 Hz (E5 note)
- **Volume:** 72 dB
- **Duration:** Continuous
- **ADSR:** Attack 300ms, Decay 0ms, Sustain 72dB, Release 150ms

#### 6.4.3 Motion Signal

- **Action:** Decelerates and yields path
- **Speed:** 0.2–0.3 modifier
- **Deceleration:** 0.5 m/s²
- **Trajectory:** Lateral away or forward significantly reduced

#### 6.4.4 Hysteresis Rules

- **Escalation to CRITICAL:** Immediate (no hysteresis)
- **De-escalation to INTENT:** Requires 3.0 seconds sustained TTC > 3.5 seconds

---

### 6.5 CRITICAL State

**Semantic Meaning:** Immediate danger detected. Robot transitioning to emergency response protocols. High collision risk within 0.5–1.5 seconds.

**Triggering:** TTC < 1.5 seconds AND human within 1.5m, collision trajectory high confidence, rapid approach (> 1.5 m/s).

#### 6.5.1 Light Signal

- **Pattern:** Asymmetric double pulse ("pulse–pulse–pause")
- **Timing:** 100 ms on / 150 ms off / 100 ms on / 650 ms off — period 1.0 s = **2 flashes per second**
- **Intensity:** 0.70–1.0
- **Color:** Bright red RGB(255, 0, 0)
- **Waveform:** Rectangular pulses within the double-pulse pattern above
- **Transition:** Emergency curve (instantaneous)
- **Photosensitivity:** Complies with the protocol-wide flash cap — see Section 6.5.5 (normative)

*Change note (v2.1-rc1, 2026-07-09, ADR-003): v2.0 defined a 3.0 Hz rectangular strobe (50% duty cycle) — replaced by the asymmetric double pulse. 2 flashes/s keeps a 33% margin below the WCAG 2.2 SC 2.3.1 three-flash limit; the asymmetric pattern preserves urgency and stays temporally distinct from the CARE pulse (1.5 Hz, Section 6.4.1). Sound signal (880 Hz, 85 dB) unchanged.*

#### 6.5.2 Sound Signal

- **Pattern:** Clear warning tone
- **Frequency:** 880 Hz (A5 note, two octaves above INTENT)
- **Volume:** 85 dB
- **Duration:** Continuous
- **ADSR:** Attack 100ms, Decay 0ms, Sustain 85dB, Release 50ms

#### 6.5.3 Motion Signal

- **Action:** Stops or retreats
- **Speed:** -0.5 modifier (rapid deceleration)
- **Deceleration:** 1.0–2.0 m/s²
- **Trajectory:** Immediate reversal of approach vector

#### 6.5.4 Escalation Rules

- **Immediate escalation:** No hysteresis required
- **Bypass to THREAT:** If TTC drops below 0.5s, escalate directly to THREAT

#### 6.5.5 Photosensitivity Safety (Normative)

*Added 2026-07-09 (v2.1-rc1) per ADR-003.*

1. **Protocol-wide flash cap:** No LSEP light signal that exceeds the WCAG "general flash" threshold may produce more than **2 flashes per second**. For rectangular/on-off patterns this means a hard frequency cap of **2.0 Hz**.
2. **Scope (normative):** This cap binds the ENTIRE protocol — all nine defined states AND any future Extended States, including third-party implementations. Medical safety limits are not optional (Lead Architect decision, 2026-07-09).
3. **Flash definitions (by reference):** "General flash" and "red flash" as defined in WCAG 2.2 SC 2.3.1 — a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance where the relative luminance of the darker state is below 0.80; red flash: any pair of opposing transitions involving a saturated red.
4. **Conformance test rule:** The reference implementation MUST include a flash-rate lint: no light signal above the general-flash threshold may produce more than 2 flashes per second, including under timing jitter.
5. **Sources:** WCAG 2.2 SC 2.3.1 (Three Flashes or Below Threshold); ISO 9241-391:2016; ITU-R BT.1702-3 (11/2023).
6. **Marked assumption:** These thresholds are defined for screen/broadcast content. LSEP adopts them as a conservative adaptation for physical robot lights and claims no conformance within those standards' scopes. Photometric verification (specification "intensity" vs. relative luminance) on reference hardware is pending.

---

### 6.6 THREAT State

**Semantic Meaning:** Imminent collision; TTC < 0.5 seconds. Maximum-alert state representing catastrophic collision likelihood. All safety systems at maximum output.

**Triggering:** TTC < 0.5 seconds (collision expected within 500ms), bypass rule overrides all hysteresis.

#### 6.6.1 Light Signal

- **Pattern:** Red steady
- **Frequency:** None (steady)
- **Intensity:** 1.0 (maximum)
- **Color:** Bright red RGB(255, 0, 0)
- **Transition:** Emergency curve (instantaneous)

#### 6.6.2 Sound Signal

- **Pattern:** Urgent alarm
- **Frequency:** 1100 Hz (C6 note, very high-pitched)
- **Volume:** 95 dB (maximum safe continuous exposure)
- **Duration:** Continuous
- **ADSR:** Attack 50ms, Decay 0ms, Sustain 95dB, Release 0ms

#### 6.6.3 Motion Signal

- **Action:** Full stop + emergency backup
- **Speed:** -1.0 modifier (maximum emergency)
- **Deceleration:** 2.0–3.0 m/s²
- **Trajectory:** Immediate full reversal with maximum backward acceleration

#### 6.6.4 Post-THREAT Protocol

- Clear when TTC > 1.0s sustained 2.0+ seconds
- Transitions to CRITICAL
- May require diagnostic check after event

---

## 7. Extended State Definitions

### 7.1 MED_CONF State (Medium Confidence)

**Semantic Meaning:** Sensor confidence degraded to medium (60–80%). Robot operating with reduced certainty about distance/velocity, typically due to occlusion, reflective surfaces, or noise.

**Triggering:** Confidence 60–80%, significant uncertainty ranges, multiple sensors disagreeing.

#### 7.1.1 Light Signal

- **Pattern:** Shimmer
- **Frequency:** 4.0 Hz
- **Intensity:** 0.40–0.60
- **Color:** Cyan RGB(0, 255, 255)
- **Waveform:** Sinusoidal shimmer
- **Formula:** Intensity(t) = 0.50 + 0.10 × sin(2π × 4.0 × t)
- **Photosensitivity constraint (v2.1-rc1, normative — Section 6.5.5):** As specified above (4.0 Hz, 20% luminance modulation, darker state below 0.80), this signal exceeds the general-flash threshold and MUST be revised for v2.1 final: either reduce modulation depth below 10% of maximum relative luminance (preferred — preserves the shimmer character) or reduce frequency to ≤ 2.0 Hz. Exact revised parameter values: **OPEN** (ADR-003 names 0.50 ± 0.04 only as an example, not a normative value).

#### 7.1.2 Sound Signal

- **Pattern:** Query tone (rising pitch)
- **Frequency:** Sweep 400 Hz → 600 Hz over 500ms
- **Volume:** 68 dB
- **Duration:** Repeating every 2.0 seconds
- **ADSR:** Attack 100ms, Decay 50ms, Sustain 300ms, Release 50ms

#### 7.1.3 Motion Signal

- **Action:** Cautious/slower movement
- **Speed:** 0.3 modifier
- **Scanning:** Head may scan slowly to improve sensor input
- **Behavior:** Appears cautious, "trying to understand"

---

### 7.2 LOW_CONF State (Low Confidence)

**Semantic Meaning:** Sensor confidence critically degraded (< 60%). Robot barely estimates position/velocity. Enters conservative survival mode.

**Triggering:** Confidence < 60%, unable to estimate TTC meaningfully, critical sensor failure or occlusion.

#### 7.2.1 Light Signal

- **Pattern:** Blinking
- **Frequency:** 2.0 Hz
- **Intensity:** 0.0–0.80
- **Color:** Yellow RGB(255, 255, 0)
- **Waveform:** Rectangular
- **Formula:** Intensity(t) = 0.40 + 0.40 × square_wave(2.0 × t)

*Change note (v2.1-rc1, 2026-07-09, ADR-003): v2.0 defined 5.0 Hz — reduced to 2.0 Hz to comply with Section 6.5.5 (blink character preserved).*

#### 7.2.2 Sound Signal

- **Pattern:** Error chirp
- **Frequency:** Sweep 800 Hz → 300 Hz over 800ms
- **Volume:** 75 dB
- **Duration:** Repeating every 3.0 seconds
- **ADSR:** Attack 50ms, Decay 400ms, Sustain 0ms, Release 350ms

#### 7.2.3 Motion Signal

- **Action:** Frozen or minimal movement
- **Speed:** 0.0–0.1 modifier
- **Behavior:** Nearly stationary, minimal orientation adjustments

---

### 7.3 INTEGRITY State (System Diagnostics)

**Semantic Meaning:** Robot performing internal system self-checks, diagnostics, or calibration. Stationary mode, not interacting with environment.

**Triggering:** Manual diagnostic entry, scheduled self-check, post-event diagnostics, system reboot, operator validation request.

#### 7.3.1 Light Signal

- **Pattern:** Sequential sweep
- **Frequency:** One complete cycle per 2.0 seconds
- **Intensity:** 0.30–0.80
- **Color:** Multicolor Blue → Green → Cyan → White
- **Waveform:** Sequential transitions

#### 7.3.2 Sound Signal

- **Pattern:** Diagnostic tone (neutral, informational)
- **Frequency:** Steps 500 Hz → 600 Hz → 700 Hz → 500 Hz
- **Volume:** 65 dB
- **Duration:** Each tone 250ms, 100ms silence between
- **ADSR:** Attack 50ms, Decay 50ms, Sustain 150ms, Release 50ms

#### 7.3.3 Motion Signal

- **Action:** Stationary
- **Speed:** 0.0 modifier
- **Behavior:** Remains in place, neutral centered posture

---

## 8. State Transition Rules

### 8.1 Time-to-Collision Calculation

Primary determinant for state transitions:

```
TTC = distance / closing_velocity

where:
  distance = current separation (meters)
  closing_velocity = rate of approach (m/s)
```

#### 8.1.1 Distance Measurement

- **Source:** LiDAR, RGB-D sensor, or radar (platform-dependent)
- **Frequency:** Minimum 10 Hz (recommended 20+ Hz)
- **Accuracy:** ± 0.1 meters for distances < 5 meters
- **Occlusion Handling:** Use maximum extent of visible human body
- **Multi-Human:** Track closest human for TTC calculation

#### 8.1.2 Closing Velocity

- **Method:** First derivative of position over time (Kalman filter smoothing typical)
- **Direction:** Component along approach vector
- **Stationary Human:** Zero closing velocity (TTC → infinity)

#### 8.1.3 Sensor Fusion

- **Multiple sensors:** Fuse for robust TTC estimate
- **High confidence (> 80%):** Multiple sensors agree within 0.3m
- **Medium confidence (60–80%):** Sensors agree within 0.5m
- **Low confidence (< 60%):** Disagreement > 0.5m

### 8.2 TTC Threshold Table

| TTC Range (seconds) | Primary State | Justification |
|---|---|---|
| TTC ≥ 10.0 | IDLE | Safe separation |
| 5.0 ≤ TTC < 10.0 | AWARENESS | Human detected, no concern |
| 3.0 ≤ TTC < 5.0 | INTENT | Robot planning action near human |
| 1.5 ≤ TTC < 3.0 | CARE | Proximity concern |
| 0.5 ≤ TTC < 1.5 | CRITICAL | High-risk proximity |
| TTC < 0.5 | THREAT | Imminent collision |

#### 8.2.1 Platform Risk Class (`platform_risk_class`) — v2.1 Candidate

*Added 2026-07-09 (v2.1-rc1) per ADR-003 (GitHub Issue #1).*

**Definition:** Optional field `platform_risk_class` (enum `PRC_1`–`PRC_4`) classifying the platform by its **maximum kinetic energy capability** (capability, not momentary value — deterministic and certifiable at design time):

```
E_max = 0.5 × m × v_max²

where:
  m     = total platform mass incl. maximum payload (kg)
  v_max = maximum platform velocity (m/s)
```

| Class | E_max | TTC Multiplier k | Example (illustrative) |
|---|---|---|---|
| PRC_1 | ≤ 10 J | 1.0 (baseline, default) | 3 kg vacuum robot, ≤ 2.5 m/s (≈ 9 J) |
| PRC_2 | 10–100 J | 1.5 | 30 kg service robot, ≤ 2.5 m/s (≈ 94 J) |
| PRC_3 | 100–1,000 J | 2.0 | 150 kg platform, ≤ 3.5 m/s (≈ 919 J) |
| PRC_4 | > 1,000 J | 3.0 | 500 kg platform, ≥ 2.0 m/s (≥ 1,000 J) |

**Effect:** `TTC_effective(State) = TTC_base(State) × k` for the **escalation** thresholds of CARE and CRITICAL (optionally AWARENESS/INTENT). Example (SSOT constants): a PRC_3 platform escalates to CRITICAL at TTC < 3.0 s instead of < 1.5 s.

**Backward compatibility:** The field is optional; **default = PRC_1 (k = 1.0)** — existing v2.0 implementations remain valid unchanged.

**THREAT bypass does NOT scale:** The 0.5 s bypass threshold (Section 8.4) is identical for all PRC classes (Lead Architect decision 2026-07-09: 0.5 s marks the physical point of no return — a universal rigid anchor, independent of platform mass).

**Anti-bias constraint:** k depends EXCLUSIVELY on mass and maximum velocity. No demographic, personal, or situation-classifying parameters (see Section 12).

**Marked as discussion basis:** The class boundaries 10 / 100 / 1,000 J are engineering judgment without a normative source and are explicitly a **discussion basis** for a community RFC. Classification by kinetic energy (not momentum) is definitive (Lead Architect decision 2026-07-09: injury severity scales quadratically with velocity).

### 8.3 Hysteresis Rules

#### 8.3.1 Escalation

- **Rule:** Immediate; no hysteresis buffer
- **Rationale:** Collision risk increase requires instant response
- **Exception:** THREAT bypass rule for TTC < 0.5s

#### 8.3.2 De-escalation

| From State | To State | Required Duration |
|---|---|---|
| THREAT | CRITICAL | 2.0 seconds at TTC > 1.0 |
| CRITICAL | CARE | 2.0 seconds at TTC > 2.0 |
| CARE | INTENT | 3.0 seconds at TTC > 3.5 |
| INTENT | AWARENESS | 2.0 seconds at TTC > 5.5 |

#### 8.3.3 Deadzone

```
CARE ↔ INTENT boundary:
  - Escalate: TTC < 3.0s (immediate)
  - De-escalate: TTC > 3.5s for 3.0s (deadzone: 0.5s)
```

Prevents flickering when human drifts near boundary.

### 8.4 THREAT Bypass Rule

**Critical Exception:** If TTC < 0.5 seconds, immediately escalate to THREAT, **bypassing all intermediate states and hysteresis**.

**Rationale:** At TTC < 0.5s, collision is imminent (< 500ms); no time for gradual transitions.

```
Example: INTENT state, TTC suddenly drops to 0.4s
  → Jump directly to THREAT (skip CARE and CRITICAL)
  → Red light, 1100 Hz alarm, emergency stop activate instantly
  → No hysteresis delay; maximum signal amplitude immediately
```

**v2.1-rc1 note (2026-07-09, ADR-003):** The 0.5 s bypass threshold does **NOT** scale with `platform_risk_class` (Section 8.2.1); it is a universal rigid anchor for all PRC classes.

### 8.5 Escalation Protocol

Hierarchical state escalation (no skipping except THREAT rule):

```
IDLE
  ↓ (human detected, TTC > 5s)
AWARENESS
  ↓ (robot moves, TTC 3-5s)
INTENT
  ↓ (proximity risk, TTC 1.5-3s)
CARE
  ↓ (high risk, TTC 0.5-1.5s)
CRITICAL
  ↓ (imminent, TTC < 0.5s)
THREAT
```

**Latency:** < 200 milliseconds (hardware processing + signal output)

### 8.6 De-escalation Protocol

Reverse hierarchy with hysteresis:

```
THREAT (requires 2.0s at TTC > 1.0s)
  ↓
CRITICAL (requires 2.0s at TTC > 2.0s)
  ↓
CARE (requires 3.0s at TTC > 3.5s)
  ↓
INTENT (requires 2.0s at TTC > 5.5s)
  ↓
AWARENESS
  ↓
IDLE (10+ seconds no detection)
```

**Velocity:** Gradual (1–3 seconds per level) to avoid alarming humans

### 8.7 Multi-Human Environments

1. **Tracking:** All detected humans tracked
2. **Closest Priority:** TTC uses closest human only
3. **State Determination:** Based on closest human's TTC
4. **Signal Broadcast:** All three modalities broadcast state for closest human
5. **Peripheral:** Other humans tracked for early warning

---

## 9. Signal Specification Summary

### 9.1 Light Modality

#### Physical Requirements

- **Color Space:** RGB (sRGB, CIE 1931)
- **Brightness:** 0–1000 nits
- **Minimum Peak:** 0.35 intensity in low light (≥ 35 nits)
- **Maximum Peak:** 1.0 intensity (≥ 500 nits)
- **Frequency Range:** 0.3–5.0 Hz
- **CRI:** ≥ 85
- **Visibility Range:** Minimum 20 meters line of sight

#### Color Coding

| State | Color | RGB | Semantic |
|---|---|---|---|
| IDLE | Soft White | (240, 240, 240) | Dormant |
| AWARENESS | Bright White | (255, 255, 255) | Attention |
| INTENT | Bright White | (255, 255, 255) | Active |
| CARE | Amber | (255, 165, 0) | Caution |
| CRITICAL | Red | (255, 0, 0) | Danger |
| THREAT | Bright Red | (255, 0, 0) | Emergency |
| MED_CONF | Cyan | (0, 255, 255) | Uncertain |
| LOW_CONF | Yellow | (255, 255, 0) | Help Needed |
| INTEGRITY | Multicolor | Cycling | Diagnostic |

### 9.2 Sound Modality

#### Physical Requirements

- **Frequency Range:** 300–1100 Hz
- **Volume Range:** 0–95 dB SPL
- **Stereo/Mono:** Mono
- **Sample Rate:** 48 kHz minimum
- **Bit Depth:** 16-bit or 24-bit
- **Waveform:** Sine, triangle, or square

#### Volume Reference

| dB | Perception | Example |
|---|---|---|
| 60 | Quiet | Normal conversation |
| 70 | Moderate | Busy office |
| 80 | Loud | Heavy traffic |
| 85 | Very loud | Vacuum cleaner |
| 95 | Dangerous | Motorcycle, power drill |

### 9.3 Motion Modality

#### Physical Requirements

- **DOF:** Minimum 1 (head yaw); recommend 2+ (yaw + pitch)
- **Angular Velocity:** 0–180 deg/s
- **Linear Velocity:** 0–2.0 m/s
- **Acceleration:** 0–1.0 m/s²
- **Emergency Deceleration:** 0–3.0 m/s²

#### Speed Modifiers

| Modifier | Meaning | Velocity |
|---|---|---|
| 0.0 | Stopped | 0 m/s |
| 0.1–0.2 | Crawl | 0.1–0.3 m/s |
| 0.3–0.4 | Walk | 0.3–0.6 m/s |
| 0.5–0.7 | Purposeful | 0.6–1.2 m/s |
| 0.8–1.0 | Maximum | 1.2–2.0 m/s |
| -0.5 to -1.0 | Reverse | Backward motion |

---

## 10. Bézier Curve Transitions

### 10.1 Cubic Bézier Formula

```
B(t) = (1 - t)³ * P0 + 3(1 - t)² * t * P1 + 3(1 - t) * t² * P2 + t³ * P3

where t ∈ [0, 1]
```

### 10.2 Curve Types

#### Standard Curve (Ease-In-Out)

- **Control Points:** [0.4, 0.0, 0.2, 1.0]
- **Duration:** 500 milliseconds
- **Use:** General-purpose transitions
- **Behavior:** Smooth acceleration at start, deceleration at end

#### Emergency Curve (Instant)

- **Control Points:** [0.0, 0.0, 0.0, 1.0]
- **Duration:** 0 milliseconds
- **Use:** Emergency escalations
- **Behavior:** Instantaneous transition

#### Graceful De-escalation Curve

- **Control Points:** [0.4, 0.0, 0.2, 1.0]
- **Duration:** 1000 milliseconds
- **Use:** Returning from high-urgency states
- **Behavior:** Slower, reassuring transition

---

## 11. Trimodal Redundancy

### 11.1 Core Principle

LSEP designed with three independent channels such that semantic meaning preserved even if one channel fails.

**Goal:** No single point of failure in human-robot communication.

### 11.2 Failure Modes

#### Light Failure

**Scenario:** Complete darkness or LED failure

**Compensation:** Sound + motion fully encode state

#### Sound Failure

**Scenario:** Extremely loud environment or speaker failure

**Compensation:** Light + motion fully encode state

#### Motion Failure

**Scenario:** Mobility impairment or confined space

**Compensation:** Light + sound fully encode state

### 11.3 Cross-Modal Consistency

All three modalities for each state encode identical semantic meaning through different channels. No contradictory signals possible.

### 11.4 Minimum Requirements

1. Two of three channels always available during normal operation
2. Graceful degradation if one channel fails
3. Cross-modal consistency maintained
4. Fail-safe default (IDLE or LOW_CONF if signal generation fails)

---

## 12. Physics-Based Non-Discrimination

### 12.1 Core Principle

All state decisions grounded in physics-based metrics (distance, velocity, acceleration) independent of demographic attributes.

**Rule:** Safety state depends exclusively on kinematic data; never on age, gender, ethnicity, disability status, or demographic characteristic.

### 12.2 State Determination Inputs

```
Kinematic_Inputs = {
  distance: meters
  velocity_approach: m/s
  acceleration: m/s²
  sensor_confidence: 0.0–1.0
}

Safety_State = f(Kinematic_Inputs)

// Explicitly EXCLUDED:
// Age, gender, ethnicity, nationality
// Disability status, mobility limitations
// Clothing, appearance, identity
// Social status, economic class
```

### 12.3 Examples of Non-Discriminatory Behavior

#### Scenario 1: Child vs. Adult

**Condition:** Both approach at identical velocity

**Distance:** 2.0 meters
**Closing Velocity:** 1.0 m/s (both)
**TTC:** 2.0 seconds (both)

**Response:** AWARENESS state (identical signals)

**Protection:** No age-based discrimination. Child and adult receive identical behavior.

#### Scenario 2: Wheelchair User

**Condition:** Person using wheelchair approaches

**Distance:** 1.5 meters
**Closing Velocity:** 0.5 m/s
**TTC:** 3.0 seconds

**Response:** AWARENESS/INTENT state

**Protection:** Wheelchair use is not a factor. Mobility aid users receive identical safety logic.

#### Scenario 3: Diverse Approaching Group

**Condition:** Three humans, identical velocity and distance

**TTC:** 1.8 seconds (all)

**Response:** CARE state (identical signals for all)

**Protection:** Demographic diversity irrelevant. All receive identical safety treatment.

### 12.4 Explicitly Prohibited

```
// PROHIBITED
if detected_age < 10:
    enter_maximum_care_state()  // VIOLATES LSEP

if detected_ethnicity == "minority":
    increase_alert_level()  // VIOLATES LSEP

if wheelchair_detected:
    trigger_higher_safety_state()  // VIOLATES LSEP

// ALLOWED
if TTC < 1.5_seconds:
    enter_care_state()  // COMPLIANT
```

### 12.5 Compliance Verification

Log entry structure (no demographic attributes):

```
Log_Entry = {
  timestamp: ISO8601,
  detected_distance: meters,
  detected_velocity: m/s,
  calculated_TTC: seconds,
  determined_state: string,
  triggered_signals: {light, sound, motion}
  // Demographics NEVER logged or processed
}
```

Auditors can verify by:
1. Collecting 100+ logs
2. Analyzing TTC values and states
3. Confirming identical TTC → identical states
4. Confirming no demographic attributes processed

---

## 13. Regulatory Compliance Mapping

### 13.1 EU AI Act (2024)

#### Article 50: Transparency

**Requirement:** Inform users they interact with AI system

**LSEP Compliance:** All states explicitly communicate robot presence and operational status via light, sound, motion.

#### Article 10: Non-Discrimination

**Requirement:** Prohibit discrimination based on protected characteristics

**LSEP Compliance:** State determination uses physics-only metrics. No protected characteristics influence safety state.

#### Article 15: Risk Assessment

**Requirement:** Assess discrimination risks for high-risk systems

**LSEP Compliance:** Section 12 includes explicit non-discrimination testing and audit trail.

### 13.2 ISO 13482:2014 (Personal Care Robot Safety)

#### Section 4.2.1: Hazard Identification

**Requirement:** Identify hazards in risk assessment

**LSEP Mapping:** CARE, CRITICAL, THREAT states address collision hazards.

#### Section 5.2: Safety Signals

**Requirement:** Provide safety-related signals to warn users

**LSEP Compliance:** Sections 6.4–6.6 specify safety signal design.

#### Section 5.3: User Interface

**Requirement:** Enable understanding of robot state and intentions

**LSEP Compliance:** All nine states include explicit indicators.

### 13.3 EU Machinery Regulation 2023/1230

#### Annex I, Requirement 1.5.1: Collision Avoidance

**Requirement:** Appropriate devices to avoid/reduce collision risks

**LSEP Compliance:** CARE, CRITICAL, THREAT states with escalating signals and deceleration.

#### Annex I, Requirement 1.7.1: Warning Devices

**Requirement:** Appropriate warning devices

**LSEP Compliance:** Light and sound signals serve as warning devices.

### 13.4 ISO/IEC 22380: AI Safety

#### Section 5.2: Safety Assurance

**Requirement:** Maintain safety properties during operation

**LSEP Compliance:** Deterministic logic, hysteresis rules, trimodal redundancy.

---

## 14. Implementation Guidance

### 14.1 Hardware Requirements

#### Light Modality

- LED array or display (RGB, ≥ 500 nits)
- Refresh rate ≥ 60 Hz
- CRI ≥ 85
- Minimum 100 cm² display area
- IP65 rating (dust/moisture resistant)

#### Sound Modality

- Full-range speaker
- Frequency response 300–2000 Hz ± 3 dB
- SPL output minimum 85 dB
- Mono acceptable

#### Motion Modality

- Servo or stepper motors
- Speed range 0–2.0 m/s (mobile) or 0–180 deg/s (rotation)
- Acceleration 0–1.0 m/s²
- Emergency deceleration 3.0 m/s² max

#### Sensor Suite

- Distance: LiDAR, RGB-D, or radar
- Frequency: ≥ 10 Hz (recommend 20+ Hz)
- Accuracy: ± 0.1 m for < 5 m
- Velocity: Kalman filter smoothing

### 14.2 Software Architecture

#### State Machine Loop (20 Hz)

```
while robot_powered_on:
    distance = get_human_distance()
    velocity = get_relative_velocity()
    confidence = get_sensor_confidence()
    TTC = distance / velocity
    new_state = determine_safety_state(TTC, confidence)

    if new_state != current_state:
        apply_bezier_transition()
        current_state = new_state

    light_signal = generate_light_signal()
    sound_signal = generate_sound_signal()
    motion_signal = generate_motion_signal()

    apply_signals()
    log_event()
    sleep(50 ms)
```

#### Latency Budget

- Sensor → State Determination: < 50 ms
- State → Signal Generation: < 50 ms
- Signal → Hardware: < 100 ms
- **Total:** < 200 ms (LSEP requirement)

### 14.3 Testing Protocol

#### Functional Testing

Per each state:
- Light: Pattern, frequency, color, intensity
- Sound: Frequency, volume, envelope, duration
- Motion: Action, speed, trajectory, timing
- Transitions: Bézier curve application
- Redundancy: Disable each modality separately

#### Safety Testing

- TTC Threshold: Verify transitions at correct values
- Hysteresis: Verify no flickering near boundaries
- Emergency: Verify immediate THREAT escalation (TTC < 0.5s)
- Failure Mode: Verify graceful LOW_CONF degradation

#### Non-Discrimination Testing

- Demographic Parity: Test identical TTC across variations
- Equal Treatment: Verify identical state and signals
- Audit Trail: Confirm no demographic attributes processed

---

## 15. Versioning & Change Log

### 15.1 Version History

| Version | Release | Status | Changes |
|---|---|---|---|
| 1.0 | Jan 2024 | Deprecated | Initial; 6 core states |
| 1.5 | Aug 2025 | Deprecated | Extended states; refined TTC |
| 2.0 | Feb 2026 | Current | Formal spec; regulatory mapping; non-discrimination |
| 2.1-rc1 | Jul 2026 | Candidate | TTC SSOT errata; photosensitivity cap + CRITICAL double pulse (ADR-003); `platform_risk_class` |

### 15.2 Backward Compatibility

**v1.5 → v2.0:** Fully backward compatible.

**Enhanced:**
- Refined hysteresis
- JSON schema
- Explicit non-discrimination
- Regulatory mapping

### 15.3 Future Roadmap

**v2.1 (Q3 2026):**
- Haptic modality
- Multi-robot coordination
- Environmental sensor integration

**v3.0 (2027):**
- Verbal communication
- Gesture signaling
- ML confidence estimation

### 15.4 Errata & Change Log

- **2026-07-09:** TTC thresholds consolidated to Terminology Dictionary SSOT (errata); THREAT semantics confirmed as TTC-based collision state (CEO decision, Option 1).
- **2026-07-09 (v2.1-rc1, ADR-003):** CRITICAL light signal changed from 3.0 Hz rectangular strobe to asymmetric double pulse (100/150/100/650 ms, period 1.0 s = 2 flashes/s); new normative subsection 6.5.5 "Photosensitivity Safety" (protocol-wide ≤ 2 flashes/s cap, normative incl. third-party Extended States); LOW_CONF blink 5.0 Hz → 2.0 Hz; MED_CONF flagged for revision (exact parameters OPEN); optional `platform_risk_class` introduced (Section 8.2.1, PRC boundaries marked as discussion basis); standards alignment extended (WCAG 2.2 SC 2.3.1, ISO 9241-391:2016, ITU-R BT.1702-3); version raised to 2.1-rc1 (Candidate). Approved by CEO 2026-07-09.

---

## 16. Authors & Attribution

**LSEP v2.0** developed by **Nemanja Galić** at the **Experience Design Institute**, Zurich, Switzerland.

### 16.1 Institution

**Experience Design Institute**
Zurich, Switzerland
**Website:** https://www.experiencedesigninstitute.ch
**Contact:** nemanja@experiencedesigninstitute.ch

### 16.2 Acknowledgments

This specification was developed with reference to published standards and publicly available robotics safety research. Target platform compatibility listed in Section 1.2 is aspirational and does not imply endorsement by any manufacturer.

### 16.3 Citation

**APA:**
```
Experience Design Institute. (2026). LSEP v2.0: Luminae Signal Expression
Protocol formal technical specification. Experience Design Institute, Zurich, Switzerland.
```

### 16.4 License

Released under **Creative Commons Attribution 4.0 International (CC-BY-4.0)**

**Terms:**
- Free to share, copy, redistribute
- Free to remix, transform, build upon
- Must credit Experience Design Institute
- No warranties provided (as-is)

Full license: https://creativecommons.org/licenses/by/4.0/

### 16.5 Contact

Email: nemanja@experiencedesigninstitute.ch
Website: https://www.experiencedesigninstitute.ch
Issues: https://github.com/NemanjaGalic/LSEP/issues

---

## End of Document

**LSEP v2.0 Specification Document**
Version: 2.1-rc1 (Candidate)
Last Updated: July 9, 2026
Status: Technical Review — v2.1 Release Candidate

This specification is published for technical review. Contributions and feedback are welcome via GitHub Issues. Complete implementation guidance and testing protocols provided for LSEP-compliant systems.

Latest version: https://github.com/NemanjaGalic/LSEP/blob/main/LSEP_SPECIFICATION_v2.0.md
