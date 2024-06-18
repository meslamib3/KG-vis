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

# Function to extract nodes and links from JSON-LD data
def extract_graph_data(data):
    nodes = []
    links = []
    node_types = {
        "emmo:EMMO_4207e895_8b83_4318_996a_72cfb32acd94": "Material",
        "emmo:EMMO_d1d436e7_72fc_49cd_863b_7bfb4ba5276a": "Parameter",
        "emmo:EMMO_463bcfda_867b_41d9_a967_211d4d437cfb": "Measurement",
        "emmo:EMMO_a4d66059_5dd3_4b90_b4cb_10960559441b": "Process",
        "emmo:EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba": "Property",
        "emmo:EMMO_e1097637": "is_manufacturing_input",
        "emmo:EMMO_e1245987": "has_manufacturing_output",
        "emmo:EMMO_m5677989": "is_measurement_input",
        "emmo:EMMO_m87987545": "has_measurement_output",
        "emmo:EMMO_p5778r78": "has_property",
        "emmo:EMMO_p46903ar7": "has_parameter"
    }
    colors = {
        "Material": "#5470c6",
        "Parameter": "#91cc75",
        "Measurement": "#fac858",
        "Process": "#ee6666",
        "Property": "#73c0de"
    }

    # Extract nodes and links
    for item in data["@graph"]:
        if "@id" in item and "@type" in item:
            node_type = node_types.get(item["@type"], "Unknown")
            nodes.append({
                "name": item["@id"],
                "symbolSize": 10,
                "itemStyle": {"color": colors.get(node_type, "#ccc")},
                "category": node_type
            })

            for key, value in item.items():
                if key.startswith("emmo:") and key != "@type" and key != "@id":
                    if isinstance(value, list):
                        for v in value:
                            if isinstance(v, dict) and "@id" in v:
                                links.append({
                                    "source": item["@id"],
                                    "target": v["@id"],
                                    "value": key
                                })
                    elif isinstance(value, dict) and "@id" in value:
                        links.append({
                            "source": item["@id"],
                            "target": value["@id"],
                            "value": key
                        })

    return nodes, links

# Function to create the ECharts option
def create_echarts_option(nodes, links, layout='force'):
    option = {
        'title': {
            'text': 'Knowledge Graph',
            'subtext': layout.capitalize() + ' layout',
            'top': 'bottom',
            'left': 'right'
        },
        'tooltip': {},
        'legend': [{
            'data': ['Material', 'Parameter', 'Measurement', 'Process', 'Property'],
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
                {"name": "Material"},
                {"name": "Parameter"},
                {"name": "Measurement"},
                {"name": "Process"},
                {"name": "Property"}
            ],
            'roam': True,
            'label': {
                'position': 'right',
                'formatter': '{b}',
                'hideOverlap': True
            },
            'lineStyle': {'color': 'source', 'curveness': 0.3}
        }]
    }

    if layout == 'circular':
        option['series'][0]['circular'] = {'rotateLabel': True}

    return option

# Streamlit app
def main():
    st.title("JSON-LD Graph Visualization")
    
    uploaded_file = st.file_uploader("Upload a JSON-LD file", type="json")
    
    if uploaded_file is not None:
        try:
            data = read_json_ld(uploaded_file)
            nodes, links = extract_graph_data(data)
            
            layout = st.selectbox("Choose Layout", ["force", "circular"])
            option = create_echarts_option(nodes, links, layout)
            
            st_echarts(options=option, height="800px")
        
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
