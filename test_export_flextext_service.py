"""Unit tests for FLEXText export conversion service."""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.parsers.flextext_parser import parse_flextext_file  # noqa: E402
from app.services.export_flextext_service import generate_flextext_xml  # noqa: E402


def _mock_graph_data():
    return {
        "text": {
            "id": "text-1",
            "title": "Demo Text",
            "source": "Field Session",
            "comment": "Collected for testing",
            "language_code": "en",
            "analysis_language": "en",
        },
        "sections": [
            {
                "id": "section-1",
                "order": 2,
                "phrases": [
                    {
                        "id": "phrase-1",
                        "order": 5,
                        "segnum": "1",
                        "surface_text": "demo phrase",
                        "language": "eng",
                        "words": [
                            {
                                "id": "word-1",
                                "order": 1,
                                "surface_form": "demo",
                                "gloss": "DEM",
                                "pos": "N",
                                "language": "eng",
                                "morphemes": [
                                    {
                                        "id": "morph-1",
                                        "order": 1,
                                        "type": "stem",
                                        "surface_form": "demo",
                                        "citation_form": "demo",
                                        "gloss": "DEM",
                                        "msa": "n",
                                        "language": "eng",
                                    }
                                ],
                            },
                            {
                                "id": "word-2",
                                "order": 2,
                                "surface_form": ".",
                                "is_punctuation": True,
                            },
                        ],
                    }
                ],
            },
            {
                "id": "section-0",
                "order": 1,
                "phrases": [],
            },
        ],
    }


def test_generate_flextext_xml_produces_expected_structure():
    xml_str = generate_flextext_xml(_mock_graph_data())

    root = ET.fromstring(xml_str)
    assert root.tag == "document"
    assert root.get("version") == "2"

    texts = root.findall("interlinear-text")
    assert len(texts) == 1

    interlinear_text = texts[0]

    metadata = {item.get("type"): item.text for item in interlinear_text.findall("item")}
    assert metadata["title"] == "Demo Text"
    assert metadata["source"] == "Field Session"
    assert metadata["comment"].startswith("Collected for testing")

    title_item = interlinear_text.find("item[@type='title']")
    assert title_item is not None and title_item.get("lang") == "en"
    source_item = interlinear_text.find("item[@type='source']")
    assert source_item is not None and source_item.get("lang") == "en"

    paragraphs = interlinear_text.find("paragraphs")
    assert paragraphs is not None

    paragraph_guids = [p.get("guid") for p in paragraphs.findall("paragraph")]
    # Sections should be sorted by order (section-0 first)
    assert paragraph_guids == ["section-0", "section-1"]

    phrase_nodes = paragraphs.findall("paragraph/phrases/phrase")
    assert len(phrase_nodes) == 1

    phrase = phrase_nodes[0]
    assert phrase.get("guid") == "phrase-1"
    assert phrase.find("item[@type='segnum']").text == "1"
    assert phrase.find("item[@type='txt']").text == "demo phrase"
    assert phrase.find("item[@type='segnum']").get("lang") == "en"
    assert phrase.find("item[@type='txt']").get("lang") == "eng"

    words = phrase.find("words").findall("word")
    assert len(words) == 2

    first_word = words[0]
    assert first_word.find("item[@type='txt']").text == "demo"
    assert first_word.find("item[@type='txt']").get("lang") == "eng"
    assert first_word.find("item[@type='gls']").get("lang") == "en"
    assert first_word.find("item[@type='pos']").get("lang") == "en"
    morphs = first_word.find("morphemes").findall("morph")
    assert len(morphs) == 1
    assert morphs[0].find("item[@type='gls']").text == "DEM"
    assert morphs[0].find("item[@type='txt']").get("lang") == "eng"
    assert morphs[0].find("item[@type='cf']").get("lang") == "eng"
    assert morphs[0].find("item[@type='gls']").get("lang") == "en"
    assert morphs[0].find("item[@type='msa']").get("lang") == "en"

    punct_word = words[1]
    assert punct_word.find("item[@type='punct']").text == "."


def test_generate_flextext_xml_supports_multiple_texts():
    first = _mock_graph_data()
    second = _mock_graph_data()
    second["text"]["id"] = "text-2"
    second["text"]["title"] = "Second Text"
    second["sections"][0]["phrases"][0]["words"][0]["surface_form"] = "second"

    xml_str = generate_flextext_xml({"texts": [first, second]})

    root = ET.fromstring(xml_str)
    texts = root.findall("interlinear-text")
    assert len(texts) == 2

    titles = [item.text for item in root.findall("interlinear-text/item[@type='title']")]
    assert titles == ["Demo Text", "Second Text"]
    langs = [item.get("lang") for item in root.findall("interlinear-text/item[@type='title']")]
    assert langs == ["en", "en"]


def test_generate_flextext_handles_duplicate_morpheme_guids():
    graph_data = {
        "text": {
            "id": "dup-text",
            "title": "Dup",
            "source": "",
            "comment": "",
            "language_code": "en",
            "analysis_language": "en",
        },
        "sections": [
            {
                "id": "sec-1",
                "order": 0,
                "phrases": [
                    {
                        "id": "phr-1",
                        "order": 0,
                        "segnum": "1",
                        "surface_text": "alpha beta",
                        "language": "eng",
                        "words": [
                            {
                                "id": "w-1",
                                "order": 0,
                                "surface_form": "alpha",
                                "gloss": "A",
                                "pos": "N",
                                "language": "eng",
                                "morphemes": [
                                    {
                                        "id": "m-1",
                                        "original_id": "shared-guid",
                                        "type": "stem",
                                        "surface_form": "al",
                                        "citation_form": "al",
                                        "gloss": "root1",
                                        "msa": "n",
                                        "language": "eng",
                                    }
                                ],
                            },
                            {
                                "id": "w-2",
                                "order": 1,
                                "surface_form": "beta",
                                "gloss": "B",
                                "pos": "N",
                                "language": "eng",
                                "morphemes": [
                                    {
                                        "id": "m-2",
                                        "original_id": "shared-guid",
                                        "type": "stem",
                                        "surface_form": "be",
                                        "citation_form": "be",
                                        "gloss": "root2",
                                        "msa": "n",
                                        "language": "eng",
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
    }

    xml_str = generate_flextext_xml(graph_data)

    root = ET.fromstring(xml_str)
    words = root.findall("interlinear-text/paragraphs/paragraph/phrases/phrase/words/word")
    assert len(words) == 2

    first_morph = words[0].find("morphemes/morph")
    second_morph = words[1].find("morphemes/morph")

    assert first_morph.find("item[@type='txt']").text == "al"
    assert second_morph.find("item[@type='txt']").text == "be"

    # Guid should prefer original shared guid even though DB IDs differ
    assert first_morph.get("guid") == "shared-guid"
    assert second_morph.get("guid") == "shared-guid"


def _normalize_msa(msa_value):
    if isinstance(msa_value, dict):
        return ",".join(f"{k}:{v}" for k, v in msa_value.items())
    if isinstance(msa_value, list):
        return ",".join(str(item) for item in msa_value)
    if msa_value is None:
        return None
    return str(msa_value)


def _word_to_graph(word, idx, fallback_language):
    is_punct = any((pos or "").upper() == "PUNCT" for pos in word.pos)
    language = getattr(word, "language", None) or fallback_language

    graph_word = {
        "id": word.id,
        "order": idx,
        "surface_form": word.surface_form,
        "gloss": word.gloss,
        "pos": ",".join(word.pos) if word.pos else None,
        "language": language,
        "is_punctuation": is_punct,
    }

    if is_punct:
        graph_word["punctuation"] = word.surface_form
        graph_word["morphemes"] = []
        return graph_word

    morphemes = []
    for m_idx, morpheme in enumerate(word.morphemes):
        morphemes.append(
            {
                "id": morpheme.id,
                "guid": getattr(morpheme, "original_guid", None),
                "original_id": getattr(morpheme, "original_guid", None),
                "order": m_idx,
                "type": morpheme.type.value if morpheme.type else None,
                "surface_form": morpheme.surface_form,
                "citation_form": morpheme.citation_form,
                "gloss": morpheme.gloss,
                "msa": _normalize_msa(morpheme.msa),
                "language": getattr(morpheme, "language", None),
            }
        )

    graph_word["morphemes"] = morphemes
    return graph_word


def _phrase_to_graph(phrase, idx):
    language = getattr(phrase, "language", None)
    graph_phrase = {
        "id": phrase.id,
        "order": phrase.order if phrase.order is not None else idx,
        "segnum": phrase.segnum,
        "surface_text": phrase.surface_text,
        "language": language,
        "words": [
            _word_to_graph(word, w_idx, language)
            for w_idx, word in enumerate(phrase.words)
        ],
    }
    return graph_phrase


def _section_to_graph(section, idx):
    graph_section = {
        "id": section.id,
        "order": section.order if section.order is not None else idx,
        "phrases": [
            _phrase_to_graph(phrase, p_idx)
            for p_idx, phrase in enumerate(section.phrases)
        ],
    }
    return graph_section


def _text_to_graph_data(text):
    metadata_language = getattr(text, "language", None)
    if metadata_language and metadata_language.lower() == "unknown":
        metadata_language = None
    sections = [_section_to_graph(section, s_idx) for s_idx, section in enumerate(text.sections)]

    return {
        "text": {
            "id": text.id,
            "title": text.title,
            "source": text.source,
            "comment": text.comment,
            "language_code": metadata_language,
            "analysis_language": metadata_language or "en",
            "metadata_language": metadata_language,
        },
        "sections": sections,
    }


def test_round_trip_with_sample_flextext(tmp_path):
    sample_path = Path(__file__).resolve().parent / "a.flextext"
    if not sample_path.exists():
        raise AssertionError("Sample flextext file 'a.flextext' is missing from repository root")

    original_texts = parse_flextext_file(str(sample_path))
    assert original_texts, "Expected at least one text in a.flextext"

    graph_payloads = [_text_to_graph_data(text) for text in original_texts]
    xml_str = generate_flextext_xml({"texts": graph_payloads})

    round_trip_path = tmp_path / "roundtrip.flextext"
    round_trip_path.write_text(xml_str, encoding="utf-8")

    parsed_round_trip = parse_flextext_file(str(round_trip_path))

    assert len(parsed_round_trip) == len(original_texts)

    for original, regenerated in zip(original_texts, parsed_round_trip):
        assert regenerated.title == original.title
        assert regenerated.source == original.source
        assert len(regenerated.sections) == len(original.sections)

        for orig_section, regen_section in zip(original.sections, regenerated.sections):
            assert len(regen_section.phrases) == len(orig_section.phrases)

            for orig_phrase, regen_phrase in zip(orig_section.phrases, regen_section.phrases):
                assert regen_phrase.surface_text == orig_phrase.surface_text
                assert len(regen_phrase.words) == len(orig_phrase.words)

                for orig_word, regen_word in zip(orig_phrase.words, regen_phrase.words):
                    assert regen_word.surface_form == orig_word.surface_form
                    assert regen_word.gloss == orig_word.gloss

                    if any((pos or "").upper() == "PUNCT" for pos in orig_word.pos):
                        assert not regen_word.morphemes
                        continue

                    assert len(regen_word.morphemes) == len(orig_word.morphemes)

                    for orig_morph, regen_morph in zip(orig_word.morphemes, regen_word.morphemes):
                        assert regen_morph.surface_form == orig_morph.surface_form
                        assert regen_morph.gloss == orig_morph.gloss
