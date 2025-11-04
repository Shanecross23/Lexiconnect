"""Utilities for converting graph-structured linguistic data into FLEXText XML."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
import xml.etree.ElementTree as ET

from app.exporters import flextext_exporter as fx


GraphDict = Dict[str, Any]


def _get_paragraphs_container(root: ET.Element) -> ET.Element:
    paragraphs = root.find("./paragraphs")
    if paragraphs is None:
        paragraphs = ET.SubElement(root, "paragraphs")
    return paragraphs


def _sorted_sections(sections: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return sorted(sections, key=lambda s: (s.get("order", 0), s.get("id", "")))


def _sorted_phrases(phrases: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return sorted(phrases, key=lambda p: p.get("order", 0))


def _sorted_words(words: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return sorted(words, key=lambda w: w.get("order", 0))


def _sorted_morphemes(morphemes: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return sorted(morphemes, key=lambda m: m.get("order", 0))


def generate_flextext_xml(graph_data: GraphDict) -> str:
    """Transform graph data into FLEXText XML.

    Args:
        graph_data: Nested dictionary containing text metadata and linguistic
            hierarchy data (sections → phrases → words → morphemes).

    Returns:
        XML string encoded as UTF-8 text suitable for download.
    """

    text_info = graph_data.get("text", {}) or {}
    tree = fx.build_flextext_tree(guid=text_info.get("id"))
    root = tree.getroot()

    fx.add_metadata_item(root, "title", text_info.get("title"))
    fx.add_metadata_item(root, "source", text_info.get("source"))
    fx.add_metadata_item(root, "comment", text_info.get("comment"))

    paragraphs_container = _get_paragraphs_container(root)

    for section in _sorted_sections(graph_data.get("sections", [])):
        paragraph_el = fx.add_paragraph(
            paragraphs_container,
            guid=section.get("id"),
        )
        phrases_container = paragraph_el.find("./phrases")
        assert phrases_container is not None  # ensured by exporter helper

        for phrase in _sorted_phrases(section.get("phrases", [])):
            phrase_el = fx.add_phrase(
                phrases_container,
                guid=phrase.get("id"),
                segnum=phrase.get("segnum"),
                surface_text=phrase.get("surface_text"),
                language=phrase.get("language"),
            )

            words_container = phrase_el.find("./words")
            assert words_container is not None

            for word in _sorted_words(phrase.get("words", [])):
                is_punct = bool(word.get("is_punctuation"))
                punctuation_value: Optional[str] = None
                if is_punct:
                    punctuation_value = word.get("surface_form") or word.get("punctuation")

                word_el = fx.add_word(
                    words_container,
                    guid=word.get("id"),
                    surface_form=word.get("surface_form"),
                    gloss=word.get("gloss"),
                    pos=word.get("pos"),
                    language=word.get("language"),
                    punctuation=punctuation_value,
                )

                if is_punct:
                    continue

                morphemes = word.get("morphemes", [])
                if not morphemes:
                    continue

                morphemes_container = fx.get_or_create_morphemes_container(word_el)
                for morpheme in _sorted_morphemes(morphemes):
                    fx.add_morph(
                        morphemes_container,
                        guid=morpheme.get("id"),
                        morph_type=morpheme.get("type"),
                        surface_form=morpheme.get("surface_form"),
                        citation_form=morpheme.get("citation_form"),
                        gloss=morpheme.get("gloss"),
                        msa=morpheme.get("msa"),
                        language=morpheme.get("language"),
                    )

    xml_bytes = fx.serialize_flextext(tree)
    return xml_bytes.decode("utf-8")


