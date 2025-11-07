"""Tests for the Neo4j export data retrieval service."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterable


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.neo4j_service import (  # noqa: E402
    Neo4jExportDataError,
    get_file_graph_data,
)


class _FakeResult:
    def __init__(self, records: Iterable[Dict[str, Any]]):
        self._records = list(records)

    def single(self):
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _FakeSession:
    def __init__(self):
        self.last_query = None
        self.last_params = None

    def run(self, query: str, **params):
        self.last_query = query
        self.last_params = params

        if "SECTION_PART_OF_TEXT" in query:
            return _FakeResult(
                [
                    {"id": "section-2", "order": 2},
                    {"id": "section-1", "order": 1},
                ]
            )

        if "PHRASE_IN_SECTION" in query:
            return _FakeResult(
                [
                    {
                        "section_id": "section-1",
                        "id": "phrase-1",
                        "segnum": "1",
                        "surface_text": "hello world",
                        "language": "eng",
                        "order": 1,
                    },
                    {
                        "section_id": "section-2",
                        "id": "phrase-2",
                        "segnum": "2",
                        "surface_text": "second phrase",
                        "language": None,
                        "order": 5,
                    },
                ]
            )

        if "PHRASE_COMPOSED_OF" in query:
            return _FakeResult(
                [
                    {
                        "phrase_id": "phrase-1",
                        "word_id": "word-1",
                        "word_order": 2,
                        "word_surface_form": "hello",
                        "word_gloss": "HEL",
                        "word_pos": "N",
                        "word_language": "eng",
                        "morph_id": "morph-1",
                        "morph_order": 1,
                        "morph_type": "stem",
                        "morph_surface_form": "hello",
                        "morph_citation_form": "hello",
                        "morph_gloss": "HEL",
                        "morph_msa": "n",
                        "morph_language": "eng",
                    },
                    {
                        "phrase_id": "phrase-1",
                        "word_id": "word-2",
                        "word_order": 3,
                        "word_surface_form": ".",
                        "word_gloss": None,
                        "word_pos": "PUNCT",
                        "word_language": None,
                        "morph_id": None,
                        "morph_order": None,
                        "morph_type": None,
                        "morph_surface_form": None,
                        "morph_citation_form": None,
                        "morph_gloss": None,
                        "morph_msa": None,
                        "morph_language": None,
                    },
                    {
                        "phrase_id": "phrase-2",
                        "word_id": "word-3",
                        "word_order": 1,
                        "word_surface_form": "goodbye",
                        "word_gloss": "BYE",
                        "word_pos": "V",
                        "word_language": None,
                        "morph_id": "morph-2",
                        "morph_order": 1,
                        "morph_type": "stem",
                        "morph_surface_form": "good",
                        "morph_citation_form": "good",
                        "morph_gloss": "GOOD",
                        "morph_msa": "v",
                        "morph_language": "eng",
                    },
                ]
            )

        if "RETURN t.ID AS id" in query:
            return _FakeResult(
                [
                    {
                        "id": params["text_id"],
                        "title": "Sample Text",
                        "source": "Field Notes",
                        "comment": "Test dataset",
                        "language_code": "eng",
                    }
                ]
            )

        raise AssertionError(f"Unexpected query dispatched: {query}")


def test_get_file_graph_data_returns_nested_structure():
    session = _FakeSession()
    graph = get_file_graph_data("text-123", session)

    assert graph["text"]["id"] == "text-123"
    assert graph["text"]["language_code"] == "eng"

    sections = graph["sections"]
    assert [section["id"] for section in sections] == ["section-1", "section-2"]

    first_section = sections[0]
    assert len(first_section["phrases"]) == 1
    phrase = first_section["phrases"][0]
    assert phrase["id"] == "phrase-1"
    assert phrase["language"] == "eng"

    words = phrase["words"]
    assert [word["id"] for word in words] == ["word-1", "word-2"]
    assert words[1]["is_punctuation"] is True
    assert words[1]["surface_form"] == "."

    morphemes = words[0]["morphemes"]
    assert len(morphemes) == 1
    assert morphemes[0]["gloss"] == "HEL"


def test_get_file_graph_data_raises_when_text_missing():
    class _EmptySession(_FakeSession):
        def run(self, query: str, **params):
            query_key = query.strip().split("\n", 1)[0]
            if query_key.startswith("MATCH (t:Text"):
                return _FakeResult([])
            return super().run(query, **params)

    session = _EmptySession()

    try:
        get_file_graph_data("missing", session)
    except Neo4jExportDataError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected Neo4jExportDataError to be raised")


