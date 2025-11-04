"""Exporter registry for serializing Lexiconnect data to external formats."""

from __future__ import annotations

from typing import Dict

from .base import Exporter, ExporterNotFoundError
from .flextext_exporter import FlextextExporter


_exporters: Dict[str, Exporter] = {}


def register_exporter(exporter: Exporter) -> None:
    """Register an exporter implementation by its file type."""

    key = exporter.file_type.lower()
    _exporters[key] = exporter


def get_exporter(file_type: str) -> Exporter:
    """Retrieve a registered exporter for the requested file type."""

    key = (file_type or "").strip().lower()
    if not key:
        raise ExporterNotFoundError("file_type must be provided")

    try:
        return _exporters[key]
    except KeyError as exc:
        raise ExporterNotFoundError(f"Unsupported export file_type '{file_type}'") from exc


register_exporter(FlextextExporter())


__all__ = [
    "Exporter",
    "ExporterNotFoundError",
    "register_exporter",
    "get_exporter",
]
