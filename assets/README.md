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

# Assets and Their Purpose

## 1. `slang.json`
**Purpose:**
Map slang abbreviations → normalized informal forms.

**Examples:**
`gmn → gimana`, `cmn → cuma`

**Used in:**
✔ clean_for_model
✖ tokenizer / analysis

**Priority:**
Slang > Typo

---

## 2. `typo.json`
**Purpose:**
Fix common misspellings.

**Examples:**
`bnaget → banget`, `lemott → lemot`

**Used in:**
✔ clean_for_model
✖ tokenizer / analysis

**Priority:**
Slang > Typo > Fuzzy

---

## 3. `whitelist.txt`
**Purpose:**
Hard-guard: words that must never be modified.

**Examples:**
brand names, product terms, domain vocabulary

**Used in:**
✔ all pipelines (tokenizer, analysis, model)

**Priority:**
Whitelist overrides everything.

---

## 4. `fuzzy_targets.json`
**Purpose:**
Map chaotic/noisy word variations using fuzzy matching.

**Examples:**
`gkjls → gak jelas`, `baaaaanget → banget`

**Used in:**
✔ clean_for_model (final step)

**Priority:**
Fuzzy is always the last semantic operation.

---

## 5. `prefix_suffix.json`
**Purpose:**
Rules to split merged words or attached affixes.

**Examples:**
`harusdijual → harus dijual`, `updatenya → update nya`

**Used in:**
✔ analysis
✔ model
✖ tokenizer

**Priority:**
Applied before slang/typo/fuzzy.

---

## 6. `emoji_map.json`
**Purpose:**
Map emoji into semantic categories/tokens.

**Examples:**
`😭 → [EMOJI_SAD]`
`😂 → [EMOJI_FUNNY]`

**Used in:**
✖ tokenizer (emoji removed)
✔ analysis (category)
✔ model (token)

---

## 7. `laughter.txt`
**Purpose:**
Normalize chaotic laughter forms.

**Examples:**
`wkwkwk`, `awokawok`, `hahahaha`

**Used in:**
✖ tokenizer
✔ analysis
✔ model (tokenized to `[LAUGH]`)

---

## 8. `negation.txt`
**Purpose:**
Normalize negation words into consistent form.

**Examples:**
`gk / ga / kagak / tdk → tidak`

**Used in:**
✔ clean_for_model

**Priority:**
Before fuzzy.

---

## 9. `stopwords.txt`
**Purpose:**
Remove common stopwords (optional for the model).

**Examples:**
`yang`, `ke`, `dari`, `lah`

**Used in:**
✔ clean_for_model (optional)

---

## 10. `pos_lexicon.json`
**Purpose:**
Part-of-speech information for advanced semantic cleaning.

**Used in:**
✔ clean_for_model (optional)

---

# Global Priority Order (Override Rules)

```
1. WHITELIST (never modify)
2. Structural fixes (unicode, punctuation, number-word split, prefix/suffix)
3. Noise cleanup (stretch, laughter, emoji)
4. Slang normalization
5. Typo correction
6. Negation normalization
7. Fuzzy matching (final semantic step)
8. Stopword removal (optional)
```

---

# Summary

Each asset handles a different cleaning responsibility:
- structural fixes
- slang normalization
- typo repair
- semantic normalization
- laughter/emoji mapping
- fuzzy correction
- domain protection via whitelist

Understanding each asset prevents double-processing and guarantees consistent cleaning across tokenizer training, analysis, and modeling.