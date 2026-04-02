import unittest

from dependency_explorer import build_dependency_view, normalize_dependency_graph


LEGACY_GRAPH = {
    "nodes": [
        {"id": "PSI-Exp-method-upload20260402_001", "component_id": 0},
        {"id": "FZJ-Mod-method-upload20260402_002", "component_id": 1}
    ],
    "edges": [
        {
            "from": "PSI-Exp-method-upload20260402_001",
            "to": "FZJ-Mod-method-upload20260402_002",
            "relation": "input"
        }
    ]
}


ENRICHED_GRAPH = {
    "nodes": [
        {
            "id": "A-Exp-upload20260402_001",
            "label": "A Experiment",
            "component_id": "comp-1",
            "method_kind": "Experiment",
            "method_level": "Low Scale"
        },
        {
            "id": "B-Mod-upload20260402_002",
            "label": "B Model",
            "component_id": "comp-1",
            "method_kind": "Model",
            "method_level": "MEA"
        },
        {
            "id": "C-Mod-upload20260402_003",
            "label": "C Model",
            "component_id": "comp-2",
            "method_kind": "Model",
            "method_level": "MEA"
        }
    ],
    "edges": [
        {
            "from": "A-Exp-upload20260402_001",
            "to": "B-Mod-upload20260402_002",
            "relation": "input",
            "connecting_properties": ["Porosity", "Pt loading"]
        },
        {
            "from": "B-Mod-upload20260402_002",
            "to": "C-Mod-upload20260402_003",
            "relation": "input",
            "connecting_properties": ["Water saturation"]
        }
    ]
}


METADATA_FOR_GRAPH = {
    "1675": {
        "data_id": {
            "value": "B-Mod-upload20260402_002"
        },
        "input_datasets": {
            "value": [
                [
                    {
                        "name": "A-file-1.txt",
                        "dataId": "A-Exp-upload20260402_001",
                        "fileId": 1
                    }
                ],
                [
                    {
                        "name": "C-file-1.txt",
                        "dataId": "C-Mod-upload20260402_003",
                        "fileId": 2
                    }
                ]
            ]
        },
        "additional_input_datasets": {
            "value": []
        },
        "input_properties": {
            "value": [
                {
                    "input": "Porosity",
                    "datasets": ["A-file-1.txt"]
                },
                {
                    "input": "Water saturation",
                    "datasets": ["C-file-1.txt"]
                },
                {
                    "input": "Ignored",
                    "datasets": ["none"]
                }
            ]
        }
    }
}


class DependencyExplorerTests(unittest.TestCase):
    def test_legacy_graph_remains_supported(self):
        model = normalize_dependency_graph(LEGACY_GRAPH)

        self.assertFalse(model["has_method_levels"])
        self.assertFalse(model["has_property_metadata"])
        self.assertEqual(len(model["nodes_by_id"]), 2)
        self.assertEqual(len(model["edges"]), 1)

    def test_enriched_graph_detects_new_metadata(self):
        model = normalize_dependency_graph(ENRICHED_GRAPH)

        self.assertTrue(model["has_method_levels"])
        self.assertTrue(model["has_property_metadata"])
        self.assertEqual(model["method_levels"], ["Low Scale", "MEA"])
        self.assertEqual(model["edges"][0]["connecting_properties"], ["Porosity", "Pt loading"])

    def test_metadata_file_can_enrich_edge_properties(self):
        graph = {
            "nodes": ENRICHED_GRAPH["nodes"],
            "edges": [
                {
                    "from": "A-Exp-upload20260402_001",
                    "to": "B-Mod-upload20260402_002",
                    "relation": "input"
                },
                {
                    "from": "C-Mod-upload20260402_003",
                    "to": "B-Mod-upload20260402_002",
                    "relation": "input"
                }
            ]
        }

        model = normalize_dependency_graph(graph, metadata=METADATA_FOR_GRAPH)

        self.assertTrue(model["has_property_metadata"])
        self.assertEqual(model["metadata_enriched_edges"], 2)
        self.assertEqual(model["edges"][0]["connecting_properties"], ["Porosity"])
        self.assertEqual(model["edges"][1]["connecting_properties"], ["Water saturation"])

    def test_property_search_highlights_connected_nodes(self):
        model = normalize_dependency_graph(ENRICHED_GRAPH)
        view = build_dependency_view(model, search_text="porosity")

        highlighted = {node["name"] for node in view["nodes"] if node["itemStyle"]["opacity"] > 0.5}
        self.assertEqual(highlighted, {"A-Exp-upload20260402_001", "B-Mod-upload20260402_002"})

    def test_component_and_method_level_filters_reduce_visible_graph(self):
        model = normalize_dependency_graph(ENRICHED_GRAPH)
        view = build_dependency_view(
            model,
            selected_components=["comp-1"],
            selected_method_levels=["MEA"],
        )

        visible = {node["name"] for node in view["nodes"]}
        self.assertEqual(visible, {"B-Mod-upload20260402_002"})
        self.assertEqual(view["summary"]["edge_count"], 0)

    def test_focus_node_restricts_graph_to_direct_neighbors(self):
        model = normalize_dependency_graph(ENRICHED_GRAPH)
        view = build_dependency_view(model, focus_node="B-Mod-upload20260402_002")

        visible = {node["name"] for node in view["nodes"]}
        self.assertEqual(
            visible,
            {
                "A-Exp-upload20260402_001",
                "B-Mod-upload20260402_002",
                "C-Mod-upload20260402_003"
            }
        )
        self.assertEqual(len(view["links"]), 2)


if __name__ == "__main__":
    unittest.main()
