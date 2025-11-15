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
import ExportFileTypeModal, { ExportOption } from "./ExportFileTypeModal";
import GraphFilters from "./GraphFilters";

type ExportFeedback = {
  id: number;
  type: "success" | "error";
  message: string;
};

type GraphFetchOptions = {
  limit?: number;
  textId?: string;
  language?: string;
  nodeTypes?: string[];
  signal?: AbortSignal;
};

type GraphQueryFilters = {
  limit: number;
  textId?: string;
  language?: string;
  nodeTypes?: string[];
};

const MIN_GRAPH_LIMIT = 10;
const MAX_GRAPH_LIMIT = 1000;
const DEFAULT_GRAPH_LIMIT = 200;

const clampLimitValue = (value?: number) => {
  const numeric =
    typeof value === "number" && Number.isFinite(value)
      ? value
      : DEFAULT_GRAPH_LIMIT;

  return Math.min(MAX_GRAPH_LIMIT, Math.max(MIN_GRAPH_LIMIT, numeric));
};

const sanitizeOptionalString = (value?: string | null) => {
  if (typeof value !== "string") {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
};

const arraysMatch = (a?: string[], b?: string[]) => {
  if (!a && !b) {
    return true;
  }

  if (!a || !b) {
    return false;
  }

  if (a.length !== b.length) {
    return false;
  }

  return a.every((value, index) => value === b[index]);
};

// Fetch graph data from API
async function fetchGraphData(options: GraphFetchOptions = {}) {
  const { limit, textId, language, nodeTypes, signal } = options;
  try {
    const params = new URLSearchParams();
    params.append("limit", clampLimitValue(limit).toString());

    if (textId) {
      params.append("text_id", textId);
    }

    if (language) {
      params.append("language", language);
    }

    if (nodeTypes && nodeTypes.length > 0) {
      params.append("node_types", nodeTypes.join(","));
    }

    const url = `/api/v1/linguistic/graph-data?${params.toString()}`;
    const response = await fetch(url, { signal });
    if (!response.ok) {
      throw new Error(
        `Failed to fetch graph data: ${response.status} ${response.statusText}`
      );
    }
    const data = await response.json();
    console.log("Fetched graph data:", {
      nodeCount: data.nodes?.length || 0,
      edgeCount: data.edges?.length || 0,
      sampleEdges: data.edges?.slice(0, 3) || [],
    });
    return data;
  } catch (error) {
    const err = error as { name?: string; message?: string };
    if (err?.name === "AbortError") {
      throw error;
    }
    console.error("Error fetching graph data:", error);
    // Re-throw connection errors so they can be handled by the UI
    if (
      err?.message?.includes("ECONNRESET") ||
      err?.message?.includes("socket hang up") ||
      err?.message?.includes("Failed to fetch") ||
      err?.name === "TypeError"
    ) {
      throw new Error(
        "Backend connection failed. Please ensure the backend server is running."
      );
    }
    return { nodes: [], edges: [] };
  }
}

// Apply radial layout: nodes grouped by type in concentric rings
function applyRadialLayout(graph: MultiDirectedGraph) {
  // Define the hierarchy order
  const typeOrder = ["Text", "Section", "Phrase", "Word", "Morpheme", "Gloss"];

  // Group nodes by type
  const nodesByType: Record<string, string[]> = {};

  graph.forEachNode((id, attrs) => {
    const t = attrs.nodeType || "Other";
    if (!nodesByType[t]) nodesByType[t] = [];
    nodesByType[t].push(id);
  });

  // Radial layout: each type on its own ring
  const radiusStep = 200; // increase to spread rings farther apart

  typeOrder.forEach((type, levelIndex) => {
    const nodes = nodesByType[type] || [];
    if (!nodes.length) return;

    const radius = levelIndex * radiusStep; // 0, 200, 400, ...

    nodes.forEach((nodeId, i) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      graph.setNodeAttribute(nodeId, "x", radius * Math.cos(angle));
      graph.setNodeAttribute(nodeId, "y", radius * Math.sin(angle));
    });
  });
}

// Build graph from API data
function buildGraphFromData(data: any) {
  const graph = new MultiDirectedGraph();

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

      graph.addNode(nodeId, {
        label: nodeLabel,
        size: dynamicSize,
        color: node.color || "#64748b",
        nodeType: node.type, // Store as nodeType to avoid conflict with Sigma's type
        // temporary, will be overwritten by radial layout:
        x: 0,
        y: 0,
      });
    });

    // Apply radial layout: nodes grouped by type in concentric rings
    applyRadialLayout(graph);

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
            // Adjust edge styling - use light blue with transparency
            const edgeSize = isDenseGraph
              ? Math.max((edge.size || 2) * 0.8, 1.5) // Ensure minimum size of 1.5
              : Math.max(edge.size || 2, 1.5);
            const edgeColor = (edge.color || "#60a5fa") + "DD"; // Light blue with 87% opacity

            // Use a unique edge ID
            const edgeId =
              edge.id || `edge-${edge.source}-${edge.target}-${index}`;

            // For MultiDirectedGraph, pass the edge key as first parameter to allow duplicate edges
            graph.addEdge(edgeId, sourceId, targetId, {
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

  // Apply ForceAtlas2 gently to untangle edges, not collapse rings
  if (graph.order > 0) {
    const baseSettings = forceAtlas2.inferSettings(graph);

    forceAtlas2.assign(graph, {
      iterations: 50, // slightly more iterations for better separation
      settings: {
        ...baseSettings,
        gravity: 0.03, // even lower gravity to preserve ring structure
        scalingRatio: 15, // increase spread to reduce edge overlap
        strongGravityMode: false,
        barnesHutOptimize: true,
        slowDown: 15, // slower movement for gentler adjustments
        linLogMode: true,
        outboundAttractionDistribution: true,
        adjustSizes: true,
        edgeWeightInfluence: 0.2, // reduce edge influence for cleaner layout
      },
    });
  }

  return graph;
}

function LoadGraph({
  filters,
  onDataLoaded,
  onError,
}: {
  filters: GraphQueryFilters;
  onDataLoaded?: (data: any) => void;
  onError?: (error: Error) => void;
}) {
  const loadGraph = useLoadGraph();

  useEffect(() => {
    const controller = new AbortController();

    const loadData = async () => {
      try {
        const data = await fetchGraphData({
          ...filters,
          signal: controller.signal,
        });
        if (controller.signal.aborted) {
          return;
        }

        onDataLoaded?.(data);
        const graph = buildGraphFromData(data);
        loadGraph(graph);
      } catch (error) {
        const err = error as { name?: string; message?: string };
        if (err?.name === "AbortError") {
          return;
        }
        console.error("Error loading graph data:", error);
        if (err?.message && onError) {
          onError(new Error(err.message));
        }
      }
    };

    loadData();
    return () => controller.abort();
  }, [filters, loadGraph, onDataLoaded, onError]);

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
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-sm p-4 border border-stone-200 z-10 max-w-xs">
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
    </>
  );
}

function ZoomControls() {
  const sigma = useSigma();

  const handleZoomIn = () => {
    const camera = sigma.getCamera();
    const ratio = camera.ratio * 0.7;
    camera.animate({ ratio }, { duration: 200 });
  };

  const handleZoomOut = () => {
    const camera = sigma.getCamera();
    const ratio = camera.ratio * 1.3;
    camera.animate({ ratio }, { duration: 200 });
  };

  const handleFitToView = () => {
    sigma.getCamera().animatedReset({ duration: 300 });
  };

  return (
    <div className="absolute bottom-4 right-4 z-20 flex flex-col space-y-1 bg-white rounded-lg shadow-sm border border-stone-200 p-1">
      <button
        onClick={handleZoomIn}
        className="p-2 hover:bg-stone-50 rounded transition-colors"
        title="Zoom in"
      >
        <svg
          className="w-4 h-4 text-stone-700"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
      </button>
      <button
        onClick={handleZoomOut}
        className="p-2 hover:bg-stone-50 rounded transition-colors"
        title="Zoom out"
      >
        <svg
          className="w-4 h-4 text-stone-700"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M18 12H6"
          />
        </svg>
      </button>
      <div className="border-t border-stone-200 my-1"></div>
      <button
        onClick={handleFitToView}
        className="p-2 hover:bg-stone-50 rounded transition-colors"
        title="Fit to view"
      >
        <svg
          className="w-4 h-4 text-stone-700"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
          />
        </svg>
      </button>
    </div>
  );
}

function GraphLegend() {
  const nodeTypes = [
    { type: "Text", color: "#f59e0b" },
    { type: "Section", color: "#8b5cf6" },
    { type: "Phrase", color: "#06b6d4" },
    { type: "Word", color: "#0ea5e9" },
    { type: "Morpheme", color: "#10b981" },
    { type: "Gloss", color: "#ec4899" },
  ];

  return (
    <div className="absolute bottom-4 left-4 z-20 bg-white rounded-lg shadow-sm border border-stone-200 p-3">
      <div className="text-xs font-semibold text-stone-700 mb-2 uppercase tracking-wide">
        Node Types
      </div>
      <div className="space-y-1.5">
        {nodeTypes.map((item) => (
          <div key={item.type} className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full border border-stone-300"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-xs text-stone-600">{item.type}</span>
          </div>
        ))}
      </div>
    </div>
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
        endpoint: "/api/v1/export",
      },
      {
        value: "json",
        label: "Lexiconnect JSON snapshot (.json)",
        description:
          "Structured JSON export mirroring the Text → Section → Phrase → Word → Morpheme hierarchy.",
        extension: "json",
        endpoint: "/api/v1/export",
      },
    ],
    []
  );

  const [selectedExportType, setSelectedExportType] = useState(
    exportOptions[0]?.value ?? "flextext"
  );
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showWipeConfirm, setShowWipeConfirm] = useState(false);
  const [isWiping, setIsWiping] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [activeTextId, setActiveTextId] = useState<string | null>(null);
  const [exportFeedback, setExportFeedback] = useState<ExportFeedback | null>(
    null
  );
  const [graphFilters, setGraphFilters] = useState<GraphQueryFilters>({
    limit: DEFAULT_GRAPH_LIMIT,
  });
  const [hasData, setHasData] = useState<boolean | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const showExportFeedback = useCallback(
    (type: ExportFeedback["type"], message: string) => {
      setExportFeedback({ id: Date.now(), type, message });
    },
    []
  );

  useEffect(() => {
    if (!exportFeedback) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      setExportFeedback(null);
    }, 6000);
    return () => window.clearTimeout(timer);
  }, [exportFeedback]);

  const handleRefresh = () => {
    setConnectionError(null);
    setRefreshKey((prev) => prev + 1);
  };

  const handleFilterChange = useCallback(
    (update: Partial<GraphQueryFilters>) => {
      setGraphFilters((prev) => {
        const next: GraphQueryFilters = { ...prev };
        let hasChanges = false;

        if ("limit" in update && update.limit !== undefined) {
          const sanitizedLimit = clampLimitValue(update.limit);
          if (sanitizedLimit !== next.limit) {
            next.limit = sanitizedLimit;
            hasChanges = true;
          }
        }

        if ("textId" in update) {
          const sanitized = sanitizeOptionalString(update.textId ?? undefined);
          const current = next.textId;
          if (sanitized && sanitized !== current) {
            next.textId = sanitized;
            hasChanges = true;
          } else if (!sanitized && current !== undefined) {
            delete next.textId;
            hasChanges = true;
          }
        }

        if ("language" in update) {
          const sanitized = sanitizeOptionalString(
            update.language ?? undefined
          );
          const current = next.language;
          if (sanitized && sanitized !== current) {
            next.language = sanitized;
            hasChanges = true;
          } else if (!sanitized && current !== undefined) {
            delete next.language;
            hasChanges = true;
          }
        }

        if ("nodeTypes" in update) {
          const cleaned =
            update.nodeTypes
              ?.map((value) => value.trim())
              .filter((value) => value.length > 0) ?? undefined;
          const current = next.nodeTypes;

          if (cleaned && !arraysMatch(cleaned, current)) {
            next.nodeTypes = cleaned;
            hasChanges = true;
          } else if (!cleaned && current) {
            delete next.nodeTypes;
            hasChanges = true;
          }
        }

        return hasChanges ? next : prev;
      });
    },
    []
  );

  const handleDataLoaded = useCallback((data: any) => {
    const nodeCount = data?.nodes?.length || 0;
    const edgeCount = data?.edges?.length || 0;
    setHasData(nodeCount > 0 || edgeCount > 0);
    setConnectionError(null); // Clear any previous errors on successful load

    if (data?.nodes && Array.isArray(data.nodes)) {
      const textNode = data.nodes.find((node: any) => node?.type === "Text");

      if (textNode) {
        const candidate =
          textNode?.properties?.ID ?? textNode?.properties?.id ?? textNode?.id;

        if (candidate) {
          setActiveTextId(String(candidate));
        }
      }
    }
  }, []);

  const handleGraphError = useCallback((error: Error) => {
    setConnectionError(error.message);
    setHasData(false);
  }, []);

  const triggerExport = useCallback(
    async (fileType: string, targetFileId: string) => {
      const option =
        exportOptions.find((item) => item.value === fileType) ||
        exportOptions[0];
      const endpoint = option?.endpoint ?? "/api/v1/export";
      const extension = (option?.extension ?? fileType ?? "flextext")
        .toString()
        .replace(/^\./, "");

      const resolvedFileType = option?.value || fileType;
      const query = new URLSearchParams({
        file_type: resolvedFileType,
      }).toString();
      const requestUrl = `${endpoint}${
        endpoint.includes("?") ? "&" : "?"
      }${query}`;

      const extractExportError = async (response: Response) => {
        const contentType = response.headers.get("content-type") ?? "";
        const rawText = await response.text();

        if (contentType.includes("application/json")) {
          try {
            const json = JSON.parse(rawText);
            if (json && typeof json === "object" && "detail" in json) {
              const detail = (json as { detail?: unknown }).detail;
              if (Array.isArray(detail)) {
                return detail
                  .map((item) =>
                    typeof item === "string"
                      ? item
                      : JSON.stringify(item, null, 2)
                  )
                  .join("\n");
              }
              if (detail) {
                return String(detail);
              }
            }
          } catch (error) {
            console.debug("Failed to parse export error JSON", error);
          }
        }

        if (rawText) {
          return rawText;
        }

        return "Export failed";
      };

      setIsExporting(true);

      try {
        const response = await fetch(requestUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ file_id: targetFileId }),
        });

        if (!response.ok) {
          const errorText = await extractExportError(response);
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
        showExportFeedback(
          "success",
          `Download started for ${filenameBase}.${extension}`
        );
      } catch (error) {
        const label = option?.label ?? "export file";
        console.error(`Error exporting ${label}:`, error);
        const message =
          error instanceof Error && error.message
            ? error.message
            : `Failed to export ${label}. Please try again.`;
        showExportFeedback("error", message);
      } finally {
        setIsExporting(false);
      }
    },
    [exportOptions, showExportFeedback]
  );

  const handleExportButtonClick = () => {
    const targetFileId = (activeTextId ?? "").trim();

    if (!targetFileId) {
      showExportFeedback(
        "error",
        "No text available for export. Please upload a file first."
      );
      return;
    }

    setIsExportModalOpen(true);
  };

  const handleExportConfirm = useCallback(async () => {
    const targetFileId = (activeTextId ?? "").trim();

    if (!targetFileId) {
      showExportFeedback(
        "error",
        "No text available for export. Please upload a file first."
      );
      setIsExportModalOpen(false);
      return;
    }

    await triggerExport(selectedExportType, targetFileId);
  }, [activeTextId, selectedExportType, triggerExport, showExportFeedback]);

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
      {exportFeedback ? (
        <div
          className={`absolute left-1/2 top-4 z-30 w-[min(90vw,28rem)] -translate-x-1/2 rounded-lg border px-4 py-3 text-sm shadow-lg transition-opacity ${
            exportFeedback.type === "success"
              ? "border-green-200 bg-green-50 text-green-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {exportFeedback.message}
        </div>
      ) : null}

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
      <div className="absolute top-4 right-4 z-20 flex flex-col space-y-2">
        <div className="flex space-x-2">
          {/* Export button */}
          <button
            onClick={handleExportButtonClick}
            disabled={isExporting}
            className="bg-stone-600 hover:bg-stone-700 text-white rounded-lg shadow-sm px-3 py-2 border border-stone-700 transition-colors flex items-center space-x-2 disabled:bg-stone-400 disabled:border-stone-400"
            title="Export current dataset"
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
            className="bg-white hover:bg-stone-50 rounded-lg shadow-sm p-2 border border-stone-200 transition-colors"
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
            className="bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-sm p-2 border border-red-600 transition-colors"
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
      </div>

      <GraphFilters
        initialLimit={DEFAULT_GRAPH_LIMIT}
        onFilterChange={handleFilterChange}
      />

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
          defaultEdgeColor: "#60a5faDD",
          defaultEdgeType: "line",
          minEdgeSize: 0.5,
          maxEdgeSize: 3,
          edgeColor: "#60a5faDD",
          labelSize: 10,
          labelWeight: "normal",
          labelColor: { color: "#44403c" },
          labelRenderedSizeThreshold: 12, // only show labels for larger / central nodes
          labelDensity: 0.2,
          labelGridCellSize: 100,
          enableEdgeEvents: true,
          allowInvalidContainer: true,
          zIndex: true,
        }}
      >
        <LoadGraph
          filters={graphFilters}
          onDataLoaded={handleDataLoaded}
          onError={handleGraphError}
        />
        <GraphEvents />
        {hasData && <ZoomControls />}
        {hasData && <GraphLegend />}
      </SigmaContainer>

      {/* Connection Error Overlay */}
      {connectionError && (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-50/95 z-10">
          <div className="text-center max-w-md px-6">
            <div className="mb-4 flex justify-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-stone-900 mb-2">
              Backend Connection Error
            </h3>
            <p className="text-sm text-stone-600 mb-4">{connectionError}</p>
            <p className="text-xs text-stone-500 mb-6">
              Please ensure the backend server is running and accessible. Check
              your environment configuration and try refreshing.
            </p>
            <button
              onClick={handleRefresh}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-stone-600 hover:bg-stone-700 rounded-md transition-colors"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {/* Empty State Overlay */}
      {hasData === false && !connectionError && (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-50/95 z-10">
          <div className="text-center max-w-md px-6">
            <div className="mb-4 flex justify-center">
              <div className="w-16 h-16 bg-stone-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-stone-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-stone-900 mb-2">
              No data loaded yet
            </h3>
            <p className="text-sm text-stone-600 mb-6">
              Upload a FLEx text file to start visualizing your linguistic
              network. Navigate to the upload page to import your corpus.
            </p>
            <a
              href="/upload"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-stone-600 hover:bg-stone-700 rounded-md transition-colors"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Import corpus
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
