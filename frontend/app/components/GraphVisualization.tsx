"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
import ExportFileTypeModal, { ExportOption } from "./ExportFileTypeModal";

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

// Get radial level for circular positioning (0 = center, higher = outer rings)
// Based on schema: Text (center) -> Section -> Phrase -> Word -> Morpheme -> Gloss (outer)
function getRadialLevel(nodeType: string): number {
  const hierarchy: { [key: string]: number } = {
    Text: 0, // Center
    Section: 1, // First ring
    Phrase: 2, // Second ring
    Word: 3, // Third ring
    Morpheme: 4, // Fourth ring
    Gloss: 5, // Outermost ring
  };
  return hierarchy[nodeType] ?? 3;
}

// Apply circular positioning based on schema hierarchy
function applyCircularPositioning(
  graph: MultiDirectedGraph,
  nodesByType: { [key: string]: string[] }
) {
  const nodeCount = graph.order;
  // Scale canvas based on node count
  const baseCanvasSize = Math.max(Math.sqrt(nodeCount) * 150, 1200);
  const canvasSize = Math.min(baseCanvasSize, 3000);
  
  // Base radius for each ring level
  const baseRadius = canvasSize / 8;
  const centerX = 0;
  const centerY = 0;

  // Sort node types by radial level
  const sortedTypes = Object.keys(nodesByType).sort(
    (a, b) => getRadialLevel(a) - getRadialLevel(b)
  );

  sortedTypes.forEach((type) => {
    const nodesOfType = nodesByType[type];
    const level = getRadialLevel(type);
    const count = nodesOfType.length;

    // Calculate radius for this ring level
    // Text at center (radius 0), others in expanding rings
    const radius = level === 0 ? 0 : baseRadius * level * 1.2;
    
    // For center node (Text), place at origin
    if (level === 0 && count > 0) {
      nodesOfType.forEach((nodeId) => {
        graph.setNodeAttribute(nodeId, "x", centerX);
        graph.setNodeAttribute(nodeId, "y", centerY);
      });
      return;
    }

    // Distribute nodes evenly around the circle
    const angleStep = (2 * Math.PI) / Math.max(count, 1);

    nodesOfType.forEach((nodeId, index) => {
      // Calculate angle for this node
      const angle = index * angleStep;
      
      // Add slight randomness to prevent perfect alignment
      const angleVariation = (Math.random() - 0.5) * angleStep * 0.15;
      const radiusVariation = (Math.random() - 0.5) * radius * 0.1;
      
      const finalAngle = angle + angleVariation;
      const finalRadius = Math.max(0, radius + radiusVariation);
      
      // Convert polar to cartesian coordinates
      const x = centerX + finalRadius * Math.cos(finalAngle);
      const y = centerY + finalRadius * Math.sin(finalAngle);

      graph.setNodeAttribute(nodeId, "x", x);
      graph.setNodeAttribute(nodeId, "y", y);
      // Store radial level for constraint during layout
      graph.setNodeAttribute(nodeId, "radialLevel", level);
      graph.setNodeAttribute(nodeId, "targetRadius", radius);
    });
  });
}

// Build graph from API data
function buildGraphFromData(data: any) {
  const graph = new MultiDirectedGraph();

  // Group nodes by type for hierarchical positioning
  const nodesByType: { [key: string]: string[] } = {};

  // Track sequential IDs for Section nodes
  let sectionCounter = 0;
  const sectionIdMap = new Map<string, number>();

  // First pass: collect Section nodes and assign sequential IDs
  if (data.nodes && data.nodes.length > 0) {
    data.nodes.forEach((node: any) => {
      if (node.type === "Section") {
        const nodeId = String(node.id);
        if (!sectionIdMap.has(nodeId)) {
          sectionCounter++;
          sectionIdMap.set(nodeId, sectionCounter);
        }
      }
    });
  }

  // Add nodes with initial positions
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

      // Determine label: use sequential ID for Section nodes, otherwise use node.label
      let nodeLabel = node.label || nodeId;
      if (node.type === "Section" && sectionIdMap.has(nodeId)) {
        nodeLabel = String(sectionIdMap.get(nodeId));
      }

      // Group by type
      const nodeType = node.type || "Unknown";
      if (!nodesByType[nodeType]) {
        nodesByType[nodeType] = [];
      }
      nodesByType[nodeType].push(nodeId);

      graph.addNode(nodeId, {
        label: nodeLabel,
        size: dynamicSize,
        color: node.color || "#64748b",
        nodeType: node.type, // Store as nodeType to avoid conflict with Sigma's type
        x: 0, // Will be set by hierarchical positioning
        y: 0,
      });
    });

    // Apply circular positioning based on schema hierarchy
    applyCircularPositioning(graph, nodesByType);

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

  // Apply ForceAtlas2 layout with radial constraints
  if (graph.order > 0) {
    const settings = forceAtlas2.inferSettings(graph);

    // Adjust settings based on graph complexity
    const nodeCount = graph.order;
    const edgeCount = graph.size;
    const density = edgeCount / Math.max(nodeCount * (nodeCount - 1), 1);

    // For dense graphs, use stronger separation and more iterations
    const isDenseGraph = density > 0.01 || nodeCount > 200;

    // Apply ForceAtlas2 with moderate iterations to refine circular structure
    forceAtlas2.assign(graph, {
      iterations: isDenseGraph ? 200 : 150,
      settings: {
        ...settings,
        // Moderate gravity to maintain circular structure
        gravity: isDenseGraph ? 0.3 : 0.5,
        // Scaling to allow nodes to spread in circular pattern
        scalingRatio: isDenseGraph ? 25 : 15,
        strongGravityMode: false,
        barnesHutOptimize: true,
        // Moderate movement for stable circular layout
        slowDown: isDenseGraph ? 8 : 6,
        // Enable logarithmic mode for dense graphs
        linLogMode: isDenseGraph,
        outboundAttractionDistribution: isDenseGraph,
        // Adjust sizes to prevent overlap
        adjustSizes: true,
        // Edge weight influence for natural connections
        edgeWeightInfluence: isDenseGraph ? 0.4 : 0.6,
      },
    });

    // After ForceAtlas2, constrain nodes to their radial rings
    // This ensures the circular structure is preserved
    graph.forEachNode((nodeId) => {
      const radialLevel = graph.getNodeAttribute(nodeId, "radialLevel");
      const targetRadius = graph.getNodeAttribute(nodeId, "targetRadius");
      
      if (radialLevel !== undefined && targetRadius !== undefined) {
        const currentX = graph.getNodeAttribute(nodeId, "x");
        const currentY = graph.getNodeAttribute(nodeId, "y");
        
        // Calculate distance from center
        const distance = Math.sqrt(currentX * currentX + currentY * currentY);
        
        // For center nodes (Text), keep at origin
        if (radialLevel === 0) {
          graph.setNodeAttribute(nodeId, "x", 0);
          graph.setNodeAttribute(nodeId, "y", 0);
        } else {
          // Constrain to radial ring with some tolerance
          const radiusTolerance = targetRadius * 0.3;
          const minRadius = Math.max(0, targetRadius - radiusTolerance);
          const maxRadius = targetRadius + radiusTolerance;
          
          let constrainedDistance = distance;
          if (distance < minRadius) {
            constrainedDistance = minRadius;
          } else if (distance > maxRadius) {
            constrainedDistance = maxRadius;
          }
          
          // Normalize and scale to constrained radius
          if (distance > 0) {
            const scale = constrainedDistance / distance;
            graph.setNodeAttribute(nodeId, "x", currentX * scale);
            graph.setNodeAttribute(nodeId, "y", currentY * scale);
          }
        }
        
        // Clean up temporary attributes
        graph.removeNodeAttribute(nodeId, "radialLevel");
        graph.removeNodeAttribute(nodeId, "targetRadius");
      }
    });
  }

  return graph;
}

function LoadGraph({
  filters,
  onDataLoaded,
}: {
  filters?: any;
  onDataLoaded?: (data: any) => void;
}) {
  const loadGraph = useLoadGraph();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      const data = await fetchGraphData(filters);
      onDataLoaded?.(data);
      const graph = buildGraphFromData(data);
      loadGraph(graph);
      setIsLoading(false);
    };

    loadData();
  }, [loadGraph, filters, onDataLoaded]);

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
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 border border-stone-200 z-10 max-w-xs">
          <div className="flex items-center space-x-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor: sigma
                  .getGraph()
                  .getNodeAttribute(hoveredNode, "color"),
              }}
            />
            <div className="text-xs font-medium text-stone-700 uppercase">
              {sigma.getGraph().getNodeAttribute(hoveredNode, "nodeType")}
            </div>
          </div>
          <div className="text-sm font-semibold text-stone-950 break-words">
            {sigma.getGraph().getNodeAttribute(hoveredNode, "label")}
          </div>
          <div className="text-xs text-stone-700 mt-1">
            Click to view details
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 border border-stone-200 z-10">
        <div className="text-xs font-semibold text-stone-950 mb-3">
          Node Types
        </div>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#f59e0b" }}
            />
            <span className="text-xs text-stone-700">Text</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#8b5cf6" }}
            />
            <span className="text-xs text-stone-700">Section</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#06b6d4" }}
            />
            <span className="text-xs text-stone-700">Phrase</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#0ea5e9" }}
            />
            <span className="text-xs text-stone-700">Word</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#10b981" }}
            />
            <span className="text-xs text-stone-700">Morpheme</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "#ec4899" }}
            />
            <span className="text-xs text-stone-700">Gloss</span>
          </div>
        </div>
      </div>
    </>
  );
}

export default function GraphVisualization() {
  const exportOptions = useMemo<ExportOption[]>(
    () => [
      {
        value: "flextext",
        label: "FieldWorks FLEXText (.flextext)",
        description:
          "Interlinear text XML compatible with FieldWorks Language Explorer and related tools.",
        extension: "flextext",
        endpoint: "/api/v1/export/flextext",
      },
    ],
    []
  );

  const [selectedExportType, setSelectedExportType] = useState(
    exportOptions[0]?.value ?? "flextext"
  );
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [filters, setFilters] = useState<any>(undefined);
  const [showWipeConfirm, setShowWipeConfirm] = useState(false);
  const [isWiping, setIsWiping] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [activeTextId, setActiveTextId] = useState<string | null>(null);

  const selectedTextId = filters?.textId;

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleFilterChange = (newFilters: any) => {
    setFilters(newFilters);
    setRefreshKey((prev) => prev + 1);
    setActiveTextId(newFilters?.textId ?? null);
  };

  const handleDataLoaded = useCallback(
    (data: any) => {
      if (selectedTextId) {
        setActiveTextId(selectedTextId);
        return;
      }

      if (data?.nodes && Array.isArray(data.nodes)) {
        const textNode = data.nodes.find(
          (node: any) => node?.type === "Text"
        );

        if (textNode) {
          const candidate =
            textNode?.properties?.ID ??
            textNode?.properties?.id ??
            textNode?.id;

          if (candidate) {
            setActiveTextId(String(candidate));
          }
        }
      }
    },
    [selectedTextId]
  );

  const triggerExport = useCallback(
    async (fileType: string, targetFileId: string) => {
      const option =
        exportOptions.find((item) => item.value === fileType) ||
        exportOptions[0];
      const endpoint = option?.endpoint ?? "/api/v1/export/flextext";
      const extension = (option?.extension ?? fileType ?? "flextext")
        .toString()
        .replace(/^\./, "");

      setIsExporting(true);

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ file_id: targetFileId }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || "Export failed");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        const filenameBase = targetFileId || "export";
        const filename = `${filenameBase}.${extension}`;

        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        setIsExportModalOpen(false);
      } catch (error) {
        console.error("Error exporting FLEXText:", error);
        alert("Failed to export the FLEXText file. Please try again.");
      } finally {
        setIsExporting(false);
      }
    },
    [exportOptions]
  );

  const handleExportButtonClick = () => {
    const targetFileId = (activeTextId ?? "").trim();

    if (!targetFileId) {
      alert("Please select a specific text before exporting.");
      return;
    }

    setIsExportModalOpen(true);
  };

  const handleExportConfirm = useCallback(async () => {
    const targetFileId = (activeTextId ?? "").trim();

    if (!targetFileId) {
      alert("Please select a specific text before exporting.");
      setIsExportModalOpen(false);
      return;
    }

    await triggerExport(selectedExportType, targetFileId);
  }, [activeTextId, selectedExportType, triggerExport]);

  const handleExportCancel = useCallback(() => {
    if (!isExporting) {
      setIsExportModalOpen(false);
    }
  }, [isExporting]);

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

      <ExportFileTypeModal
        isOpen={isExportModalOpen}
        options={exportOptions}
        selectedType={selectedExportType}
        onSelect={setSelectedExportType}
        onCancel={handleExportCancel}
        onConfirm={handleExportConfirm}
        isSubmitting={isExporting}
      />

      {/* Control buttons */}
      <div className="absolute top-4 right-4 z-20 flex space-x-2">
        {/* Export button */}
        <button
          onClick={handleExportButtonClick}
          disabled={isExporting}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg px-3 py-2 border border-blue-700 transition-colors flex items-center space-x-2 disabled:bg-blue-400 disabled:border-blue-400"
          title="Export current dataset as FLEXText"
        >
          {isExporting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm font-medium">Exporting...</span>
            </>
          ) : (
            <>
              <svg
                className="w-5 h-5"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span className="text-sm font-medium">Export</span>
            </>
          )}
        </button>

        {/* Refresh button */}
        <button
          onClick={handleRefresh}
          className="bg-white hover:bg-stone-50 rounded-lg shadow-lg p-2 border border-stone-200 transition-colors"
          title="Refresh graph data"
        >
          <svg
            className="w-5 h-5 text-stone-700"
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
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md mx-4 border border-stone-200">
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
              <h3 className="text-lg font-semibold text-stone-950">
                Wipe Database
              </h3>
            </div>

            <p className="text-stone-950 mb-6">
              Are you sure you want to wipe all data from the database? This
              will permanently delete all texts, sections, phrases, words,
              morphemes, and glosses. This action cannot be undone.
            </p>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowWipeConfirm(false)}
                className="flex-1 px-4 py-2 text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-lg transition-colors"
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
          defaultNodeColor: "#57534e",
          defaultEdgeColor: "#a8a29e",
          defaultEdgeType: "line",
          minEdgeSize: 2,
          maxEdgeSize: 8,
          edgeColor: "#a8a29e",
          labelSize: 10,
          labelWeight: "normal",
          labelColor: { color: "#44403c" },
          labelRenderedSizeThreshold: 8,
          labelDensity: 0.5,
          labelGridCellSize: 100,
          enableEdgeEvents: true,
          allowInvalidContainer: true,
          zIndex: true,
        }}
      >
        <LoadGraph filters={filters} onDataLoaded={handleDataLoaded} />
        <GraphEvents />
      </SigmaContainer>
    </div>
  );
}
