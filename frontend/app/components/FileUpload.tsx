"use client";

import { useState, useCallback } from "react";

interface FileUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: string) => void;
}

export default function FileUpload({
  onUploadSuccess,
  onUploadError,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [statusMessage, setStatusMessage] = useState("");

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith(".flextext")) {
        setSelectedFile(file);
        setUploadStatus("idle");
      } else {
        setUploadStatus("error");
        setStatusMessage("Please upload a .flextext file");
      }
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (file.name.endsWith(".flextext")) {
          setSelectedFile(file);
          setUploadStatus("idle");
        } else {
          setUploadStatus("error");
          setStatusMessage("Please upload a .flextext file");
        }
      }
    },
    []
  );

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus("idle");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch("/api/v1/linguistic/upload-flextext", {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      setUploadStatus("success");
      setStatusMessage("File uploaded successfully!");
      onUploadSuccess?.(data);

      // Reset after 3 seconds
      setTimeout(() => {
        setSelectedFile(null);
        setUploadStatus("idle");
        setUploadProgress(0);
      }, 3000);
    } catch (error) {
      setUploadStatus("error");
      setStatusMessage("Upload failed. Please try again.");
      onUploadError?.(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadStatus("idle");
    setStatusMessage("");
    setUploadProgress(0);
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
          isDragging
            ? "border-stone-400 bg-stone-50"
            : "border-stone-300 bg-white"
        } ${selectedFile ? "pb-4" : ""}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <div className="mx-auto w-16 h-16 mb-4 bg-stone-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-stone-700"
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

          <h3 className="text-lg font-semibold text-stone-950 mb-2">
            Upload FLEx Text File
          </h3>
          <p className="text-sm text-stone-700 mb-4">
            Drag and drop your .flextext file here, or click to browse
          </p>

          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-stone-800 hover:bg-stone-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-stone-500 transition-colors">
              Select File
            </span>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".flextext"
              onChange={handleFileSelect}
            />
          </label>
        </div>

        {selectedFile && (
          <div className="mt-6 pt-6 border-t border-stone-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <div className="w-10 h-10 bg-stone-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-5 h-5 text-stone-700"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-stone-950 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-stone-700">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="ml-4 p-2 text-stone-400 hover:text-stone-700 transition-colors"
                disabled={isUploading}
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
                  <path d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {isUploading && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-stone-700">
                    Uploading...
                  </span>
                  <span className="text-xs text-stone-700">
                    {uploadProgress}%
                  </span>
                </div>
                <div className="w-full bg-stone-200 rounded-full h-2">
                  <div
                    className="bg-stone-800 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {uploadStatus === "success" && (
              <div className="mb-4 p-3 bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm text-green-800 dark:text-green-200 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                  {statusMessage}
                </p>
              </div>
            )}

            {uploadStatus === "error" && (
              <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-200 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {statusMessage}
                </p>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={isUploading || uploadStatus === "success"}
              className="w-full py-2 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-stone-800 hover:bg-stone-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-stone-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isUploading
                ? "Uploading..."
                : uploadStatus === "success"
                ? "Uploaded!"
                : "Upload File"}
            </button>
          </div>
        )}
      </div>

      <div className="mt-4 text-xs text-stone-700">
        <p>Supported file format: .flextext</p>
        <p className="mt-1">Maximum file size: 10MB</p>
      </div>
    </div>
  );
}
