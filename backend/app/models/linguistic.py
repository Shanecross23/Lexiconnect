from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple, Union

from pydantic import BaseModel, Field, ConfigDict, conint, confloat, model_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class IdSchema(BaseSchema):
    id: str = Field(alias="ID")


class MorphemeType(str, Enum):
    STEM = "stem"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    INFIX = "infix"
    CIRCUMFIX = "circumfix"
    ROOT = "root"
    CLITIC = "clitic"
    REDUP = "redup"
    OTHER = "other"


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


class GlossTarget(str, Enum):
    WORD = "word"
    PHRASE = "phrase"
    MORPHEME = "morpheme"


class RelationType(str, Enum):
    ALLOMORPH = "allomorph"
    COGNATE = "cognate"
    VARIANT = "variant"


class FrequencyItem(str, Enum):
    WORD = "word"
    MORPHEME = "morpheme"
    POS = "pos"


# Create models
class MorphemeCreate(IdSchema):
    original_guid: Optional[str] = None
    type: MorphemeType
    surface_form: str = ""
    citation_form: str = ""
    gloss: str = ""
    msa: Union[Dict[str, str], List[str], str] = ""
    language: str


class WordCreate(IdSchema):
    surface_form: str
    gloss: str = ""
    pos: List[str] = Field(default_factory=list)
    morphemes: List[MorphemeCreate] = Field(default_factory=list)
    language: str


class PhraseCreate(IdSchema):
    segnum: str = ""
    surface_text: str = ""
    words: List[WordCreate] = Field(default_factory=list)
    language: str
    order: conint(ge=0) = 0


class SectionCreate(IdSchema):
    order: conint(ge=0) = 0
    phrases: List[PhraseCreate] = Field(default_factory=list)
    # If you truly allow words-at-section, ensure phrases==[] when words!=[]
    words: List[WordCreate] = Field(default_factory=list)


class GlossCreate(IdSchema):
    annotation: str
    gloss_type: GlossTarget = GlossTarget.WORD
    target_id: str  # the id of the word/phrase/morpheme
    language: str = "en"


class InterlinearTextCreate(IdSchema):
    title: str
    source: str = ""
    comment: str = ""
    language: str
    sections: List[SectionCreate] = Field(default_factory=list)
    paragraphs: List["ParagraphCreate"] = Field(
        default_factory=list
    )  # if keeping legacy


# Response models
class MorphemeResponse(IdSchema):
    type: MorphemeType
    surface_form: str
    citation_form: str
    gloss: str
    msa: Union[Dict[str, str], List[str], str]
    language: str
    created_at: datetime


class WordResponse(IdSchema):
    surface_form: str
    gloss: str
    pos: List[str]
    language: str
    morpheme_count: int
    created_at: datetime


class PhraseResponse(IdSchema):
    segnum: str
    surface_text: str
    language: str
    word_count: int
    created_at: datetime


class SectionResponse(IdSchema):
    order: int
    phrase_count: int
    word_count: int
    created_at: datetime


class GlossResponse(IdSchema):
    annotation: str
    gloss_type: GlossTarget
    language: str
    created_at: datetime


class InterlinearTextResponse(IdSchema):
    title: str
    source: str
    comment: str
    language: str
    section_count: int
    word_count: int
    morpheme_count: int
    created_at: datetime


# Keep Paragraph models for backward compatibility during transition
# Note: Parser uses guid=, but we standardize to ID for consistency
class ParagraphCreate(BaseSchema):
    id: str = Field(alias="ID")
    order: conint(ge=0) = 0
    phrases: List[PhraseCreate] = Field(default_factory=list)

    # Allow 'guid' as a field name for backward compatibility with parser
    @model_validator(mode="before")
    @classmethod
    def convert_guid_to_id(cls, data):
        if (
            isinstance(data, dict)
            and "guid" in data
            and "ID" not in data
            and "id" not in data
        ):
            data["ID"] = data.pop("guid")
        return data


class ParagraphResponse(IdSchema):
    order: int
    phrase_count: int
    created_at: datetime


# Queries
class MorphemeSearchQuery(BaseSchema):
    surface_form: Optional[str] = None
    citation_form: Optional[str] = None
    gloss: Optional[str] = None
    type: Optional[MorphemeType] = None
    language: Optional[str] = None
    limit: conint(ge=1, le=200) = 50
    offset: conint(ge=0) = 0


class WordSearchQuery(BaseSchema):
    surface_form: Optional[str] = None
    gloss: Optional[str] = None
    pos: Optional[str] = None
    language: Optional[str] = None
    contains_morpheme: Optional[str] = None
    limit: conint(ge=1, le=200) = 50
    offset: conint(ge=0) = 0


class ConcordanceQuery(BaseSchema):
    target: str
    target_type: GlossTarget  # reuse enum for target granularity if you like
    context_size: conint(ge=0, le=10) = 3
    language: Optional[str] = None
    limit: conint(ge=1, le=500) = 100


class ConcordanceResult(BaseSchema):
    target: str
    left_context: List[str]
    right_context: List[str]
    phrase_id: str
    text_title: str
    segnum: str
    word_index: Optional[int] = None
    token_span: Optional[Tuple[int, int]] = None
    glosses: Optional[List[str]] = None


class FrequencyQuery(BaseSchema):
    item_type: FrequencyItem
    language: Optional[str] = None
    min_frequency: conint(ge=1) = 1
    limit: conint(ge=1, le=1000) = 100


class FrequencyResult(BaseSchema):
    item: str
    frequency: int
    percentage: float


class MorphemeRelation(BaseSchema):
    morpheme1_id: str
    morpheme2_id: str
    relation_type: RelationType
    confidence: confloat(ge=0.0, le=1.0) = 1.0
    notes: Optional[str] = None


class LexemeCreate(BaseSchema):
    citation_form: str
    meaning: str
    pos: List[str] = Field(default_factory=list)
    language: str
    frequency: conint(ge=0) = 0


class LexemeResponse(IdSchema):
    citation_form: str
    meaning: str
    pos: List[str]
    language: str
    frequency: int
    morpheme_count: int
    created_at: datetime
