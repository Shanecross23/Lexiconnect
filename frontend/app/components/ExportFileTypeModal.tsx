"use client";

import { Fragment } from "react";

export interface ExportOption {
  value: string;
  label: string;
  description?: string;
  extension?: string;
  endpoint?: string;
  disabled?: boolean;
  note?: string;
}

interface ExportFileTypeModalProps {
  isOpen: boolean;
  options: ExportOption[];
  selectedType: string;
  onSelect: (value: string) => void;
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting?: boolean;
}

export default function ExportFileTypeModal({
  isOpen,
  options,
  selectedType,
  onSelect,
  onCancel,
  onConfirm,
  isSubmitting = false,
}: ExportFileTypeModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-modal-title"
        className="w-full max-w-md rounded-xl border border-stone-200 bg-white shadow-2xl"
      >
        <div className="border-b border-stone-200 px-6 py-4">
          <h2
            id="export-modal-title"
            className="text-lg font-semibold text-stone-950"
          >
            Choose export format
          </h2>
          <p className="mt-1 text-sm text-stone-600">
            Select the file type you would like to download. Additional formats
            will be available soon.
          </p>
        </div>

        <div className="max-h-[22rem] space-y-3 overflow-y-auto px-6 py-4">
          {options.map((option) => {
            const isSelected = option.value === selectedType;
            const isDisabled = Boolean(option.disabled);

            return (
              <Fragment key={option.value}>
                <button
                  type="button"
                  onClick={() => {
                    if (!isDisabled) {
                      onSelect(option.value);
                    }
                  }}
                  className={`w-full rounded-lg border px-4 py-3 text-left transition-colors ${
                    isSelected
                      ? "border-blue-500 bg-blue-50"
                      : "border-stone-200 hover:border-blue-400"
                  } ${isDisabled ? "cursor-not-allowed opacity-60" : ""}`}
                  aria-pressed={isSelected}
                  aria-disabled={isDisabled}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-stone-900">
                        {option.label}
                      </div>
                      {option.description ? (
                        <div className="mt-1 text-xs text-stone-600">
                          {option.description}
                        </div>
                      ) : null}
                    </div>
                    <div
                      className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                        isSelected
                          ? "border-blue-500 bg-blue-500"
                          : "border-stone-300"
                      }`}
                    >
                      <div className="h-2.5 w-2.5 rounded-full bg-white" />
                    </div>
                  </div>
                  {option.note ? (
                    <div className="mt-3 rounded-md bg-blue-50 px-3 py-2 text-xs text-blue-700">
                      {option.note}
                    </div>
                  ) : null}
                </button>
              </Fragment>
            );
          })}
        </div>

        <div className="flex items-center justify-end space-x-3 border-t border-stone-200 px-6 py-4">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-100"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting || !selectedType}
            className="inline-flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
          >
            {isSubmitting ? (
              <>
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Preparing...</span>
              </>
            ) : (
              <span>Download</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}


