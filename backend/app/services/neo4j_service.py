"""Interfaces for retrieving linguistic data from Neo4j for export workflows."""

from __future__ import annotations

from typing import Any, Dict, List

GraphData = Dict[str, Any]


class Neo4jExportDataError(RuntimeError):
    """Raised when graph data required for export cannot be assembled."""


def _normalize_language_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def get_file_graph_data(file_id: str, db) -> GraphData:
    """Fetch the linguistic hierarchy for the given file/dataset from Neo4j.

    Args:
        file_id: Identifier for the uploaded FLEXText dataset (Text node ID).
        db: Neo4j session obtained from :func:`app.database.get_db_dependency`.

    Returns:
        Nested dictionary containing text metadata, sections, phrases, words,
        and morphemes suitable for downstream XML generation.
    """

    text_query = """
        MATCH (t:Text {ID: $text_id})
        RETURN t.ID AS id,
               t.title AS title,
               t.source AS source,
               t.comment AS comment,
               t.language_code AS language_code
    """

    text_result = db.run(text_query, text_id=file_id)
    text_record = text_result.single()
    if not text_record:
        raise Neo4jExportDataError(f"No Text node found for id '{file_id}'")

    text_data = {
        "id": text_record["id"],
        "title": text_record.get("title"),
        "source": text_record.get("source"),
        "comment": text_record.get("comment"),
        "language_code": _normalize_language_code(text_record.get("language_code"))
        or "unknown",
    }

    sections_query = """
        MATCH (t:Text {ID: $text_id})-[:SECTION_PART_OF_TEXT]->(s:Section)
        RETURN s.ID AS id,
               s.order AS order
        ORDER BY order, id
    """

    sections_result = db.run(sections_query, text_id=file_id)

    sections: List[Dict[str, Any]] = []
    section_map: Dict[str, Dict[str, Any]] = {}

    for index, record in enumerate(sections_result):
        section_id = record["id"]
        order_value = record.get("order")
        section_data = {
            "id": section_id,
            "order": order_value if order_value is not None else index,
            "phrases": [],
        }
        sections.append(section_data)
        section_map[section_id] = section_data

    if not sections:
        return {"text": text_data, "sections": []}

    section_ids = list(section_map.keys())

    phrases_query = """
        MATCH (s:Section)-[:PHRASE_IN_SECTION]->(p:Phrase)
        WHERE s.ID IN $section_ids
        RETURN s.ID AS section_id,
               p.ID AS id,
               p.segnum AS segnum,
               p.surface_text AS surface_text,
               p.language AS language,
               p.order AS order
        ORDER BY section_id, order, id
    """

    phrases_result = db.run(phrases_query, section_ids=section_ids)

    phrase_map: Dict[str, Dict[str, Any]] = {}

    for index, record in enumerate(phrases_result):
        section_id = record["section_id"]
        if section_id not in section_map:
            continue

        phrase_id = record["id"]
        order_value = record.get("order")
        phrase_data = {
            "id": phrase_id,
            "order": order_value if order_value is not None else index,
            "segnum": record.get("segnum"),
            "surface_text": record.get("surface_text"),
            "language": _normalize_language_code(record.get("language"))
            or text_data["language_code"],
            "words": [],
        }

        section_map[section_id]["phrases"].append(phrase_data)
        phrase_map[phrase_id] = phrase_data

    if not phrase_map:
        return {"text": text_data, "sections": sections}

    phrase_ids = list(phrase_map.keys())

    words_query = """
        MATCH (p:Phrase)-[r:PHRASE_COMPOSED_OF]->(w:Word)
        WHERE p.ID IN $phrase_ids
        OPTIONAL MATCH (w)-[rm:WORD_MADE_OF]->(m:Morpheme)
        RETURN p.ID AS phrase_id,
               w.ID AS word_id,
               r.Order AS word_order,
               w.surface_form AS word_surface_form,
               w.gloss AS word_gloss,
               w.pos AS word_pos,
               w.language AS word_language,
               m.ID AS morph_id,
               rm.Order AS morph_order,
               m.type AS morph_type,
               m.surface_form AS morph_surface_form,
               m.citation_form AS morph_citation_form,
               m.gloss AS morph_gloss,
               m.msa AS morph_msa,
               m.language AS morph_language,
               m.original_guid AS morph_original_guid
        ORDER BY phrase_id, word_order, morph_order
    """

    words_result = db.run(words_query, phrase_ids=phrase_ids)

    word_map: Dict[str, Dict[str, Any]] = {}
    phrase_word_orders: Dict[str, List[Dict[str, Any]]] = {
        phrase_id: phrase["words"] for phrase_id, phrase in phrase_map.items()
    }

    for record in words_result:
        phrase_id = record["phrase_id"]
        if phrase_id not in phrase_map:
            continue

        word_id = record["word_id"]
        if word_id is None:
            continue

        word_order = record.get("word_order")
        if word_id not in word_map:
            pos_value = record.get("word_pos")
            is_punctuation = False
            if pos_value:
                pos_upper = str(pos_value).upper()
                is_punctuation = pos_upper in {"PUNCT", "PUNCTUATION", "SYM"}

            word_data = {
                "id": word_id,
                "order": word_order if word_order is not None else len(phrase_word_orders[phrase_id]),
                "surface_form": record.get("word_surface_form"),
                "gloss": record.get("word_gloss"),
                "pos": None if is_punctuation else record.get("word_pos"),
                "language": _normalize_language_code(record.get("word_language"))
                or phrase_map[phrase_id]["language"],
                "is_punctuation": is_punctuation,
                "morphemes": [],
            }

            phrase_word_orders[phrase_id].append(word_data)
            word_map[word_id] = word_data

        word_data = word_map[word_id]

        morph_id = record.get("morph_id")
        if not morph_id or word_data["is_punctuation"]:
            continue

        morph_order = record.get("morph_order")
        morphemes = word_data["morphemes"]

        if not any(morph.get("id") == morph_id for morph in morphemes):
            morphemes.append(
                {
                    "id": morph_id,
                    "order": morph_order if morph_order is not None else len(morphemes),
                    "type": record.get("morph_type"),
                    "surface_form": record.get("morph_surface_form"),
                    "citation_form": record.get("morph_citation_form"),
                    "gloss": record.get("morph_gloss"),
                    "msa": record.get("morph_msa"),
                    "language": _normalize_language_code(record.get("morph_language"))
                    or word_data["language"],
                    "original_id": record.get("morph_original_guid"),
                }
            )

    # Ensure deterministic ordering for downstream processing
    for section in sections:
        section["phrases"].sort(key=lambda p: (p.get("order", 0), p.get("id", "")))
        for phrase in section["phrases"]:
            phrase["words"].sort(key=lambda w: (w.get("order", 0), w.get("id", "")))
            for word in phrase["words"]:
                word["morphemes"].sort(key=lambda m: (m.get("order", 0), m.get("id", "")))

    sections.sort(key=lambda s: (s.get("order", 0), s.get("id", "")))

    return {
        "text": text_data,
        "sections": sections,
    }


def get_all_texts_graph_data(db) -> List[GraphData]:
    """Return graph data for every Text node in the database."""

    text_ids_query = """
        MATCH (t:Text)
        RETURN COALESCE(t.ID, toString(id(t))) AS id
        ORDER BY id
    """

    result = db.run(text_ids_query)

    graph_payloads: List[GraphData] = []
    seen_ids: set[str] = set()

    for record in result:
        text_id = record.get("id")
        if not text_id or text_id in seen_ids:
            continue

        try:
            graph_data = get_file_graph_data(text_id, db)
        except Neo4jExportDataError:
            continue

        graph_payloads.append(graph_data)
        seen_ids.add(text_id)

    return graph_payloads


