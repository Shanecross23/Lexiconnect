"use client";

import { useState, useEffect } from "react";

interface FilterOptions {
  texts: Array<{ id: string; title: string; language: string }>;
  languages: string[];
  node_types: string[];
}

interface GraphFiltersProps {
  onFilterChange: (filters: {
    textId?: string;
    language?: string;
    nodeTypes?: string[];
    limit?: number;
  }) => void;
}

export default function GraphFilters({ onFilterChange }: GraphFiltersProps) {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(
    null
  );
  const [selectedText, setSelectedText] = useState<string>("");
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<Set<string>>(
    new Set()
  );
  const [limit, setLimit] = useState<number>(50);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await fetch("/api/v1/linguistic/graph-filters");
      if (response.ok) {
        const data = await response.json();
        setFilterOptions(data);
      }
    } catch (error) {
      console.error("Error fetching filter options:", error);
    }
  };

  const handleApplyFilters = () => {
    onFilterChange({
      textId: selectedText || undefined,
      language: selectedLanguage || undefined,
      nodeTypes:
        selectedNodeTypes.size > 0 ? Array.from(selectedNodeTypes) : undefined,
      limit,
    });
  };

  const handleResetFilters = () => {
    setSelectedText("");
    setSelectedLanguage("");
    setSelectedNodeTypes(new Set());
    setLimit(50);
    onFilterChange({ limit: 50 });
  };

  const toggleNodeType = (nodeType: string) => {
    const newSet = new Set(selectedNodeTypes);
    if (newSet.has(nodeType)) {
      newSet.delete(nodeType);
    } else {
      newSet.add(nodeType);
    }
    setSelectedNodeTypes(newSet);
  };

  if (!filterOptions) return null;

  return (
    <div className="absolute top-20 right-4 z-20 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 text-left font-medium text-slate-900 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg transition-colors flex items-center justify-between"
      >
        <span className="flex items-center">
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          Filters
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 space-y-4 border-t border-slate-200 dark:border-slate-700 min-w-[300px]">
          {/* Text Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Specific Text
            </label>
            <select
              value={selectedText}
              onChange={(e) => setSelectedText(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Texts</option>
              {filterOptions.texts.map((text) => (
                <option key={text.id} value={text.id}>
                  {text.title} ({text.language || "unknown"})
                </option>
              ))}
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Language
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Languages</option>
              {filterOptions.languages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
          </div>

          {/* Node Types */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
              Node Types
            </label>
            <div className="space-y-1">
              {filterOptions.node_types.map((nodeType) => (
                <label
                  key={nodeType}
                  className="flex items-center cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedNodeTypes.has(nodeType)}
                    onChange={() => toggleNodeType(nodeType)}
                    className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                    {nodeType}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Limit */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Max Nodes: {limit}
            </label>
            <input
              type="range"
              min="10"
              max="1000"
              step="10"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700"
            />
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>10</span>
              <span>1000</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2 pt-2 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={handleApplyFilters}
              className="flex-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
            >
              Apply
            </button>
            <button
              onClick={handleResetFilters}
              className="flex-1 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-md transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
