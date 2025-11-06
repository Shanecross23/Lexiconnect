## FLEXText export mapping (DB → FLEXText XML)

This document defines how Lexiconnect data is serialized to FLEXText XML, mirroring what `backend/app/parsers/flextext_parser.py` consumes. The goal is round‑trip stability: exporting then parsing should preserve core structure and content.

### XML structure expected by the parser

- Root: `interlinear-text`
  - Optional `guid` attribute (stable UUID recommended)
  - Child `item` elements for metadata (see below)
  - Container `paragraphs`
    - `paragraph` (0..n)
      - Optional `guid`
      - Container `phrases`
        - `phrase` (0..n)
          - Optional `guid`
          - `item type="segnum"` (optional but useful)
          - `item type="txt"` (phrase surface text; carries default `lang` for children if set)
          - Container `words`
            - `word` (0..n)
              - Optional `guid`
              - `item type="txt"` (surface form) OR `item type="punct"` for punctuation
              - Optional `item type="gls"`
              - Optional `item type="pos"`
              - Container `morphemes`
                - `morph` (0..n) with optional `type` attr: `stem|prefix|suffix|infix|circumfix|root`
                  - Optional `guid`
                  - `item type="txt"`
                  - Optional `item type="cf"` (citation form)
                  - Optional `item type="gls"`
                  - Optional `item type="msa"` (morphosyntactic analysis)

Notes:
- The parser uses the `lang` attribute on `item` (not `lng`).
- Wrapper containers (`paragraphs`, `phrases`, `words`, `morphemes`) are required for parsing.
- If an item `type="punct"` is present within a `word`, the parser treats the whole unit as punctuation and ignores morphemes.

### Metadata items at `interlinear-text`

- `item type="title"` — text title; `lang` optional (first seen language becomes `language_code`).
- `item type="source"` — source string.
- `item type="comment"` — free comment.

### Language handling

- `item@lang` is propagated down as defaults:
  - `phrase` sets default language when its `item type="txt"` has `lang`.
  - `word` or `morph` `item type="txt"` with `lang` can override the default.
- Unknown languages may be omitted or set to a project default.

### Ordering and IDs

- Export elements in stable, deterministic order: paragraphs → phrases (increasing order) → words → morphemes.
- `guid` attributes are optional; when provided, generate stable UUIDs (e.g., using a namespace + path of parent IDs and index) to allow future diffing.
- `phrase` order can be echoed via `item type="segnum"`.

### DB → FLEXText mapping

- Interlinear text (project text/document):
  - title → `interlinear-text/item[type=title]`
  - source → `interlinear-text/item[type=source]`
  - comment → `interlinear-text/item[type=comment]`
  - language_code (if known) → `item@lang` on `title` (preferred) or on phrase `txt`

- Section (mapped to paragraph):
  - section.order → paragraph order (by position in XML)
  - section.ID → `paragraph@guid` (optional)

- Phrase:
  - phrase.segnum → `phrase/item[type=segnum]`
  - phrase.surface_text → `phrase/item[type=txt]`
  - phrase.language → `phrase/item[type=txt]@lang`
  - phrase.ID → `phrase@guid` (optional)

- Word:
  - word.surface_form → `word/item[type=txt]` (unless punctuation)
  - word.gloss → `word/item[type=gls]` (optional)
  - word.pos → `word/item[type=pos]` (optional; if POS == `PUNCT`, export as punctuation, see below)
  - word.language → `word/item[type=txt]@lang` (optional override)
  - word.ID → `word@guid` (optional)
  - Punctuation: if the word is punctuation, export `word/item[type=punct]` with the punctuation string and omit morphemes.

- Morpheme:
  - morpheme.type → `morph@type` (values: `stem|prefix|suffix|infix|circumfix|root`; default `stem` if unknown)
  - morpheme.surface_form → `morph/item[type=txt]`
  - morpheme.citation_form → `morph/item[type=cf]` (optional)
  - morpheme.gloss → `morph/item[type=gls]` (optional)
  - morpheme.msa → `morph/item[type=msa]` (optional)
  - morpheme.language → `morph/item[type=txt]@lang` (optional override)
  - morpheme.ID → `morph@guid` (optional)

### What NOT to include in MVP (parser-agnostic fields)

- Phrase-level free translation `item type="tr"` — current parser does not consume it; skip for round‑trip stability.
- Namespaces and additional metadata attributes — keep XML simple and un-namespaced for now.

### Minimal valid example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<interlinear-text>
  <item type="title" lang="nhi-Latn">Sample Text</item>
  <paragraphs>
    <paragraph>
      <phrases>
        <phrase>
          <item type="segnum">1</item>
          <item type="txt" lang="nhi-Latn">ka̱ni</item>
          <words>
            <word>
              <item type="txt" lang="nhi-Latn">ka̱ni</item>
              <morphemes>
                <morph type="prefix">
                  <item type="txt" lang="nhi-Latn">ka̱</item>
                  <item type="gls" lang="en">1sg</item>
                </morph>
                <morph type="stem">
                  <item type="txt" lang="nhi-Latn">ni</item>
                </morph>
              </morphemes>
            </word>
          </words>
        </phrase>
      </phrases>
    </paragraph>
  </paragraphs>
  </interlinear-text>
```

### Word with POS and gloss (no morphemes)

```xml
<word>
  <item type="txt" lang="nhi-Latn">yɨʼa</item>
  <item type="gls" lang="en">dog</item>
  <item type="pos">NOUN</item>
</word>
```

### Punctuation word

```xml
<word>
  <item type="punct">.</item>
</word>
```

### Round‑trip invariants

- If a DB field is absent/empty, omit the corresponding `item` rather than emitting an empty element.
- `lang` on `item[type=txt]` at the lowest relevant level should reflect the data’s writing system; higher levels provide defaults.
- Export order must match DB order fields so that re-parse yields identical ordering counts.

### Future extensions (out of MVP)

- Phrase-level translations (`item type="tr"`).
- Text-level metadata beyond title/source/comment (e.g., `date`, `author`).
- Namespaced FLEXText variants and schema validation.
- Media references and alignment annotations.


