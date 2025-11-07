"""Base protocol and exceptions for exporter implementations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Exporter(Protocol):
    """Exporter interface for generating serialized output."""

    file_type: str
    media_type: str
    file_extension: str

    def export(self, graph_data: dict) -> str:
        """Return a serialized representation of graph_data."""


class ExporterNotFoundError(LookupError):
    """Raised when no exporter is registered for the requested file type."""


