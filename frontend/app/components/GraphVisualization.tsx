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

// Sample data generator for demonstration
function generateSampleGraph() {
  const graph = new MultiDirectedGraph();

  // Add nodes with different types
  const nodes = [
    { id: "word1", label: "lexeme", type: "word", size: 15, color: "#0ea5e9" },
    {
      id: "word2",
      label: "morpheme",
      type: "word",
      size: 12,
      color: "#0ea5e9",
    },
    { id: "word3", label: "phoneme", type: "word", size: 14, color: "#0ea5e9" },
    {
      id: "phrase1",
      label: "noun phrase",
      type: "phrase",
      size: 18,
      color: "#8b5cf6",
    },
    {
      id: "phrase2",
      label: "verb phrase",
      type: "phrase",
      size: 16,
      color: "#8b5cf6",
    },
    {
      id: "gloss1",
      label: "meaning",
      type: "gloss",
      size: 10,
      color: "#10b981",
    },
    {
      id: "gloss2",
      label: "definition",
      type: "gloss",
      size: 10,
      color: "#10b981",
    },
    {
      id: "lang1",
      label: "English",
      type: "language",
      size: 20,
      color: "#f59e0b",
    },
    {
      id: "lang2",
      label: "Spanish",
      type: "language",
      size: 20,
      color: "#f59e0b",
    },
  ];

  nodes.forEach((node) => {
    graph.addNode(node.id, {
      label: node.label,
      size: node.size,
      color: node.color,
      x: Math.random() * 100,
      y: Math.random() * 100,
    });
  });

  // Add edges
  const edges = [
    { source: "word1", target: "phrase1" },
    { source: "word2", target: "phrase1" },
    { source: "word3", target: "phrase2" },
    { source: "phrase1", target: "gloss1" },
    { source: "phrase2", target: "gloss2" },
    { source: "word1", target: "lang1" },
    { source: "word2", target: "lang1" },
    { source: "word3", target: "lang2" },
    { source: "gloss1", target: "lang1" },
    { source: "gloss2", target: "lang2" },
  ];

  edges.forEach((edge, i) => {
    graph.addEdge(edge.source, edge.target, {
      size: 2,
      color: "#94a3b8",
    });
  });

  return graph;
}

function LoadGraph() {
  const loadGraph = useLoadGraph();

  useEffect(() => {
    const graph = generateSampleGraph();
    loadGraph(graph);
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
      },
    });
  }, [registerEvents, sigma]);

  return (
    <>
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-200 dark:border-slate-700 z-10">
          <div className="text-sm font-semibold text-slate-900 dark:text-white">
            {sigma.getGraph().getNodeAttribute(hoveredNode, "label")}
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            Node ID: {hoveredNode}
          </div>
        </div>
      )}
    </>
  );
}

export default function GraphVisualization() {
  return (
    <div className="w-full h-full relative">
      <SigmaContainer
        style={{ height: "100%", width: "100%" }}
        settings={{
          renderEdgeLabels: false,
          defaultNodeColor: "#0ea5e9",
          defaultEdgeColor: "#94a3b8",
          labelSize: 12,
          labelWeight: "bold",
          labelColor: { color: "#1e293b" },
          enableEdgeEvents: true,
        }}
      >
        <LoadGraph />
        <GraphEvents />
      </SigmaContainer>
    </div>
  );
}
