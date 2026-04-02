from __future__ import annotations

from collections import Counter
from typing import Any


DEPENDENCY_KIND_COLORS = {
    "Experiment": "#4e79a7",
    "Model": "#f28e2b",
    "Other": "#9aa0a6",
}

DEPENDENCY_COMPONENT_COLORS = [
    "#2f4b7c",
    "#665191",
    "#a05195",
    "#d45087",
    "#f95d6a",
    "#ff7c43",
    "#ffa600",
    "#5f0f40",
    "#0f4c5c",
    "#1d3557",
    "#457b9d",
    "#2a9d8f",
]

PROPERTY_FIELD_NAMES = ("connecting_properties", "properties", "property_names")


def _sort_key(value: Any) -> tuple[str, str]:
    return (str(type(value)), str(value))


def shorten_dependency_label(value: str, max_length: int = 42) -> str:
    trimmed = value.split("_upload", 1)[0]
    if len(trimmed) <= max_length:
        return trimmed
    return f"{trimmed[: max_length - 3]}..."


def infer_dependency_kind(node_id: str, explicit_kind: str | None = None) -> str:
    normalized = (explicit_kind or "").strip().lower()
    if normalized in {"experiment", "exp"}:
        return "Experiment"
    if normalized in {"model", "mod", "simulation"}:
        return "Model"
    if "-Exp-" in node_id:
        return "Experiment"
    if "-Mod-" in node_id:
        return "Model"
    return "Other"


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = [value]

    normalized: list[str] = []
    for item in raw_items:
        text = str(item).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _extract_connecting_properties(edge: dict[str, Any]) -> list[str]:
    for field_name in PROPERTY_FIELD_NAMES:
        if field_name in edge:
            return _normalize_string_list(edge.get(field_name))
    return []


def _build_node_search_blob(node: dict[str, Any]) -> str:
    parts = [
        node["id"],
        node["label"],
        node.get("method_level") or "",
        node.get("method_kind") or "",
        node.get("component_id") or "",
    ]
    return " ".join(parts).lower()


def normalize_dependency_graph(data: dict[str, Any]) -> dict[str, Any]:
    raw_nodes = data.get("nodes", [])
    raw_edges = data.get("edges") or data.get("links") or []

    nodes_by_id: dict[str, dict[str, Any]] = {}
    for raw_node in raw_nodes:
        node_id = raw_node.get("id") or raw_node.get("name")
        if not node_id:
            continue

        label = str(raw_node.get("label") or node_id)
        node = {
            "id": str(node_id),
            "label": label,
            "short_label": shorten_dependency_label(label),
            "component_id": str(raw_node.get("component_id", "Unknown")),
            "method_kind": infer_dependency_kind(str(node_id), raw_node.get("method_kind")),
            "method_level": str(raw_node["method_level"]).strip() if raw_node.get("method_level") else None,
            "raw": raw_node,
        }
        node["search_blob"] = _build_node_search_blob(node)
        nodes_by_id[node["id"]] = node

    edges: list[dict[str, Any]] = []
    for index, raw_edge in enumerate(raw_edges):
        source = raw_edge.get("from") or raw_edge.get("source")
        target = raw_edge.get("to") or raw_edge.get("target")
        if not source or not target:
            continue

        source_id = str(source)
        target_id = str(target)

        for missing_id in (source_id, target_id):
            if missing_id not in nodes_by_id:
                placeholder = {
                    "id": missing_id,
                    "label": missing_id,
                    "short_label": shorten_dependency_label(missing_id),
                    "component_id": "Unknown",
                    "method_kind": infer_dependency_kind(missing_id),
                    "method_level": None,
                    "raw": {"id": missing_id},
                }
                placeholder["search_blob"] = _build_node_search_blob(placeholder)
                nodes_by_id[missing_id] = placeholder

        relation = str(raw_edge.get("relation") or raw_edge.get("label") or "related_to")
        connecting_properties = _extract_connecting_properties(raw_edge)
        edges.append(
            {
                "edge_id": f"edge_{index}",
                "source": source_id,
                "target": target_id,
                "relation": relation,
                "connecting_properties": connecting_properties,
                "search_blob": " ".join(connecting_properties).lower(),
                "raw": raw_edge,
            }
        )

    component_ids = sorted({node["component_id"] for node in nodes_by_id.values()}, key=_sort_key)
    method_levels = sorted(
        {node["method_level"] for node in nodes_by_id.values() if node.get("method_level")},
        key=_sort_key,
    )

    return {
        "nodes_by_id": nodes_by_id,
        "edges": edges,
        "component_ids": component_ids,
        "method_levels": method_levels,
        "timeline": data.get("timeline", []),
        "has_property_metadata": any(edge["connecting_properties"] for edge in edges),
        "has_method_levels": bool(method_levels),
    }


def build_dependency_categories() -> list[dict[str, Any]]:
    return [
        {"name": name, "itemStyle": {"color": color}}
        for name, color in DEPENDENCY_KIND_COLORS.items()
    ]


def _matches_search(node: dict[str, Any], query: str) -> bool:
    return query in node["search_blob"]


def _edge_matches_search(edge: dict[str, Any], query: str) -> bool:
    return bool(edge["search_blob"]) and query in edge["search_blob"]


def _edge_label(edge: dict[str, Any], include_properties: bool, focus_node: str | None) -> str:
    if include_properties and focus_node and edge["connecting_properties"]:
        preview = edge["connecting_properties"][:3]
        suffix = ""
        if len(edge["connecting_properties"]) > len(preview):
            suffix = f" +{len(edge['connecting_properties']) - len(preview)}"
        return ", ".join(preview) + suffix
    return edge["relation"]


def _build_node_details(
    model: dict[str, Any],
    node_id: str | None,
    eligible_edges: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not node_id or node_id not in model["nodes_by_id"]:
        return None

    node = model["nodes_by_id"][node_id]
    incoming = []
    outgoing = []

    for edge in eligible_edges:
        if edge["target"] == node_id:
            source_node = model["nodes_by_id"][edge["source"]]
            incoming.append(
                {
                    "method_id": source_node["id"],
                    "method_label": source_node["label"],
                    "relation": edge["relation"],
                    "connecting_properties": edge["connecting_properties"],
                }
            )
        if edge["source"] == node_id:
            target_node = model["nodes_by_id"][edge["target"]]
            outgoing.append(
                {
                    "method_id": target_node["id"],
                    "method_label": target_node["label"],
                    "relation": edge["relation"],
                    "connecting_properties": edge["connecting_properties"],
                }
            )

    incoming.sort(key=lambda item: item["method_label"].lower())
    outgoing.sort(key=lambda item: item["method_label"].lower())

    return {
        "node": node,
        "incoming": incoming,
        "outgoing": outgoing,
        "neighbor_count": len({item["method_id"] for item in incoming + outgoing}),
    }


def build_dependency_view(
    model: dict[str, Any],
    selected_components: list[str] | None = None,
    selected_method_levels: list[str] | None = None,
    search_text: str = "",
    focus_node: str | None = None,
    selected_node: str | None = None,
    include_properties: bool = False,
) -> dict[str, Any]:
    component_filter = set(selected_components or model["component_ids"])
    method_level_filter = set(selected_method_levels or model["method_levels"])

    eligible_nodes: dict[str, dict[str, Any]] = {}
    for node_id, node in model["nodes_by_id"].items():
        if node["component_id"] not in component_filter:
            continue
        if model["has_method_levels"] and node.get("method_level") not in method_level_filter:
            continue
        eligible_nodes[node_id] = node

    eligible_edges = [
        edge
        for edge in model["edges"]
        if edge["source"] in eligible_nodes and edge["target"] in eligible_nodes
    ]

    if focus_node not in eligible_nodes:
        focus_node = None
    if selected_node not in eligible_nodes:
        selected_node = None

    if focus_node:
        visible_node_ids = {focus_node}
        visible_edges = []
        for edge in eligible_edges:
            if focus_node in {edge["source"], edge["target"]}:
                visible_edges.append(edge)
                visible_node_ids.add(edge["source"])
                visible_node_ids.add(edge["target"])
    else:
        visible_node_ids = set(eligible_nodes)
        visible_edges = eligible_edges

    query = search_text.strip().lower()
    if query:
        matched_node_ids = {
            node_id for node_id in visible_node_ids if _matches_search(eligible_nodes[node_id], query)
        }
        matched_edge_ids = set()
        for edge in visible_edges:
            if _edge_matches_search(edge, query):
                matched_edge_ids.add(edge["edge_id"])
                matched_node_ids.add(edge["source"])
                matched_node_ids.add(edge["target"])
        for edge in visible_edges:
            if edge["source"] in matched_node_ids or edge["target"] in matched_node_ids:
                matched_edge_ids.add(edge["edge_id"])
    else:
        matched_node_ids = set(visible_node_ids)
        matched_edge_ids = {edge["edge_id"] for edge in visible_edges}

    degree_counter: Counter[str] = Counter()
    for edge in visible_edges:
        degree_counter[edge["source"]] += 1
        degree_counter[edge["target"]] += 1

    component_colors = {
        component_id: DEPENDENCY_COMPONENT_COLORS[index % len(DEPENDENCY_COMPONENT_COLORS)]
        for index, component_id in enumerate(model["component_ids"])
    }

    nodes = []
    for node_id in sorted(visible_node_ids):
        node = eligible_nodes[node_id]
        degree = degree_counter[node_id]
        is_focus = node_id == focus_node
        is_selected = node_id == selected_node
        is_match = node_id in matched_node_ids

        symbol_size = 20 + min(degree, 6) * 4
        if is_selected:
            symbol_size += 4
        if is_focus:
            symbol_size += 8

        border_color = component_colors.get(node["component_id"], "#444444")
        if is_focus:
            border_color = "#f8fafc"
        elif is_selected:
            border_color = "#fde68a"

        nodes.append(
            {
                "name": node_id,
                "symbolSize": symbol_size,
                "category": node["method_kind"],
                "itemStyle": {
                    "color": DEPENDENCY_KIND_COLORS[node["method_kind"]],
                    "borderColor": border_color,
                    "borderWidth": 4 if is_focus else 3 if is_selected else 2,
                    "opacity": 1.0 if is_match else 0.16,
                    "shadowBlur": 20 if is_focus else 12 if is_selected else 0,
                    "shadowColor": DEPENDENCY_KIND_COLORS[node["method_kind"]],
                },
                "label": {
                    "show": True,
                    "formatter": node["short_label"],
                    "color": "#f8fafc" if is_match else "#64748b",
                },
                "value": {
                    "label": node["label"],
                    "component_id": node["component_id"],
                    "method_level": node.get("method_level"),
                    "method_kind": node["method_kind"],
                },
            }
        )

    links = []
    for edge in visible_edges:
        is_focus_edge = focus_node and focus_node in {edge["source"], edge["target"]}
        is_match = edge["edge_id"] in matched_edge_ids
        links.append(
            {
                "source": edge["source"],
                "target": edge["target"],
                "value": _edge_label(edge, include_properties, focus_node),
                "lineStyle": {
                    "type": "dashed" if edge["relation"] == "additional_input" else "solid",
                    "opacity": 0.95 if is_focus_edge and is_match else 0.78 if is_match else 0.08,
                    "width": 3.5 if is_focus_edge else 2.2 if is_match else 1.0,
                    "curveness": 0.18,
                },
                "label": {"show": True},
                "emphasis": {"disabled": False},
            }
        )

    summary = {
        "node_count": len(visible_node_ids),
        "edge_count": len(visible_edges),
        "component_count": len({eligible_nodes[node_id]["component_id"] for node_id in visible_node_ids}),
        "timeline_points": len(model["timeline"]),
    }

    return {
        "nodes": nodes,
        "links": links,
        "categories": build_dependency_categories(),
        "summary": summary,
        "focus_node": focus_node,
        "selected_node": selected_node,
        "details": _build_node_details(model, selected_node or focus_node, eligible_edges),
        "match_count": len(matched_node_ids),
    }


def create_dependency_echarts_option(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    subtitle: str,
    show_edge_labels: bool,
) -> dict[str, Any]:
    return {
        "title": {
            "text": "Dependency Graph Explorer",
            "subtext": subtitle,
            "top": "bottom",
            "left": "right",
        },
        "legend": [
            {
                "data": [category["name"] for category in categories],
                "orient": "vertical",
                "left": "left",
                "top": "middle",
            }
        ],
        "animationDurationUpdate": 1200,
        "animationEasingUpdate": "quinticInOut",
        "series": [
            {
                "name": "Dependency Graph Explorer",
                "type": "graph",
                "layout": "force",
                "data": nodes,
                "links": links,
                "categories": categories,
                "roam": True,
                "draggable": True,
                "focusNodeAdjacency": True,
                "label": {
                    "position": "right",
                    "hideOverlap": True,
                    "fontSize": 10,
                },
                "lineStyle": {"color": "source"},
                "edgeSymbol": ["none", "arrow"],
                "edgeSymbolSize": [4, 10],
                "edgeLabel": {
                    "show": show_edge_labels,
                    "fontSize": 9,
                    "formatter": "{c}",
                },
                "force": {
                    "repulsion": 380,
                    "gravity": 0.05,
                    "edgeLength": [90, 180],
                },
                "emphasis": {"focus": "adjacency", "lineStyle": {"width": 4}},
                "tooltip": {"show": True},
            }
        ],
    }
