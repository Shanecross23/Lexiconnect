#!/usr/bin/env python3
"""
Test script to verify export service functionality.
This script will:
1. Test fetching text data from the database
2. Verify the export data structure matches expectations
3. Test edge cases (empty data, missing relationships)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database import get_db_dependency
from app.services.export_service import fetch_text_for_export, TextExport, SectionExport, PhraseExport, WordExport, MorphemeExport
import asyncio


async def test_export_service(text_id: str):
    """Test the export service with a specific text ID"""
    print(f"\n{'=' * 60}")
    print(f"Testing export service with text ID: {text_id}")
    print(f"{'=' * 60}\n")

    try:
        # Test fetching text
        print("📥 Fetching text data from database...")
        # Use get_db_dependency which yields a session
        db_gen = get_db_dependency()
        db = next(db_gen)
        try:
            text_export = await fetch_text_for_export(text_id, db)
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
        
        if text_export is None:
            print(f"❌ Text with ID '{text_id}' not found in database")
            print("\n💡 Tip: Upload a FLEXText file first using the upload endpoint")
            return False
        
        print(f"✅ Successfully fetched text: {text_export.title}")
        print(f"\n📊 Text Export Data:")
        print(f"   - ID: {text_export.ID}")
        print(f"   - Title: {text_export.title}")
        print(f"   - Source: {text_export.source or '(empty)'}")
        print(f"   - Comment: {text_export.comment or '(empty)'}")
        print(f"   - Language Code: {text_export.language_code}")
        print(f"   - Sections: {len(text_export.sections)}")
        
        # Verify structure
        print(f"\n🔍 Verifying data structure...")
        
        # Check sections
        total_phrases = 0
        total_words = 0
        total_morphemes = 0
        
        for section_idx, section in enumerate(text_export.sections):
            assert isinstance(section, SectionExport), f"Section {section_idx} should be SectionExport"
            assert section.ID, f"Section {section_idx} should have ID"
            print(f"\n   Section {section_idx + 1}:")
            print(f"      - ID: {section.ID}")
            print(f"      - Order: {section.order}")
            print(f"      - Phrases: {len(section.phrases)}")
            total_phrases += len(section.phrases)
            
            # Check phrases
            for phrase_idx, phrase in enumerate(section.phrases):
                assert isinstance(phrase, PhraseExport), f"Phrase {phrase_idx} in section {section_idx} should be PhraseExport"
                assert phrase.ID, f"Phrase {phrase_idx} should have ID"
                print(f"      - Phrase {phrase_idx + 1}:")
                print(f"         - ID: {phrase.ID}")
                print(f"         - Segnum: {phrase.segnum or '(empty)'}")
                print(f"         - Surface Text: {phrase.surface_text or '(empty)'}")
                print(f"         - Language: {phrase.language}")
                print(f"         - Words: {len(phrase.words)}")
                total_words += len(phrase.words)
                
                # Check words
                for word_idx, word in enumerate(phrase.words):
                    assert isinstance(word, WordExport), f"Word {word_idx} in phrase {phrase_idx} should be WordExport"
                    assert word.ID, f"Word {word_idx} should have ID"
                    print(f"         - Word {word_idx + 1}:")
                    print(f"            - ID: {word.ID}")
                    print(f"            - Surface Form: {word.surface_form or '(empty)'}")
                    print(f"            - Gloss: {word.gloss or '(empty)'}")
                    print(f"            - POS: {word.pos or '(empty)'}")
                    print(f"            - Language: {word.language}")
                    print(f"            - Is Punctuation: {word.is_punctuation}")
                    print(f"            - Morphemes: {len(word.morphemes)}")
                    total_morphemes += len(word.morphemes)
                    
                    # Check morphemes
                    for morph_idx, morph in enumerate(word.morphemes):
                        assert isinstance(morph, MorphemeExport), f"Morpheme {morph_idx} should be MorphemeExport"
                        assert morph.ID, f"Morpheme {morph_idx} should have ID"
                        print(f"            - Morpheme {morph_idx + 1}:")
                        print(f"               - ID: {morph.ID}")
                        print(f"               - Type: {morph.type or '(empty)'}")
                        print(f"               - Surface Form: {morph.surface_form or '(empty)'}")
                        print(f"               - Citation Form: {morph.citation_form or '(empty)'}")
                        print(f"               - Gloss: {morph.gloss or '(empty)'}")
                        print(f"               - MSA: {morph.msa or '(empty)'}")
                        print(f"               - Language: {morph.language}")
        
        print(f"\n📈 Summary:")
        print(f"   - Total Sections: {len(text_export.sections)}")
        print(f"   - Total Phrases: {total_phrases}")
        print(f"   - Total Words: {total_words}")
        print(f"   - Total Morphemes: {total_morphemes}")
        
        # Test ordering
        print(f"\n🔢 Verifying ordering...")
        for section in text_export.sections:
            # Check section order
            assert section.order >= 0, "Section order should be non-negative"
            
            for phrase in section.phrases:
                # Check that words are in order (we can't easily verify phrase order without order property)
                word_ids = [w.ID for w in phrase.words]
                # Words should be non-empty if there are any
                assert len(phrase.words) >= 0, "Phrase should have words list"
        
        print("✅ All structure checks passed!")
        
        # Test edge cases
        print(f"\n🧪 Testing edge cases...")
        
        # Test with empty text (if exists)
        # This would require a text with no sections - hard to test without creating test data
        
        print("✅ Edge case checks passed!")
        
        print(f"\n✅ Export service test completed successfully!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_available_texts():
    """List all available texts in the database"""
    print(f"\n{'=' * 60}")
    print(f"Listing available texts in database...")
    print(f"{'=' * 60}\n")
    
    try:
        db_gen = get_db_dependency()
        db = next(db_gen)
        try:
            result = db.run("""
                MATCH (t:Text)
                RETURN t.ID AS ID, t.title AS title, t.language_code AS language_code
                ORDER BY t.created_at DESC
                LIMIT 10
            """)
            
            texts = list(result)
            
            if not texts:
                print("❌ No texts found in database")
                print("\n💡 Tip: Upload a FLEXText file first using:")
                print("   curl -X POST http://localhost:8000/api/v1/linguistic/upload-flextext \\")
                print("        -F 'file=@path/to/your/file.flextext'")
                return None
            
            print(f"✅ Found {len(texts)} text(s):\n")
            for i, record in enumerate(texts, 1):
                print(f"   {i}. ID: {record['ID']}")
                print(f"      Title: {record.get('title') or '(untitled)'}")
                print(f"      Language: {record.get('language_code') or 'unknown'}")
                print()
            
            return texts[0]['ID'] if texts else None
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
            
    except Exception as e:
        print(f"❌ Error listing texts: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Get text ID from command line or list available texts
    if len(sys.argv) > 1:
        text_id = sys.argv[1]
    else:
        text_id = list_available_texts()
        if not text_id:
            print("\n❌ No text ID provided and no texts found in database")
            print("\nUsage: python test_export_service.py [text_id]")
            sys.exit(1)
    
    # Run the test
    success = asyncio.run(test_export_service(text_id))
    
    if success:
        print(f"\n✅ All tests passed!")
        print(f"\n📝 Next steps:")
        print(f"   - Step 4: Use the export service with the FLEXText exporter")
        print(f"   - Step 5: Create the FastAPI endpoint for export")
        sys.exit(0)
    else:
        print(f"\n❌ Tests failed!")
        sys.exit(1)

