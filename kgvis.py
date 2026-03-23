import json
from collections import Counter
from pathlib import Path

import chardet
import streamlit as st
from streamlit_echarts import st_echarts


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DEPENDENCY_GRAPH_PATH = BASE_DIR / "dependency-graph-lab-35.json"


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


EXAMPLES = [
    {
        "description": "Linking Material to Manufacturing",
        "nodes": ["Material", "Manufacturing"],
        "relationship": "is_manufacturing_input",
        "purpose": "To indicate which materials are inputs for specific manufacturing processes.",
        "json_ld": {
            "@id": "ex:Material",
            "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
            "skos:prefLabel": "Material",
            "emmo:EMMO_e1097637": {"@id": "ex:Manufacturing"},
        },
    },
    {
        "description": "Linking Manufacturing to Material",
        "nodes": ["Manufacturing", "Material"],
        "relationship": "has_manufacturing_output",
        "purpose": "To show which materials are produced as outputs from manufacturing processes.",
        "json_ld": {
            "@id": "ex:Manufacturing",
            "@type": "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b",
            "skos:prefLabel": "Manufacturing",
            "emmo:EMMO_e1245987": {"@id": "ex:Material"},
        },
    },
    {
        "description": "Linking Measurement to Material",
        "nodes": ["Measurement", "Material"],
        "relationship": "is_measurement_input",
        "purpose": "To identify which measurements are performed on specific materials.",
        "json_ld": {
            "@id": "ex:Measurement",
            "@type": "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb",
            "skos:prefLabel": "Measurement",
            "emmo:EMMO_m5677989": {"@id": "ex:Material"},
        },
    },
    {
        "description": "Linking Material to Measurement",
        "nodes": ["Material", "Measurement"],
        "relationship": "has_measurement_output",
        "purpose": "To track which measurements result from the study of specific materials.",
        "json_ld": {
            "@id": "ex:Material",
            "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
            "skos:prefLabel": "Material",
            "emmo:EMMO_m87987545": {"@id": "ex:Measurement"},
        },
    },
    {
        "description": "Linking Model to Material",
        "nodes": ["Simulation", "Material"],
        "relationship": "is_model_input",
        "purpose": "To indicate which materials are inputs for simulation models.",
        "json_ld": {
            "@id": "ex:Simulation",
            "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
            "skos:prefLabel": "Simulation",
            "emmo:EMMO_m5677980": {"@id": "ex:Material"},
        },
    },
    {
        "description": "Linking Simulation to Output",
        "nodes": ["Simulation", "Property"],
        "relationship": "has_model_output",
        "purpose": "To show which properties are predicted or calculated by simulation models.",
        "json_ld": {
            "@id": "ex:Simulation",
            "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
            "skos:prefLabel": "Simulation",
            "emmo:EMMO_m87987546": {"@id": "ex:Property"},
        },
    },
    {
        "description": "Linking Property to Material",
        "nodes": ["Property", "Material"],
        "relationship": "has_property",
        "purpose": "To describe specific properties associated with materials.",
        "json_ld": {
            "@id": "ex:Material",
            "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
            "skos:prefLabel": "Material",
            "emmo:EMMO_p5778r78": {"@id": "ex:Property"},
        },
    },
    {
        "description": "Linking Parameter to Property",
        "nodes": ["Parameter", "Property"],
        "relationship": "has_parameter",
        "purpose": "To specify parameters that define properties.",
        "json_ld": {
            "@id": "ex:Property",
            "@type": "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba",
            "skos:prefLabel": "Property",
            "emmo:EMMO_p46903ar7": {"@id": "ex:Parameter"},
        },
    },
]


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


def shorten_dependency_label(node_id, max_length=42):
    trimmed = node_id.split("_upload", 1)[0]
    if len(trimmed) <= max_length:
        return trimmed
    return f"{trimmed[: max_length - 3]}..."


def infer_dependency_kind(node_id):
    if "-Exp-" in node_id:
        return "Experiment"
    if "-Mod-" in node_id:
        return "Model"
    return "Other"


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


def build_dependency_categories():
    return [
        {"name": name, "itemStyle": {"color": color}}
        for name, color in DEPENDENCY_KIND_COLORS.items()
    ]


def extract_dependency_graph_data(data, selected_components=None):
    raw_nodes = data.get("nodes", [])
    raw_edges = data.get("edges") or data.get("links") or []

    node_map = {node["id"]: node for node in raw_nodes if "id" in node}
    filtered_nodes = []
    allowed_components = None if selected_components is None else set(selected_components)

    for node in raw_nodes:
        component_id = node.get("component_id")
        if allowed_components is not None and component_id not in allowed_components:
            continue
        filtered_nodes.append(node)

    included_node_ids = {node["id"] for node in filtered_nodes if "id" in node}
    filtered_edges = []

    for edge in raw_edges:
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        if not source or not target:
            continue
        if allowed_components is not None and (source not in included_node_ids or target not in included_node_ids):
            continue
        filtered_edges.append(edge)
        if source not in node_map:
            node_map[source] = {"id": source, "component_id": "Unknown"}
            included_node_ids.add(source)
        if target not in node_map:
            node_map[target] = {"id": target, "component_id": "Unknown"}
            included_node_ids.add(target)

    degree_counter = Counter()
    for edge in filtered_edges:
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        degree_counter[source] += 1
        degree_counter[target] += 1

    component_ids = sorted(
        {node_map[node_id].get("component_id", "Unknown") for node_id in included_node_ids},
        key=lambda value: (str(type(value)), str(value)),
    )
    component_colors = {
        component_id: DEPENDENCY_COMPONENT_COLORS[index % len(DEPENDENCY_COMPONENT_COLORS)]
        for index, component_id in enumerate(component_ids)
    }

    nodes = []
    for node_id in sorted(included_node_ids):
        node = node_map[node_id]
        component_id = node.get("component_id", "Unknown")
        kind = infer_dependency_kind(node_id)
        degree = degree_counter[node_id]
        nodes.append(
            {
                "name": node_id,
                "symbolSize": 12 + min(degree, 6) * 3,
                "category": kind,
                "itemStyle": {
                    "color": DEPENDENCY_KIND_COLORS[kind],
                    "borderColor": component_colors.get(component_id, "#444444"),
                    "borderWidth": 2,
                },
                "label": {"show": True, "formatter": shorten_dependency_label(node_id)},
            }
        )

    links = []
    for edge in filtered_edges:
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        relation = edge.get("relation") or edge.get("label") or "related_to"
        links.append(
            {
                "source": source,
                "target": target,
                "value": relation,
                "lineStyle": {"type": "dashed" if relation == "additional_input" else "solid"},
            }
        )

    summary = {
        "node_count": len(nodes),
        "edge_count": len(links),
        "component_count": len(component_ids),
        "timeline_points": len(data.get("timeline", [])),
    }
    return nodes, links, build_dependency_categories(), summary, "Dependency Graph"


def extract_graph_data(data, hide_units_and_literals=False, selected_components=None):
    graph_format = detect_graph_format(data)
    if graph_format == "json-ld":
        return extract_json_ld_graph_data(data, hide_units_and_literals=hide_units_and_literals)
    if graph_format == "dependency-graph":
        return extract_dependency_graph_data(data, selected_components=selected_components)
    raise ValueError("Unsupported graph format.")


def create_echarts_option(nodes, links, categories, title, subtitle, layout="force", show_edge_labels=True):
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
                "layout": layout,
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


def display_examples():
    st.subheader("Examples")
    for example in EXAMPLES:
        with st.expander(example["description"]):
            st.write(f"**Nodes:** {', '.join(example['nodes'])}")
            st.write(f"**Relationship:** {example['relationship']}")
            st.write(f"**Purpose:** {example['purpose']}")
            st.code(json.dumps(example["json_ld"], indent=2), language="json")


def load_source_data(source_choice, uploaded_file):
    if source_choice == "Local dependency graph":
        return read_json_path(DEFAULT_DEPENDENCY_GRAPH_PATH)
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


def main():
    st.set_page_config(layout="wide")
    st.title("Graph Visualization")

    source_options = ["Default JSON-LD example", "Upload JSON file"]
    if DEFAULT_DEPENDENCY_GRAPH_PATH.exists():
        source_options.insert(0, "Local dependency graph")

    source_choice = st.radio("Data source", source_options, horizontal=True)
    uploaded_file = None

    if source_choice == "Upload JSON file":
        uploaded_file = st.file_uploader("Upload a JSON or JSON-LD file", type=["json", "jsonld"])
        if uploaded_file is None:
            st.info("Upload a file to visualize it.")
            return
    elif source_choice == "Local dependency graph":
        st.caption(f"Loaded from `{DEFAULT_DEPENDENCY_GRAPH_PATH}`")

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

    st.caption(f"Detected format: `{graph_format}`")

    hide_units_and_literals = False
    selected_components = None
    show_edge_labels = st.checkbox("Show edge labels", value=graph_format == "dependency-graph")

    if graph_format == "json-ld":
        hide_units_and_literals = st.checkbox("Hide literal nodes", value=False)
    else:
        component_ids = sorted(
            {node.get("component_id", "Unknown") for node in edited_data.get("nodes", [])},
            key=lambda value: (str(type(value)), str(value)),
        )
        selected_components = st.multiselect(
            "Filter by component_id",
            component_ids,
            default=component_ids,
        )
        st.caption("Node fill color shows workflow kind. Border color shows component membership.")

    try:
        nodes, links, categories, summary, title = extract_graph_data(
            edited_data,
            hide_units_and_literals=hide_units_and_literals,
            selected_components=selected_components,
        )
    except Exception as exc:
        st.error(f"Error extracting graph data: {exc}")
        return

    if not nodes:
        st.error("No nodes were extracted from the data.")
        return

    show_summary(summary)
    option = create_echarts_option(
        nodes,
        links,
        categories,
        title=title,
        subtitle="Force layout",
        layout="force",
        show_edge_labels=show_edge_labels,
    )
    st_echarts(options=option, height="1000px")

    if graph_format == "dependency-graph" and edited_data.get("timeline"):
        with st.expander("Timeline data"):
            st.dataframe(edited_data["timeline"], use_container_width=True)
    elif graph_format == "json-ld":
        display_examples()


if __name__ == "__main__":
    main()
