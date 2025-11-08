
from xml.etree import ElementTree as ET
import uuid, json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from app.models.linguistic import (
    InterlinearTextCreate,
    SectionCreate,
    PhraseCreate,
    WordCreate,
    MorphemeCreate,
    MorphemeType,
)

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")

def stable_uuid(*parts: str) -> str:
    return str(uuid.uuid5(_UUID_NS, "|".join(parts)))

@dataclass
class ElanAnnotation:
    ID: str
    start_ms: Optional[int]
    end_ms: Optional[int]
    value: str
    ref_id: Optional[str] = None
    tier_id: Optional[str] = None

@dataclass
class ElanTier:
    ID: str
    participant: Optional[str]
    linguistic_type_ref: Optional[str]
    parent_ref: Optional[str]
    annotations: List[ElanAnnotation] = field(default_factory=list)

@dataclass
class ElanDoc:
    file: str
    author: Optional[str]
    date: Optional[str]
    media: List[Dict[str, Any]]
    time_slots: Dict[str, int]
    tiers: List[ElanTier]

class ElanParser:
    def parse_file(self, file_path: str) -> ElanDoc:
        tree = ET.parse(file_path)
        root = tree.getroot()
        author = root.attrib.get("AUTHOR")
        date = root.attrib.get("DATE")
        media = [md.attrib.copy() for md in root.findall("./HEADER/MEDIA_DESCRIPTOR")]
        time_slots: Dict[str, int] = {}
        for ts in root.findall("./TIME_ORDER/TIME_SLOT"):
            ts_id = ts.attrib.get("TIME_SLOT_ID")
            tv = ts.attrib.get("TIME_VALUE")
            if ts_id and tv is not None:
                try:
                    time_slots[ts_id] = int(tv)
                except:
                    pass
        tiers: List[ElanTier] = []
        for tier_el in root.findall("./TIER"):
            tier = ElanTier(
                ID = tier_el.attrib.get("TIER_ID", ""),
                participant = tier_el.attrib.get("PARTICIPANT"),
                linguistic_type_ref = tier_el.attrib.get("LINGUISTIC_TYPE_REF"),
                parent_ref = tier_el.attrib.get("PARENT_REF"),
            )
            for ann_wrap in tier_el.findall("./ANNOTATION"):
                align = ann_wrap.find("./ALIGNABLE_ANNOTATION")
                if align is not None:
                    aid = align.attrib.get("ANNOTATION_ID")
                    ts1 = align.attrib.get("TIME_SLOT_REF1")
                    ts2 = align.attrib.get("TIME_SLOT_REF2")
                    start_ms = time_slots.get(ts1)
                    end_ms = time_slots.get(ts2)
                    val_el = align.find("./ANNOTATION_VALUE")
                    value = (val_el.text or "") if val_el is not None else ""
                    tier.annotations.append(
                        ElanAnnotation(
                            ID=aid or stable_uuid(file_path, tier.ID, str(start_ms or 0), str(end_ms or 0), value[:32]),
                            start_ms=start_ms,
                            end_ms=end_ms,
                            value=value.strip(),
                            ref_id=None,
                            tier_id=tier.ID
                        )
                    )
                    continue
                ref = ann_wrap.find("./REF_ANNOTATION")
                if ref is not None:
                    aid = ref.attrib.get("ANNOTATION_ID")
                    ref_id = ref.attrib.get("ANNOTATION_REF")
                    val_el = ref.find("./ANNOTATION_VALUE")
                    value = (val_el.text or "") if val_el is not None else ""
                    tier.annotations.append(
                        ElanAnnotation(
                            ID=aid or stable_uuid(file_path, tier.ID, ref_id or "", value[:32]),
                            start_ms=None,
                            end_ms=None,
                            value=value.strip(),
                            ref_id=ref_id,
                            tier_id=tier.ID
                        )
                    )
            tiers.append(tier)
        return ElanDoc(
            file=file_path.split("/")[-1],
            author=author,
            date=date,
            media=media,
            time_slots=time_slots,
            tiers=tiers
        )

    def get_file_stats(self, doc: ElanDoc) -> Dict[str, Any]:
        total_annotations = sum(len(t.annotations) for t in doc.tiers)
        alignable = sum(1 for t in doc.tiers for a in t.annotations if a.start_ms is not None)
        ref_only = total_annotations - alignable
        return {
            "file": doc.file,
            "num_tiers": len(doc.tiers),
            "num_time_slots": len(doc.time_slots),
            "total_annotations": total_annotations,
            "alignable_annotations": alignable,
            "ref_annotations": ref_only,
            "tiers": [
                {"tier_id": t.ID, "num_annotations": len(t.annotations),
                 "participant": t.participant, "ling_type": t.linguistic_type_ref, "parent": t.parent_ref}
                for t in doc.tiers
            ]
        }

    def to_jsonable(self, doc: ElanDoc) -> Dict[str, Any]:
        return {
            "file": doc.file,
            "author": doc.author,
            "date": doc.date,
            "media": doc.media,
            "time_slots": doc.time_slots,
            "tiers": [
                {
                    "tier_id": t.ID,
                    "participant": t.participant,
                    "linguistic_type_ref": t.linguistic_type_ref,
                    "parent_ref": t.parent_ref,
                    "annotations": [
                        {
                            "id": a.ID,
                            "start_ms": a.start_ms,
                            "end_ms": a.end_ms,
                            "value": a.value,
                            "ref_id": a.ref_id
                        } for a in t.annotations
                    ]
                } for t in doc.tiers
            ]
        }

    def to_json_string(self, doc: ElanDoc, pretty: bool = True) -> str:
        data = self.to_jsonable(doc)
        return json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)

    def parse_to_interlinear_texts(self, file_path: str) -> List[InterlinearTextCreate]:
        """Parse an ELAN file and return list of InterlinearText objects matching Flex model"""
        doc = self.parse_file(file_path)
        return self._convert_elan_to_interlinear_texts(doc, file_path)

    def _convert_elan_to_interlinear_texts(
        self, doc: ElanDoc, file_path: str
    ) -> List[InterlinearTextCreate]:
        """Convert ElanDoc structure to InterlinearTextCreate objects"""
        
        # Find the main transcription tier (typically a tier without parent or most common parent)
        main_tier = self._find_main_transcription_tier(doc.tiers)
        if not main_tier:
            # If no main tier found, use the first tier with alignable annotations
            for tier in doc.tiers:
                if any(a.start_ms is not None for a in tier.annotations):
                    main_tier = tier
                    break
        
        if not main_tier:
            # Fallback: create empty text if no suitable tier found
            text_id = stable_uuid("text", file_path, doc.file)
            return [
                InterlinearTextCreate(
                    id=text_id,
                    title=doc.file,
                    source=doc.author or "",
                    comment=doc.date or "",
                    language="unknown",
                    sections=[],
                    paragraphs=[],
                )
            ]

        # Group alignable annotations by time to create sections
        alignable_anns = [
            a for a in main_tier.annotations if a.start_ms is not None
        ]
        alignable_anns.sort(key=lambda x: x.start_ms or 0)

        # Create sections from alignable annotations (each annotation becomes a phrase)
        sections = []
        for section_idx, ann in enumerate(alignable_anns):
            phrases = []
            phrase = self._create_phrase_from_annotation(
                ann, main_tier, doc.tiers, section_idx, file_path
            )
            if phrase:
                phrases.append(phrase)

            if phrases:
                section_id = stable_uuid("section", file_path, str(section_idx))
                all_words = []
                for phrase in phrases:
                    all_words.extend(phrase.words)

                sections.append(
                    SectionCreate(
                        id=section_id,
                        order=section_idx,
                        phrases=phrases,
                        words=all_words,
                    )
                )

        # Create the text
        text_id = stable_uuid("text", file_path, doc.file)
        language = self._detect_language(doc.tiers) or "unknown"

        return [
            InterlinearTextCreate(
                id=text_id,
                title=doc.file,
                source=doc.author or "",
                comment=doc.date or "",
                language=language,
                sections=sections,
                paragraphs=[],
            )
        ]

    def _find_main_transcription_tier(self, tiers: List[ElanTier]) -> Optional[ElanTier]:
        """Find the main transcription tier (typically one without parent)"""
        # Look for tier without parent
        for tier in tiers:
            if not tier.parent_ref:
                # Check if it has alignable annotations
                if any(a.start_ms is not None for a in tier.annotations):
                    return tier
        
        # If all have parents, find the most common parent (likely the main tier)
        parent_counts: Dict[str, int] = {}
        for tier in tiers:
            if tier.parent_ref:
                parent_counts[tier.parent_ref] = parent_counts.get(tier.parent_ref, 0) + 1
        
        if parent_counts:
            most_common_parent = max(parent_counts.items(), key=lambda x: x[1])[0]
            for tier in tiers:
                if tier.ID == most_common_parent:
                    return tier
        
        return None

    def _create_phrase_from_annotation(
        self,
        ann: ElanAnnotation,
        main_tier: ElanTier,
        all_tiers: List[ElanTier],
        phrase_order: int,
        file_path: str,
    ) -> Optional[PhraseCreate]:
        """Create a PhraseCreate from an ELAN annotation and its child annotations"""
        
        phrase_id = stable_uuid("phrase", file_path, ann.ID, str(phrase_order))
        surface_text = ann.value.strip()
        
        # Find child tiers (tiers that have this tier as parent)
        child_tiers = [
            tier for tier in all_tiers if tier.parent_ref == main_tier.ID
        ]
        
        # Look for annotations that reference this annotation
        child_annotations: Dict[str, List[ElanAnnotation]] = {}
        for tier in child_tiers:
            for child_ann in tier.annotations:
                if child_ann.ref_id == ann.ID:
                    tier_type = tier.linguistic_type_ref or tier.ID.lower()
                    if tier_type not in child_annotations:
                        child_annotations[tier_type] = []
                    child_annotations[tier_type].append(child_ann)

        # Parse words from surface text and match with gloss/translation tiers
        words = []
        if surface_text:
            # Split surface text into words
            word_tokens = surface_text.split()
            for word_idx, token in enumerate(word_tokens):
                word_id = stable_uuid("word", phrase_id, str(word_idx))
                
                # Try to find matching gloss/translation from child annotations
                gloss = ""
                pos: List[str] = []
                morphemes: List[MorphemeCreate] = []
                
                # Look for gloss tier
                for tier_type, anns in child_annotations.items():
                    tier_type_lower = tier_type.lower()
                    if "gloss" in tier_type_lower or "gls" in tier_type_lower:
                        # Try to match by position or use first available
                        if anns:
                            # Simple heuristic: use annotation at same index or first one
                            if word_idx < len(anns):
                                gloss = anns[word_idx].value.strip()
                            elif anns:
                                # If fewer annotations than words, use first available
                                gloss = anns[0].value.strip()
                    elif "pos" in tier_type_lower or "part" in tier_type_lower:
                        if anns and word_idx < len(anns):
                            pos_str = anns[word_idx].value.strip()
                            pos = [p.strip() for p in pos_str.split(",") if p.strip()]
                    elif "morph" in tier_type_lower or "morpheme" in tier_type_lower:
                        if anns and word_idx < len(anns):
                            morph_value = anns[word_idx].value.strip()
                            # Try to parse morpheme (simple heuristic)
                            if morph_value:
                                morph_id = stable_uuid(
                                    "morph", word_id, morph_value, str(0)
                                )
                                morphemes.append(
                                    MorphemeCreate(
                                        id=morph_id,
                                        type=MorphemeType.OTHER,
                                        surface_form=morph_value,
                                        citation_form="",
                                        gloss="",
                                        msa="",
                                        language="unknown",
                                    )
                                )

                words.append(
                    WordCreate(
                        id=word_id,
                        surface_form=token,
                        gloss=gloss,
                        pos=pos,
                        morphemes=morphemes,
                        language="unknown",
                    )
                )

        language = self._detect_language_from_tier(main_tier) or "unknown"

        return PhraseCreate(
            id=phrase_id,
            segnum=str(phrase_order),
            surface_text=surface_text,
            words=words,
            language=language,
            order=phrase_order,
        )

    def _detect_language(self, tiers: List[ElanTier]) -> Optional[str]:
        """Try to detect language from tier names or linguistic types"""
        for tier in tiers:
            lang = self._detect_language_from_tier(tier)
            if lang and lang != "unknown":
                return lang
        return None

    def _detect_language_from_tier(self, tier: ElanTier) -> Optional[str]:
        """Try to detect language from a single tier"""
        # Check linguistic type ref for language codes
        if tier.linguistic_type_ref:
            ling_type = tier.linguistic_type_ref.lower()
            # Common language codes in tier names
            for code in ["eng", "en", "spa", "es", "fra", "fr", "deu", "de"]:
                if code in ling_type:
                    return code[:2] if len(code) > 2 else code
        
        # Check tier ID
        tier_id_lower = tier.ID.lower()
        for code in ["eng", "en", "spa", "es", "fra", "fr", "deu", "de"]:
            if code in tier_id_lower:
                return code[:2] if len(code) > 2 else code
        
        return None

    def get_language_stats(self, texts: List[InterlinearTextCreate]) -> Dict[str, Any]:
        """Generate comprehensive statistics about the parsed texts (matching Flex parser interface)"""
        languages_set: set[str] = set()
        pos_tags_set: set[str] = set()
        morpheme_types_dict: Dict[str, int] = {}

        total_sections = 0
        total_phrases = 0
        total_words = 0
        total_morphemes = 0
        
        words_with_morphemes = 0
        words_with_only_translation = 0
        annotated_texts = 0
        words_by_whitespace = 0
        
        texts_with_morphemes = set()

        for text in texts:
            languages_set.add(text.language)
            total_sections += len(text.sections)
            text_has_morphemes = False

            for section in text.sections:
                total_phrases += len(section.phrases)

                for phrase in section.phrases:
                    total_words += len(phrase.words)
                    
                    if phrase.surface_text:
                        whitespace_words = [
                            w for w in phrase.surface_text.split() 
                            if w.strip()
                        ]
                        words_by_whitespace += len(whitespace_words)

                    for word in phrase.words:
                        if word.pos:
                            for pos_tag in word.pos:
                                pos_tags_set.add(pos_tag)
                        
                        if word.morphemes and len(word.morphemes) > 0:
                            words_with_morphemes += 1
                            text_has_morphemes = True
                        elif word.gloss and word.gloss.strip():
                            words_with_only_translation += 1
                        
                        total_morphemes += len(word.morphemes)

                        for morpheme in word.morphemes:
                            morph_type = morpheme.type.value
                            morpheme_types_dict[morph_type] = (
                                morpheme_types_dict.get(morph_type, 0) + 1
                            )
            
            if text_has_morphemes:
                texts_with_morphemes.add(text.id)
        
        annotated_texts = len(texts_with_morphemes)

        return {
            "total_texts": len(texts),
            "annotated_texts": annotated_texts,
            "total_sections": total_sections,
            "total_phrases": total_phrases,
            "total_sentences": total_phrases,
            "total_words": total_words,
            "words_by_whitespace": words_by_whitespace,
            "words_with_morphemes": words_with_morphemes,
            "words_with_only_translation": words_with_only_translation,
            "total_morphemes": total_morphemes,
            "languages": list(languages_set),
            "morpheme_types": morpheme_types_dict,
            "pos_tags": list(pos_tags_set),
        }


def parse_eaf_file(file_path: str) -> Dict[str, Any]:
    parser = ElanParser()
    doc = parser.parse_file(file_path)
    return parser.to_jsonable(doc)

def parse_eaf_to_json_string(file_path: str, pretty: bool = True) -> str:
    parser = ElanParser()
    doc = parser.parse_file(file_path)
    return parser.to_json_string(doc, pretty=pretty)


def parse_elan_file(file_path: str) -> List[InterlinearTextCreate]:
    """Convenience function to parse an ELAN file to InterlinearTextCreate objects (matching Flex parser interface)"""
    parser = ElanParser()
    return parser.parse_to_interlinear_texts(file_path)


def get_elan_file_stats(file_path: str) -> Dict[str, Any]:
    """Get statistics for an ELAN file (matching Flex parser interface)"""
    parser = ElanParser()
    texts = parser.parse_to_interlinear_texts(file_path)
    return parser.get_language_stats(texts)
