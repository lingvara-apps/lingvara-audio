You translate one vocabulary file of an English course (the app "Lingvara" teaches English to speakers of many languages) into ONE target language. The source was written for Turkish speakers: column 2 and column 5 are Turkish. You produce the same file for speakers of the target language.

SOURCE LINE FORMAT:
  # UNIT: <Turkish unit title> | <Turkish subtitle>
  ## <Turkish lesson title>
  <English headword> | <Turkish meaning> | <part of speech> | <English example sentence> | <Turkish translation of the example>

OUTPUT (overlay) FORMAT — exactly one output line per source line, same order:
  # UNIT: <unit title in target language> | <subtitle in target language>
  ## <lesson title in target language>
  <English headword copied EXACTLY> | <meaning in target language> | <translation of the English example into the target language>

RULES
- Same number of lines; '# UNIT:' and '##' lines in the same places. Exactly 3 fields per word line, separated by ' | '. Never use '|' inside a field.
- Column 1 = the English headword copied character by character (including brackets like "go (went, gone)").
- Meaning: short dictionary gloss of the headword in the sense shown by the Turkish meaning and the example (1–3 synonyms, separated by ", "). Translate labels like (informal), (formal), (slang), (BrE), (AmE) into the target language.
- The ten meanings inside one lesson (between two '##' lines) must all be clearly different from each other — the app uses them as quiz answer options. If two words would get the same gloss, add a short distinguishing note in brackets.
- Example translation: natural, idiomatic target language; translate the English example (column 4), not the Turkish.
- Idioms and proverbs: use the real equivalent idiom/proverb of the target language when one exists, otherwise a natural faithful rendering.
- A0 alphabet/sound lines (part of speech "harf · …" or "ses"): column 2 of the source is a pronunciation tip for Turkish speakers — rewrite it as a pronunciation tip for speakers of the TARGET language (compare with sounds/words of the target language). Column 3 of the output = the translation of the example word's meaning.
- No Turkish may remain anywhere (titles, meanings, examples).
- Lesson/unit titles: short, natural.
