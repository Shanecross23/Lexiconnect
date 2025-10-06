// ============================================================
// Lexiconnect Graph Database Schema (schema.cypher)
// ============================================================

// ---------------------
// Node Constraints
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

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.ID IS UNIQUE;


// ---------------------
// Relationship Patterns
// ---------------------

CREATE (:Word)-[:WORD_MADE_OF]->(:Morpheme);
CREATE (:Phrase)-[:PHRASE_COMPOSED_OF {Order: 0}]->(:Word);
CREATE (:Section)-[:SECTION_CONTAINS]->(:Word);
CREATE (:Section)-[:PHRASE_IN_SECTION]->(:Phrase);
CREATE (:Text)-[:SECTION_PART_OF_TEXT]->(:Section);
CREATE (:Gloss)-[:ANALYZES]->(:Word);
CREATE (:Gloss)-[:ANALYZES]->(:Phrase);
CREATE (:Gloss)-[:ANALYZES]->(:Morpheme);
CREATE (:User)-[:HAS_PERMISSIONS]->(:Text);


// ---------------------
// Notes
// ---------------------

// Each Text acts as a document container composed of Sections.
// Phrase, Word, and Morpheme form the linguistic decomposition chain.
// Gloss nodes attach to analyzed linguistic units (Word, Phrase, Morpheme).
// User nodes define access through HAS_PERMISSIONS; authentication is external.

