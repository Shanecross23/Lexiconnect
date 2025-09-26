import xml.etree.ElementTree as ET
import json
import uuid
from typing import List, Dict, Optional, Any
from app.models.linguistic import (
    InterlinearTextCreate,
    ParagraphCreate,
    PhraseCreate,
    WordCreate,
    MorphemeCreate,
    LinguisticItem,
    MorphemeType,
    ItemType,
)


_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")

def stable_uuid(*parts: str) -> str:
    """Deterministic UUID"""
    return str(uuid.uuid5(_UUID_NS, "|".join(parts)))

class FlexTextParser:
    """Parser for FLEx XML (.flextext) files"""

    def __init__(self):
        self.namespace_map = {}

    def parse_file(self, file_path: str) -> List[InterlinearTextCreate]:
        """Parse a .flextext file and return list of InterlinearText objects"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Handle namespace if present
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"
            self.namespace_map = {"": namespace}

        texts = []
        for interlinear_text in root.findall(".//interlinear-text"):
            text = self._parse_interlinear_text(interlinear_text)
            if text:
                texts.append(text)

        return texts

    def _parse_interlinear_text(self, element) -> Optional[InterlinearTextCreate]:
        """Parse an interlinear-text element"""

        # Extract metadata items
        title = ""
        source = ""
        comment = ""
        language_code = "unknown"

        for item in element.findall("./item"):
            item_type = item.get("type", "")
            item_lang = item.get("lang", "")
            item_text = item.text or ""

            if item_type == "title":
                title = item_text
                if item_lang and language_code == "unknown":
                    language_code = item_lang
            elif item_type == "source":
                source = item_text
            elif item_type == "comment":
                comment = item_text

        guid = element.get("guid") or stable_uuid("text", title.strip(), source.strip())

        # Parse paragraphs
        paragraphs = []
        paragraphs_element = element.find("./paragraphs")
        if paragraphs_element is not None:
            for i, paragraph_elem in enumerate(paragraphs_element.findall("./paragraph")):
                paragraph = self._parse_paragraph(paragraph_elem, i, guid)
                if paragraph:
                    paragraphs.append(paragraph)

        return InterlinearTextCreate(
            guid=guid,
            title=title,
            source=source,
            comment=comment,
            language_code=language_code,
            paragraphs=paragraphs,
        )

    def _parse_paragraph(self, element, order: int, parent_guid: str) -> Optional[ParagraphCreate]:
        """Parse a paragraph element"""
        guid = element.get("guid") or stable_uuid("paragraph", parent_guid, str(order))

        phrases = []
        phrases_element = element.find("./phrases")
        if phrases_element is not None:
            for i, phrase_elem in enumerate(phrases_element.findall("./phrase")):
                phrase = self._parse_phrase(phrase_elem, guid, i)
                if phrase:
                    phrases.append(phrase)

        return ParagraphCreate(guid=guid, order=order, phrases=phrases)

    def _parse_phrase(self, element, parent_guid: str, order: int) -> Optional[PhraseCreate]:
        """Parse a phrase element"""

        # Extract phrase-level items
        segnum = ""
        surface_text = ""
        language = "unknown"

        for item in element.findall("./item"):
            item_type = item.get("type", "")
            item_lang = item.get("lang", "")
            item_text = item.text or ""

            if item_type == "segnum":
                segnum = item_text
            elif item_type == "txt":
                surface_text = item_text
                if item_lang:
                    language = item_lang

        guid = element.get("guid") or stable_uuid("phrase", parent_guid, str(order))

        # Parse words
        words = []
        words_element = element.find("./words")
        if words_element is not None:
            for k, word_elem in enumerate(words_element.findall("./word")):
                word = self._parse_word(word_elem, language, guid, k)
                if word:
                    words.append(word)

        return PhraseCreate(
            guid=guid,
            segnum=segnum,
            surface_text=surface_text,
            words=words,
            language=language,
        )

    def _parse_word(self, element, default_language: str, parent_guid: str, order: int) -> Optional[WordCreate]:
        """Parse a word element"""

        # Extract word-level items
        surface_form = ""
        gloss = ""
        pos = ""
        language = default_language

        for item in element.findall("./item"):
            item_type = item.get("type", "")
            item_lang = item.get("lang", "")
            item_text = item.text or ""

            if item_type == "txt":
                surface_form = item_text
                if item_lang:
                    language = item_lang
            elif item_type == "gls":
                gloss = item_text
            elif item_type == "pos":
                pos = item_text
            elif item_type == "punct":
                # Handle punctuation as special case
                return WordCreate(
                    guid=stable_uuid("punct", parent_guid, str(order), item_text),
                    surface_form=item_text,
                    gloss="",
                    pos="PUNCT",
                    morphemes=[],
                    language=language,
                )

        # Parse morphemes
        morphemes = []
        morphemes_element = element.find("./morphemes")
        if morphemes_element is not None:
            for j, morph_elem in enumerate(morphemes_element.findall("./morph")):
                morpheme = self._parse_morpheme(morph_elem, language, parent_guid=parent_guid, index=j, word_order=order)
                if morpheme:
                    morphemes.append(morpheme)

        guid = element.get("guid") or stable_uuid("word", parent_guid, str(order))
        return WordCreate(
            guid=guid,
            surface_form=surface_form,
            gloss=gloss,
            pos=pos,
            morphemes=morphemes,
            language=language,
        )

    def _parse_morpheme(self,element,default_language: str,parent_guid: str, index: int = 0, word_order: Optional[int] = None,) -> Optional[MorphemeCreate]:
        """Parse a morpheme element"""

        # Convert FLEx morph types to our enum
        type_mapping = {
            "stem": MorphemeType.STEM,
            "prefix": MorphemeType.PREFIX,
            "suffix": MorphemeType.SUFFIX,
            "infix": MorphemeType.INFIX,
            "circumfix": MorphemeType.CIRCUMFIX,
            "root": MorphemeType.ROOT,
        }
        raw_type = element.get("type", "stem")
        morpheme_type = type_mapping.get(raw_type, MorphemeType.STEM)

        # Extract morpheme items
        surface_form = ""
        citation_form = ""
        gloss = ""
        msa = ""
        language = default_language

        for item in element.findall("./item"):
            item_type = item.get("type", "")
            item_lang = item.get("lang", "")
            item_text = item.text or ""

            if item_type == "txt":
                surface_form = item_text
                if item_lang:
                    language = item_lang
            elif item_type == "cf":
                citation_form = item_text
            elif item_type == "gls":
                gloss = item_text
            elif item_type == "msa":
                msa = item_text

        guid = element.get("guid") or stable_uuid("morph", parent_guid, str(word_order or ""), str(index))

        return MorphemeCreate(
            guid=guid,
            type=morpheme_type,
            surface_form=surface_form,
            citation_form=citation_form,
            gloss=gloss,
            msa=msa,
            language=language,
        )

    def get_language_stats(self, texts: List[InterlinearTextCreate]) -> Dict[str, Any]:
        """Generate statistics about the parsed texts"""
        languages_set = set()
        pos_tags_set = set()
        morpheme_types_dict: Dict[str, int] = {}

        stats = {
            "total_texts": len(texts),
            "total_paragraphs": 0,
            "total_phrases": 0,
            "total_words": 0,
            "total_morphemes": 0,
            "languages": languages_set,
            "morpheme_types": morpheme_types_dict,
            "pos_tags": pos_tags_set,
        }

        for text in texts:
            languages_set.add(text.language_code)
            stats["total_paragraphs"] += len(text.paragraphs)

            for paragraph in text.paragraphs:
                stats["total_phrases"] += len(paragraph.phrases)

                for phrase in paragraph.phrases:
                    stats["total_words"] += len(phrase.words)

                    for word in phrase.words:
                        if word.pos:
                            pos_tags_set.add(word.pos)
                        stats["total_morphemes"] += len(word.morphemes)

                        for morpheme in word.morphemes:
                            morph_type = morpheme.type.value
                            morpheme_types_dict[morph_type] = (
                                morpheme_types_dict.get(morph_type, 0) + 1
                            )

        # Convert sets to lists for JSON serialization
        stats["languages"] = list(languages_set)
        stats["pos_tags"] = list(pos_tags_set)

        return stats


def parse_flextext_file(file_path: str) -> List[InterlinearTextCreate]:
    """Convenience function to parse a FLEx file"""
    parser = FlexTextParser()
    return parser.parse_file(file_path)


def get_file_stats(file_path: str) -> Dict[str, Any]:
    """Get statistics for a FLEx file"""
    parser = FlexTextParser()
    texts = parser.parse_file(file_path)
    return parser.get_language_stats(texts)

# Methods for creating JSON objects from FLEx
def _morpheme_to_dict(m) -> Dict[str, Any]:
    return {
        "guid": getattr(m, "guid", None),
        "type": getattr(m.type, "value", None) if getattr(m, "type", None) else None,
        "surface_form": getattr(m, "surface_form", ""),
        "citation_form": getattr(m, "citation_form", ""),
        "gloss": getattr(m, "gloss", ""),
        "msa": getattr(m, "msa", ""),
        "language": getattr(m, "language", None),
    }

def _word_to_dict(w) -> Dict[str, Any]:
    return {
        "guid": getattr(w, "guid", None),
        "surface_form": getattr(w, "surface_form", ""),
        "gloss": getattr(w, "gloss", ""),
        "pos": getattr(w, "pos", ""),
        "language": getattr(w, "language", None),
        "morphemes": [_morpheme_to_dict(m) for m in getattr(w, "morphemes", []) or []],
    }

def _phrase_to_dict(ph) -> Dict[str, Any]:
    return {
        "guid": getattr(ph, "guid", None),
        "segnum": getattr(ph, "segnum", ""),
        "surface_text": getattr(ph, "surface_text", ""),
        "language": getattr(ph, "language", None),
        "words": [_word_to_dict(w) for w in getattr(ph, "words", []) or []],
    }

def _paragraph_to_dict(p) -> Dict[str, Any]:
    return {
        "guid": getattr(p, "guid", None),
        "order": getattr(p, "order", None),
        "phrases": [_phrase_to_dict(ph) for ph in getattr(p, "phrases", []) or []],
    }

def _text_to_dict(t) -> Dict[str, Any]:
    return {
        "guid": getattr(t, "guid", None),
        "title": getattr(t, "title", ""),
        "source": getattr(t, "source", ""),
        "comment": getattr(t, "comment", ""),
        "language_code": getattr(t, "language_code", None),
        "paragraphs": [_paragraph_to_dict(p) for p in getattr(t, "paragraphs", []) or []],
    }

def texts_to_jsonable(texts: List[InterlinearTextCreate]) -> List[Dict[str, Any]]:
    return [_text_to_dict(t) for t in texts]

def parse_flextext_to_json(file_path: str) -> List[Dict[str, Any]]:
    parser = FlexTextParser()
    texts = parser.parse_file(file_path)
    return texts_to_jsonable(texts)

def parse_flextext_to_json_string(file_path: str, pretty: bool = True) -> str:
    data = parse_flextext_to_json(file_path)
    return json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)
