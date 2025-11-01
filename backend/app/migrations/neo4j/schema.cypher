// ============================================================
// Lexiconnect Graph Database Schema (schema.cypher)
// ============================================================

// ---------------------
// Node Constraints (Unique IDs)
// ---------------------

CREATE CONSTRAINT gloss_id IF NOT EXISTS
FOR (g:Gloss) REQUIRE g.ID IS UNIQUE;

CREATE CONSTRAINT morpheme_id IF NOT EXISTS
FOR (m:Morpheme) REQUIRE m.ID IS UNIQUE;

CREATE CONSTRAINT word_id IF NOT EXISTS
FOR (w:Word) REQUIRE w.ID IS UNIQUE;

CREATE CONSTRAINT phrase_id IF NOT EXISTS
FOR (p:Phrase) REQUIRE p.ID IS UNIQUE;

CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (s:Section) REQUIRE s.ID IS UNIQUE;

CREATE CONSTRAINT text_id IF NOT EXISTS
FOR (t:Text) REQUIRE t.ID IS UNIQUE;

CREATE CONSTRAINT interlinear_text_id IF NOT EXISTS
FOR (t:InterlinearText) REQUIRE t.ID IS UNIQUE;

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.ID IS UNIQUE;


// ---------------------
// Indexes for Performance
// ---------------------

CREATE INDEX word_surface_form IF NOT EXISTS
FOR (w:Word) ON (w.surface_form);

CREATE INDEX word_language IF NOT EXISTS
FOR (w:Word) ON (w.language);

CREATE INDEX morpheme_citation_form IF NOT EXISTS
FOR (m:Morpheme) ON (m.citation_form);

CREATE INDEX morpheme_gloss IF NOT EXISTS
FOR (m:Morpheme) ON (m.gloss);

CREATE INDEX text_language IF NOT EXISTS
FOR (t:Text) ON (t.language_code);

CREATE INDEX gloss_annotation IF NOT EXISTS
FOR (g:Gloss) ON (g.annotation);


// ---------------------
// Relationship Pattern Documentation
// ---------------------

// NOTE: The following are EXAMPLES of relationship patterns.
// These are not executable CREATE statements, but documentation
// of the expected relationship structure in the graph.

// Text → Section relationship:
// (:Text)-[:SECTION_PART_OF_TEXT]->(:Section)

// Section → Word relationship:
// (:Section)-[:SECTION_CONTAINS]->(:Word)

// Section → Phrase relationship:
// (:Section)-[:PHRASE_IN_SECTION]->(:Phrase)

// Phrase → Word relationship (with Order property):
// (:Phrase)-[:PHRASE_COMPOSED_OF {Order: integer}]->(:Word)

// Word → Morpheme relationship:
// (:Word)-[:WORD_MADE_OF]->(:Morpheme)

// Gloss → linguistic unit relationships:
// (:Gloss)-[:ANALYZES]->(:Word)
// (:Gloss)-[:ANALYZES]->(:Phrase)
// (:Gloss)-[:ANALYZES]->(:Morpheme)

// User permissions:
// (:User)-[:HAS_PERMISSIONS]->(:Text)


// ---------------------
// Schema Notes
// ---------------------

// 1. All nodes use 'ID' property (not 'id' or 'guid')
// 2. Text nodes are document containers
// 3. Section nodes subdivide texts (paragraphs, chapters, etc.)
// 4. Phrase, Word, and Morpheme form the linguistic decomposition chain
// 5. Gloss nodes attach linguistic annotations via ANALYZES relationship
// 6. User nodes define access control via HAS_PERMISSIONS relationship
// 7. Authentication and authorization are handled at the application layer

