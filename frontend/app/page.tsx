"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
            Linguistic Network Visualization
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300">
            Explore and interact with linguistic connections and relationships
          </p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden border border-slate-200 dark:border-slate-700">
          <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Interactive Graph
              </h2>
              <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400">
                <span>
                  Drag to pan • Scroll to zoom • Click nodes to interact
                </span>
              </div>
            </div>
          </div>

          <div className="relative" style={{ height: "calc(100vh - 300px)" }}>
            {mounted ? (
              <GraphVisualization />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-slate-800 rounded-full animate-bounce"></div>
                  <div
                    className="w-4 h-4 bg-slate-800 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-4 h-4 bg-slate-800 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-slate-700 dark:text-slate-200"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Fast & Interactive
              </h3>
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm">
              Powered by Sigma.js for smooth, real-time visualization of complex
              linguistic networks
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-slate-700 dark:text-slate-200"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Easy Upload
              </h3>
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm">
              Upload FLEx text files directly and visualize your linguistic data
              instantly
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-slate-700 dark:text-slate-200"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Rich Insights
              </h3>
            </div>
            <p className="text-slate-600 dark:text-slate-300 text-sm">
              Discover connections and patterns in your linguistic data through
              interactive exploration
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
