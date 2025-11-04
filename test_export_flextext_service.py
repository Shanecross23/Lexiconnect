"""Unit tests for FLEXText export conversion service."""

import os
import sys
import xml.etree.ElementTree as ET


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.export_flextext_service import generate_flextext_xml  # noqa: E402


def _mock_graph_data():
    return {
        "text": {
            "id": "text-1",
            "title": "Demo Text",
            "source": "Field Session",
            "comment": "Collected for testing",
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
    assert root.tag == "interlinear-text"

    metadata = {item.get("type"): item.text for item in root.findall("item")}
    assert metadata["title"] == "Demo Text"
    assert metadata["source"] == "Field Session"
    assert metadata["comment"].startswith("Collected for testing")

    paragraphs = root.find("paragraphs")
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

    words = phrase.find("words").findall("word")
    assert len(words) == 2

    first_word = words[0]
    assert first_word.find("item[@type='txt']").text == "demo"
    morphs = first_word.find("morphemes").findall("morph")
    assert len(morphs) == 1
    assert morphs[0].find("item[@type='gls']").text == "DEM"

    punct_word = words[1]
    assert punct_word.find("item[@type='punct']").text == "."


