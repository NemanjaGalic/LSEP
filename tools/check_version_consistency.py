#!/usr/bin/env python3
"""Check that current protocol-version labels agree across repository artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(text: str, pattern: str, label: str) -> None:
    if not re.search(pattern, text, flags=re.MULTILINE):
        raise SystemExit(f"version check failed: {label}")


def main() -> None:
    catalog_path = ROOT / "lsep_signals_v2.0.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    expected_version = catalog.get("version")
    if not expected_version:
        raise SystemExit("version check failed: catalog version is missing")
        
    badge_ver = expected_version.replace("-", "--").replace(".", r"\.")
    rgx_ver = expected_version.replace(".", r"\.")

    require(
        read("README.md"),
        rf"Version-v{badge_ver}-blue\.svg",
        "README badge",
    )
    require(read("README.md"), rf'"version": "{rgx_ver}"', "README JSON example")
    require(
        read("LSEP_SPECIFICATION_v2.0.md"),
        rf"\*\*Version:\*\* {rgx_ver} \(Candidate\)",
        "specification version",
    )
    require(
        read("ros2/src/lsep_ros2/lsep_ros2/engine.py"),
        rf"PROTOCOL_VERSION = ['\"]{rgx_ver}['\"]",
        "ROS 2 engine version",
    )
    require(
        read("ros2/src/lsep_msgs/msg/Signal.msg"),
        rf'^string version\s+# "{rgx_ver}"',
        "ROS message version",
    )

    stale = []
    for relative_path in (
        "ros2/src/lsep_ros2/lsep_ros2/engine.py",
        "ros2/src/lsep_msgs/msg/Signal.msg",
        "ros2/src/README.md",
        "ros2/src/lsep_ros2/README.md",
        "README.md",
        "LSEP_SPECIFICATION_v2.0.md",
    ):
        if "v2.1-draft" in read(relative_path):
            stale.append(relative_path)
    if stale:
        raise SystemExit("version check failed: stale v2.1-draft labels in " + ", ".join(stale))

    print(f"version consistency: PASS ({expected_version})")


if __name__ == "__main__":
    main()
