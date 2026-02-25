#!/usr/bin/env python3
"""
LSEP v2.0 — SafetyDecisionEngine Reference Implementation

Physics-based state determination using Time-to-Collision (TTC).
Every human triggers identical safety logic. No demographic classification.

License: MIT
Author: Experience Design Institute, Zurich, Switzerland
URL: https://github.com/NemanjaGalic/LSEP
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


class LSEPState(Enum):
    """LSEP v2.0 Core States"""
    IDLE = "IDLE"
    AWARENESS = "AWARENESS"
    INTENT = "INTENT"
    CARE = "CARE"
    CRITICAL = "CRITICAL"
    THREAT = "THREAT"
    # Extended States
    MED_CONF = "MED_CONF"
    LOW_CONF = "LOW_CONF"
    INTEGRITY = "INTEGRITY"


@dataclass
class SensorReading:
    """Fused sensor data from LiDAR + Camera + Ultrasonic"""
    distance_m: float
    closing_velocity_ms: float
    confidence: float  # 0.0 to 1.0
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class SafetyDecisionEngine:
    """
    LSEP v2.0 — Physics-based state determination.
    
    Core principle: TTC (Time-to-Collision) determines state.
    No demographic inputs. No algorithmic life-value assessment.
    A child, an elderly person, and a factory worker all trigger
    the same physics-based calculation.
    """

    # TTC thresholds (seconds) — maps to state transitions
    TTC_THRESHOLDS = {
        LSEPState.THREAT:    0.5,   # Hysteresis bypass — immediate response
        LSEPState.CRITICAL:  1.5,   # Emergency response
        LSEPState.CARE:      3.0,   # Active safety measures
        LSEPState.INTENT:    5.0,   # Planning awareness
        LSEPState.AWARENESS: 10.0,  # Passive detection
    }

    # Proximity floor: human within this distance → minimum AWARENESS
    PROXIMITY_FLOOR_M = 1.5

    # Hysteresis bypass threshold
    HYSTERESIS_BYPASS_TTC_S = 0.5

    # Hysteresis cooldown (seconds)
    HYSTERESIS_COOLDOWN_S = 2.0

    # Confidence thresholds for extended states
    CONFIDENCE_MED = 0.7
    CONFIDENCE_LOW = 0.4

    def __init__(self):
        self._current_state = LSEPState.IDLE
        self._last_transition_time = 0.0
        self._state_history: list[tuple[float, LSEPState, float]] = []

    @property
    def current_state(self) -> LSEPState:
        return self._current_state

    def compute_ttc(self, distance_m: float, closing_velocity_ms: float) -> float:
        """
        TTC = distance / closing_velocity
        
        Returns float('inf') if velocity <= 0 (not approaching).
        """
        if closing_velocity_ms <= 0:
            return float('inf')
        return distance_m / closing_velocity_ms

    def determine_state(self, reading: SensorReading) -> LSEPState:
        """
        Main entry point. Determines LSEP state from sensor reading.
        
        Decision chain:
        1. Check sensor confidence → MED_CONF / LOW_CONF if degraded
        2. Compute TTC
        3. Apply proximity floor
        4. Map TTC to state with hysteresis
        5. THREAT bypass: TTC < 0.5s overrides everything
        """
        # Step 1: Confidence check
        if reading.confidence < self.CONFIDENCE_LOW:
            return self._transition(LSEPState.LOW_CONF, reading.timestamp)
        if reading.confidence < self.CONFIDENCE_MED:
            return self._transition(LSEPState.MED_CONF, reading.timestamp)

        # Step 2: Compute TTC
        ttc = self.compute_ttc(reading.distance_m, reading.closing_velocity_ms)

        # Step 3: THREAT bypass — no hysteresis at TTC < 0.5s
        if ttc < self.HYSTERESIS_BYPASS_TTC_S:
            return self._transition(LSEPState.THREAT, reading.timestamp)

        # Step 4: Proximity floor
        if reading.distance_m < self.PROXIMITY_FLOOR_M and ttc == float('inf'):
            target = LSEPState.AWARENESS
            return self._apply_hysteresis(target, reading.timestamp)

        # Step 5: TTC-based state mapping
        target = LSEPState.IDLE
        for state, threshold in self.TTC_THRESHOLDS.items():
            if ttc < threshold:
                target = state
                break

        return self._apply_hysteresis(target, reading.timestamp)

    def _apply_hysteresis(self, target: LSEPState, timestamp: float) -> LSEPState:
        """
        Hysteresis logic:
        - Escalation (higher severity) → immediate
        - De-escalation (lower severity) → requires sustained readings
        
        Prevents flickering from sensor noise.
        """
        severity_order = [
            LSEPState.IDLE,
            LSEPState.AWARENESS,
            LSEPState.INTENT,
            LSEPState.CARE,
            LSEPState.CRITICAL,
            LSEPState.THREAT,
        ]

        current_idx = (
            severity_order.index(self._current_state)
            if self._current_state in severity_order
            else 0
        )
        target_idx = (
            severity_order.index(target)
            if target in severity_order
            else 0
        )

        # Escalation: always immediate
        if target_idx > current_idx:
            return self._transition(target, timestamp)

        # De-escalation: require cooldown period
        time_in_state = timestamp - self._last_transition_time
        if time_in_state >= self.HYSTERESIS_COOLDOWN_S:
            return self._transition(target, timestamp)

        # Hold current state during cooldown
        return self._current_state

    def _transition(self, new_state: LSEPState, timestamp: float) -> LSEPState:
        """Execute state transition and record in history."""
        if new_state != self._current_state:
            ttc_at_transition = timestamp  # simplified for reference impl
            self._state_history.append(
                (timestamp, new_state, ttc_at_transition)
            )
            self._current_state = new_state
            self._last_transition_time = timestamp
        return self._current_state


# --- Demo / Quick Start ---

if __name__ == "__main__":
    engine = SafetyDecisionEngine()

    # Scenario: Human approaching robot
    scenarios = [
        SensorReading(distance_m=12.0, closing_velocity_ms=0.0, confidence=0.95, timestamp=0.0),
        SensorReading(distance_m=8.0,  closing_velocity_ms=1.2, confidence=0.95, timestamp=1.0),
        SensorReading(distance_m=4.5,  closing_velocity_ms=1.2, confidence=0.95, timestamp=2.0),
        SensorReading(distance_m=2.8,  closing_velocity_ms=1.2, confidence=0.95, timestamp=3.0),
        SensorReading(distance_m=1.2,  closing_velocity_ms=1.5, confidence=0.95, timestamp=4.0),
        SensorReading(distance_m=0.4,  closing_velocity_ms=2.0, confidence=0.95, timestamp=5.0),
    ]

    print("LSEP v2.0 — SafetyDecisionEngine Demo")
    print("=" * 55)
    print(f"{'Time':>5}  {'Dist':>6}  {'Vel':>5}  {'TTC':>7}  {'State':<12}")
    print("-" * 55)

    for s in scenarios:
        state = engine.determine_state(s)
        ttc = engine.compute_ttc(s.distance_m, s.closing_velocity_ms)
        ttc_str = f"{ttc:.2f}s" if ttc != float('inf') else "∞"
        print(f"{s.timestamp:>5.1f}  {s.distance_m:>5.1f}m  {s.closing_velocity_ms:>4.1f}  {ttc_str:>7}  {state.value:<12}")

    print("-" * 55)
    print("Physics-based. No demographics. Every human is equal.")
ng.distance_m < self.PROXIMITY_FLOOR_M and ttc == float('inf'):
            target = LSEPState.AWARENESS
            return self._apply_hysteresis(target, reading.timestamp)

        # Step 5: TTC-based state mapping
        target = LSEPState.IDLE
        for state, threshold in self.TTC_THRESHOLDS.items():
            if ttc < threshold:
                target = state
                break

        return self._apply_hysteresis(target, reading.timestamp)

    def _apply_hysteresis(self, target: LSEPState, timestamp: float) -> LSEPState:
        """
        Hysteresis logic:
        - Escalation (higher severity) → immediate
        - De-escalation (lower severity) → requires sustained readings
        
        Prevents flickering from sensor noise.
        """
        severity_order = [
            LSEPState.IDLE,
            LSEPState.AWARENESS,
            LSEPState.INTENT,
            LSEPState.CARE,
            LSEPState.CRITICAL,
            LSEPState.THREAT,
        ]

        current_idx = (
            severity_order.index(self._current_state)
            if self._current_state in severity_order
            else 0
        )
        target_idx = (
            severity_order.index(target)
            if target in severity_order
            else 0
        )

        # Escalation: always immediate
        if target_idx > current_idx:
            return self._transition(target, timestamp)

        # De-escalation: require cooldown period
        time_in_state = timestamp - self._last_transition_time
        if time_in_state >= self.HYSTERESIS_COOLDOWN_S:
            return self._transition(target, timestamp)

        # Hold current state during cooldown
        return self._current_state

    def _transition(self, new_state: LSEPState, timestamp: float) -> LSEPState:
        """Execute state transition and record in history."""
        if new_state != self._current_state:
            ttc_at_transition = timestamp  # simplified for reference impl
            self._state_history.append(
                (timestamp, new_state, ttc_at_transition)
            )
            self._current_state = new_state
            self._last_transition_time = timestamp
        return self._current_state


# --- Demo / Quick Start ---

if __name__ == "__main__":
    engine = SafetyDecisionEngine()

    # Scenario: Human approaching robot
    scenarios = [
        SensorReading(distance_m=12.0, closing_velocity_ms=0.0, confidence=0.95, timestamp=0.0),
        SensorReading(distance_m=8.0,  closing_velocity_ms=1.2, confidence=0.95, timestamp=1.0),
        SensorReading(distance_m=4.5,  closing_velocity_ms=1.2, confidence=0.95, timestamp=2.0),
        SensorReading(distance_m=2.8,  closing_velocity_ms=1.2, confidence=0.95, timestamp=3.0),
        SensorReading(distance_m=1.2,  closing_velocity_ms=1.5, confidence=0.95, timestamp=4.0),
        SensorReading(distance_m=0.4,  closing_velocity_ms=2.0, confidence=0.95, timestamp=5.0),
    ]

    print("LSEP v2.0 — SafetyDecisionEngine Demo")
    print("=" * 55)
    print(f"{'Time':>5}  {'Dist':>6}  {'Vel':>5}  {'TTC':>7}  {'State':<12}")
    print("-" * 55)

    for s in scenarios:
        state = engine.determine_state(s)
        ttc = engine.compute_ttc(s.distance_m, s.closing_velocity_ms)
        ttc_str = f"{ttc:.2f}s" if ttc != float('inf') else "∞"
        print(f"{s.timestamp:>5.1f}  {s.distance_m:>5.1f}m  {s.closing_velocity_ms:>4.1f}  {ttc_str:>7}  {state.value:<12}")

    print("-" * 55)
    print("Physics-based. No demographics. Every human is equal.")
