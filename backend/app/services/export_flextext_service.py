"""Utilities for converting graph-structured linguistic data into FLEXText XML."""

from __future__ import annotations

from typing import Any, Dict

from app.exporters.flextext_exporter import FlextextExporter, GraphDict


def generate_flextext_xml(graph_data: GraphDict) -> str:
    """Transform graph data into FLEXText XML."""

    exporter = FlextextExporter()
    return exporter.export(graph_data)


