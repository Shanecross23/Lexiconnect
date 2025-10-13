"use client";

import { useEffect, useRef, useState } from "react";
import {
  SigmaContainer,
  useLoadGraph,
  useRegisterEvents,
  useSigma,
} from "@react-sigma/core";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/react-sigma.min.css";

// Fetch graph data from API
async function fetchGraphData() {
  try {
    const response = await fetch("/api/v1/linguistic/graph-data");
    if (!response.ok) {
      throw new Error("Failed to fetch graph data");
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching graph data:", error);
    return { nodes: [], edges: [] };
  }
}

// Build graph from API data
function buildGraphFromData(data: any) {
  const graph = new MultiDirectedGraph();

  // Add nodes
  if (data.nodes && data.nodes.length > 0) {
    data.nodes.forEach((node: any) => {
      graph.addNode(node.id, {
        label: node.label || node.id,
        size: node.size || 10,
        color: node.color || "#64748b",
        nodeType: node.type, // Store as nodeType to avoid conflict with Sigma's type
        x: Math.random() * 100,
        y: Math.random() * 100,
      });
    });

    // Add edges
    if (data.edges && data.edges.length > 0) {
      data.edges.forEach((edge: any) => {
        try {
          // Only add edge if both source and target nodes exist
          if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
            graph.addEdge(edge.source, edge.target, {
              size: edge.size || 2,
              color: edge.color || "#94a3b8",
              relationshipType: edge.type || "", // Store relationship type separately
            });
          }
        } catch (error) {
          console.warn("Error adding edge:", edge, error);
        }
      });
    }
  } else {
    // If no data, create a helpful message node
    graph.addNode("empty", {
      label: "No data yet - upload a .flextext file!",
      size: 20,
      color: "#64748b",
      nodeType: "Empty",
      x: 50,
      y: 50,
    });
  }

  return graph;
}

function LoadGraph() {
  const loadGraph = useLoadGraph();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      const data = await fetchGraphData();
      const graph = buildGraphFromData(data);
      loadGraph(graph);
      setIsLoading(false);
    };

    loadData();
  }, [loadGraph]);

  return null;
}

function GraphEvents() {
  const registerEvents = useRegisterEvents();
  const sigma = useSigma();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  useEffect(() => {
    registerEvents({
      enterNode: (event) => {
        setHoveredNode(event.node);
        sigma.getGraph().setNodeAttribute(event.node, "highlighted", true);
        sigma.refresh();
      },
      leaveNode: (event) => {
        setHoveredNode(null);
        sigma.getGraph().setNodeAttribute(event.node, "highlighted", false);
        sigma.refresh();
      },
      clickNode: (event) => {
        console.log("Clicked node:", event.node);
        const nodeData = sigma.getGraph().getNodeAttributes(event.node);
        console.log("Node data:", nodeData);
      },
    });
  }, [registerEvents, sigma]);

  return (
    <>
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-200 dark:border-slate-700 z-10 max-w-xs">
          <div className="flex items-center space-x-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor: sigma
                  .getGraph()
                  .getNodeAttribute(hoveredNode, "color"),
              }}
            />
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              {sigma.getGraph().getNodeAttribute(hoveredNode, "nodeType")}
            </div>
          </div>
          <div className="text-sm font-semibold text-slate-900 dark:text-white break-words">
            {sigma.getGraph().getNodeAttribute(hoveredNode, "label")}
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            Click to view details
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-200 dark:border-slate-700 z-10">
        <div className="text-xs font-semibold text-slate-900 dark:text-white mb-3">
          Node Types
        </div>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#f59e0b" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Text
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#8b5cf6" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Section
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#06b6d4" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Phrase
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#0ea5e9" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Word
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#10b981" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Morpheme
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#ec4899" }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Gloss
            </span>
          </div>
        </div>
      </div>
    </>
  );
}

export default function GraphVisualization() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="w-full h-full relative">
      {/* Refresh button */}
      <button
        onClick={handleRefresh}
        className="absolute top-4 right-4 z-20 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-lg p-2 border border-slate-200 dark:border-slate-700 transition-colors"
        title="Refresh graph data"
      >
        <svg
          className="w-5 h-5 text-slate-700 dark:text-slate-200"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <SigmaContainer
        key={refreshKey}
        style={{ height: "100%", width: "100%", minHeight: "400px" }}
        settings={{
          renderEdgeLabels: false,
          defaultNodeColor: "#0ea5e9",
          defaultEdgeColor: "#94a3b8",
          labelSize: 12,
          labelWeight: "bold",
          labelColor: { color: "#1e293b" },
          enableEdgeEvents: true,
          allowInvalidContainer: true,
        }}
      >
        <LoadGraph />
        <GraphEvents />
      </SigmaContainer>
    </div>
  );
}
