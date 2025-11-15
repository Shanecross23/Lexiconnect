"""
Test script to debug missing edges between Gloss, Morpheme, and Word nodes
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import Neo4jDatabase
from app.core.config import get_settings

settings = get_settings()

def test_gloss_relationships():
    """Check if ANALYZES relationships exist in the database"""
    
    db = Neo4jDatabase(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    
    try:
        # Test 1: Count Gloss nodes
        result = db.run("MATCH (g:Gloss) RETURN count(g) as count")
        gloss_count = result.single()["count"]
        print(f"✓ Found {gloss_count} Gloss nodes")
        
        # Test 2: Count Word nodes
        result = db.run("MATCH (w:Word) RETURN count(w) as count")
        word_count = result.single()["count"]
        print(f"✓ Found {word_count} Word nodes")
        
        # Test 3: Count Morpheme nodes
        result = db.run("MATCH (m:Morpheme) RETURN count(m) as count")
        morpheme_count = result.single()["count"]
        print(f"✓ Found {morpheme_count} Morpheme nodes")
        
        # Test 4: Count ANALYZES relationships
        result = db.run("MATCH ()-[r:ANALYZES]->() RETURN count(r) as count")
        analyzes_count = result.single()["count"]
        print(f"✓ Found {analyzes_count} ANALYZES relationships")
        
        # Test 5: Check Gloss -> Word relationships
        result = db.run("""
            MATCH (g:Gloss)-[r:ANALYZES]->(w:Word) 
            RETURN count(r) as count
        """)
        gloss_word_count = result.single()["count"]
        print(f"  - {gloss_word_count} Gloss→Word ANALYZES relationships")
        
        # Test 6: Check Gloss -> Morpheme relationships
        result = db.run("""
            MATCH (g:Gloss)-[r:ANALYZES]->(m:Morpheme) 
            RETURN count(r) as count
        """)
        gloss_morph_count = result.single()["count"]
        print(f"  - {gloss_morph_count} Gloss→Morpheme ANALYZES relationships")
        
        # Test 7: Sample some actual relationships
        if analyzes_count > 0:
            print("\nSample ANALYZES relationships:")
            result = db.run("""
                MATCH (g:Gloss)-[r:ANALYZES]->(target)
                RETURN 
                    labels(g)[0] as source_type,
                    g.annotation as gloss_text,
                    labels(target)[0] as target_type,
                    CASE 
                        WHEN target:Word THEN target.surface_form
                        WHEN target:Morpheme THEN target.surface_form
                        ELSE 'N/A'
                    END as target_text
                LIMIT 5
            """)
            for record in result:
                print(f"  - {record['source_type']}('{record['gloss_text']}') → {record['target_type']}('{record['target_text']}')")
        
        # Test 8: Check Word -> Morpheme relationships
        result = db.run("""
            MATCH (w:Word)-[r:WORD_MADE_OF]->(m:Morpheme) 
            RETURN count(r) as count
        """)
        word_morph_count = result.single()["count"]
        print(f"\n✓ Found {word_morph_count} Word→Morpheme WORD_MADE_OF relationships")
        
        # Test 9: Test the actual graph-data query
        print("\n--- Testing graph-data query ---")
        result = db.run("""
            MATCH (t:Text)
            WITH t LIMIT 1
            OPTIONAL MATCH (t)-[:SECTION_PART_OF_TEXT]->(s:Section)
            OPTIONAL MATCH (s)-[:PHRASE_IN_SECTION]->(ph:Phrase)
            OPTIONAL MATCH (s)-[:SECTION_CONTAINS]->(w:Word)
            OPTIONAL MATCH (ph)-[rc:PHRASE_COMPOSED_OF]->(pw:Word)
            OPTIONAL MATCH (w)-[:WORD_MADE_OF]->(m:Morpheme)
            OPTIONAL MATCH (pw)-[:WORD_MADE_OF]->(pm:Morpheme)
            
            // Get all words (combined list for gloss matching)
            WITH t, s, ph, w, pw, m, pm, rc,
                 collect(DISTINCT w) + collect(DISTINCT pw) as allWords,
                 collect(DISTINCT m) + collect(DISTINCT pm) as allMorphemes
            
            // Get all glosses that analyze words in this text
            OPTIONAL MATCH (gw:Gloss)-[:ANALYZES]->(analyzedW:Word)
            WHERE analyzedW IN allWords
            
            // Get all glosses that analyze morphemes in this text  
            OPTIONAL MATCH (gm:Gloss)-[:ANALYZES]->(analyzedM:Morpheme)
            WHERE analyzedM IN allMorphemes
            
            RETURN 
                size([w IN allWords WHERE w IS NOT NULL]) as word_count,
                size([m IN allMorphemes WHERE m IS NOT NULL]) as morpheme_count,
                count(DISTINCT gw) as gloss_word_count,
                count(DISTINCT gm) as gloss_morpheme_count
        """)
        record = result.single()
        if record:
            print(f"Words in text: {record['word_count']}")
            print(f"Morphemes in text: {record['morpheme_count']}")
            print(f"Glosses analyzing words: {record['gloss_word_count']}")
            print(f"Glosses analyzing morphemes: {record['gloss_morpheme_count']}")
        
        # Summary
        print("\n=== SUMMARY ===")
        if analyzes_count == 0:
            print("❌ PROBLEM: No ANALYZES relationships found!")
            print("   This means glosses are not being linked to words/morphemes.")
            print("   Check the _store_gloss_for_word() and _store_gloss_for_morpheme() functions.")
        elif gloss_word_count == 0 and gloss_morph_count == 0:
            print("❌ PROBLEM: ANALYZES relationships exist but not to Word/Morpheme!")
            print(f"   Total ANALYZES: {analyzes_count}, but 0 to Word and 0 to Morpheme")
        else:
            print("✓ Relationships appear to be in the database correctly")
            print("  The issue is likely in the frontend graph rendering or layout")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_gloss_relationships()

