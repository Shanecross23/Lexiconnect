
from xml.etree import ElementTree as ET
import uuid, json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

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


def parse_eaf_file(file_path: str) -> Dict[str, Any]:
    parser = ElanParser()
    doc = parser.parse_file(file_path)
    return parser.to_jsonable(doc)

def parse_eaf_to_json_string(file_path: str, pretty: bool = True) -> str:
    parser = ElanParser()
    doc = parser.parse_file(file_path)
    return parser.to_json_string(doc, pretty=pretty)
