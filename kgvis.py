import streamlit as st
import json
import chardet
from streamlit_echarts import st_echarts

# Function to read and parse the uploaded JSON-LD file
def read_json_ld(file):
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    data = raw_data.decode(encoding)
    return json.loads(data)

# Function to extract nodes and links from JSON-LD data for graph
def extract_graph_data(data):
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
        "emmo:EMMO_p5778r78": "has_property",
        "emmo:EMMO_p46903ar7": "has_parameter",
        "skos:prefLabel": "skos:prefLabel"
    }

    # Step 1: Add Type/Class nodes
    for type_id, type_name in node_types.items():
        nodes.append({
            "name": type_id,
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
                    "category": "Instance/Individual"
                })
                node_ids.add(node_id)

            # Link instance to its type
            if node_type in node_types.values():
                links.append({
                    "source": node_id,
                    "target": item["@type"],
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
                            if literal_value not in node_ids:
                                nodes.append({
                                    "name": literal_value,
                                    "symbolSize": 10,
                                    "itemStyle": {"color": colors["Value/Literal"]},
                                    "category": "Value/Literal"
                                })
                                node_ids.add(literal_value)
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
                    if literal_value not in node_ids:
                        nodes.append({
                            "name": literal_value,
                            "symbolSize": 10,
                            "itemStyle": {"color": colors["Value/Literal"]},
                            "category": "Value/Literal"
                        })
                        node_ids.add(literal_value)
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
        'tooltip': {
            'trigger': 'item',
            'formatter': '{a} <br/>{b} : {c}'
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
            'lineStyle': {'color': 'source', 'curveness': 0.3},
            'edgeSymbol': ['none', 'arrow'],
            'edgeSymbolSize': [4, 10],
            'edgeLabel': {
                'show': True,
                'fontSize': 8,
                'formatter': '{c}'
            }
        }]
    }

    return option

# Streamlit app
def main():
    st.set_page_config(layout="wide")
    st.title("JSON-LD Graph Visualization")

    uploaded_file = st.file_uploader("Upload a JSON-LD file", type="json")
    if uploaded_file is not None:
        try:
            data = read_json_ld(uploaded_file)

            editable_data = st.text_area("Edit JSON-LD Data", value=json.dumps(data, indent=2), height=400)
            try:
                edited_data = json.loads(editable_data)
            except json.JSONDecodeError as e:
                st.error(f"JSON Decode Error: {e}")
                return

            nodes, links = extract_graph_data(edited_data)
            if not nodes or not links:
                st.error("No nodes or links extracted from JSON-LD data. Please check the structure of your JSON-LD.")
                return

            option = create_echarts_option(nodes, links, layout='force')
            st_echarts(options=option, height="1000px")
        
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
