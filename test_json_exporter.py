"""Tests for the JSON exporter."""

import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.exporters.json_exporter import JsonExporter  # noqa: E402


def _sample_graph_data():
    return {
        "text": {
            "id": "text-1",
            "title": "Sample",
            "source": "Field Notes",
            "comment": "",
            "language_code": "eng",
        },
        "sections": [
            {
                "id": "section-1",
                "order": 2,
                "phrases": [
                    {
                        "id": "phrase-1",
                        "order": 1,
                        "segnum": "1",
                        "surface_text": "hello world",
                        "language": "eng",
                        "words": [
                            {
                                "id": "word-1",
                                "order": 0,
                                "surface_form": "hello",
                                "gloss": "HELLO",
                                "pos": "INTJ",
                                "language": "eng",
                                "is_punctuation": False,
                                "morphemes": [
                                    {
                                        "id": "morph-1",
                                        "order": 0,
                                        "type": "stem",
                                        "surface_form": "hello",
                                        "citation_form": "hello",
                                        "gloss": "HELLO",
                                        "msa": "intj",
                                        "language": "eng",
                                    }
                                ],
                            },
                            {
                                "id": "word-2",
                                "order": 1,
                                "surface_form": ".",
                                "gloss": "",
                                "pos": None,
                                "language": "eng",
                                "is_punctuation": True,
                                "morphemes": [],
                            },
                        ],
                    }
                ],
            }
        ],
    }


def test_json_exporter_serializes_nested_structure():
    exporter = JsonExporter()
    graph_data = {"texts": [_sample_graph_data()]}

    payload = exporter.export(graph_data)
    parsed = json.loads(payload)

    assert "exported_at" in parsed
    assert len(parsed["texts"]) == 1

    text = parsed["texts"][0]
    assert text["id"] == "text-1"
    assert text["language_code"] == "eng"

    section = text["sections"][0]
    assert section["order"] == 2

    phrase = section["phrases"][0]
    assert phrase["segnum"] == "1"

    word = phrase["words"][0]
    assert word["surface_form"] == "hello"
    assert word["is_punctuation"] is False

    morph = word["morphemes"][0]
    assert morph["type"] == "stem"

