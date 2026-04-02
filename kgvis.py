import json
from pathlib import Path

import chardet
import streamlit as st

from dependency_explorer import (
    build_dependency_view,
    create_dependency_echarts_option,
    normalize_dependency_graph,
)
from graph_component import render_graph_component


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DEPENDENCY_GRAPH_PATH = BASE_DIR / "dependency-graph-lab-35.json"
ENRICHED_DEPENDENCY_GRAPH_PATH = BASE_DIR / "dependency-graph-enriched-sample.json"


DEFAULT_JSON_LD = {
    "@context": {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "dcterms": "http://purl.org/dc/terms/",
        "emmo": "http://emmo.info/emmo#",
        "ex": "http://example.com/",
        "is_manufacturing_input": {"@id": "emmo:EMMO_e1097637", "@type": "@id"},
        "has_manufacturing_output": {"@id": "emmo:EMMO_e1245987", "@type": "@id"},
        "is_measurement_input": {"@id": "emmo:EMMO_m5677989", "@type": "@id"},
        "has_measurement_output": {"@id": "emmo:EMMO_m87987545", "@type": "@id"},
        "is_model_input": {"@id": "emmo:EMMO_m5677980", "@type": "@id"},
        "has_model_output": {"@id": "emmo:EMMO_m87987546", "@type": "@id"},
        "has_property": {"@id": "emmo:EMMO_p5778r78", "@type": "@id"},
        "has_parameter": {"@id": "emmo:EMMO_p46903ar7", "@type": "@id"},
        "Material": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
        "Manufacturing": "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b",
        "Measurement": "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb",
        "Property": "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba",
        "Parameter": "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a",
        "Simulation": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
        "Metadata": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92",
    },
    "@graph": [
        {
            "@id": "ex:Material",
            "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
            "skos:prefLabel": "Material",
        },
        {
            "@id": "ex:Manufacturing",
            "@type": "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b",
            "skos:prefLabel": "Manufacturing",
        },
        {
            "@id": "ex:Measurement",
            "@type": "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb",
            "skos:prefLabel": "Measurement",
        },
        {
            "@id": "ex:Property",
            "@type": "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba",
            "skos:prefLabel": "Property",
        },
        {
            "@id": "ex:Parameter",
            "@type": "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a",
            "skos:prefLabel": "Parameter",
        },
        {
            "@id": "ex:Simulation",
            "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
            "skos:prefLabel": "Simulation",
        },
        {
            "@id": "ex:Metadata",
            "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92",
            "skos:prefLabel": "Metadata",
        },
    ],
}


JSON_LD_NODE_TYPES = {
    "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94": "Matter",
    "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b": "Manufacturing",
    "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb": "Measurement",
    "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba": "Property",
    "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a": "Parameter",
    "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93": "Simulation",
    "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92": "Metadata",
}


JSON_LD_COLORS = {
    "Matter": "#5470c6",
    "Manufacturing": "#ee6666",
    "Measurement": "#fac858",
    "Property": "#73c0de",
    "Parameter": "#91cc75",
    "Simulation": "#a5a5a5",
    "Metadata": "#9b59b6",
    "Instance/Individual": "#3ba272",
    "Value/Literal": "#fc8452",
    "Unit": "#d14a61",
    "Unknown": "#cccccc",
}


RELATIONSHIP_KEYS = {
    "emmo:EMMO_e1097637": "is_manufacturing_input",
    "emmo:EMMO_e1245987": "has_manufacturing_output",
    "emmo:EMMO_m5677989": "is_measurement_input",
    "emmo:EMMO_m87987545": "has_measurement_output",
    "emmo:EMMO_m5677980": "is_model_input",
    "emmo:EMMO_m87987546": "has_model_output",
    "emmo:EMMO_p5778r78": "has_property",
    "emmo:EMMO_p46903ar7": "has_parameter",
    "skos:prefLabel": "skos:prefLabel",
}


def decode_json_bytes(raw_data):
    encoding = chardet.detect(raw_data).get("encoding") or "utf-8"
    return json.loads(raw_data.decode(encoding))


def read_json_file(uploaded_file):
    return decode_json_bytes(uploaded_file.read())


def read_json_path(path):
    return decode_json_bytes(path.read_bytes())


def detect_graph_format(data):
    if isinstance(data, dict):
        if "@graph" in data:
            return "json-ld"
        if "nodes" in data and ("edges" in data or "links" in data):
            return "dependency-graph"
    return "unknown"


def build_json_ld_categories():
    category_names = [
        "Matter",
        "Manufacturing",
        "Measurement",
        "Property",
        "Parameter",
        "Simulation",
        "Metadata",
        "Instance/Individual",
        "Value/Literal",
        "Unit",
    ]
    return [{"name": name, "itemStyle": {"color": JSON_LD_COLORS[name]}} for name in category_names]


def ensure_reference_node(nodes, node_ids, target_id, color):
    if target_id in node_ids:
        return
    nodes.append(
        {
            "name": target_id,
            "symbolSize": 10,
            "itemStyle": {"color": color},
            "category": "Instance/Individual",
            "label": {"show": True, "formatter": target_id},
        }
    )
    node_ids.add(target_id)


def extract_json_ld_graph_data(data, hide_units_and_literals=False):
    nodes = []
    links = []
    node_ids = set()

    for type_name in JSON_LD_NODE_TYPES.values():
        nodes.append(
            {
                "name": type_name,
                "symbolSize": 15,
                "itemStyle": {"color": JSON_LD_COLORS[type_name]},
                "category": type_name,
            }
        )
        node_ids.add(type_name)

    for item in data.get("@graph", []):
        if "@id" not in item or "@type" not in item:
            continue

        node_id = item["@id"]
        type_candidates = item["@type"] if isinstance(item["@type"], list) else [item["@type"]]
        node_type = next(
            (JSON_LD_NODE_TYPES[type_id] for type_id in type_candidates if type_id in JSON_LD_NODE_TYPES),
            "Instance/Individual",
        )
        node_label = item.get("skos:prefLabel") or item.get("rdfs:label") or node_id

        if node_id not in node_ids:
            nodes.append(
                {
                    "name": node_id,
                    "symbolSize": 10,
                    "itemStyle": {"color": JSON_LD_COLORS["Instance/Individual"]},
                    "category": "Instance/Individual",
                    "label": {"show": True, "formatter": node_label},
                }
            )
            node_ids.add(node_id)

        if node_type in JSON_LD_NODE_TYPES.values():
            links.append({"source": node_id, "target": node_type, "value": "rdf:type"})

        for key, value in item.items():
            if key in {"@id", "@type"}:
                continue
            relation_name = RELATIONSHIP_KEYS.get(key, key)

            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict) and "@id" in entry:
                        ensure_reference_node(nodes, node_ids, entry["@id"], JSON_LD_COLORS["Instance/Individual"])
                        links.append({"source": node_id, "target": entry["@id"], "value": relation_name})
                    elif not hide_units_and_literals:
                        literal_value = f"{node_id}_{key}_{entry}"
                        if literal_value not in node_ids:
                            nodes.append(
                                {
                                    "name": literal_value,
                                    "symbolSize": 10,
                                    "itemStyle": {"color": JSON_LD_COLORS["Value/Literal"]},
                                    "category": "Value/Literal",
                                    "label": {"show": True, "formatter": str(entry)},
                                }
                            )
                            node_ids.add(literal_value)
                        links.append({"source": node_id, "target": literal_value, "value": relation_name})
            elif isinstance(value, dict) and "@id" in value:
                ensure_reference_node(nodes, node_ids, value["@id"], JSON_LD_COLORS["Instance/Individual"])
                links.append({"source": node_id, "target": value["@id"], "value": relation_name})
            elif not hide_units_and_literals:
                literal_value = f"{node_id}_{key}_{value}"
                if literal_value not in node_ids:
                    nodes.append(
                        {
                            "name": literal_value,
                            "symbolSize": 10,
                            "itemStyle": {"color": JSON_LD_COLORS["Value/Literal"]},
                            "category": "Value/Literal",
                            "label": {"show": True, "formatter": str(value)},
                        }
                    )
                    node_ids.add(literal_value)
                links.append({"source": node_id, "target": literal_value, "value": relation_name})

    summary = {
        "node_count": len(nodes),
        "edge_count": len(links),
        "component_count": len(data.get("@graph", [])),
    }
    return nodes, links, build_json_ld_categories(), summary, "JSON-LD Knowledge Graph"


def create_json_ld_option(nodes, links, categories, title, subtitle, show_edge_labels):
    return {
        "title": {
            "text": title,
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
        "animationDurationUpdate": 1500,
        "animationEasingUpdate": "quinticInOut",
        "series": [
            {
                "name": title,
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
                    "formatter": "{b}",
                    "hideOverlap": True,
                    "fontSize": 10,
                },
                "lineStyle": {"color": "source", "curveness": 0.2, "opacity": 0.7},
                "edgeSymbol": ["none", "arrow"],
                "edgeSymbolSize": [4, 10],
                "edgeLabel": {
                    "show": show_edge_labels,
                    "fontSize": 8,
                    "formatter": "{c}",
                },
                "force": {
                    "repulsion": 340,
                    "gravity": 0.05,
                    "edgeLength": [80, 160],
                },
                "emphasis": {"focus": "adjacency", "lineStyle": {"width": 4}},
                "tooltip": {"show": True},
            }
        ],
    }


def load_source_data(source_choice, uploaded_file):
    if source_choice == "Local dependency graph":
        return read_json_path(DEFAULT_DEPENDENCY_GRAPH_PATH)
    if source_choice == "Enriched dependency sample":
        return read_json_path(ENRICHED_DEPENDENCY_GRAPH_PATH)
    if source_choice == "Default JSON-LD example":
        return DEFAULT_JSON_LD
    if source_choice == "Upload JSON file":
        if uploaded_file is None:
            return None
        return read_json_file(uploaded_file)
    return DEFAULT_JSON_LD


def sync_editor(source_choice, source_data, uploaded_file):
    if source_data is None:
        return

    signature = source_choice
    if uploaded_file is not None:
        signature = f"{source_choice}:{uploaded_file.name}"

    if st.session_state.get("editor_signature") != signature:
        st.session_state["editor_text"] = json.dumps(source_data, indent=2)
        st.session_state["editor_signature"] = signature


def get_query_param_list(name):
    params = st.query_params
    getter = getattr(params, "get_all", None)
    if callable(getter):
        return [str(value) for value in getter(name) if str(value)]
    value = params.get(name)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def get_query_param_value(name, default=""):
    values = get_query_param_list(name)
    return values[0] if values else default


def get_query_param_bool(name, default=False):
    raw_value = get_query_param_value(name, "true" if default else "false").strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def sync_dependency_query_params(focus_node, search_text, include_properties, method_levels):
    try:
        params = st.query_params
        if focus_node:
            params["focus"] = focus_node
        elif "focus" in params:
            del params["focus"]

        if search_text.strip():
            params["search"] = search_text.strip()
        elif "search" in params:
            del params["search"]

        params["include_properties"] = "true" if include_properties else "false"

        if method_levels:
            params["method_level"] = list(method_levels)
        elif "method_level" in params:
            del params["method_level"]
    except Exception:
        return


def show_summary(summary):
    metrics = [
        ("Nodes", summary.get("node_count", 0)),
        ("Edges", summary.get("edge_count", 0)),
        ("Components", summary.get("component_count", 0)),
    ]
    if "timeline_points" in summary:
        metrics.append(("Timeline Rows", summary["timeline_points"]))

    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def render_dependency_details(details):
    st.subheader("Method Details")
    if not details:
        st.info("Single-click a node to inspect it. Double-click a node to focus on its connected neighborhood.")
        return

    node = details["node"]
    st.markdown(f"**{node['label']}**")
    st.caption(node["id"])

    metadata_lines = [
        f"Kind: {node['method_kind']}",
        f"Component: {node['component_id']}",
    ]
    if node.get("method_level"):
        metadata_lines.append(f"Level: {node['method_level']}")
    st.write(" | ".join(metadata_lines))
    st.write(f"Connected methods: {details['neighbor_count']}")

    for title, entries in (("Incoming methods", details["incoming"]), ("Outgoing methods", details["outgoing"])):
        st.markdown(f"**{title}**")
        if not entries:
            st.caption("None")
            continue
        for entry in entries:
            st.write(f"- {entry['method_label']} ({entry['relation']})")
            if entry["connecting_properties"]:
                st.caption("Properties: " + ", ".join(entry["connecting_properties"]))


def initialize_dependency_state(model):
    if "dep_search_text" not in st.session_state:
        st.session_state["dep_search_text"] = get_query_param_value("search", "")
    if "dep_include_properties" not in st.session_state:
        st.session_state["dep_include_properties"] = get_query_param_bool("include_properties", False)
    if "dep_show_edge_labels" not in st.session_state:
        st.session_state["dep_show_edge_labels"] = True
    if "dep_focus_node" not in st.session_state:
        st.session_state["dep_focus_node"] = get_query_param_value("focus", "") or None
    if "dep_selected_node" not in st.session_state:
        st.session_state["dep_selected_node"] = st.session_state.get("dep_focus_node")
    if "dep_selected_components" not in st.session_state:
        st.session_state["dep_selected_components"] = list(model["component_ids"])
    if "dep_selected_method_levels" not in st.session_state:
        requested_levels = [value for value in get_query_param_list("method_level") if value in model["method_levels"]]
        st.session_state["dep_selected_method_levels"] = requested_levels or list(model["method_levels"])

    valid_components = set(model["component_ids"])
    st.session_state["dep_selected_components"] = [
        value for value in st.session_state["dep_selected_components"] if value in valid_components
    ] or list(model["component_ids"])

    valid_levels = set(model["method_levels"])
    if model["has_method_levels"]:
        selected_levels = [
            value for value in st.session_state["dep_selected_method_levels"] if value in valid_levels
        ]
        st.session_state["dep_selected_method_levels"] = selected_levels or list(model["method_levels"])
    else:
        st.session_state["dep_selected_method_levels"] = []
        st.session_state["dep_include_properties"] = False

    valid_node_ids = set(model["nodes_by_id"])
    if st.session_state.get("dep_focus_node") not in valid_node_ids:
        st.session_state["dep_focus_node"] = None
    if st.session_state.get("dep_selected_node") not in valid_node_ids:
        st.session_state["dep_selected_node"] = st.session_state.get("dep_focus_node")


def handle_dependency_event(chart_event, model):
    if not chart_event:
        st.session_state.pop("dep_last_event_signature", None)
        return False

    signature = json.dumps(chart_event, sort_keys=True)
    if st.session_state.get("dep_last_event_signature") == signature:
        return False

    st.session_state["dep_last_event_signature"] = signature
    node_id = chart_event.get("nodeId")
    if node_id not in model["nodes_by_id"]:
        return False

    st.session_state["dep_selected_node"] = node_id
    if chart_event.get("eventType") == "dblclick":
        st.session_state["dep_focus_node"] = node_id
    return True


def render_dependency_explorer(edited_data):
    model = normalize_dependency_graph(edited_data)
    initialize_dependency_state(model)

    st.sidebar.header("Dependency Explorer")
    st.sidebar.caption("Single-click a node to inspect it. Double-click a node to focus its connected neighborhood.")

    properties_available = model["has_property_metadata"]
    method_levels_available = model["has_method_levels"]

    include_properties = st.sidebar.checkbox(
        "Include connecting properties",
        value=st.session_state["dep_include_properties"],
        key="dep_include_properties",
        disabled=not properties_available,
    )
    if not properties_available:
        st.sidebar.caption("Legacy file detected: no `connecting_properties` metadata is available yet.")

    if method_levels_available:
        selected_method_levels = st.sidebar.multiselect(
            "Filter by method level",
            model["method_levels"],
            default=st.session_state["dep_selected_method_levels"],
            key="dep_selected_method_levels",
        )
    else:
        st.sidebar.multiselect(
            "Filter by method level",
            ["Unavailable in this file"],
            default=[],
            disabled=True,
        )
        st.sidebar.caption("Legacy file detected: no `method_level` metadata is available yet.")
        selected_method_levels = []

    selected_components = st.sidebar.multiselect(
        "Filter by component_id",
        model["component_ids"],
        default=st.session_state["dep_selected_components"],
        key="dep_selected_components",
    )
    search_text = st.sidebar.text_input(
        "Search methods or properties",
        value=st.session_state["dep_search_text"],
        key="dep_search_text",
        placeholder="Type a method or property name",
    )
    show_edge_labels = st.sidebar.checkbox(
        "Show edge labels",
        value=st.session_state["dep_show_edge_labels"],
        key="dep_show_edge_labels",
    )

    if st.sidebar.button("Reset focus"):
        st.session_state["dep_focus_node"] = None
        st.session_state["dep_selected_node"] = None
        st.rerun()

    sync_dependency_query_params(
        st.session_state.get("dep_focus_node"),
        search_text,
        include_properties,
        selected_method_levels,
    )

    view = build_dependency_view(
        model,
        selected_components=selected_components,
        selected_method_levels=selected_method_levels,
        search_text=search_text,
        focus_node=st.session_state.get("dep_focus_node"),
        selected_node=st.session_state.get("dep_selected_node"),
        include_properties=include_properties,
    )

    st.caption("Detected format: `dependency-graph`")
    show_summary(view["summary"])

    subtitle_parts = ["Force layout"]
    if view["focus_node"]:
        subtitle_parts.append(f"focused on {view['focus_node']}")
    if search_text.strip():
        subtitle_parts.append(f"{view['match_count']} highlighted match(es)")

    option = create_dependency_echarts_option(
        view["nodes"],
        view["links"],
        view["categories"],
        subtitle=" | ".join(subtitle_parts),
        show_edge_labels=show_edge_labels,
    )

    graph_col, details_col = st.columns([2.7, 1.3], gap="large")
    with graph_col:
        chart_event = render_graph_component(
            option,
            height_px=960,
            enable_events=True,
            key="dependency_graph_chart",
        )
        if handle_dependency_event(chart_event, model):
            sync_dependency_query_params(
                st.session_state.get("dep_focus_node"),
                st.session_state.get("dep_search_text", ""),
                st.session_state.get("dep_include_properties", False),
                st.session_state.get("dep_selected_method_levels", []),
            )
            st.rerun()

    with details_col:
        if view["focus_node"]:
            st.success(f"Focused neighborhood: {view['focus_node']}")
        render_dependency_details(view["details"])

    if edited_data.get("timeline"):
        with st.expander("Timeline data"):
            st.dataframe(edited_data["timeline"], use_container_width=True)


def render_json_ld_view(edited_data):
    st.caption("Detected format: `json-ld`")
    hide_units_and_literals = st.sidebar.checkbox("Hide literal nodes", value=False)
    show_edge_labels = st.sidebar.checkbox("Show edge labels", value=False)
    nodes, links, categories, summary, title = extract_json_ld_graph_data(
        edited_data,
        hide_units_and_literals=hide_units_and_literals,
    )
    show_summary(summary)
    option = create_json_ld_option(
        nodes,
        links,
        categories,
        title=title,
        subtitle="Force layout",
        show_edge_labels=show_edge_labels,
    )
    render_graph_component(
        option,
        height_px=1000,
        enable_events=False,
        key="json_ld_graph_chart",
    )


def main():
    st.set_page_config(layout="wide")
    st.title("Graph Visualization")

    source_options = ["Default JSON-LD example", "Upload JSON file"]
    if DEFAULT_DEPENDENCY_GRAPH_PATH.exists():
        source_options.insert(0, "Local dependency graph")
    if ENRICHED_DEPENDENCY_GRAPH_PATH.exists():
        source_options.insert(1, "Enriched dependency sample")

    source_choice = st.radio("Data source", source_options, horizontal=True)
    uploaded_file = None

    if source_choice == "Upload JSON file":
        uploaded_file = st.file_uploader("Upload a JSON or JSON-LD file", type=["json", "jsonld"])
        if uploaded_file is None:
            st.info("Upload a file to visualize it.")
            return
    elif source_choice == "Local dependency graph":
        st.caption(f"Loaded from `{DEFAULT_DEPENDENCY_GRAPH_PATH}`")
    elif source_choice == "Enriched dependency sample":
        st.caption(f"Loaded from `{ENRICHED_DEPENDENCY_GRAPH_PATH}`")

    try:
        source_data = load_source_data(source_choice, uploaded_file)
        sync_editor(source_choice, source_data, uploaded_file)
    except Exception as exc:
        st.error(f"Error reading source data: {exc}")
        return

    editable_data = st.text_area("Edit JSON data", key="editor_text", height=420)

    try:
        edited_data = json.loads(editable_data)
    except json.JSONDecodeError as exc:
        st.error(f"JSON decode error: {exc}")
        return

    graph_format = detect_graph_format(edited_data)
    if graph_format == "unknown":
        st.error("Unsupported format. Expected JSON-LD with @graph or a dependency graph with nodes and edges.")
        return

    if graph_format == "dependency-graph":
        render_dependency_explorer(edited_data)
    else:
        render_json_ld_view(edited_data)


if __name__ == "__main__":
    main()
