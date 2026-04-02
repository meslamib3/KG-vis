from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components


_COMPONENT_DIR = Path(__file__).resolve().parent / "graph_component_frontend"
_graph_component = components.declare_component(
    "dependency_graph_component",
    path=str(_COMPONENT_DIR),
)


def render_graph_component(
    option: dict[str, Any],
    *,
    height_px: int = 960,
    key: str | None = None,
    enable_events: bool = False,
) -> dict[str, Any] | None:
    return _graph_component(
        option=option,
        height_px=height_px,
        enable_events=enable_events,
        default=None,
        key=key,
    )
