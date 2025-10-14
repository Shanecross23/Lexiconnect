from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from typing import List, Optional, Any
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
    SectionCreate,
    PhraseCreate,
)
from app.parsers.flextext_parser import parse_flextext_file, get_file_stats
import tempfile
import os

router = APIRouter()


@router.post("/upload-flextext")
async def upload_flextext_file(
    file: UploadFile = File(...), db=Depends(get_db_dependency)
):
    """Upload and parse a FLEx .flextext file and store in Neo4j using DATABASE.md schema"""
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

            # Store in graph database using correct schema
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
    """Store an interlinear text using DATABASE.md schema relationships"""

    # Create the Text node with ID property (matching schema)
    db.run(
        """
        MERGE (t:Text {ID: $ID})
          ON CREATE SET t.created_at = datetime()
        SET t.title = $title,
            t.source = $source,
            t.comment = $comment,
            t.language_code = $language_code,
            t.updated_at = datetime()
        """,
        ID=text.ID,
        title=text.title,
        source=text.source,
        comment=text.comment,
        language_code=text.language_code,
    )

    # Store sections and their components using correct relationships
    for section in text.sections:
        await _store_section(section, text.ID, db)

    return text.ID


async def _store_section(section: SectionCreate, text_id: str, db):
    """Store a Section node with SECTION_PART_OF_TEXT relationship"""

    # Create Section node
    db.run(
        """
        MATCH (t:Text {ID: $text_id})
        MERGE (s:Section {ID: $ID})
          ON CREATE SET s.created_at = datetime()
        SET s.order = $order,
            s.updated_at = datetime()
        MERGE (t)-[:SECTION_PART_OF_TEXT]->(s)
        """,
        text_id=text_id,
        ID=section.ID,
        order=section.order,
    )

    # Store phrases with PHRASE_IN_SECTION relationship
    for phrase in section.phrases:
        await _store_phrase(phrase, section.ID, db)

    # Store words with SECTION_CONTAINS relationship
    for word in section.words:
        await _store_word_in_section(word, section.ID, db)


async def _store_phrase(phrase: PhraseCreate, section_id: str, db):
    """Store a Phrase node with PHRASE_IN_SECTION relationship"""

    # Create Phrase node
    db.run(
        """
        MATCH (s:Section {ID: $section_id})
        MERGE (p:Phrase {ID: $ID})
          ON CREATE SET p.created_at = datetime()
        SET p.segnum = $segnum,
            p.surface_text = $surface_text,
            p.language = $language,
            p.updated_at = datetime()
        MERGE (s)-[:PHRASE_IN_SECTION]->(p)
        """,
        section_id=section_id,
        ID=phrase.ID,
        segnum=phrase.segnum,
        surface_text=phrase.surface_text,
        language=phrase.language,
    )

    # Store words in phrase with PHRASE_COMPOSED_OF relationship (includes Order property)
    for idx, word in enumerate(phrase.words):
        await _store_word_in_phrase(word, phrase.ID, idx, db)


async def _store_word_in_section(word: WordCreate, section_id: str, db):
    """Store word with SECTION_CONTAINS relationship"""

    # Create Word node
    db.run(
        """
        MATCH (s:Section {ID: $section_id})
        MERGE (w:Word {ID: $ID})
          ON CREATE SET w.created_at = datetime()
        SET w.surface_form = $surface_form,
            w.gloss = $gloss,
            w.pos = $pos,
            w.language = $language,
            w.updated_at = datetime()
        MERGE (s)-[:SECTION_CONTAINS]->(w)
        """,
        section_id=section_id,
        ID=word.ID,
        surface_form=word.surface_form,
        gloss=word.gloss,
        pos=word.pos,
        language=word.language,
    )

    # Store morphemes
    for morpheme in word.morphemes:
        await _store_morpheme(morpheme, word.ID, db)

    # Create Gloss node if word has gloss annotation
    if word.gloss:
        await _store_gloss(word.ID, word.gloss, "word", db)


async def _store_word_in_phrase(word: WordCreate, phrase_id: str, order: int, db):
    """Store word with PHRASE_COMPOSED_OF relationship (with Order property)"""

    # Create Word node
    db.run(
        """
        MATCH (p:Phrase {ID: $phrase_id})
        MERGE (w:Word {ID: $ID})
          ON CREATE SET w.created_at = datetime()
        SET w.surface_form = $surface_form,
            w.gloss = $gloss,
            w.pos = $pos,
            w.language = $language,
            w.updated_at = datetime()
        MERGE (p)-[:PHRASE_COMPOSED_OF {Order: $order}]->(w)
        """,
        phrase_id=phrase_id,
        ID=word.ID,
        order=order,
        surface_form=word.surface_form,
        gloss=word.gloss,
        pos=word.pos,
        language=word.language,
    )

    # Store morphemes
    for morpheme in word.morphemes:
        await _store_morpheme(morpheme, word.ID, db)

    # Create Gloss node if word has gloss annotation
    if word.gloss:
        await _store_gloss(word.ID, word.gloss, "word", db)


async def _store_morpheme(morpheme: MorphemeCreate, word_id: str, db):
    """Store a Morpheme node with WORD_MADE_OF relationship"""

    db.run(
        """
        MATCH (w:Word {ID: $word_id})
        MERGE (m:Morpheme {ID: $ID})
          ON CREATE SET m.created_at = datetime()
        SET m.type = $type,
            m.surface_form = $surface_form,
            m.citation_form = $citation_form,
            m.gloss = $gloss,
            m.msa = $msa,
            m.language = $language,
            m.updated_at = datetime()
        MERGE (w)-[:WORD_MADE_OF]->(m)
        """,
        word_id=word_id,
        ID=morpheme.ID,
        type=morpheme.type.value,
        surface_form=morpheme.surface_form,
        citation_form=morpheme.citation_form,
        gloss=morpheme.gloss,
        msa=morpheme.msa,
        language=morpheme.language,
    )

    # Create Gloss node if morpheme has gloss
    if morpheme.gloss:
        await _store_gloss(morpheme.ID, morpheme.gloss, "morpheme", db)


async def _store_gloss(target_id: str, annotation: str, gloss_type: str, db):
    """Create a Gloss node with ANALYZES relationship"""

    gloss_id = f"gloss-{target_id}"

    db.run(
        """
        MATCH (target {ID: $target_id})
        MERGE (g:Gloss {ID: $gloss_id})
          ON CREATE SET g.created_at = datetime()
        SET g.annotation = $annotation,
            g.gloss_type = $gloss_type,
            g.updated_at = datetime()
        MERGE (g)-[:ANALYZES]->(target)
        """,
        target_id=target_id,
        gloss_id=gloss_id,
        annotation=annotation,
        gloss_type=gloss_type,
    )


@router.post("/search/words", response_model=List[WordResponse])
async def search_words(
    query: WordSearchQuery, response: Response, db=Depends(get_db_dependency)
):
    """Search for words based on various criteria"""
    try:
        base = ["MATCH (w:Word)"]
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
            base.append("MATCH (w)-[:WORD_MADE_OF]->(m:Morpheme)")
            conditions.append(
                "(m.surface_form CONTAINS $morpheme OR m.citation_form CONTAINS $morpheme)"
            )
            params["morpheme"] = query.contains_morpheme

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_cypher = (
            "".join(base) + where_clause + " RETURN count(DISTINCT w) AS total"
        )
        total = db.run(count_cypher, **params).single()["total"]

        cypher_query = (
            "".join(base)
            + where_clause
            + """
            OPTIONAL MATCH (w)-[:WORD_MADE_OF]->(m2:Morpheme)
            WITH w, COUNT(m2) AS morpheme_count
            RETURN w.ID as ID, w.surface_form as surface_form,
                   w.gloss as gloss, w.pos as pos, w.language as language,
                   morpheme_count, toString(w.created_at) as created_at
            ORDER BY w.surface_form
            SKIP $offset
            LIMIT $limit
        """
        )
        params.update({"limit": query.limit, "offset": query.offset})

        result = db.run(cypher_query, **params)
        words = [WordResponse(**dict(record)) for record in result]

        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Limit"] = str(query.limit)
        response.headers["X-Offset"] = str(query.offset)

        return words

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search/morphemes", response_model=List[MorphemeResponse])
async def search_morphemes(
    query: MorphemeSearchQuery, response: Response, db=Depends(get_db_dependency)
):
    """Search for morphemes based on various criteria"""
    try:
        base = ["MATCH (m:Morpheme)"]
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

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_cypher = (
            "".join(base) + where_clause + " RETURN count(DISTINCT m) AS total"
        )
        total = db.run(count_cypher, **params).single()["total"]

        cypher_query = (
            "".join(base)
            + where_clause
            + """
            RETURN m.ID as ID, m.type as type,
                   m.surface_form as surface_form, m.citation_form as citation_form,
                   m.gloss as gloss, m.msa as msa, m.language as language,
                   toString(m.created_at) as created_at
            ORDER BY m.citation_form
            SKIP $offset
            LIMIT $limit
        """
        )
        params.update({"limit": query.limit, "offset": query.offset})

        result = db.run(cypher_query, **params)
        morphemes = [MorphemeResponse(**dict(record)) for record in result]

        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Limit"] = str(query.limit)
        response.headers["X-Offset"] = str(query.offset)

        return morphemes

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/texts", response_model=List[InterlinearTextResponse])
async def get_texts(
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    response: Response = None,
    db=Depends(get_db_dependency),
):
    """Get list of interlinear texts"""
    try:
        total = db.run(
            """
            MATCH (t:Text)
            WHERE ($language IS NULL OR t.language_code = $language)
            RETURN count(t) AS total
            """,
            language=language,
        ).single()["total"]

        cypher_query = """
            MATCH (t:Text)
            WHERE ($language IS NULL OR t.language_code = $language)
            OPTIONAL MATCH (t)-[:SECTION_PART_OF_TEXT]->(s:Section)
            OPTIONAL MATCH (s)-[:SECTION_CONTAINS]->(w:Word)
            OPTIONAL MATCH (w)-[:WORD_MADE_OF]->(m:Morpheme)
            WITH t, 
                 COUNT(DISTINCT s) AS section_count,
                 COUNT(DISTINCT w) AS word_count,
                 COUNT(DISTINCT m) AS morpheme_count
            RETURN
              COALESCE(t.ID, toString(id(t)))                     AS ID,
              COALESCE(t.title, '')                               AS title,
              COALESCE(t.source, '')                              AS source,
              COALESCE(t.comment, '')                             AS comment,
              COALESCE(t.language_code, '')                       AS language_code,
              section_count, word_count, morpheme_count,
              toString(COALESCE(t.created_at, datetime()))        AS created_at
            ORDER BY COALESCE(t.created_at, datetime()) DESC
            SKIP $skip
            LIMIT $limit
        """
        result = db.run(cypher_query, language=language, skip=skip, limit=limit)

        texts = [InterlinearTextResponse(**dict(record)) for record in result]

        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Limit"] = str(limit)
        response.headers["X-Offset"] = str(skip)

        return texts

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_database_stats(db=Depends(get_db_dependency)):
    """Get overall database statistics"""
    try:
        cypher_query = """
            MATCH (t:Text) WITH COUNT(t) as text_count
            MATCH (s:Section) WITH text_count, COUNT(s) as section_count
            MATCH (p:Phrase) WITH text_count, section_count, COUNT(p) as phrase_count
            MATCH (w:Word) WITH text_count, section_count, phrase_count, COUNT(w) as word_count
            MATCH (m:Morpheme) WITH text_count, section_count, phrase_count, word_count, COUNT(m) as morpheme_count
            MATCH (g:Gloss) WITH text_count, section_count, phrase_count, word_count, morpheme_count, COUNT(g) as gloss_count
            RETURN text_count, section_count, phrase_count, word_count, morpheme_count, gloss_count
        """

        result = db.run(cypher_query)
        record = result.single()

        if not record:
            return {
                "text_count": 0,
                "section_count": 0,
                "phrase_count": 0,
                "word_count": 0,
                "morpheme_count": 0,
                "gloss_count": 0,
            }

        return dict(record)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schema-visualization")
async def get_schema_visualization(db=Depends(get_db_dependency)):
    """Get a sample of the graph structure for visualization"""
    try:
        return {
            "message": "Schema visualization data",
            "note": "Connect to Neo4j Browser at http://localhost:7474 for full visualization",
            "schema_url": "http://localhost:7474",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph-filters")
async def get_graph_filters(db=Depends(get_db_dependency)):
    """Get available filter options for graph visualization"""
    try:
        # Get available texts
        texts_query = """
            MATCH (t:Text)
            RETURN t.ID as id, 
                   COALESCE(t.title, t.ID, 'Untitled') as title,
                   t.language_code as language
            ORDER BY t.title
            LIMIT 50
        """
        texts_result = db.run(texts_query)
        texts = [dict(record) for record in texts_result]

        # Get available languages
        languages_query = """
            MATCH (t:Text)
            WHERE t.language_code IS NOT NULL
            RETURN DISTINCT t.language_code as code
            ORDER BY code
        """
        lang_result = db.run(languages_query)
        languages = [record["code"] for record in lang_result if record["code"]]

        return {
            "texts": texts,
            "languages": languages,
            "node_types": ["Text", "Section", "Phrase", "Word", "Morpheme", "Gloss"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph-data")
async def get_graph_data(
    text_id: Optional[str] = None,
    language: Optional[str] = None,
    node_types: Optional[str] = None,  # Comma-separated: "Text,Word,Gloss"
    limit: int = 50,
    db=Depends(get_db_dependency),
):
    """Get graph data for visualization with nodes and edges

    Args:
        text_id: Filter to specific text (shows all related nodes)
        language: Filter by language code
        node_types: Comma-separated node types to include (e.g. "Word,Gloss,Morpheme")
        limit: Max nodes per type (default 50)
    """
    try:
        nodes = []
        edges = []

        # Query to get all nodes and relationships
        # If text_id is provided, filter by that text, otherwise get a sample
        if text_id:
            cypher_query = """
                // Get Text node
                MATCH (t:Text {ID: $text_id})
                OPTIONAL MATCH (t)-[:SECTION_PART_OF_TEXT]->(s:Section)
                OPTIONAL MATCH (s)-[:PHRASE_IN_SECTION]->(ph:Phrase)
                OPTIONAL MATCH (s)-[:SECTION_CONTAINS]->(w:Word)
                OPTIONAL MATCH (ph)-[r:PHRASE_COMPOSED_OF]->(pw:Word)
                OPTIONAL MATCH (w)-[:WORD_MADE_OF]->(m:Morpheme)
                OPTIONAL MATCH (pw)-[:WORD_MADE_OF]->(pm:Morpheme)
                OPTIONAL MATCH (g:Gloss)-[:ANALYZES]->(analyzed)
                WHERE analyzed IN [w, pw, m, pm, ph]
                
                // Collect all nodes and relationships
                WITH collect(DISTINCT t) + collect(DISTINCT s) + collect(DISTINCT ph) + 
                     collect(DISTINCT w) + collect(DISTINCT pw) + collect(DISTINCT m) + 
                     collect(DISTINCT pm) + collect(DISTINCT g) as allNodes,
                     collect(DISTINCT {source: id(t), target: id(s), type: 'SECTION_PART_OF_TEXT'}) +
                     collect(DISTINCT {source: id(s), target: id(ph), type: 'PHRASE_IN_SECTION'}) +
                     collect(DISTINCT {source: id(s), target: id(w), type: 'SECTION_CONTAINS'}) +
                     collect(DISTINCT {source: id(ph), target: id(pw), type: 'PHRASE_COMPOSED_OF', order: r.Order}) +
                     collect(DISTINCT {source: id(w), target: id(m), type: 'WORD_MADE_OF'}) +
                     collect(DISTINCT {source: id(pw), target: id(pm), type: 'WORD_MADE_OF'}) +
                     collect(DISTINCT {source: id(g), target: id(analyzed), type: 'ANALYZES'}) as allEdges
                
                RETURN allNodes, allEdges
            """
            params = {"text_id": text_id}
        else:
            # Parse node types filter
            allowed_types = set()
            if node_types:
                allowed_types = set(t.strip() for t in node_types.split(","))

            # Build query parts based on filters
            query_parts = []

            if not node_types or "Text" in allowed_types:
                lang_filter = "WHERE t.language_code = $language" if language else ""
                query_parts.append(f"CALL {{ MATCH (t:Text) {lang_filter} RETURN t }}")

            if not node_types or "Section" in allowed_types:
                query_parts.append("CALL { MATCH (s:Section) RETURN s LIMIT 10 }")

            if not node_types or "Phrase" in allowed_types:
                query_parts.append("CALL { MATCH (ph:Phrase) RETURN ph LIMIT 20 }")

            if not node_types or "Word" in allowed_types:
                lang_filter = "WHERE w.language = $language" if language else ""
                query_parts.append(
                    f"CALL {{ MATCH (w:Word) {lang_filter} RETURN w LIMIT $limit }}"
                )

            if not node_types or "Morpheme" in allowed_types:
                lang_filter = "WHERE m.language = $language" if language else ""
                query_parts.append(
                    f"CALL {{ MATCH (m:Morpheme) {lang_filter} RETURN m LIMIT 30 }}"
                )

            if not node_types or "Gloss" in allowed_types:
                query_parts.append("CALL { MATCH (g:Gloss) RETURN g LIMIT 40 }")

            # Collect node variables
            node_vars = []
            if not node_types or "Text" in allowed_types:
                node_vars.append("collect(DISTINCT t)")
            if not node_types or "Section" in allowed_types:
                node_vars.append("collect(DISTINCT s)")
            if not node_types or "Phrase" in allowed_types:
                node_vars.append("collect(DISTINCT ph)")
            if not node_types or "Word" in allowed_types:
                node_vars.append("collect(DISTINCT w)")
            if not node_types or "Morpheme" in allowed_types:
                node_vars.append("collect(DISTINCT m)")
            if not node_types or "Gloss" in allowed_types:
                node_vars.append("collect(DISTINCT g)")

            cypher_query = (
                "\n".join(query_parts)
                + f"""
                
                // Get all relationships between these nodes
                WITH {" + ".join(node_vars)} as allNodes
                
                UNWIND allNodes as node
                WITH collect(DISTINCT node) as uniqueNodes
                
                // Now get relationships between these nodes
                UNWIND uniqueNodes as n1
                OPTIONAL MATCH (n1)-[r]->(n2)
                WHERE n2 IN uniqueNodes
                
                WITH uniqueNodes,
                     collect(DISTINCT {{
                         source: id(startNode(r)), 
                         target: id(endNode(r)), 
                         type: type(r)
                     }}) as edges
                
                RETURN uniqueNodes as allNodes,
                       [edge IN edges WHERE edge.source IS NOT NULL AND edge.target IS NOT NULL] as allEdges
            """
            )
            params = {"limit": limit, "language": language}

        result = db.run(cypher_query, **params)
        record = result.single()

        if not record:
            # Return empty graph if no data
            return {"nodes": [], "edges": []}

        # Define colors for each node type
        node_colors = {
            "Text": "#f59e0b",  # amber
            "Section": "#8b5cf6",  # purple
            "Phrase": "#06b6d4",  # cyan
            "Word": "#0ea5e9",  # blue
            "Morpheme": "#10b981",  # green
            "Gloss": "#ec4899",  # pink
        }

        # Define sizes for each node type (larger = more important in hierarchy)
        node_sizes = {
            "Text": 30,
            "Section": 22,
            "Phrase": 16,
            "Word": 8,
            "Morpheme": 6,
            "Gloss": 7,
        }

        # Process nodes (track seen IDs to avoid duplicates)
        all_nodes = record["allNodes"]
        seen_node_ids = set()

        for node in all_nodes:
            if node is None:
                continue

            # Skip duplicates
            node_id = str(node.id)
            if node_id in seen_node_ids:
                continue
            seen_node_ids.add(node_id)

            labels = list(node.labels)
            if not labels:
                continue

            node_type = labels[0]
            node_props = dict(node)

            # Get label text
            label_text = node_props.get("ID", "")
            if node_type == "Text":
                label_text = node_props.get("title", label_text)
            elif node_type == "Word":
                label_text = node_props.get("surface_form", label_text)
            elif node_type == "Morpheme":
                label_text = node_props.get(
                    "surface_form", node_props.get("citation_form", label_text)
                )
            elif node_type == "Gloss":
                label_text = node_props.get("annotation", label_text)[
                    :20
                ]  # Truncate long glosses
            elif node_type == "Phrase":
                label_text = node_props.get("surface_text", label_text)[:30]

            nodes.append(
                {
                    "id": node_id,
                    "label": label_text,
                    "type": node_type,
                    "color": node_colors.get(node_type, "#64748b"),
                    "size": node_sizes.get(node_type, 10),
                    "properties": node_props,
                }
            )

        # Process edges
        all_edges = record["allEdges"]
        for idx, edge in enumerate(all_edges):
            if edge is None or edge.get("source") is None or edge.get("target") is None:
                continue

            edges.append(
                {
                    "id": f"edge-{idx}",
                    "source": str(edge["source"]),
                    "target": str(edge["target"]),
                    "type": edge.get("type", ""),
                    "size": 2,
                    "color": "#94a3b8",
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {"node_count": len(nodes), "edge_count": len(edges)},
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error fetching graph data: {str(e)}"
        )
