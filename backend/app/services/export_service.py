"""Service layer for exporting linguistic data from the database to FLEXText format."""

from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class MorphemeExport:
    """Morpheme data for export."""
    ID: str
    type: Optional[str]  # MorphemeType enum value as string
    surface_form: Optional[str]
    citation_form: Optional[str]
    gloss: Optional[str]
    msa: Optional[str]
    language: Optional[str]
    original_guid: Optional[str] = None


@dataclass
class WordExport:
    """Word data for export."""
    ID: str
    surface_form: Optional[str]
    gloss: Optional[str]
    pos: Optional[str]
    language: Optional[str]
    morphemes: List[MorphemeExport]
    # For punctuation words
    is_punctuation: bool = False


@dataclass
class PhraseExport:
    """Phrase data for export."""
    ID: str
    segnum: Optional[str]
    surface_text: Optional[str]
    language: Optional[str]
    words: List[WordExport]
    order: int = 0


@dataclass
class SectionExport:
    """Section (paragraph) data for export."""
    ID: str
    order: int
    phrases: List[PhraseExport]


@dataclass
class TextExport:
    """Complete text data for export."""
    ID: str
    title: Optional[str]
    source: Optional[str]
    comment: Optional[str]
    language_code: Optional[str]
    sections: List[SectionExport]


async def fetch_text_for_export(text_id: str, db) -> Optional[TextExport]:
    """Fetch a complete Text with all nested data for export.
    
    Retrieves the text and all sections, phrases, words, and morphemes
    in the correct order for FLEXText export.
    
    Args:
        text_id: The ID of the Text node to fetch
        db: Neo4j database session
        
    Returns:
        TextExport with all nested data, or None if text not found
    """
    # Fetch text metadata
    text_query = """
        MATCH (t:Text {ID: $text_id})
        RETURN 
            t.ID AS ID,
            t.title AS title,
            t.source AS source,
            t.comment AS comment,
            t.language_code AS language_code
    """
    
    result = db.run(text_query, text_id=text_id)
    record = result.single()
    
    if not record:
        return None
    
    text_data = {
        "ID": record["ID"],
        "title": record.get("title") or "",
        "source": record.get("source") or "",
        "comment": record.get("comment") or "",
        "language_code": record.get("language_code") or "unknown",
    }
    
    # Fetch sections ordered by section.order
    sections_query = """
        MATCH (t:Text {ID: $text_id})-[:SECTION_PART_OF_TEXT]->(s:Section)
        RETURN s.ID AS section_id, s.order AS section_order
        ORDER BY s.order
    """
    
    sections_result = db.run(sections_query, text_id=text_id)
    sections_dict: Dict[str, SectionExport] = {}
    
    for record in sections_result:
        section_id = record["section_id"]
        section_order = record.get("section_order", 0)
        sections_dict[section_id] = SectionExport(
            ID=section_id,
            order=section_order,
            phrases=[]
        )
    
    if not sections_dict:
        # No sections found, return text with empty sections
        return TextExport(
            ID=text_data["ID"],
            title=text_data["title"],
            source=text_data["source"],
            comment=text_data["comment"],
            language_code=text_data["language_code"],
            sections=[]
        )
    
    # Fetch phrases for each section
    phrases_query = """
        MATCH (s:Section)-[:PHRASE_IN_SECTION]->(p:Phrase)
        WHERE s.ID IN $section_ids
        RETURN 
            s.ID AS section_id,
            p.ID AS phrase_id,
            p.segnum AS phrase_segnum,
            p.surface_text AS phrase_surface_text,
            p.language AS phrase_language
        ORDER BY s.ID, p.ID
    """
    
    section_ids = list(sections_dict.keys())
    phrases_result = db.run(phrases_query, section_ids=section_ids)
    phrases_dict: Dict[str, PhraseExport] = {}
    
    for record in phrases_result:
        section_id = record["section_id"]
        phrase_id = record["phrase_id"]
        
        phrase = PhraseExport(
            ID=phrase_id,
            segnum=record.get("phrase_segnum") or "",
            surface_text=record.get("phrase_surface_text") or "",
            language=normalize_language_code(record.get("phrase_language")) or text_data["language_code"],
            words=[],
            order=len(sections_dict[section_id].phrases)
        )
        
        phrases_dict[phrase_id] = phrase
        phrase_section_map[phrase_id] = section_id
        sections_dict[section_id].phrases.append(phrase)
    
    if not phrases_dict:
        # No phrases found, return text with sections but no phrases
        sections = sorted(sections_dict.values(), key=lambda s: s.order)
        return TextExport(
            ID=text_data["ID"],
            title=text_data["title"],
            source=text_data["source"],
            comment=text_data["comment"],
            language_code=text_data["language_code"],
            sections=sections
        )
    
    # Fetch words for each phrase with their order from PHRASE_COMPOSED_OF relationship
    words_query = """
        MATCH (p:Phrase)-[r:PHRASE_COMPOSED_OF]->(w:Word)
        WHERE p.ID IN $phrase_ids
        OPTIONAL MATCH (w)-[:WORD_MADE_OF]->(m:Morpheme)
        WITH p, r, w, m
        ORDER BY p.ID, r.Order, m.ID
        RETURN 
            p.ID AS phrase_id,
            r.Order AS word_order,
            w.ID AS word_id,
            w.surface_form AS word_surface_form,
            w.gloss AS word_gloss,
            w.pos AS word_pos,
            w.language AS word_language,
            m.ID AS morph_id,
            m.type AS morph_type,
            m.surface_form AS morph_surface_form,
            m.citation_form AS morph_citation_form,
            m.gloss AS morph_gloss,
            m.msa AS morph_msa,
            m.language AS morph_language,
            m.original_guid AS morph_original_guid
    """
    
    phrase_ids = list(phrases_dict.keys())
    words_result = db.run(words_query, phrase_ids=phrase_ids)
    
    words_dict: Dict[str, WordExport] = {}  # word_id -> word
    phrase_word_order: Dict[str, List[tuple]] = {}  # phrase_id -> [(word_id, order)]
    
    for record in words_result:
        phrase_id = record["phrase_id"]
        word_id = record["word_id"]
        word_order = record.get("word_order", 999)
        
        # Track word order in phrase
        if phrase_id not in phrase_word_order:
            phrase_word_order[phrase_id] = []
        if word_id not in [wid for wid, _ in phrase_word_order[phrase_id]]:
            phrase_word_order[phrase_id].append((word_id, word_order))
        
        # Create word if not exists
        if word_id not in words_dict:
            pos = record.get("word_pos") or ""
            is_punct = pos.upper() == "PUNCT" or pos.lower() == "punct"
            
            phrase = phrases_dict[phrase_id]
            word = WordExport(
                ID=word_id,
                surface_form=record.get("word_surface_form") or "",
                gloss=record.get("word_gloss") or "",
                pos=pos if not is_punct else "",
                language=normalize_language_code(record.get("word_language")) or phrase.language,
                morphemes=[],
                is_punctuation=is_punct
            )
            words_dict[word_id] = word
        
        word = words_dict[word_id]
        
        # Handle morpheme
        morph_id = record.get("morph_id")
        if morph_id:
            # Check if morpheme already added
            if not any(m.ID == morph_id for m in word.morphemes):
                morph = MorphemeExport(
                    ID=morph_id,
                    type=record.get("morph_type"),
                    surface_form=record.get("morph_surface_form") or "",
                    citation_form=record.get("morph_citation_form") or "",
                    gloss=record.get("morph_gloss") or "",
                    msa=record.get("morph_msa") or "",
                    language=normalize_language_code(record.get("morph_language")) or word.language,
                    original_guid=record.get("morph_original_guid"),
                )
                word.morphemes.append(morph)
    
    # Add words to phrases in correct order
    for phrase_id, phrase in phrases_dict.items():
        if phrase_id in phrase_word_order:
            # Sort by word_order
            ordered_words = sorted(phrase_word_order[phrase_id], key=lambda x: x[1])
            for word_id, _ in ordered_words:
                if word_id in words_dict:
                    phrase.words.append(words_dict[word_id])
    
    # Sort sections by order
    sections = sorted(sections_dict.values(), key=lambda s: s.order)
    
    return TextExport(
        ID=text_data["ID"],
        title=text_data["title"],
        source=text_data["source"],
        comment=text_data["comment"],
        language_code=text_data["language_code"],
        sections=sections
    )


def normalize_language_code(code: Optional[str]) -> Optional[str]:
    """Normalize language code for FLEXText export.
    
    Handles empty strings, None, and ensures proper formatting.
    
    Args:
        code: Language code string (may be None or empty)
        
    Returns:
        Normalized language code or None
    """
    if not code or not code.strip():
        return None
    return code.strip()

