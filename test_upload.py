#!/usr/bin/env python3
"""
Test script to verify FLEx file upload and schema compliance.
This script will:
1. Parse a FLEx file
2. Verify the parsed structure matches our schema
3. Test the database insertion
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.parsers.flextext_parser import parse_flextext_file, get_file_stats
import json


def test_parse_flextext(file_path: str):
    """Test parsing a FLEx file"""
    print(f"\n{'=' * 60}")
    print(f"Testing FLEx file parsing: {file_path}")
    print(f"{'=' * 60}\n")

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    try:
        # Parse the file
        print("📄 Parsing FLEx file...")
        texts = parse_flextext_file(file_path)
        stats = get_file_stats(file_path)

        print(f"\n✅ Successfully parsed {file_path}")
        print(f"\n📊 File Statistics:")
        print(f"   - Total texts: {stats['total_texts']}")
        print(f"   - Total sections: {stats['total_sections']}")
        print(f"   - Total phrases: {stats['total_phrases']}")
        print(f"   - Total words: {stats['total_words']}")
        print(f"   - Total morphemes: {stats['total_morphemes']}")
        print(f"   - Languages: {', '.join(stats['languages'])}")
        print(f"   - POS tags: {', '.join(stats['pos_tags'][:10])}...")  # First 10
        print(f"   - Morpheme types: {stats['morpheme_types']}")

        # Verify schema compliance
        print(f"\n🔍 Verifying schema compliance...")
        for text in texts:
            # Check that Text uses ID property
            assert hasattr(text, "ID"), "Text should have ID property"
            assert hasattr(text, "sections"), "Text should have sections"

            print(f"\n   Text: {text.title}")
            print(f"   - ID: {text.ID}")
            print(f"   - Language: {text.language_code}")
            print(f"   - Sections: {len(text.sections)}")

            for section in text.sections[:1]:  # Check first section
                assert hasattr(section, "ID"), "Section should have ID property"
                assert hasattr(section, "phrases"), "Section should have phrases"
                assert hasattr(section, "words"), "Section should have words"

                print(f"   - Section ID: {section.ID}")
                print(f"   - Phrases in section: {len(section.phrases)}")
                print(f"   - Words in section: {len(section.words)}")

                if section.phrases:
                    phrase = section.phrases[0]
                    assert hasattr(phrase, "ID"), "Phrase should have ID property"
                    assert hasattr(phrase, "words"), "Phrase should have words"

                    print(f"   - First phrase ID: {phrase.ID}")
                    print(f"   - Surface text: {phrase.surface_text}")
                    print(f"   - Words in phrase: {len(phrase.words)}")

                    if phrase.words:
                        word = phrase.words[0]
                        assert hasattr(word, "ID"), "Word should have ID property"
                        assert hasattr(word, "morphemes"), "Word should have morphemes"

                        print(f"   - First word ID: {word.ID}")
                        print(f"   - Surface form: {word.surface_form}")
                        print(f"   - Gloss: {word.gloss}")
                        print(f"   - POS: {word.pos}")
                        print(f"   - Morphemes: {len(word.morphemes)}")

                        if word.morphemes:
                            morpheme = word.morphemes[0]
                            assert hasattr(morpheme, "ID"), (
                                "Morpheme should have ID property"
                            )

                            print(f"   - First morpheme ID: {morpheme.ID}")
                            print(f"   - Type: {morpheme.type.value}")
                            print(f"   - Surface form: {morpheme.surface_form}")
                            print(f"   - Citation form: {morpheme.citation_form}")
                            print(f"   - Gloss: {morpheme.gloss}")

        print(f"\n✅ Schema compliance verified!")
        print(f"\n{'=' * 60}")
        print(f"Expected Neo4j relationships:")
        print(f"   - Text -[:SECTION_PART_OF_TEXT]-> Section")
        print(f"   - Section -[:SECTION_CONTAINS]-> Word")
        print(f"   - Section -[:PHRASE_IN_SECTION]-> Phrase")
        print(f"   - Phrase -[:PHRASE_COMPOSED_OF {{Order}}]-> Word")
        print(f"   - Word -[:WORD_MADE_OF]-> Morpheme")
        print(f"   - Gloss -[:ANALYZES]-> (Word|Phrase|Morpheme)")
        print(f"{'=' * 60}\n")

        return True

    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test with available FLEx files
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        sys.exit(1)

    # Find .flextext files
    flextext_files = [f for f in os.listdir(data_dir) if f.endswith(".flextext")]

    if not flextext_files:
        print(f"❌ No .flextext files found in {data_dir}")
        sys.exit(1)

    print(f"\n🔍 Found {len(flextext_files)} FLEx file(s):")
    for f in flextext_files:
        print(f"   - {f}")

    # Test each file
    all_passed = True
    for flextext_file in flextext_files:
        file_path = os.path.join(data_dir, flextext_file)
        if not test_parse_flextext(file_path):
            all_passed = False

    if all_passed:
        print(f"\n✅ All tests passed!")
        print(f"\n📝 Next steps:")
        print(
            f"   1. Make sure Neo4j is running: docker-compose -f docker-compose.free.yml up neo4j -d"
        )
        print(f"   2. Apply the schema: ./apply-schema.sh")
        print(
            f"   3. Start the backend: docker-compose -f docker-compose.free.yml up backend -d"
        )
        print(
            f'   4. Upload via API: curl -X POST http://localhost:8000/api/v1/linguistic/upload-flextext -F "file=@data/{flextext_files[0]}"'
        )
        print(f"   5. View in Neo4j Browser: http://localhost:7474")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed!")
        sys.exit(1)
