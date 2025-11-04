"""Tests for the export FLEXText endpoint."""

import os
import sys
import xml.etree.ElementTree as ET
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient


# Ensure backend package is importable when running tests from repository root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from main import app  # noqa: E402  # isort:skip
from app.database import get_db_dependency  # noqa: E402  # isort:skip


class _StubSession:
    """Minimal stub for the Neo4j session used during testing."""

    def close(self) -> None:  # pragma: no cover - compatibility stub
        """Mirror the real session interface without performing any work."""


def _override_get_db():  # pragma: no cover - simple generator
    """Dependency override that yields a stub database session."""

    yield _StubSession()


def test_export_flextext_returns_valid_xml_attachment():
    """POST /api/v1/export/flextext should return an XML attachment."""

    app.dependency_overrides[get_db_dependency] = _override_get_db

    fake_graph = {"text": {"id": "text-123"}, "sections": []}
    fake_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<interlinear-text><paragraphs /></interlinear-text>"
    )

    with patch("app.routers.export.get_file_graph_data", return_value=fake_graph) as mocked_graph, patch(
        "app.routers.export.generate_flextext_xml", return_value=fake_xml
    ) as mocked_xml:
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/export/flextext",
                json={"file_id": "test-dataset"},
            )
        finally:
            app.dependency_overrides.pop(get_db_dependency, None)

    mocked_graph.assert_called_once_with("test-dataset", ANY)
    mocked_xml.assert_called_once_with(fake_graph)

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/xml")

    content_disposition = response.headers.get("content-disposition")
    assert content_disposition is not None
    assert "export.flextext" in content_disposition

    # Ensure payload is well-formed XML
    ET.fromstring(response.content)

