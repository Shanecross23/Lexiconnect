from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from app.database import get_db_dependency
from app.models.linguistic import (
    InterlinearTextCreate,
    InterlinearTextResponse,
    WordCreate,
    WordSearchQuery,
    WordResponse,
    MorphemeCreate,
    MorphemeSearchQuery,
    MorphemeResponse,
    ConcordanceQuery,
    ConcordanceResult,
    FrequencyQuery,
    FrequencyResult,
    LexemeResponse,
)
from app.parsers.flextext_parser import parse_flextext_file, get_file_stats
import uuid
import tempfile
import os

router = APIRouter()


@router.post("/upload-flextext")
async def upload_flextext_file(
    file: UploadFile = File(...), db=Depends(get_db_dependency)
):
    """Upload and parse a FLEx .flextext file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".flextext") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Parse the file
            texts = parse_flextext_file(temp_file_path)
            stats = get_file_stats(temp_file_path)

            # Store in graph database
            processed_texts = []
            for text in texts:
                text_id = await _store_interlinear_text(text, db)
                processed_texts.append(text_id)

            return {
                "message": f"Successfully uploaded and processed {file.filename}",
                "file_stats": stats,
                "processed_texts": processed_texts,
            }

        finally:
            # Clean up temp file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _store_interlinear_text(text: InterlinearTextCreate, db) -> str:
    """Store an interlinear text and all its components in the graph database"""

    # Create the text node
    text_id = str(uuid.uuid4())
    db.run(
        """
        CREATE (t:Text {
            id: $id,
            guid: $guid,
            title: $title,
            source: $source,
            comment: $comment,
            language_code: $language_code,
            created_at: datetime()
        })
    """,
        id=text_id,
        guid=text.guid,
        title=text.title,
        source=text.source,
        comment=text.comment,
        language_code=text.language_code,
    )

    # Store paragraphs and their components
    for paragraph in text.paragraphs:
        paragraph_id = str(uuid.uuid4())
        db.run(
            """
            MATCH (t:Text {id: $text_id})
            CREATE (p:Paragraph {
                id: $id,
                guid: $guid,
                order: $order,
                created_at: datetime()
            })
            CREATE (t)-[:CONTAINS]->(p)
        """,
            text_id=text_id,
            id=paragraph_id,
            guid=paragraph.guid,
            order=paragraph.order,
        )

        # Store phrases and their components
        for phrase in paragraph.phrases:
            phrase_id = str(uuid.uuid4())
            db.run(
                """
                MATCH (p:Paragraph {id: $paragraph_id})
                CREATE (ph:Phrase {
                    id: $id,
                    guid: $guid,
                    segnum: $segnum,
                    surface_text: $surface_text,
                    language: $language,
                    created_at: datetime()
                })
                CREATE (p)-[:CONTAINS]->(ph)
            """,
                paragraph_id=paragraph_id,
                id=phrase_id,
                guid=phrase.guid,
                segnum=phrase.segnum,
                surface_text=phrase.surface_text,
                language=phrase.language,
            )

            # Store words and morphemes
            for word in phrase.words:
                word_id = await _store_word(word, phrase_id, db)

    return text_id


async def _store_word(word: WordCreate, phrase_id: str, db) -> str:
    """Store a word and its morphemes"""
    word_id = str(uuid.uuid4())

    # Create word node
    db.run(
        """
        MATCH (ph:Phrase {id: $phrase_id})
        CREATE (w:Word {
            id: $id,
            guid: $guid,
            surface_form: $surface_form,
            gloss: $gloss,
            pos: $pos,
            language: $language,
            created_at: datetime()
        })
        CREATE (ph)-[:CONTAINS]->(w)
    """,
        phrase_id=phrase_id,
        id=word_id,
        guid=word.guid,
        surface_form=word.surface_form,
        gloss=word.gloss,
        pos=word.pos,
        language=word.language,
    )

    # Store morphemes
    for morpheme in word.morphemes:
        morpheme_id = await _store_morpheme(morpheme, word_id, db)

    return word_id


async def _store_morpheme(morpheme: MorphemeCreate, word_id: str, db) -> str:
    """Store a morpheme and create/link to lexeme if appropriate"""

    # Check if this morpheme already exists (same citation form + gloss + language)
    existing = db.run(
        """
        MATCH (m:Morpheme {citation_form: $cf, gloss: $gloss, language: $lang})
        RETURN m.id as id
        LIMIT 1
    """,
        cf=morpheme.citation_form,
        gloss=morpheme.gloss,
        lang=morpheme.language,
    ).single()

    if existing:
        morpheme_id = existing["id"]
        # Link existing morpheme to this word
        db.run(
            """
            MATCH (w:Word {id: $word_id})
            MATCH (m:Morpheme {id: $morpheme_id})
            CREATE (w)-[:CONTAINS]->(m)
        """,
            word_id=word_id,
            morpheme_id=morpheme_id,
        )
    else:
        # Create new morpheme
        morpheme_id = str(uuid.uuid4())
        db.run(
            """
            MATCH (w:Word {id: $word_id})
            CREATE (m:Morpheme {
                id: $id,
                guid: $guid,
                type: $type,
                surface_form: $surface_form,
                citation_form: $citation_form,
                gloss: $gloss,
                msa: $msa,
                language: $language,
                created_at: datetime()
            })
            CREATE (w)-[:CONTAINS]->(m)
        """,
            word_id=word_id,
            id=morpheme_id,
            guid=morpheme.guid,
            type=morpheme.type.value,
            surface_form=morpheme.surface_form,
            citation_form=morpheme.citation_form,
            gloss=morpheme.gloss,
            msa=morpheme.msa,
            language=morpheme.language,
        )

        # Create or link to lexeme if this is a stem
        if morpheme.type.value == "stem" and morpheme.citation_form:
            await _create_or_link_lexeme(morpheme_id, morpheme, db)

    return morpheme_id


async def _create_or_link_lexeme(morpheme_id: str, morpheme: MorphemeCreate, db):
    """Create or link to a lexeme for stem morphemes"""

    # Check if lexeme already exists
    existing = db.run(
        """
        MATCH (l:Lexeme {citation_form: $cf, language: $lang})
        RETURN l.id as id
        LIMIT 1
    """,
        cf=morpheme.citation_form,
        lang=morpheme.language,
    ).single()

    if existing:
        lexeme_id = existing["id"]
        # Update frequency
        db.run(
            """
            MATCH (l:Lexeme {id: $lexeme_id})
            SET l.frequency = l.frequency + 1
        """,
            lexeme_id=lexeme_id,
        )
    else:
        # Create new lexeme
        lexeme_id = str(uuid.uuid4())
        db.run(
            """
            CREATE (l:Lexeme {
                id: $id,
                citation_form: $citation_form,
                meaning: $meaning,
                pos: $pos,
                language: $language,
                frequency: 1,
                created_at: datetime()
            })
        """,
            id=lexeme_id,
            citation_form=morpheme.citation_form,
            meaning=morpheme.gloss,
            pos=morpheme.msa,
            language=morpheme.language,
        )

    # Link morpheme to lexeme
    db.run(
        """
        MATCH (m:Morpheme {id: $morpheme_id})
        MATCH (l:Lexeme {id: $lexeme_id})
        CREATE (m)-[:REALIZES]->(l)
    """,
        morpheme_id=morpheme_id,
        lexeme_id=lexeme_id,
    )


@router.post("/search/words", response_model=List[WordResponse])
async def search_words(query: WordSearchQuery, db=Depends(get_db_dependency)):
    """Search for words based on various criteria"""
    try:
        cypher_query = "MATCH (w:Word)"
        params = {}
        conditions = []

        if query.surface_form:
            conditions.append("w.surface_form CONTAINS $surface_form")
            params["surface_form"] = query.surface_form

        if query.gloss:
            conditions.append("w.gloss CONTAINS $gloss")
            params["gloss"] = query.gloss

        if query.pos:
            conditions.append("w.pos = $pos")
            params["pos"] = query.pos

        if query.language:
            conditions.append("w.language = $language")
            params["language"] = query.language

        if query.contains_morpheme:
            cypher_query += " MATCH (w)-[:CONTAINS]->(m:Morpheme)"
            conditions.append(
                "(m.surface_form CONTAINS $morpheme OR m.citation_form CONTAINS $morpheme)"
            )
            params["morpheme"] = query.contains_morpheme

        if conditions:
            cypher_query += " WHERE " + " AND ".join(conditions)

        cypher_query += """
            OPTIONAL MATCH (w)-[:CONTAINS]->(m:Morpheme)
            RETURN w.id as id, w.guid as guid, w.surface_form as surface_form,
                   w.gloss as gloss, w.pos as pos, w.language as language,
                   COUNT(m) as morpheme_count, toString(w.created_at) as created_at
            ORDER BY w.surface_form
            LIMIT $limit
        """
        params["limit"] = query.limit

        result = db.run(cypher_query, **params)
        words = [WordResponse(**record) for record in result]
        return words

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search/morphemes", response_model=List[MorphemeResponse])
async def search_morphemes(query: MorphemeSearchQuery, db=Depends(get_db_dependency)):
    """Search for morphemes based on various criteria"""
    try:
        cypher_query = "MATCH (m:Morpheme)"
        params = {}
        conditions = []

        if query.surface_form:
            conditions.append("m.surface_form CONTAINS $surface_form")
            params["surface_form"] = query.surface_form

        if query.citation_form:
            conditions.append("m.citation_form CONTAINS $citation_form")
            params["citation_form"] = query.citation_form

        if query.gloss:
            conditions.append("m.gloss CONTAINS $gloss")
            params["gloss"] = query.gloss

        if query.type:
            conditions.append("m.type = $type")
            params["type"] = query.type.value

        if query.language:
            conditions.append("m.language = $language")
            params["language"] = query.language

        if conditions:
            cypher_query += " WHERE " + " AND ".join(conditions)

        cypher_query += """
            RETURN m.id as id, m.guid as guid, m.type as type,
                   m.surface_form as surface_form, m.citation_form as citation_form,
                   m.gloss as gloss, m.msa as msa, m.language as language,
                   toString(m.created_at) as created_at
            ORDER BY m.citation_form
            LIMIT $limit
        """
        params["limit"] = query.limit

        result = db.run(cypher_query, **params)
        morphemes = [MorphemeResponse(**record) for record in result]
        return morphemes

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/concordance", response_model=List[ConcordanceResult])
async def get_concordance(query: ConcordanceQuery, db=Depends(get_db_dependency)):
    """Get concordance (words in context) for a target word or morpheme"""
    try:
        if query.target_type == "word":
            cypher_query = """
                MATCH (ph:Phrase)-[:CONTAINS]->(target:Word {surface_form: $target})
                MATCH (ph)-[:CONTAINS]->(w:Word)
                MATCH (ph)<-[:CONTAINS]-(p:Paragraph)<-[:CONTAINS]-(t:Text)
                WITH ph, target, t, ph.segnum as segnum,
                     COLLECT({word: w.surface_form, order: id(w)}) as all_words
                UNWIND all_words as word_info
                WITH ph, target, t, segnum, word_info
                ORDER BY word_info.order
                WITH ph, target, t, segnum, COLLECT(word_info.word) as ordered_words,
                     [i IN range(0, size(COLLECT(word_info.word))-1) 
                      WHERE COLLECT(word_info.word)[i] = $target][0] as target_idx
                WHERE target_idx IS NOT NULL
                RETURN $target as target,
                       ordered_words[max(0, target_idx - $context_size)..target_idx] as left_context,
                       ordered_words[target_idx + 1..target_idx + 1 + $context_size] as right_context,
                       ph.id as phrase_id, t.title as text_title, segnum
                LIMIT $limit
            """
        else:  # morpheme
            cypher_query = """
                MATCH (w:Word)-[:CONTAINS]->(target:Morpheme)
                WHERE target.surface_form = $target OR target.citation_form = $target
                MATCH (ph:Phrase)-[:CONTAINS]->(w)
                MATCH (ph)-[:CONTAINS]->(all_w:Word)
                MATCH (ph)<-[:CONTAINS]-(p:Paragraph)<-[:CONTAINS]-(t:Text)
                WITH ph, target, w, t, ph.segnum as segnum,
                     COLLECT({word: all_w.surface_form, order: id(all_w)}) as all_words
                UNWIND all_words as word_info
                WITH ph, target, w, t, segnum, word_info
                ORDER BY word_info.order
                WITH ph, target, w, t, segnum, COLLECT(word_info.word) as ordered_words,
                     [i IN range(0, size(COLLECT(word_info.word))-1) 
                      WHERE COLLECT(word_info.word)[i] = w.surface_form][0] as target_idx
                WHERE target_idx IS NOT NULL
                RETURN $target as target,
                       ordered_words[max(0, target_idx - $context_size)..target_idx] as left_context,
                       ordered_words[target_idx + 1..target_idx + 1 + $context_size] as right_context,
                       ph.id as phrase_id, t.title as text_title, segnum
                LIMIT $limit
            """

        result = db.run(
            cypher_query,
            target=query.target,
            context_size=query.context_size,
            limit=query.limit,
        )

        concordances = [ConcordanceResult(**record) for record in result]
        return concordances

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/frequency", response_model=List[FrequencyResult])
async def get_frequency_analysis(query: FrequencyQuery, db=Depends(get_db_dependency)):
    """Get frequency analysis for words, morphemes, or POS tags"""
    try:
        if query.item_type == "word":
            cypher_query = """
                MATCH (w:Word)
                WHERE ($language IS NULL OR w.language = $language)
                WITH w.surface_form as item, COUNT(*) as frequency
                WHERE frequency >= $min_frequency
                WITH item, frequency, sum(frequency) as total
                RETURN item, frequency, round(frequency * 100.0 / total, 2) as percentage
                ORDER BY frequency DESC
                LIMIT $limit
            """
        elif query.item_type == "morpheme":
            cypher_query = """
                MATCH (m:Morpheme)
                WHERE ($language IS NULL OR m.language = $language)
                WITH m.citation_form as item, COUNT(*) as frequency
                WHERE frequency >= $min_frequency AND item <> ""
                WITH item, frequency, sum(frequency) as total
                RETURN item, frequency, round(frequency * 100.0 / total, 2) as percentage
                ORDER BY frequency DESC
                LIMIT $limit
            """
        elif query.item_type == "pos":
            cypher_query = """
                MATCH (w:Word)
                WHERE ($language IS NULL OR w.language = $language) AND w.pos <> ""
                WITH w.pos as item, COUNT(*) as frequency
                WHERE frequency >= $min_frequency
                WITH item, frequency, sum(frequency) as total
                RETURN item, frequency, round(frequency * 100.0 / total, 2) as percentage
                ORDER BY frequency DESC
                LIMIT $limit
            """
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid item_type. Use 'word', 'morpheme', or 'pos'",
            )

        result = db.run(
            cypher_query,
            language=query.language,
            min_frequency=query.min_frequency,
            limit=query.limit,
        )

        frequencies = [FrequencyResult(**record) for record in result]
        return frequencies

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/texts", response_model=List[InterlinearTextResponse])
async def get_texts(
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db=Depends(get_db_dependency),
):
    """Get list of interlinear texts"""
    try:
        cypher_query = """
            MATCH (t:Text)
            WHERE ($language IS NULL OR t.language_code = $language)
            OPTIONAL MATCH (t)-[:CONTAINS]->(p:Paragraph)-[:CONTAINS]->(ph:Phrase)-[:CONTAINS]->(w:Word)-[:CONTAINS]->(m:Morpheme)
            RETURN t.id as id, t.guid as guid, t.title as title, t.source as source,
                   t.comment as comment, t.language_code as language_code,
                   COUNT(DISTINCT p) as paragraph_count,
                   COUNT(DISTINCT w) as word_count,
                   COUNT(DISTINCT m) as morpheme_count,
                   toString(t.created_at) as created_at
            ORDER BY t.created_at DESC
            SKIP $skip LIMIT $limit
        """

        result = db.run(cypher_query, language=language, skip=skip, limit=limit)
        texts = [InterlinearTextResponse(**record) for record in result]
        return texts

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lexemes", response_model=List[LexemeResponse])
async def get_lexemes(
    language: Optional[str] = None,
    min_frequency: int = 1,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db_dependency),
):
    """Get lexemes (dictionary entries) with frequency information"""
    try:
        cypher_query = """
            MATCH (l:Lexeme)
            WHERE ($language IS NULL OR l.language = $language) 
              AND l.frequency >= $min_frequency
            OPTIONAL MATCH (l)<-[:REALIZES]-(m:Morpheme)
            RETURN l.id as id, l.citation_form as citation_form, l.meaning as meaning,
                   l.pos as pos, l.language as language, l.frequency as frequency,
                   COUNT(DISTINCT m) as morpheme_count, toString(l.created_at) as created_at
            ORDER BY l.frequency DESC, l.citation_form
            SKIP $skip LIMIT $limit
        """

        result = db.run(
            cypher_query,
            language=language,
            min_frequency=min_frequency,
            skip=skip,
            limit=limit,
        )
        lexemes = [LexemeResponse(**record) for record in result]
        return lexemes

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/morphemes/duplicates")
async def find_morpheme_duplicates(
    language: Optional[str] = None,
    similarity_threshold: float = 0.75,
    db=Depends(get_db_dependency),
):
    """Find potential duplicate morphemes with smart similarity detection"""
    try:
        cypher_query = """
        MATCH (m1:Morpheme), (m2:Morpheme)
        WHERE ($language IS NULL OR m1.language = $language)
          AND m1.language = m2.language 
          AND id(m1) < id(m2)
          AND (
            m1.citation_form = m2.citation_form 
            OR
            (abs(size(m1.surface_form) - size(m2.surface_form)) <= 1 
             AND m1.surface_form <> "" AND m2.surface_form <> "")
          )
        WITH m1, m2,
             case when m1.citation_form = m2.citation_form then 1.0 else 0.0 end as cf_score,
             case when m1.gloss = m2.gloss then 1.0 
                  when m1.gloss contains m2.gloss or m2.gloss contains m1.gloss then 0.5 
                  else 0.0 end as gloss_score,
             case when m1.surface_form = m2.surface_form then 1.0
                  when abs(size(m1.surface_form) - size(m2.surface_form)) <= 1 then 0.7
                  else 0.0 end as surface_score,
             case when m1.type = m2.type then 1.0 else 0.0 end as type_score

        WITH m1, m2, cf_score, gloss_score, surface_score, type_score,
             (cf_score + gloss_score + surface_score + type_score) / 4.0 as similarity_score

        WHERE similarity_score >= $threshold

        RETURN m1.id as id1, m1.citation_form as cf1, m1.surface_form as sf1, 
               m1.gloss as gloss1, m1.type as type1,
               m2.id as id2, m2.citation_form as cf2, m2.surface_form as sf2, 
               m2.gloss as gloss2, m2.type as type2,
               round(similarity_score, 3) as similarity,
               case 
                 when similarity_score = 1.0 then "EXACT_DUPLICATE"
                 when cf_score = 1.0 and gloss_score >= 0.5 then "ALLOMORPH"
                 when gloss_score = 1.0 and cf_score >= 0.5 then "VARIANT_ANNOTATION"
                 else "POTENTIAL_RELATED"
               end as relationship_type
        ORDER BY similarity_score DESC, m1.citation_form
        LIMIT 100
        """

        result = db.run(cypher_query, language=language, threshold=similarity_threshold)
        return [dict(record) for record in result]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/morphemes/allomorphs")
async def find_allomorphs(
    language: Optional[str] = None,
    min_variants: int = 2,
    db=Depends(get_db_dependency),
):
    """Find potential allomorphs (same morpheme with different surface forms)"""
    try:
        cypher_query = """
        MATCH (m:Morpheme)
        WHERE ($language IS NULL OR m.language = $language)
          AND m.citation_form <> ""
        WITH m.citation_form as cf, m.language as lang, 
             collect(distinct m.surface_form) as surface_forms,
             collect(distinct m.gloss) as glosses,
             count(m) as instances,
             collect(m.id) as morpheme_ids
        WHERE size(surface_forms) >= $min_variants
        RETURN cf, lang, surface_forms, glosses, instances, morpheme_ids,
               size(surface_forms) as variant_count
        ORDER BY instances DESC, variant_count DESC
        LIMIT 50
        """

        result = db.run(cypher_query, language=language, min_variants=min_variants)
        return [dict(record) for record in result]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/morphemes/data-quality")
async def check_morpheme_data_quality(
    language: Optional[str] = None,
    db=Depends(get_db_dependency),
):
    """Check for data quality issues in morpheme annotations"""
    try:
        cypher_query = """
        MATCH (m:Morpheme)
        WHERE ($language IS NULL OR m.language = $language)
          AND m.citation_form <> ""
        WITH m.citation_form as cf, m.language as lang,
             collect(distinct m.type) as types,
             collect(distinct m.msa) as msas,
             collect(distinct m.gloss) as glosses,
             count(m) as instances
        WHERE size(types) > 1 OR size(msas) > 2 OR size(glosses) > 3

        RETURN cf, lang, instances,
               types as conflicting_types,
               msas as conflicting_msas,
               glosses as variant_glosses,
               case 
                 when size(types) > 1 then "TYPE_CONFLICT"
                 when size(msas) > 2 then "MSA_CONFLICT"  
                 when size(glosses) > 3 then "GLOSS_VARIANCE"
                 else "ANNOTATION_INCONSISTENCY"
               end as issue_type,
               size(types) as type_count,
               size(msas) as msa_count,
               size(glosses) as gloss_count
        ORDER BY instances DESC, type_count DESC, gloss_count DESC
        LIMIT 100
        """

        result = db.run(cypher_query, language=language)
        return [dict(record) for record in result]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
