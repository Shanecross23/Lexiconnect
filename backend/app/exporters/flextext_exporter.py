import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, Optional


_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(*parts: str) -> str:
    """Deterministic UUID to keep exports stable across runs."""
    return str(uuid.uuid5(_UUID_NS, "|".join(parts)))


def add_item(parent: ET.Element, item_type: str, text: Optional[str], lang: Optional[str] = None) -> Optional[ET.Element]:
    """Append an <item> with type and optional lang, skipping empty text.
    
    Args:
        parent: Parent XML element
        item_type: Type attribute for the item (e.g., "txt", "gls", "pos")
        text: Text content (if None or empty string, item is not created)
        lang: Optional language code for lang attribute (only set if non-empty)
        
    Returns:
        Created item element, or None if text was empty
    """
    if text is None or text == "":
        return None
    item = ET.SubElement(parent, "item")
    item.set("type", item_type)
    # Only set lang if it's a non-empty string
    if lang and lang.strip():
        item.set("lang", lang)
    item.text = text
    return item


def _ensure_container(parent: ET.Element, tag: str) -> ET.Element:
    node = parent.find(f"./{tag}")
    return node if node is not None else ET.SubElement(parent, tag)


def add_word(
    words_parent: ET.Element,
    *,
    guid: Optional[str] = None,
    surface_form: Optional[str] = None,
    gloss: Optional[str] = None,
    pos: Optional[str] = None,
    language: Optional[str] = None,
    punctuation: Optional[str] = None,
) -> ET.Element:
    """Add a word element to words container.
    
    If punctuation is provided, adds item type="punct" and returns early
    (morphemes should not be added to punctuation words per parser behavior).
    Otherwise, adds txt, gls, and pos items as provided.
    
    To add morphemes to a non-punctuation word:
        word_el = add_word(...)
        morphemes_container = get_or_create_morphemes_container(word_el)
        add_morph(morphemes_container, ...)
    
    Returns:
        The created word element
    """
    word_el = ET.SubElement(words_parent, "word")
    if guid:
        word_el.set("guid", guid)

    if punctuation is not None and punctuation != "":
        # Punctuation words should not have morphemes (parser behavior)
        add_item(word_el, "punct", punctuation)
        return word_el

    add_item(word_el, "txt", surface_form, lang=language)
    add_item(word_el, "gls", gloss)
    add_item(word_el, "pos", pos)
    return word_el


def add_morph(
    morphemes_parent: ET.Element,
    *,
    guid: Optional[str] = None,
    morph_type: Optional[str] = None,
    surface_form: Optional[str] = None,
    citation_form: Optional[str] = None,
    gloss: Optional[str] = None,
    msa: Optional[str] = None,
    language: Optional[str] = None,
) -> ET.Element:
    """Add a morph element to morphemes container.
    
    Args:
        morphemes_parent: Parent morphemes container element
        guid: Optional GUID for the morph
        morph_type: Optional type attribute (expected values: "stem", "prefix", 
                   "suffix", "infix", "circumfix", "root"). Defaults to None
                   (omitted) if not provided.
        surface_form: Surface form text (adds item type="txt")
        citation_form: Citation form (adds item type="cf")
        gloss: Gloss text (adds item type="gls")
        msa: Morphosyntactic analysis (adds item type="msa")
        language: Language code for lang attribute on txt item
        
    Returns:
        The created morph element
    """
    morph_el = ET.SubElement(morphemes_parent, "morph")
    if guid:
        morph_el.set("guid", guid)
    # Convert enum values to string if needed, or use as-is
    if morph_type:
        morph_el.set("type", str(morph_type))
    add_item(morph_el, "txt", surface_form, lang=language)
    add_item(morph_el, "cf", citation_form)
    add_item(morph_el, "gls", gloss)
    add_item(morph_el, "msa", msa)
    return morph_el


def add_metadata_item(
    root: ET.Element, item_type: str, text: Optional[str], lang: Optional[str] = None
) -> Optional[ET.Element]:
    """Add metadata item (title, source, comment) to interlinear-text root."""
    return add_item(root, item_type, text, lang=lang)


def add_paragraph(paragraphs_container: ET.Element, *, guid: Optional[str] = None) -> ET.Element:
    """Add a paragraph element to paragraphs container. Returns the paragraph element."""
    paragraph = ET.SubElement(paragraphs_container, "paragraph")
    if guid:
        paragraph.set("guid", guid)
    # Ensure phrases container exists
    _ensure_container(paragraph, "phrases")
    return paragraph


def add_phrase(
    phrases_container: ET.Element,
    *,
    guid: Optional[str] = None,
    segnum: Optional[str] = None,
    surface_text: Optional[str] = None,
    language: Optional[str] = None,
) -> ET.Element:
    """Add a phrase element to phrases container. Returns the phrase element."""
    phrase = ET.SubElement(phrases_container, "phrase")
    if guid:
        phrase.set("guid", guid)
    
    # Add phrase-level items
    add_item(phrase, "segnum", segnum)
    add_item(phrase, "txt", surface_text, lang=language)
    
    # Ensure words container exists for this phrase
    _ensure_container(phrase, "words")
    return phrase


def get_or_create_morphemes_container(word_element: ET.Element) -> ET.Element:
    """Get or create morphemes container for a word element."""
    return _ensure_container(word_element, "morphemes")


def build_flextext_tree(*, guid: Optional[str] = None) -> ET.ElementTree:
    """Create an empty interlinear-text root ready for population.
    
    Creates the root element with required containers but no content.
    The data population is handled by higher-level services that iterate DB data
    and add paragraphs/phrases/words/morphemes using the helpers above.
    
    Args:
        guid: Optional GUID for the interlinear-text root
        
    Returns:
        ElementTree with interlinear-text root and paragraphs container
    """
    root = ET.Element("interlinear-text")
    if guid:
        root.set("guid", guid)
    # Add paragraphs container (required by parser)
    ET.SubElement(root, "paragraphs")
    return ET.ElementTree(root)


def serialize_flextext(tree: ET.ElementTree) -> bytes:
    """Serialize XML tree to UTF-8 bytes with declaration."""
    return ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)


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


def _normalize_language_code(code: Optional[str]) -> Optional[str]:
    if not code or not code.strip():
        return None
    return code.strip()


class FlextextExporter:
    """Exporter implementation that produces FLEXText XML output."""

    file_type = "flextext"
    media_type = "application/xml"
    file_extension = "flextext"

    def export(self, graph_data: GraphDict) -> str:
        text_info = graph_data.get("text", {}) or {}
        tree = build_flextext_tree(guid=text_info.get("id"))
        root = tree.getroot()

        add_metadata_item(root, "title", text_info.get("title"))
        add_metadata_item(root, "source", text_info.get("source"))
        add_metadata_item(root, "comment", text_info.get("comment"))

        paragraphs_container = _get_paragraphs_container(root)

        for section in _sorted_sections(graph_data.get("sections", [])):
            paragraph_el = add_paragraph(
                paragraphs_container,
                guid=section.get("id"),
            )
            phrases_container = paragraph_el.find("./phrases")
            assert phrases_container is not None  # ensured by helper

            for phrase in _sorted_phrases(section.get("phrases", [])):
                phrase_language = _normalize_language_code(phrase.get("language"))

                phrase_el = add_phrase(
                    phrases_container,
                    guid=phrase.get("id"),
                    segnum=phrase.get("segnum"),
                    surface_text=phrase.get("surface_text"),
                    language=phrase_language,
                )

                words_container = phrase_el.find("./words")
                assert words_container is not None

                for word in _sorted_words(phrase.get("words", [])):
                    is_punct = bool(word.get("is_punctuation"))
                    punctuation_value: Optional[str] = None
                    if is_punct:
                        punctuation_value = word.get("surface_form") or word.get("punctuation")

                    word_language = _normalize_language_code(word.get("language")) or phrase_language

                    word_el = add_word(
                        words_container,
                        guid=word.get("id"),
                        surface_form=word.get("surface_form"),
                        gloss=word.get("gloss"),
                        pos=word.get("pos"),
                        language=word_language,
                        punctuation=punctuation_value,
                    )

                    if is_punct:
                        continue

                    morphemes = word.get("morphemes", [])
                    if not morphemes:
                        continue

                    morphemes_container = get_or_create_morphemes_container(word_el)
                    for morpheme in _sorted_morphemes(morphemes):
                        morph_language = (
                            _normalize_language_code(morpheme.get("language"))
                            or word_language
                        )

                        add_morph(
                            morphemes_container,
                            guid=morpheme.get("id"),
                            morph_type=morpheme.get("type"),
                            surface_form=morpheme.get("surface_form"),
                            citation_form=morpheme.get("citation_form"),
                            gloss=morpheme.get("gloss"),
                            msa=morpheme.get("msa"),
                            language=morph_language,
                        )

        xml_bytes = serialize_flextext(tree)
        return xml_bytes.decode("utf-8")

