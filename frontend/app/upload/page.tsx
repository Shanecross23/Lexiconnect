"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import FileUpload from "../components/FileUpload";
import CorpusStatistics from "../components/CorpusStatistics";

export default function UploadPage() {
  const router = useRouter();
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [uploadStats, setUploadStats] = useState<any>(null);

  const handleUploadSuccess = (data: any) => {
    setUploadedFiles((prev) => [...prev, data]);
    setShowSuccess(true);
    setUploadStats(data.file_stats || null);
    setTimeout(() => setShowSuccess(false), 5000);
  };

  const handleUploadError = (error: string) => {
    console.error("Upload error:", error);
  };

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-stone-950 mb-2">
            Upload FLEx Text Files
          </h1>
          <p className="text-lg text-stone-950">
            Import your linguistic data for visualization and analysis
          </p>
        </div>

        {/* Success Banner */}
        {showSuccess && (
          <div className="mb-6 p-4 bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg animate-fade-in">
            <div className="flex items-center">
              <svg
                className="w-6 h-6 text-green-600 dark:text-green-400 mr-3"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  File uploaded successfully!
                </p>
                <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                  Your file has been processed and is ready for visualization.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 border border-stone-200 mb-8">
          <FileUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </div>

        {/* Statistics Visualization */}
        {uploadStats && (
          <div className="bg-white rounded-xl shadow-lg p-8 border border-stone-200 mb-8">
            <CorpusStatistics stats={uploadStats} />
          </div>
        )}

        {/* Information Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-stone-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-stone-700"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-stone-950">
                About FLEx Files
              </h3>
            </div>
            <p className="text-sm text-stone-950">
              FLEx (FieldWorks Language Explorer) text files contain rich
              linguistic data including morphological analysis, glosses, and
              translations. Our platform parses these files to create
              interactive visualizations of linguistic relationships.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-stone-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-stone-700"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-stone-950">
                What Happens Next
              </h3>
            </div>
            <ul className="space-y-2 text-sm text-stone-950">
              <li className="flex items-start">
                <span className="text-stone-700 mr-2">•</span>
                File is parsed and validated
              </li>
              <li className="flex items-start">
                <span className="text-stone-700 mr-2">•</span>
                Data is stored in the graph database
              </li>
              <li className="flex items-start">
                <span className="text-stone-700 mr-2">•</span>
                Relationships are automatically mapped
              </li>
              <li className="flex items-start">
                <span className="text-stone-700 mr-2">•</span>
                Ready for interactive visualization
              </li>
            </ul>
          </div>
        </div>

        {/* Recent Uploads */}
        {uploadedFiles.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-stone-200">
            <h2 className="text-xl font-semibold text-stone-950 mb-4">
              Recent Uploads
            </h2>
            <div className="space-y-3">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-stone-50 rounded-lg border border-stone-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-green-600 dark:text-green-400"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-950">
                        Upload #{uploadedFiles.length - index}
                      </p>
                      <p className="text-xs text-stone-700">
                        {new Date().toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => router.push("/")}
                    className="text-stone-700 text-sm font-medium hover:text-stone-900 transition-colors"
                  >
                    View
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Links */}
        <div className="mt-8 flex items-center justify-center space-x-4">
          <a
            href="/"
            className="inline-flex items-center px-4 py-2 border border-stone-300 rounded-lg text-sm font-medium text-stone-950 bg-white hover:bg-stone-50 transition-colors"
          >
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Visualization
          </a>
        </div>
      </div>
    </div>
  );
}
