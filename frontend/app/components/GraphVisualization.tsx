"use client";

import { useEffect, useRef, useState } from "react";
import {
  SigmaContainer,
  useLoadGraph,
  useRegisterEvents,
  useSigma,
} from "@react-sigma/core";
import { MultiDirectedGraph } from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import "@react-sigma/core/lib/react-sigma.min.css";
import GraphFilters from "./GraphFilters";

// Fetch graph data from API
async function fetchGraphData(filters?: {
  textId?: string;
  language?: string;
  nodeTypes?: string[];
  limit?: number;
}) {
  try {
    const params = new URLSearchParams();
    if (filters?.textId) params.append("text_id", filters.textId);
    if (filters?.language) params.append("language", filters.language);
    if (filters?.nodeTypes && filters.nodeTypes.length > 0) {
      params.append("node_types", filters.nodeTypes.join(","));
    }
    if (filters?.limit) params.append("limit", filters.limit.toString());

    const url = `/api/v1/linguistic/graph-data${
      params.toString() ? `?${params.toString()}` : ""
    }`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Failed to fetch graph data");
    }
    const data = await response.json();
    console.log("Fetched graph data:", {
      nodeCount: data.nodes?.length || 0,
      edgeCount: data.edges?.length || 0,
      sampleEdges: data.edges?.slice(0, 3) || [],
    });
    return data;
  } catch (error) {
    console.error("Error fetching graph data:", error);
    return { nodes: [], edges: [] };
  }
}

// Build graph from API data
function buildGraphFromData(data: any) {
  const graph = new MultiDirectedGraph();

  // Add nodes with initial random positions
  if (data.nodes && data.nodes.length > 0) {
    data.nodes.forEach((node: any) => {
      const nodeId = String(node.id);
      // Skip if node already exists (avoid duplicates)
      if (graph.hasNode(nodeId)) {
        console.warn(`Duplicate node detected: ${nodeId}`);
        return;
      }

      // Calculate dynamic size based on node type and connections
      let dynamicSize = node.size || 10;

      // Adjust size based on node type hierarchy
      if (node.type === "Text") {
        dynamicSize = Math.max(dynamicSize, 25);
      } else if (node.type === "Section") {
        dynamicSize = Math.max(dynamicSize, 18);
      } else if (node.type === "Phrase") {
        dynamicSize = Math.max(dynamicSize, 12);
      } else if (node.type === "Word") {
        dynamicSize = Math.max(dynamicSize, 8);
      } else if (node.type === "Morpheme") {
        dynamicSize = Math.max(dynamicSize, 5);
      } else if (node.type === "Gloss") {
        dynamicSize = Math.max(dynamicSize, 6);
      }

      graph.addNode(nodeId, {
        label: node.label || nodeId,
        size: dynamicSize,
        color: node.color || "#64748b",
        nodeType: node.type, // Store as nodeType to avoid conflict with Sigma's type
        x: Math.random() * 100,
        y: Math.random() * 100,
      });
    });

    // Add edges
    if (data.edges && data.edges.length > 0) {
      const edgeCount = data.edges.length;
      const nodeCount = data.nodes ? data.nodes.length : 0;
      const isDenseGraph = nodeCount > 200 || edgeCount > 500;

      console.log(`Adding ${edgeCount} edges to graph with ${nodeCount} nodes`);
      console.log("Sample edges to process:", data.edges.slice(0, 3));
      console.log("Available nodes:", graph.nodes().slice(0, 5));

      data.edges.forEach((edge: any, index: number) => {
        try {
          // Ensure both source and target are strings
          const sourceId = String(edge.source);
          const targetId = String(edge.target);

          // Only add edge if both source and target nodes exist
          if (graph.hasNode(sourceId) && graph.hasNode(targetId)) {
            // Adjust edge styling for dense graphs
            const edgeSize = isDenseGraph
              ? Math.max((edge.size || 2) * 0.8, 1.5) // Ensure minimum size of 1.5
              : Math.max(edge.size || 2, 1.5);
            const edgeColor = isDenseGraph
              ? (edge.color || "#94a3b8") + "AA" // 67% opacity for dense graphs
              : edge.color || "#94a3b8";

            // Use a unique edge ID
            const edgeId =
              edge.id || `edge-${edge.source}-${edge.target}-${index}`;

            graph.addEdge(sourceId, targetId, {
              size: edgeSize,
              color: edgeColor,
              type: "line", // Explicitly set edge type
              relationshipType: edge.type || "", // Store relationship type separately
            });
          } else {
            console.warn(`Skipping edge ${index}: missing nodes`, {
              source: sourceId,
              target: targetId,
              hasSource: graph.hasNode(sourceId),
              hasTarget: graph.hasNode(targetId),
            });
          }
        } catch (error) {
          console.warn("Error adding edge:", edge, error);
        }
      });

      console.log(`Successfully added ${graph.size} edges to graph`);
      console.log("Graph summary:", {
        nodeCount: graph.order,
        edgeCount: graph.size,
        sampleNodes: graph.nodes().slice(0, 3),
        sampleEdges: graph.edges().slice(0, 3),
      });
    } else {
      console.log("No edges to add to graph");
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

  // Apply ForceAtlas2 layout for better positioning
  if (graph.order > 0) {
    const settings = forceAtlas2.inferSettings(graph);

    // Adjust settings based on graph complexity
    const nodeCount = graph.order;
    const edgeCount = graph.size;
    const density = edgeCount / (nodeCount * (nodeCount - 1));

    // For dense graphs (like btz1), use stronger separation
    const isDenseGraph = density > 0.01 || nodeCount > 200;

    forceAtlas2.assign(graph, {
      iterations: isDenseGraph ? 200 : 100,
      settings: {
        ...settings,
        gravity: isDenseGraph ? 0.5 : 1,
        scalingRatio: isDenseGraph ? 20 : 10,
        strongGravityMode: false,
        barnesHutOptimize: true,
        slowDown: isDenseGraph ? 8 : 5,
        // Additional settings for better separation
        linLogMode: isDenseGraph,
        outboundAttractionDistribution: isDenseGraph,
        adjustSizes: isDenseGraph,
        edgeWeightInfluence: isDenseGraph ? 0.5 : 1,
      },
    });
  }

  return graph;
}

function LoadGraph({ filters }: { filters?: any }) {
  const loadGraph = useLoadGraph();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      const data = await fetchGraphData(filters);
      const graph = buildGraphFromData(data);
      loadGraph(graph);
      setIsLoading(false);
    };

    loadData();
  }, [loadGraph, filters]);

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
  const [filters, setFilters] = useState<any>(undefined);
  const [showWipeConfirm, setShowWipeConfirm] = useState(false);
  const [isWiping, setIsWiping] = useState(false);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleFilterChange = (newFilters: any) => {
    setFilters(newFilters);
    setRefreshKey((prev) => prev + 1);
  };

  const handleWipeDatabase = async () => {
    setIsWiping(true);
    try {
      const response = await fetch("/api/v1/linguistic/wipe-database", {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to wipe database");
      }

      const result = await response.json();
      console.log("Database wiped:", result);

      // Refresh the graph after wiping
      setRefreshKey((prev) => prev + 1);
      setShowWipeConfirm(false);

      // Show success message (you could add a toast notification here)
      alert(
        `Database wiped successfully! Deleted: ${Object.entries(
          result.deleted_counts
        )
          .map(([key, count]) => `${count} ${key}`)
          .join(", ")}`
      );
    } catch (error) {
      console.error("Error wiping database:", error);
      alert("Failed to wipe database. Please try again.");
    } finally {
      setIsWiping(false);
    }
  };

  return (
    <div className="w-full h-full relative">
      {/* Filter Panel */}
      <GraphFilters onFilterChange={handleFilterChange} />

      {/* Control buttons */}
      <div className="absolute top-4 right-4 z-20 flex space-x-2">
        {/* Refresh button */}
        <button
          onClick={handleRefresh}
          className="bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-lg p-2 border border-slate-200 dark:border-slate-700 transition-colors"
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

        {/* Wipe database button */}
        <button
          onClick={() => setShowWipeConfirm(true)}
          className="bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-lg p-2 border border-red-600 transition-colors"
          title="Wipe all database data"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      {/* Wipe confirmation dialog */}
      {showWipeConfirm && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-30">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 max-w-md mx-4 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-red-600 dark:text-red-400"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Wipe Database
              </h3>
            </div>

            <p className="text-slate-600 dark:text-slate-300 mb-6">
              Are you sure you want to wipe all data from the database? This
              will permanently delete all texts, sections, phrases, words,
              morphemes, and glosses. This action cannot be undone.
            </p>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowWipeConfirm(false)}
                className="flex-1 px-4 py-2 text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleWipeDatabase}
                disabled={isWiping}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                {isWiping ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Wiping...</span>
                  </>
                ) : (
                  <span>Wipe Database</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <SigmaContainer
        key={refreshKey}
        style={{ height: "100%", width: "100%", minHeight: "400px" }}
        settings={{
          renderEdgeLabels: false,
          renderEdges: true,
          defaultNodeColor: "#0ea5e9",
          defaultEdgeColor: "#94a3b8",
          defaultEdgeType: "line",
          minEdgeSize: 2,
          maxEdgeSize: 8,
          edgeColor: "#94a3b8",
          labelSize: 10,
          labelWeight: "normal",
          labelColor: { color: "#1e293b" },
          labelRenderedSizeThreshold: 8,
          labelDensity: 0.5,
          labelGridCellSize: 100,
          enableEdgeEvents: true,
          allowInvalidContainer: true,
          zIndex: true,
        }}
      >
        <LoadGraph filters={filters} />
        <GraphEvents />
      </SigmaContainer>
    </div>
  );
}
