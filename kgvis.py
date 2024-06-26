import streamlit as st
import json
import chardet
from streamlit_echarts import st_echarts

# Default JSON-LD data
default_json_ld = {
  "@context": {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "emmo": "http://emmo.info/emmo#",
    "ex": "http://example.com/",
    "is_manufacturing_input": {
      "@id": "emmo:EMMO_e1097637",
      "@type": "@id"
    },
    "has_manufacturing_output": {
      "@id": "emmo:EMMO_e1245987",
      "@type": "@id"
    },
    "is_measurement_input": {
      "@id": "emmo:EMMO_m5677989",
      "@type": "@id"
    },
    "has_measurement_output": {
      "@id": "emmo:EMMO_m87987545",
      "@type": "@id"
    },
    "is_model_input": {
      "@id": "emmo:EMMO_m5677980",
      "@type": "@id"
    },
    "has_model_output": {
      "@id": "emmo:EMMO_m87987546",
      "@type": "@id"
    },
    "has_property": {
      "@id": "emmo:EMMO_p5778r78",
      "@type": "@id"
    },
    "has_parameter": {
      "@id": "emmo:EMMO_p46903ar7",
      "@type": "@id"
    },
    "Material": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
    "Manufacturing": "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b",
    "Measurement": "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb",
    "Property": "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba",
    "Parameter": "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a",
    "Simulation": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
    "Metadata": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92"
  },
  "@graph": [
    {
      "@id": "ex:Material",
      "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
      "skos:prefLabel": "Material"
    },
    {
      "@id": "ex:Manufacturing",
      "@type": "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b",
      "skos:prefLabel": "Manufacturing"
    },
    {
      "@id": "ex:Measurement",
      "@type": "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb",
      "skos:prefLabel": "Measurement"
    },
    {
      "@id": "ex:Property",
      "@type": "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba",
      "skos:prefLabel": "Property"
    },
    {
      "@id": "ex:Parameter",
      "@type": "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a",
      "skos:prefLabel": "Parameter"
    },
    {
      "@id": "ex:Simulation",
      "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93",
      "skos:prefLabel": "Simulation"
    },
    {
      "@id": "ex:Metadata",
      "@type": "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92",
      "skos:prefLabel": "Metadata"
    }
  ]
}

# Function to read and parse the uploaded JSON-LD file
def read_json_ld(file):
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    data = raw_data.decode(encoding)
    return json.loads(data)

# Function to extract nodes and links from JSON-LD data for graph
def extract_graph_data(data, hide_units_and_literals=False):
    nodes = []
    links = []

    node_ids = set()
    node_types = {
        "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94": "Matter",
        "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b": "Manufacturing",
        "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb": "Measurement",
        "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba": "Property",
        "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a": "Parameter",
        "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd93": "Simulation",
        "emmo:EMMO_EMMO_4207e895_8b83_4318_996a_72cfb32acd92": "Metadata"
    }

    colors = {
        "Matter": "#5470c6",         # Blue
        "Manufacturing": "#ee6666",  # Red
        "Measurement": "#fac858",    # Yellow
        "Property": "#73c0de",       # Cyan
        "Parameter": "#91cc75",      # Green
        "Simulation": "#a5a5a5",     # Grey
        "Metadata": "#9b59b6",       # Purple
        "Instance/Individual": "#3ba272", # Dark Green
        "Value/Literal": "#fc8452",  # Orange
        "Unit": "#d14a61",           # Dark Red
        "Unknown": "#ccc"            # Grey
    }

    relationship_keys = {
        "emmo:EMMO_e1097637": "is_manufacturing_input",
        "emmo:EMMO_e1245987": "has_manufacturing_output",
        "emmo:EMMO_m5677989": "is_measurement_input",
        "emmo:EMMO_m87987545": "has_measurement_output",
        "emmo:EMMO_m5677980": "is_model_input",
        "emmo:EMMO_m87987546": "has_model_output",
        "emmo:EMMO_p5778r78": "has_property",
        "emmo:EMMO_p46903ar7": "has_parameter",
        "skos:prefLabel": "skos:prefLabel"
    }

    # Step 1: Add Type/Class nodes
    for type_id, type_name in node_types.items():
        nodes.append({
            "name": type_name,
            "symbolSize": 15,
            "itemStyle": {"color": colors[type_name]},
            "category": type_name
        })
        node_ids.add(type_id)

    # Step 2: Process graph data to add instance nodes and link them to their types
    for item in data["@graph"]:
        if "@id" in item and "@type" in item:
            node_id = item["@id"]
            if isinstance(item["@type"], list):
                for t in item["@type"]:
                    if t in node_types:
                        node_type = node_types[t]
                        break
            else:
                node_type = node_types.get(item["@type"], "Instance/Individual")

            if node_id not in node_ids:
                nodes.append({
                    "name": node_id,
                    "symbolSize": 10,
                    "itemStyle": {"color": colors["Instance/Individual"]},
                    "category": "Instance/Individual",
                    "label": {"show": True, "formatter": node_id}
                })
                node_ids.add(node_id)

            # Link instance to its type
            if node_type in node_types.values():
                links.append({
                    "source": node_id,
                    "target": node_type,
                    "value": "rdf:type"
                })

            # Step 3: Add literal values and other properties
            for key, value in item.items():
                if key == "@id" or key == "@type":
                    continue
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict) and "@id" in v:
                            links.append({
                                "source": node_id,
                                "target": v["@id"],
                                "value": relationship_keys.get(key, key)
                            })
                        elif isinstance(v, str):
                            literal_value = f"{node_id}_{key}_{v}"
                            if literal_value not in node_ids and not hide_units_and_literals:
                                nodes.append({
                                    "name": literal_value,
                                    "symbolSize": 10,
                                    "itemStyle": {"color": colors["Value/Literal"]},
                                    "category": "Value/Literal"
                                })
                                node_ids.add(literal_value)
                            if not hide_units_and_literals:
                                links.append({
                                    "source": node_id,
                                    "target": literal_value,
                                    "value": relationship_keys.get(key, key)
                                })

                                # Add Unit node for each Value node
                                unit_node_id = f"{literal_value}_unit"
                                if unit_node_id not in node_ids:
                                    nodes.append({
                                        "name": unit_node_id,
                                        "symbolSize": 10,
                                        "itemStyle": {"color": colors["Unit"]},
                                        "category": "Unit"
                                    })
                                    node_ids.add(unit_node_id)
                                links.append({
                                    "source": literal_value,
                                    "target": unit_node_id,
                                    "value": "skos:prefLabel"
                                })
                elif isinstance(value, dict) and "@id" in value:
                    links.append({
                        "source": node_id,
                        "target": value["@id"],
                        "value": relationship_keys.get(key, key)
                    })
                else:
                    literal_value = f"{node_id}_{key}_{value}"
                    if literal_value not in node_ids and not hide_units_and_literals:
                        nodes.append({
                            "name": literal_value,
                            "symbolSize": 10,
                            "itemStyle": {"color": colors["Value/Literal"]},
                            "category": "Value/Literal"
                        })
                        node_ids.add(literal_value)
                    if not hide_units_and_literals:
                        links.append({
                            "source": node_id,
                            "target": literal_value,
                            "value": relationship_keys.get(key, key)
                        })

                        # Add Unit node for each Value node
                        unit_node_id = f"{literal_value}_unit"
                        if unit_node_id not in node_ids:
                            nodes.append({
                                "name": unit_node_id,
                                "symbolSize": 10,
                                "itemStyle": {"color": colors["Unit"]},
                                "category": "Unit"
                            })
                            node_ids.add(unit_node_id)
                        links.append({
                            "source": literal_value,
                            "target": unit_node_id,
                            "value": "skos:prefLabel"
                        })

    return nodes, links

# Function to create the ECharts option for graph
def create_echarts_option(nodes, links, layout='force'):
    option = {
        'title': {
            'text': 'Knowledge Graph',
            'subtext': layout.capitalize() + ' layout',
            'top': 'bottom',
            'left': 'right'
        },
        'legend': [{
            'data': ['Matter', 'Manufacturing', 'Measurement', 'Property', 'Parameter', 'Simulation', 'Metadata', 'Instance/Individual', 'Value/Literal', 'Unit'],
            'orient': 'vertical',
            'left': 'left',
            'top': 'middle'
        }],
        'animationDurationUpdate': 1500,
        'animationEasingUpdate': 'quinticInOut',
        'series': [{
            'name': 'RDF Graph',
            'type': 'graph',
            'layout': layout,
            'data': nodes,
            'links': links,
            'categories': [
                {"name": "Matter", "itemStyle": {"color": "#5470c6"}},
                {"name": "Manufacturing", "itemStyle": {"color": "#ee6666"}},
                {"name": "Measurement", "itemStyle": {"color": "#fac858"}},
                {"name": "Property", "itemStyle": {"color": "#73c0de"}},
                {"name": "Parameter", "itemStyle": {"color": "#91cc75"}},
                {"name": "Simulation", "itemStyle": {"color": "#a5a5a5"}},
                {"name": "Metadata", "itemStyle": {"color": "#9b59b6"}},
                {"name": "Instance/Individual", "itemStyle": {"color": "#3ba272"}},
                {"name": "Value/Literal", "itemStyle": {"color": "#fc8452"}},
                {"name": "Unit", "itemStyle": {"color": "#d14a61"}}
            ],
            'roam': True,
            'label': {
                'position': 'right',
                'formatter': '{b}',
                'hideOverlap': True
            },
            'focusNodeAdjacency': True,
            'lineStyle': {'color': 'source', 'curveness': 0.3},
            'edgeSymbol': ['none', 'arrow'],
            'edgeSymbolSize': [4, 10],
            'edgeLabel': {
                'show': True,
                'fontSize': 8,
                'formatter': '{c}'
            },
            'emphasis': {
                'focus': 'adjacency',
                'lineStyle': {'width': 5}
            },
            'tooltip': {
                'show': False
            }
        }]
    }

    return option

# Examples to be displayed at the bottom
examples = [
    {
        "description": "Linking Material to Manufacturing",
        "nodes": ["Material", "Manufacturing"],
        "relationship": "is_manufacturing_input",
        "purpose": "To indicate which materials are inputs for specific manufacturing processes.",
        "json_ld": {
            "@id": "ex:Material",
            "@type": "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94",
            "skos:prefLabel": "Material",
            "emmo:EMMO_e1097637": {
                "@id": "ex:Manufacturing"
            }
        }
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
            "emmo:EMMO_e1245987": {
                "@id": "ex:Material"
            }
        }
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
            "emmo:EMMO_m5677989": {
                "@id": "ex:Material"
            }
        }
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
            "emmo:EMMO_m87987545": {
                "@id": "ex:Measurement"
            }
        }
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
            "emmo:EMMO_m5677980": {
                "@id": "ex:Material"
            }
        }
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
            "emmo:EMMO_m87987546": {
                "@id": "ex:Property"
            }
        }
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
            "emmo:EMMO_p5778r78": {
                "@id": "ex:Property"
            }
        }
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
            "emmo:EMMO_p46903ar7": {
                "@id": "ex:Parameter"
            }
        }
    }
]

# Function to display examples
def display_examples():
    st.subheader("Examples")
    for example in examples:
        with st.expander(example["description"]):
            st.write(f"**Nodes:** {', '.join(example['nodes'])}")
            st.write(f"**Relationship:** {example['relationship']}")
            st.write(f"**Purpose:** {example['purpose']}")
            st.code(json.dumps(example["json_ld"], indent=2), language='json')

# Streamlit app
def main():
    st.set_page_config(layout="wide")
    st.title("JSON-LD Graph Visualization")

    hide_units_and_literals = st.checkbox("Hide Unit and Value/Literal Nodes")

    # Show a sample JSON-LD graph by default
    default_data_str = json.dumps(default_json_ld, indent=2)
    editable_data = st.text_area("Edit JSON-LD Data", value=default_data_str, height=400)

    uploaded_file = st.file_uploader("Upload a JSON-LD file", type="json")
    if uploaded_file is not None:
        try:
            data = read_json_ld(uploaded_file)
            editable_data = st.text_area("Edit JSON-LD Data", value=json.dumps(data, indent=2), height=400)
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")

    try:
        edited_data = json.loads(editable_data)
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error: {e}")
        return

    nodes, links = extract_graph_data(edited_data, hide_units_and_literals)
    if not nodes or not links:
        st.error("No nodes or links extracted from JSON-LD data. Please check the structure of your JSON-LD.")
        return

    option = create_echarts_option(nodes, links, layout='force')
    st_echarts(options=option, height="1000px")

    display_examples()

if __name__ == "__main__":
    main()
