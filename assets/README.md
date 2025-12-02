# Text Cleaning Assets Overview

This document explains the purpose of each text-cleaning asset and how they interact inside the pipeline.
Each asset exists to avoid conflicts, semantic overrides, or duplicated logic.

---

## Cleaning Pipeline Overview

The project uses three context-based cleaning modes:

| Pipeline | Purpose |
|----------|---------|
| `clean_for_tokenizer()` | Minimal cleaning for SentencePiece training & raw EDA. No semantic changes. |
| `clean_for_analysis()` | Medium cleaning for TF-IDF, clustering, topic modeling. Removes chaotic noise but preserves meaning. |
| `clean_for_model()` | Full semantic normalization for ML training/inference. Applies dictionary, typo, and fuzzy correction. |

---

# List of Assets

## 1. `slang.json`

A mapping of Indonesian slang or abbreviations into their normalized informal forms.
Since raw user-generated text — especially scraped from real-world platforms — is often extremely noisy, a comprehensive slang dictionary helps ensure more accurate text cleaning and downstream analysis.

**Examples:**

```json
{
  "gmn": "gimana", "cmn": "cuma", "bgt": "banget", "sgt": "sangat"
}
```

---

## 2. `typo.json`

Fix common misspellings found in user-generated text. These mappings help correct frequent human typos so that semantically identical words map to the same form.

**Examples:**

```json
{
  "bnaget": "banget", "lemott": "lemot", "bngt": "banget", "lmot": "lemot"
}
```

---

## 3. `whitelist.txt`

A list of words that must never be modified during cleaning.
This acts as a *hard guard*, ensuring that important domain-specific terms remain intact.

**Examples:**
```txt
tokopedia google play scraper
```

---

## 4. `prefix_suffix.json`

Rules for splitting merged words or separating attached affixes.
These mappings help detect and correct cases where users unintentionally merge words or append particles/pronouns without spacing.

**Examples:**

```json
{
  "harusdijual": "harus dijual", "updatenya": "update nya", "jualinaja": "jualin aja", "belomtau": "belom tau"
}
```

---

## 5. `emoji_map.json`

A mapping of emojis into semantic categories or tokens.
This helps downstream models interpret emotional content without relying on raw emoji characters.

**Examples:**

```json
{
  "😭": "[EMOJI_SAD]", "😂": "[EMOJI_FUNNY]", "😡": "[EMOJI_ANGRY]", "😍": "[EMOJI_LOVE]"
}
```

---

## 6. `laughter.txt`

A collection of chaotic Indonesian laughter variations.
All listed forms will be normalized into a single non-semantic token (e.g., `wkwk`), ensuring consistency across different laughter styles.

**Examples:**

```txt
wkwkwk awokawok aowkaowk hahahaha hehehe ngakak
```

---

## 7. `negation.txt`

Normalize various negation forms into a consistent canonical token (e.g., `tidak`).
This ensures that different stylistic or slang variants of negation map to the same meaning.

**Examples:**

```txt
gk ga gak tdk tak kagak engga enggak
```

---

## 8. `stopwords.txt`

A list of common Indonesian stopwords that can optionally be removed during preprocessing.
These words carry low semantic value and often do not contribute meaningfully to classification tasks, depending on the model.

**Examples:**

```txt
yang ke dari lah dia itu para
```


---

## 9. `pos_lexicon.json`

A lexicon containing part-of-speech (POS) tags for selected Indonesian words.
This resource enables *advanced semantic-aware cleaning*, where certain transformations depend on the grammatical role of a word.

Some words should not be stemmed if they function as nouns, while certain prefixes and suffixes are only valid for verbs `(V)` or adjectives `(ADJ)`. Ambiguous forms such as bisa, cepat, or jatuh can also be clarified using POS information to avoid incorrect normalization. Because of this, the POS lexicon becomes essential for enabling context-aware normalization, allowing the cleaning pipeline to filter noise without breaking important meaning and preventing over-normalization of domain vocabulary. It also lays the groundwork for more advanced syntactic features in the future, including tasks like phrase extraction or chunking that rely on accurate grammatical categories.

**Examples:**

```json
{
  "beli": "V", "jualan": "N", "cepat": "ADJ", "lebih": "ADV", "lagi": "ADV",
  "sangat": "ADV", "mau": "V", "barang": "N", "murah": "ADJ", "pengiriman": "N",
  "datang": "V", "telat": "ADJ", "lama": "ADJ", "kemarin": "ADV", "gratis": "ADJ",
  "coba": "V", "bisa": "V", "produk": "N"
}
```

---

# Global Priority Order (Override Rules)

```
START
 ↓
[1] Structural Fixes
    - Normalize unicode
    - Lowercasing
    - Remove links/emails
    - Replace punctuation
    - Handle number-word-number pattern
 ↓
[2] Noise Cleanup
    - Reduce stretched characters
    - Normalize laughter
    - Map emojis to semantic tokens
 ↓
[3] Check WHITELIST
    ├─ Fix merged words via prefix/suffix rules
    ├─ If word is in whitelist → FINISH
    └─ If not → continue
 ↓
[4] Slang Normalization
    ├─ If word in slang.json → replace
    └─ Otherwise → continue
 ↓
[5] Typo Correction
    ├─ If word in typo.json → fix
    └─ Otherwise → continue
 ↓
[6] Negation Normalization
    ├─ If word in negation list → convert to "tidak"
    └─ Otherwise → continue
 ↓
[7] Fuzzy Matching
    - Apply fuzzy_targets rules
    - Replace if similarity threshold passes
 ↓
[8] Optional Stopword Removal
 ↓
FINISH
```