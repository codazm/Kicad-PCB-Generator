"""Simple design library loader.

Loads design metadata from *designs/design_library.json* and provides helper
APIs for querying reference designs shipped with KiCad PCB Generator.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

_LIB_PATH = Path(__file__).resolve().parent.parent / "designs" / "design_library.json"

_PLACEHOLDER_TEMPLATE = """(kicad_sch (version 20211014) (generator kicad_pcb_generator)
  ;;; Placeholder schematic auto-generated on {date}
  (symbol (property \"Reference\" \"U1\" (id 0))
          (property \"Value\" \"{title}\" (id 1))
          (property \"Footprint\" \"Connector_Generic:Conn_01x01\" (id 2)))
)"""

_DEF_BASE_DIR = Path(__file__).resolve().parents[2] / "examples" / "circuits"


def _load() -> List[Dict[str, Any]]:
    if not _LIB_PATH.exists():
        return []
    with _LIB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


_DATA: List[Dict[str, Any]] = _load()


def list_designs() -> List[str]:
    """Return list of design IDs."""
    return [d["id"] for d in _DATA]


def get_design(design_id: str) -> Dict[str, Any]:
    """Return full metadata dictionary for *design_id* (raises KeyError if absent)."""
    for d in _DATA:
        if d["id"] == design_id:
            return d
    raise KeyError(f"Design '{design_id}' not found in library")


def filter_designs_by_tag(*tags: str) -> List[Dict[str, Any]]:  # noqa: D401
    """Return designs that include *all* specified *tags*.

    Parameters
    ----------
    *tags
        Arbitrary number of tag strings. Tags are compared case-insensitively.

    Returns
    -------
    list[dict[str, Any]]
        List of design dictionaries matching every given tag.
    """
    requested = {t.lower() for t in tags}
    if not requested:
        return _DATA.copy()
    return [d for d in _DATA if requested.issubset({tag.lower() for tag in d.get("tags", [])})]


def list_design_ids_by_tag(*tags: str) -> List[str]:  # noqa: D401
    """Convenience wrapper returning only IDs for :func:`filter_designs_by_tag`."""
    return [d["id"] for d in filter_designs_by_tag(*tags)]


def _placeholder_content(title: str) -> str:
    return _PLACEHOLDER_TEMPLATE.format(date=datetime.utcnow().isoformat(), title=title)


def create_placeholder_schematic(design_id: str, *, overwrite: bool = False, base_dir: Path | None = None) -> Path:
    """Create a minimal KiCad schematic placeholder for *design_id* if missing.

    The placeholder contains a single symbol with *Value* set to the design title so
    lightweight parsers can ingest it.  Returns the path to the schematic.
    """
    design = get_design(design_id)
    rel_path = Path(design["schematic"])
    path = (_DEF_BASE_DIR / rel_path.name) if not rel_path.is_absolute() and base_dir is None else (
        base_dir / rel_path.name if base_dir is not None else rel_path
    )

    if path.exists() and not overwrite:
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_placeholder_content(design["title"]), encoding="utf-8")
    return path


def ensure_placeholders(*design_ids: str, overwrite: bool = False) -> None:
    """Create placeholders for *design_ids* (or all designs if none supplied)."""
    targets = design_ids or list_designs()
    for did in targets:
        try:
            create_placeholder_schematic(did, overwrite=overwrite)
        except Exception as exc:
            logger.warning("Placeholder creation failed for %s: %s", did, exc) 