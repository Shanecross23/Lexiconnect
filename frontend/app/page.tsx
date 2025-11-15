"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import SearchBar from "./components/SearchBar";
import DatabaseStatistics from "./components/DatabaseStatistics";

// Dynamically import the graph component to avoid SSR issues with Sigma.js
const GraphVisualization = dynamic(
  () => import("./components/GraphVisualization"),
  { ssr: false }
);

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-stone-950 mb-1.5">
            Linguistic Network Visualization
          </h1>
          <p className="text-sm text-stone-600">
            Search morphemes and words, then explore their connections in the graph.
          </p>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[2fr,1fr] gap-6 mb-6">
          {/* Left Column: Search and Graph */}
          <div className="space-y-4">
            {/* Search Toolbar */}
            <SearchBar />

            {/* Graph Card */}
            <div className="bg-white rounded-lg shadow-sm border border-stone-200 overflow-hidden">
              <div className="relative w-full bg-stone-50" style={{ height: "calc(100vh - 280px)", minHeight: "500px" }}>
                {mounted ? (
                  <GraphVisualization />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-stone-700 rounded-full animate-bounce"></div>
                      <div
                        className="w-4 h-4 bg-stone-700 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-4 h-4 bg-stone-700 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              {/* Interaction hint footer */}
              <div className="px-4 py-2 border-t border-stone-200 bg-white">
                <div className="flex items-center justify-center">
                  <span className="text-xs text-stone-500">
                    Drag to pan • Scroll to zoom • Click nodes to interact
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Database Statistics */}
          <div className="lg:sticky lg:top-6 h-fit">
            <DatabaseStatistics />
          </div>
        </div>
      </div>
    </div>
  );
}
