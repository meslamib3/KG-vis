# KG-vis
KG vis for DEVODE v0

## Dependency Explorer

The Streamlit app now supports an explorer-style dependency graph workflow:

- single-click a node to inspect its incoming and outgoing method connections
- double-click a node to focus on its directly connected neighborhood
- search by method name or connecting property name
- optional edge property labels when the graph data includes `connecting_properties`
- optional method-level filtering when the graph data includes `method_level`

### Run

```bash
streamlit run kgvis.py
```

### Enriched dependency graph fields

Legacy dependency files still work. To enable the new filtering and property-aware behavior, extend the dependency graph JSON with:

- node field `method_level`
- optional node field `label`
- optional node field `method_kind`
- edge field `connecting_properties: string[]`

The repository includes `dependency-graph-enriched-sample.json` as a reference payload.
