from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class MorphemeType(str, Enum):
    STEM = "stem"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    INFIX = "infix"
    CIRCUMFIX = "circumfix"
    ROOT = "root"


class ItemType(str, Enum):
    TXT = "txt"  # surface form
    CF = "cf"  # citation form
    GLS = "gls"  # gloss
    MSA = "msa"  # morphosyntactic analysis
    POS = "pos"  # part of speech
    PUNCT = "punct"  # punctuation
    SEGNUM = "segnum"  # segment number
    TITLE = "title"  # title
    SOURCE = "source"  # source
    COMMENT = "comment"  # comment
    HN = "hn"  # homonym number


# Base models for linguistic entities
class LinguisticItem(BaseModel):
    type: ItemType
    lang: str
    text: str


class MorphemeCreate(BaseModel):
    ID: str  # Using ID to match schema
    type: MorphemeType
    surface_form: str = ""
    citation_form: str = ""
    gloss: str = ""
    msa: str = ""
    language: str


class MorphemeResponse(BaseModel):
    ID: str
    type: MorphemeType
    surface_form: str
    citation_form: str
    gloss: str
    msa: str
    language: str
    created_at: str


class WordCreate(BaseModel):
    ID: str  # Using ID to match schema
    surface_form: str
    gloss: str = ""
    pos: str = ""
    morphemes: List[MorphemeCreate] = []
    language: str


class WordResponse(BaseModel):
    ID: str
    surface_form: str
    gloss: str
    pos: str
    language: str
    morpheme_count: int
    created_at: str


class PhraseCreate(BaseModel):
    ID: str  # Using ID to match schema
    segnum: str = ""
    surface_text: str = ""
    words: List[WordCreate] = []
    language: str
    order: int = 0  # For PHRASE_COMPOSED_OF relationship


class PhraseResponse(BaseModel):
    ID: str
    segnum: str
    surface_text: str
    language: str
    word_count: int
    created_at: str


class GlossCreate(BaseModel):
    """Gloss annotation model aligned with DATABASE.md schema"""

    ID: str
    annotation: str  # The gloss text/annotation
    gloss_type: str = "word"  # "word", "phrase", or "morpheme"
    language: str = "en"  # Language of the gloss


class GlossResponse(BaseModel):
    ID: str
    annotation: str
    gloss_type: str
    language: str
    created_at: str


class SectionCreate(BaseModel):
    """Section model aligned with DATABASE.md schema"""

    ID: str  # Using ID to match schema
    order: int = 0
    phrases: List[PhraseCreate] = []
    words: List[WordCreate] = []  # Sections can contain words directly


class SectionResponse(BaseModel):
    ID: str
    order: int
    phrase_count: int
    word_count: int
    created_at: str


# Keep Paragraph models for backward compatibility during transition
class ParagraphCreate(BaseModel):
    guid: str
    order: int
    phrases: List[PhraseCreate] = []


class ParagraphResponse(BaseModel):
    id: str
    guid: str
    order: int
    phrase_count: int
    created_at: str


class InterlinearTextCreate(BaseModel):
    ID: str  # Using ID to match schema
    title: str
    source: str = ""
    comment: str = ""
    language_code: str
    sections: List[SectionCreate] = []
    # Keep for backward compatibility during transition
    paragraphs: List[ParagraphCreate] = []


class InterlinearTextResponse(BaseModel):
    ID: str
    title: str
    source: str
    comment: str
    language_code: str
    section_count: int
    word_count: int
    morpheme_count: int
    created_at: str


# Search and analysis models
class MorphemeSearchQuery(BaseModel):
    surface_form: Optional[str] = None
    citation_form: Optional[str] = None
    gloss: Optional[str] = None
    type: Optional[MorphemeType] = None
    language: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class WordSearchQuery(BaseModel):
    surface_form: Optional[str] = None
    gloss: Optional[str] = None
    pos: Optional[str] = None
    language: Optional[str] = None
    contains_morpheme: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class ConcordanceQuery(BaseModel):
    target: str  # word or morpheme to search for
    target_type: str  # "word" or "morpheme"
    context_size: int = 3  # number of words before/after
    language: Optional[str] = None
    limit: int = 100


class ConcordanceResult(BaseModel):
    target: str
    left_context: List[str]
    right_context: List[str]
    phrase_id: str
    text_title: str
    segnum: str


# Frequency analysis models
class FrequencyResult(BaseModel):
    item: str
    frequency: int
    percentage: float


class FrequencyQuery(BaseModel):
    item_type: str  # "word", "morpheme", "pos"
    language: Optional[str] = None
    min_frequency: int = 1
    limit: int = 100


# Linguistic relationship models
class MorphemeRelation(BaseModel):
    morpheme1_id: str
    morpheme2_id: str
    relation_type: str  # "allomorph", "cognate", "variant"
    confidence: float = 1.0
    notes: str = ""


class LexemeCreate(BaseModel):
    citation_form: str
    meaning: str
    pos: str
    language: str
    frequency: int = 0


class LexemeResponse(BaseModel):
    id: str
    citation_form: str
    meaning: str
    pos: str
    language: str
    frequency: int
    morpheme_count: int
    created_at: str
