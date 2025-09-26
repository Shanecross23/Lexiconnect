"use client";

import { useState, useCallback } from "react";
import {
  DocumentTextIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import axios from "axios";
import toast from "react-hot-toast";

interface UploadStats {
  total_texts: number;
  total_paragraphs: number;
  total_phrases: number;
  total_words: number;
  total_morphemes: number;
  languages: string[];
  pos_tags: string[];
  morpheme_types: { [key: string]: number };
}

interface UploadResponse {
  message: string;
  file_stats: UploadStats;
  processed_texts: string[];
}

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [uploadStats, setUploadStats] = useState<UploadStats | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const flexFile = files.find(
      (file) => file.name.endsWith(".flextext") || file.name.endsWith(".xml")
    );

    if (flexFile) {
      setSelectedFile(flexFile);
    } else {
      toast.error("Please select a valid FLEx file (.flextext or .xml)");
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setSelectedFile(file);
      }
    },
    []
  );

  const uploadFile = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadComplete(false);
    setUploadStats(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post<UploadResponse>(
        `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        }/api/v1/linguistic/upload-flextext`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setUploadStats(response.data.file_stats);
      setUploadComplete(true);
      toast.success("File uploaded and processed successfully!");
    } catch (error: any) {
      console.error("Upload error:", error);
      const errorMessage =
        error.response?.data?.detail || "Failed to upload file";
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadComplete(false);
    setUploadStats(null);
    setIsUploading(false);
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="text-center mb-6">
        {/* <DocumentTextIcon className="mx-auto h-12 w-12 text-primary-600" /> */}
        <h2 className="mt-2 text-lg font-medium text-gray-900">
          Upload FLEx Data
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Upload your .flextext files to start analyzing linguistic data
        </p>
      </div>

      {!uploadComplete ? (
        <div className="space-y-4">
          {/* File Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
              isDragging
                ? "border-primary-400 bg-primary-50"
                : "border-gray-300 hover:border-gray-400"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="text-center">
              <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    {selectedFile
                      ? selectedFile.name
                      : "Drop your FLEx file here, or click to browse"}
                  </span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".flextext,.xml"
                    onChange={handleFileSelect}
                  />
                </label>
                <p className="mt-1 text-sm text-gray-500">
                  Supports .flextext and .xml files up to 50MB
                </p>
              </div>
            </div>
          </div>

          {/* Selected File Info */}
          {selectedFile && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {/* <DocumentTextIcon className="h-8 w-8 text-primary-600" /> */}
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={resetUpload}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Remove
                </button>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={uploadFile}
            disabled={!selectedFile || isUploading}
            className={`w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${
              !selectedFile || isUploading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-primary-600 hover:bg-primary-700"
            }`}
          >
            {isUploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Processing...
              </>
            ) : (
              <>
                <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                Upload File
              </>
            )}
          </button>
        </div>
      ) : (
        /* Upload Success */
        <div className="text-center space-y-4">
          <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500" />
          <h3 className="text-lg font-medium text-gray-900">
            Upload Complete!
          </h3>

          {uploadStats && (
            <div className="bg-green-50 rounded-lg p-4 text-left">
              <h4 className="font-medium text-green-900 mb-3">
                File Statistics
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-700">Texts:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.total_texts}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Paragraphs:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.total_paragraphs}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Phrases:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.total_phrases}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Words:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.total_words}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Morphemes:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.total_morphemes}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Languages:</span>
                  <span className="ml-2 font-medium">
                    {uploadStats.languages.length}
                  </span>
                </div>
              </div>

              {uploadStats.languages.length > 0 && (
                <div className="mt-3">
                  <span className="text-green-700 text-sm">
                    Languages detected:
                  </span>
                  <div className="mt-1">
                    {uploadStats.languages.map((lang, index) => (
                      <span
                        key={index}
                        className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded mr-1 mb-1"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            onClick={resetUpload}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Upload Another File
          </button>
        </div>
      )}
    </div>
  );
}
