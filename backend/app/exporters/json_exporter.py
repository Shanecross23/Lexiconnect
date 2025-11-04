"""Exporter that serializes graph data into JSON matching the DB schema."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

GraphDict = Dict[str, Any]


def _sorted_sections(sections: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(sections, key=lambda s: (s.get("order", 0), s.get("id", "")))


def _sorted_phrases(phrases: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(phrases, key=lambda p: (p.get("order", 0), p.get("id", "")))


def _sorted_words(words: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(words, key=lambda w: (w.get("order", 0), w.get("id", "")))


def _sorted_morphemes(morphemes: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(morphemes, key=lambda m: (m.get("order", 0), m.get("id", "")))


def _serialize_morpheme(morpheme: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": morpheme.get("id"),
        "original_guid": morpheme.get("original_id"),
        "order": morpheme.get("order", 0),
        "type": morpheme.get("type"),
        "surface_form": morpheme.get("surface_form"),
        "citation_form": morpheme.get("citation_form"),
        "gloss": morpheme.get("gloss"),
        "msa": morpheme.get("msa"),
        "language": morpheme.get("language"),
    }


def _serialize_word(word: Dict[str, Any]) -> Dict[str, Any]:
    morphemes = word.get("morphemes", []) or []
    return {
        "id": word.get("id"),
        "order": word.get("order", 0),
        "surface_form": word.get("surface_form"),
        "gloss": word.get("gloss"),
        "pos": word.get("pos"),
        "language": word.get("language"),
        "is_punctuation": bool(word.get("is_punctuation")),
        "morphemes": [_serialize_morpheme(m) for m in _sorted_morphemes(morphemes)],
    }


def _serialize_phrase(phrase: Dict[str, Any]) -> Dict[str, Any]:
    words = phrase.get("words", []) or []
    return {
        "id": phrase.get("id"),
        "order": phrase.get("order", 0),
        "segnum": phrase.get("segnum"),
        "surface_text": phrase.get("surface_text"),
        "language": phrase.get("language"),
        "words": [_serialize_word(word) for word in _sorted_words(words)],
    }


def _serialize_section(section: Dict[str, Any]) -> Dict[str, Any]:
    phrases = section.get("phrases", []) or []
    return {
        "id": section.get("id"),
        "order": section.get("order", 0),
        "phrases": [_serialize_phrase(phrase) for phrase in _sorted_phrases(phrases)],
    }


def _serialize_text(graph: GraphDict) -> Dict[str, Any]:
    text_info = graph.get("text", {}) or {}
    sections = graph.get("sections", []) or []
    return {
        "id": text_info.get("id"),
        "title": text_info.get("title"),
        "source": text_info.get("source"),
        "comment": text_info.get("comment"),
        "language_code": text_info.get("language_code"),
        "sections": [_serialize_section(section) for section in _sorted_sections(sections)],
    }


class JsonExporter:
    """Exporter implementation for JSON output."""

    file_type = "json"
    media_type = "application/json"
    file_extension = "json"

    def export(self, graph_data: GraphDict) -> str:
        texts_payload = graph_data.get("texts")
        if isinstance(texts_payload, Sequence) and not isinstance(texts_payload, (str, bytes)):
            graphs = list(texts_payload)
        else:
            graphs = [graph_data]

        serialized_texts = [_serialize_text(graph) for graph in graphs]

        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "texts": serialized_texts,
        }

        return json.dumps(payload, ensure_ascii=False, indent=2)


__all__ = ["JsonExporter"]

