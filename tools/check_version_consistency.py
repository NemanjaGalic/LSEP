#!/usr/bin/env python3
"""Check that current protocol-version labels agree across repository artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "2.1-rc1"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(text: str, pattern: str, label: str) -> None:
    if not re.search(pattern, text, flags=re.MULTILINE):
        raise SystemExit(f"version check failed: {label}")


def main() -> None:
    catalog_path = ROOT / "lsep_signals_v2.0.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("version") != EXPECTED_VERSION:
        raise SystemExit(
            f"version check failed: catalog version is {catalog.get('version')!r}"
        )

    require(
        read("README.md"),
        r"Version-v2\.1--rc1-blue\.svg",
        "README badge",
    )
    require(read("README.md"), r'"version": "2\.1-rc1"', "README JSON example")
    require(
        read("LSEP_SPECIFICATION_v2.0.md"),
        r"\*\*Version:\*\* 2\.1-rc1 \(Candidate\)",
        "specification version",
    )
    require(
        read("ros2/src/lsep_ros2/lsep_ros2/engine.py"),
        r"PROTOCOL_VERSION = ['\"]2\.1-rc1['\"]",
        "ROS 2 engine version",
    )
    require(
        read("ros2/src/lsep_msgs/msg/Signal.msg"),
        r'^string version\s+# "2\.1-rc1"',
        "ROS message version",
    )

    stale = []
    for relative_path in (
        "ros2/src/lsep_ros2/lsep_ros2/engine.py",
        "ros2/src/lsep_msgs/msg/Signal.msg",
        "ros2/src/README.md",
        "ros2/src/lsep_ros2/README.md",
    ):
        if "v2.1-draft" in read(relative_path):
            stale.append(relative_path)
    if stale:
        raise SystemExit("version check failed: stale v2.1-draft labels in " + ", ".join(stale))

    print(f"version consistency: PASS ({EXPECTED_VERSION})")


if __name__ == "__main__":
    main()
