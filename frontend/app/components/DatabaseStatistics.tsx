"use client";

import React, { useState, useEffect, useCallback } from "react";

interface DatabaseStats {
  text_count: number;
  section_count: number;
  phrase_count: number;
  word_count: number;
  morpheme_count: number;
  gloss_count: number;
  relationship_count?: number;
}

export default function DatabaseStatistics() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStats = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const response = await fetch("/api/v1/linguistic/stats");
      if (!response.ok) {
        throw new Error("Failed to fetch statistics");
      }
      const data = await response.json();
      setStats(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Error fetching stats:", err);
      setError(
        err instanceof Error ? err.message : "Failed to load statistics"
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();

    // Listen for database wipe events to refresh stats
    const handleDatabaseWiped = () => {
      fetchStats(true);
    };

    window.addEventListener("databaseWiped", handleDatabaseWiped);

    return () => {
      window.removeEventListener("databaseWiped", handleDatabaseWiped);
    };
  }, [fetchStats]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-stone-200 p-4">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-stone-700 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-stone-700">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-4">
        <div className="text-sm text-red-700">{error}</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const contentGroup = [
    { label: "Texts", value: stats.text_count },
    { label: "Sections", value: stats.section_count },
    { label: "Phrases", value: stats.phrase_count },
  ];

  const unitsGroup = [
    { label: "Words", value: stats.word_count },
    { label: "Morphemes", value: stats.morpheme_count },
    { label: "Glosses", value: stats.gloss_count },
  ];

  const structureGroup =
    stats.relationship_count !== undefined
      ? [
          {
            label: "Relationships",
            value: stats.relationship_count,
            tooltip: "Connections between linguistic units",
          },
        ]
      : [];

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-stone-200">
      {/* Header */}
      <div className="p-4 border-b border-stone-200">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-stone-950">
            Database overview
          </h3>
          <button
            onClick={() => fetchStats(true)}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-2 py-1 text-xs text-stone-600 hover:text-stone-900 hover:bg-stone-50 rounded transition-colors disabled:opacity-50"
            title="Sync statistics"
          >
            {isRefreshing ? (
              <div className="w-3 h-3 border-2 border-stone-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg
                className="w-3.5 h-3.5"
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
            )}
            <span className="text-xs">Sync</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-4 space-y-4">
        {/* Content Group */}
        <div>
          <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">
            Content
          </div>
          <div className="grid grid-cols-3 gap-2">
            {contentGroup.map((item) => (
              <div
                key={item.label}
                className="bg-stone-50 rounded-md p-2.5 border border-stone-100"
              >
                <div className="text-lg font-bold text-stone-900 leading-none mb-1">
                  {item.value.toLocaleString()}
                </div>
                <div className="text-xs text-stone-600">{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Units Group */}
        <div>
          <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">
            Units
          </div>
          <div className="grid grid-cols-3 gap-2">
            {unitsGroup.map((item) => (
              <div
                key={item.label}
                className="bg-stone-50 rounded-md p-2.5 border border-stone-100"
              >
                <div className="text-lg font-bold text-stone-900 leading-none mb-1">
                  {item.value.toLocaleString()}
                </div>
                <div className="text-xs text-stone-600">{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Structure Group */}
        {structureGroup.length > 0 && (
          <div>
            <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">
              Structure
            </div>
            <div className="grid grid-cols-3 gap-2">
              {structureGroup.map((item) => (
                <div
                  key={item.label}
                  className="bg-stone-50 rounded-md p-2.5 border border-stone-100 col-span-3"
                  title={item.tooltip}
                >
                  <div className="text-lg font-bold text-stone-900 leading-none mb-1">
                    {item.value.toLocaleString()}
                  </div>
                  <div className="text-xs text-stone-600">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      {lastUpdated && (
        <div className="px-4 py-2 border-t border-stone-200 bg-stone-50">
          <div className="text-xs text-stone-500 text-center">
            Last updated: {formatTime(lastUpdated)}
          </div>
        </div>
      )}
    </div>
  );
}
