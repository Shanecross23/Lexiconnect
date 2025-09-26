from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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
    guid: str
    type: MorphemeType
    surface_form: str = ""
    citation_form: str = ""
    gloss: str = ""
    msa: str = ""
    language: str


class MorphemeResponse(BaseModel):
    id: str
    guid: str
    type: MorphemeType
    surface_form: str
    citation_form: str
    gloss: str
    msa: str
    language: str
    created_at: str


class WordCreate(BaseModel):
    guid: str
    surface_form: str
    gloss: str = ""
    pos: str = ""
    morphemes: List[MorphemeCreate] = []
    language: str


class WordResponse(BaseModel):
    id: str
    guid: str
    surface_form: str
    gloss: str
    pos: str
    language: str
    morpheme_count: int
    created_at: str


class PhraseCreate(BaseModel):
    guid: str
    segnum: str = ""
    surface_text: str = ""
    words: List[WordCreate] = []
    language: str


class PhraseResponse(BaseModel):
    id: str
    guid: str
    segnum: str
    surface_text: str
    language: str
    word_count: int
    created_at: str


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
    guid: str
    title: str
    source: str = ""
    comment: str = ""
    language_code: str
    paragraphs: List[ParagraphCreate] = []


class InterlinearTextResponse(BaseModel):
    id: str
    guid: str
    title: str
    source: str
    comment: str
    language_code: str
    paragraph_count: int
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
    limit: int = 50


class WordSearchQuery(BaseModel):
    surface_form: Optional[str] = None
    gloss: Optional[str] = None
    pos: Optional[str] = None
    contains_morpheme: Optional[str] = None
    language: Optional[str] = None
    limit: int = 50


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
