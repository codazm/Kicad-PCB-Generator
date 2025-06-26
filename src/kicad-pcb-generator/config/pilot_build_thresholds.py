"""Pilot build empirical thresholds loader.

This lightweight helper reads the JSON file *pilot_build_thresholds.json* and
exposes a single ``get_thresholds(profile)`` function used by validators and
optimisers to pull real-world limits captured from manufactured reference
boards.

The design is intentionally minimal to avoid adding a heavy configuration
framework for what is essentially static, rarely-changing data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Path resolution is relative to this module file
_JSON_PATH = Path(__file__).with_suffix("").with_name("pilot_build_thresholds.json")


class PilotThresholdsError(RuntimeError):
    """Raised when threshold loading fails or profile not found."""


def _load_data() -> Dict[str, Any]:
    if not _JSON_PATH.exists():
        raise PilotThresholdsError(f"Thresholds file not found: {_JSON_PATH}")
    try:
        with _JSON_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise PilotThresholdsError(f"Invalid JSON syntax in {_JSON_PATH}: {exc}") from exc


_DATA_CACHE: Optional[Dict[str, Any]] = None


def get_thresholds(profile: str) -> Dict[str, Any]:
    """Return empirical threshold dictionary for *profile*.

    Parameters
    ----------
    profile
        Identifier such as ``pedal_v1`` or ``preamp_v1`` matching the keys in
        *pilot_build_thresholds.json*.
    """
    global _DATA_CACHE
    if _DATA_CACHE is None:
        _DATA_CACHE = _load_data()

    if profile not in _DATA_CACHE:
        raise PilotThresholdsError(f"Profile '{profile}' not found in thresholds file")
    return _DATA_CACHE[profile] 