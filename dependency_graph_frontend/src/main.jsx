import React, { memo, useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import ELK from "elkjs/lib/elk.bundled.js";
import {
  Background,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  getSmoothStepPath,
  useReactFlow,
  useStore,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./styles.css";

const COMPONENT_READY = "streamlit:componentReady";
const SET_COMPONENT_VALUE = "streamlit:setComponentValue";
const SET_FRAME_HEIGHT = "streamlit:setFrameHeight";
const RENDER_EVENT = "streamlit:render";

const NODE_WIDTH = 256;
const NODE_HEIGHT = 98;
const ZOOM_THRESHOLD_FOR_PROPERTIES = 0.94;
const elk = new ELK();

function sendMessage(type, payload = {}) {
  window.parent.postMessage(
    {
      isStreamlitMessage: true,
      type,
      ...payload,
    },
    "*",
  );
}

function setFrameHeight(height) {
  sendMessage(SET_FRAME_HEIGHT, { height });
}

function setComponentValue(value) {
  sendMessage(SET_COMPONENT_VALUE, { value });
}

function methodKindAccent(methodKind) {
  if (methodKind === "Experiment") {
    return "#3a7bfd";
  }
  if (methodKind === "Model") {
    return "#f97316";
  }
  return "#64748b";
}

function edgeStroke(edge) {
  if (edge.focused || edge.selected) {
    return "#0f172a";
  }
  if (edge.matched) {
    return "#1d4ed8";
  }
  return "#94a3b8";
}

function edgeOpacity(edge) {
  if (edge.focused || edge.selected) {
    return 1;
  }
  if (edge.matched) {
    return 0.88;
  }
  return 0.26;
}

function buildPropertyLabel(properties) {
  if (!properties || properties.length === 0) {
    return "";
  }
  const preview = properties.slice(0, 3);
  const suffix = properties.length > preview.length ? ` +${properties.length - preview.length}` : "";
  return preview.join(", ") + suffix;
}

function MethodNode({ data, selected }) {
  const classes = [
    "method-node",
    data.matched ? "is-match" : "is-muted",
    data.focused ? "is-focused" : "",
    selected ? "is-selected" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} style={{ "--accent": methodKindAccent(data.method_kind) }}>
      <Handle className="hidden-handle" type="target" position={Position.Left} />
      <Handle className="hidden-handle" type="source" position={Position.Right} />
      <div className="method-node__eyebrow">
        <span className="pill">{data.method_kind}</span>
        <span className="pill pill-soft">{data.component_id}</span>
      </div>
      <div className="method-node__title" title={data.label}>
        {data.short_label}
      </div>
      <div className="method-node__meta">
        <span>{data.method_level || "Level not provided"}</span>
        <span>{data.degree} connection{data.degree === 1 ? "" : "s"}</span>
      </div>
    </div>
  );
}

const DependencyEdge = memo(function DependencyEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  style,
  data,
}) {
  const zoom = useStore((store) => store.transform[2]);
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 24,
  });

  const showLabel =
    data.show_edge_labels &&
    (data.emphasized || zoom >= 1.08 || (data.has_properties && zoom >= ZOOM_THRESHOLD_FOR_PROPERTIES));
  const label =
    data.include_properties && data.property_label && (data.emphasized || zoom >= ZOOM_THRESHOLD_FOR_PROPERTIES)
      ? data.property_label
      : data.relation;

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />
      {showLabel && label ? (
        <EdgeLabelRenderer>
          <div
            className={`edge-label ${data.emphasized ? "is-emphasized" : ""}`}
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
});

const nodeTypes = { method: MethodNode };
const edgeTypes = { dependency: DependencyEdge };

function toFlowElements(graph, showEdgeLabels) {
  const flowNodes = graph.nodes.map((node) => ({
    id: node.id,
    type: "method",
    position: { x: 0, y: 0 },
    draggable: false,
    selectable: true,
    data: node,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    selected: Boolean(node.selected || node.focused),
  }));

  const flowEdges = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: "dependency",
    animated: false,
    selectable: false,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 18,
      height: 18,
      color: edgeStroke(edge),
    },
    style: {
      stroke: edgeStroke(edge),
      strokeWidth: edge.focused || edge.selected ? 2.8 : edge.matched ? 2.2 : 1.4,
      opacity: edgeOpacity(edge),
    },
    data: {
      relation: edge.relation,
      include_properties: graph.include_properties,
      property_label: buildPropertyLabel(edge.connecting_properties),
      has_properties: edge.connecting_properties.length > 0,
      show_edge_labels: showEdgeLabels,
      emphasized: Boolean(edge.focused || edge.selected),
    },
  }));

  return { flowNodes, flowEdges };
}

async function layoutFlowGraph(graph, showEdgeLabels) {
  const { flowNodes, flowEdges } = toFlowElements(graph, showEdgeLabels);

  if (flowNodes.length === 0) {
    return { nodes: [], edges: flowEdges };
  }

  const elkGraph = {
    id: "dependency-root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
      "elk.layered.spacing.nodeNodeBetweenLayers": "132",
      "elk.spacing.nodeNode": "64",
      "elk.spacing.edgeNode": "28",
      "elk.padding": "[top=28,left=28,bottom=28,right=36]",
    },
    children: graph.nodes.map((node) => ({
      id: node.id,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    })),
    edges: graph.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await elk.layout(elkGraph);
  const positionedNodes = flowNodes.map((node) => {
    const positioned = layout.children.find((child) => child.id === node.id);
    return {
      ...node,
      position: {
        x: positioned?.x ?? 0,
        y: positioned?.y ?? 0,
      },
    };
  });

  return { nodes: positionedNodes, edges: flowEdges };
}

function FitController({ elements, activeNodeId }) {
  const reactFlow = useReactFlow();
  const previousKey = useRef("");

  useEffect(() => {
    const key = `${activeNodeId || "all"}:${elements.nodes.length}:${elements.edges.length}`;
    if (!elements.nodes.length || previousKey.current === key) {
      return;
    }
    previousKey.current = key;

    window.requestAnimationFrame(() => {
      const focusedNodes = activeNodeId ? elements.nodes.filter((node) => node.id === activeNodeId) : [];
      if (focusedNodes.length > 0) {
        reactFlow.fitView({
          nodes: focusedNodes,
          padding: 1.4,
          duration: 360,
          maxZoom: 1.05,
        });
        return;
      }

      reactFlow.fitView({
        padding: 0.22,
        duration: 360,
        maxZoom: 0.95,
      });
    });
  }, [activeNodeId, elements, reactFlow]);

  return null;
}

function EmptyState() {
  return (
    <div className="graph-shell empty-state">
      <div className="empty-card">
        <h3>No visible methods</h3>
        <p>Broaden the filters or reset the current focus to bring methods back into the graph.</p>
      </div>
    </div>
  );
}

function GraphCanvas({ renderArgs }) {
  const [elements, setElements] = useState({ nodes: [], edges: [] });
  const [isReady, setIsReady] = useState(false);

  const activeNodeId = renderArgs.graph.focus_node || renderArgs.graph.selected_node || null;
  const graphSummary = useMemo(
    () => ({
      nodeCount: renderArgs.graph.nodes.length,
      edgeCount: renderArgs.graph.edges.length,
      matchCount: renderArgs.graph.match_count,
    }),
    [renderArgs.graph],
  );

  useEffect(() => {
    let cancelled = false;

    async function runLayout() {
      const nextElements = await layoutFlowGraph(renderArgs.graph, renderArgs.show_edge_labels);
      if (cancelled) {
        return;
      }
      setElements(nextElements);
      setIsReady(true);
      setFrameHeight(Number(renderArgs.height_px || 960) + 12);
    }

    setIsReady(false);
    runLayout();
    return () => {
      cancelled = true;
    };
  }, [renderArgs]);

  useEffect(() => {
    function onKeyDown(event) {
      const target = event.target;
      const tagName = target?.tagName?.toLowerCase?.() || "";
      const isEditable =
        Boolean(target?.isContentEditable) ||
        tagName === "input" ||
        tagName === "textarea" ||
        Boolean(target?.closest?.("[contenteditable='true']"));

      if (isEditable) {
        return;
      }

      if ((event.ctrlKey || event.metaKey) && !event.shiftKey && event.key.toLowerCase() === "z") {
        event.preventDefault();
        setComponentValue({ eventType: "undo" });
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  if (!renderArgs.graph.nodes.length) {
    return <EmptyState />;
  }

  return (
    <div className={`graph-shell ${isReady ? "is-ready" : "is-loading"}`}>
      {!isReady ? <div className="graph-loading">Arranging methods into a stable dependency map...</div> : null}
      <ReactFlow
        nodes={elements.nodes}
        edges={elements.edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        fitView
        minZoom={0.25}
        maxZoom={1.8}
        zoomOnDoubleClick={false}
        panOnScroll
        selectionOnDrag={false}
        onNodeClick={(_, node) => {
          setComponentValue({ eventType: "click", nodeId: node.id });
        }}
        onNodeDoubleClick={(_, node) => {
          setComponentValue({ eventType: "dblclick", nodeId: node.id });
        }}
      >
        <Background color="#dbe4f0" gap={18} size={1} />
        <MiniMap
          pannable
          zoomable
          nodeColor={(node) => methodKindAccent(node.data.method_kind)}
          maskColor="rgba(227, 232, 240, 0.75)"
          position="bottom-right"
        />
        <Controls showInteractive={false} position="top-right" />
        <Panel position="top-left" className="graph-panel">
          <div className="graph-panel__title">Dependency Explorer</div>
          <div className="graph-panel__meta">
            <span>{graphSummary.nodeCount} methods</span>
            <span>{graphSummary.edgeCount} links</span>
            {renderArgs.graph.search_text ? <span>{graphSummary.matchCount} highlighted</span> : null}
          </div>
          <div className="graph-panel__actions">
            <button
              className="graph-panel__button"
              type="button"
              onClick={() => {
                setComponentValue({ eventType: "undo" });
              }}
            >
              Undo
            </button>
          </div>
          <div className="graph-panel__help">
            Click for details. Double-click to focus the local neighborhood. Press Ctrl/Cmd+Z or use Undo to step back.
          </div>
        </Panel>
        <FitController elements={elements} activeNodeId={activeNodeId} />
      </ReactFlow>
    </div>
  );
}

function App() {
  const [renderArgs, setRenderArgs] = useState({
    graph: {
      nodes: [],
      edges: [],
      selected_node: null,
      focus_node: null,
      match_count: 0,
      search_text: "",
      include_properties: false,
    },
    height_px: 960,
    show_edge_labels: true,
  });

  useEffect(() => {
    function onMessage(event) {
      if (!event.data || event.data.type !== RENDER_EVENT) {
        return;
      }
      setRenderArgs(event.data.args || {});
    }

    window.addEventListener("message", onMessage);
    sendMessage(COMPONENT_READY, { apiVersion: 1 });
    setFrameHeight(540);

    return () => {
      window.removeEventListener("message", onMessage);
    };
  }, []);

  return (
    <ReactFlowProvider>
      <GraphCanvas renderArgs={renderArgs} />
    </ReactFlowProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
