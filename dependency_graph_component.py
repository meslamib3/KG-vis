from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components


_COMPONENT_DIR = Path(__file__).resolve().parent / "dependency_graph_frontend" / "dist"
_dependency_graph_component = components.declare_component(
    "dependency_graph_component_v2",
    path=str(_COMPONENT_DIR),
)


def render_dependency_graph_component(
    *,
    graph: dict[str, Any],
    height_px: int = 960,
    show_edge_labels: bool = True,
    key: str | None = None,
) -> dict[str, Any] | None:
    return _dependency_graph_component(
        graph=graph,
        height_px=height_px,
        show_edge_labels=show_edge_labels,
        default=None,
        key=key,
    )
