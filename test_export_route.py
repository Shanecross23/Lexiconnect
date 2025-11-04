"""Tests for the export endpoints."""

import json
import os
import sys
import xml.etree.ElementTree as ET
from unittest.mock import ANY, MagicMock, patch

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

    fake_graphs = [{"text": {"id": "text-123"}, "sections": []}]
    fake_payload = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<interlinear-text><paragraphs /></interlinear-text>"
    )

    stub_exporter = MagicMock()
    stub_exporter.file_type = "flextext"
    stub_exporter.media_type = "application/xml"
    stub_exporter.file_extension = "flextext"
    stub_exporter.export.return_value = fake_payload

    with patch(
        "app.routers.export.get_all_texts_graph_data",
        return_value=fake_graphs,
    ) as mocked_graphs, patch(
        "app.routers.export.get_exporter", return_value=stub_exporter
    ) as mocked_get_exporter:
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/export",
                params={"file_type": "flextext"},
                json={"file_id": "test-dataset"},
            )
        finally:
            app.dependency_overrides.pop(get_db_dependency, None)

    mocked_get_exporter.assert_called_once_with("flextext")
    mocked_graphs.assert_called_once_with(ANY)
    stub_exporter.export.assert_called_once_with({"texts": fake_graphs})

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/xml")

    content_disposition = response.headers.get("content-disposition")
    assert content_disposition is not None
    assert "test-dataset.flextext" in content_disposition

    # Ensure payload is well-formed XML
    ET.fromstring(response.content)


def test_export_json_returns_valid_attachment():
    app.dependency_overrides[get_db_dependency] = _override_get_db

    fake_graphs = [{"text": {"id": "text-123"}, "sections": []}]
    fake_payload = "{\"texts\": []}"

    stub_exporter = MagicMock()
    stub_exporter.file_type = "json"
    stub_exporter.media_type = "application/json"
    stub_exporter.file_extension = "json"
    stub_exporter.export.return_value = fake_payload

    with patch(
        "app.routers.export.get_all_texts_graph_data",
        return_value=fake_graphs,
    ) as mocked_graphs, patch(
        "app.routers.export.get_exporter",
        return_value=stub_exporter,
    ) as mocked_get_exporter:
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/export",
                params={"file_type": "json"},
                json={"file_id": "dataset"},
            )
        finally:
            app.dependency_overrides.pop(get_db_dependency, None)

    mocked_get_exporter.assert_called_once_with("json")
    mocked_graphs.assert_called_once_with(ANY)
    stub_exporter.export.assert_called_once_with({"texts": fake_graphs})

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")
    assert "dataset.json" in response.headers.get("content-disposition", "")
    assert response.json() == json.loads(fake_payload)

