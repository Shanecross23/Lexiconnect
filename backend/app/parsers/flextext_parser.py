import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
import uuid
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
        guid = element.get("guid", str(uuid.uuid4()))

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

        # Parse paragraphs
        paragraphs = []
        paragraphs_element = element.find("./paragraphs")
        if paragraphs_element is not None:
            for i, paragraph_elem in enumerate(
                paragraphs_element.findall("./paragraph")
            ):
                paragraph = self._parse_paragraph(paragraph_elem, i)
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

    def _parse_paragraph(self, element, order: int) -> Optional[ParagraphCreate]:
        """Parse a paragraph element"""
        guid = element.get("guid", str(uuid.uuid4()))

        phrases = []
        phrases_element = element.find("./phrases")
        if phrases_element is not None:
            for phrase_elem in phrases_element.findall("./phrase"):
                phrase = self._parse_phrase(phrase_elem)
                if phrase:
                    phrases.append(phrase)

        return ParagraphCreate(guid=guid, order=order, phrases=phrases)

    def _parse_phrase(self, element) -> Optional[PhraseCreate]:
        """Parse a phrase element"""
        guid = element.get("guid", str(uuid.uuid4()))

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

        # Parse words
        words = []
        words_element = element.find("./words")
        if words_element is not None:
            for word_elem in words_element.findall("./word"):
                word = self._parse_word(word_elem, language)
                if word:
                    words.append(word)

        return PhraseCreate(
            guid=guid,
            segnum=segnum,
            surface_text=surface_text,
            words=words,
            language=language,
        )

    def _parse_word(self, element, default_language: str) -> Optional[WordCreate]:
        """Parse a word element"""
        guid = element.get("guid")
        if not guid:
            return None

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
                    guid=str(uuid.uuid4()),
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
            for morph_elem in morphemes_element.findall("./morph"):
                morpheme = self._parse_morpheme(morph_elem, language)
                if morpheme:
                    morphemes.append(morpheme)

        return WordCreate(
            guid=guid,
            surface_form=surface_form,
            gloss=gloss,
            pos=pos,
            morphemes=morphemes,
            language=language,
        )

    def _parse_morpheme(
        self, element, default_language: str
    ) -> Optional[MorphemeCreate]:
        """Parse a morpheme element"""
        guid = element.get("guid", str(uuid.uuid4()))
        morph_type = element.get("type", "stem")

        # Convert FLEx morph types to our enum
        type_mapping = {
            "stem": MorphemeType.STEM,
            "prefix": MorphemeType.PREFIX,
            "suffix": MorphemeType.SUFFIX,
            "infix": MorphemeType.INFIX,
            "circumfix": MorphemeType.CIRCUMFIX,
            "root": MorphemeType.ROOT,
        }

        morpheme_type = type_mapping.get(morph_type, MorphemeType.STEM)

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
