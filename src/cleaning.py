import re
from rapidfuzz import fuzz
from typing import List

# Core Cleaning Functions
def remove_emoji(text: str) -> str:
    """Remove emoji using unicode ranges."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)


def normalize_laughter(text: str) -> str:
    """Normalize repeated laughter patterns: hahaha, wkwkwk."""
    text = re.sub(r"(ha)+", "haha", text)
    text = re.sub(r"(wk)+", "wkwk", text)
    return text


def collapse_repeated_chars(text: str) -> str:
    """
    Reduce characters repeated >2 times into a single repetition.
    Example: 'baaaangettt' → 'banget'
    """
    return re.sub(r"(.)\1{2,}", r"\1", text)


def normalize_vowel_stretch(text: str) -> str:
    """
    Normalize vowel stretching (laaamaaa -> lama).
    This is common in Indonesian informal reviews.
    """
    return re.sub(r"([aeiou])\1+", r"\1", text)


def normalize_slang(text: str, slang_dict: dict) -> str:
    """Replace slang words using dictionary mapping."""
    tokens = text.split()
    out = [slang_dict.get(t, t) for t in tokens]
    return " ".join(out)


def fuzzy_normalize(text: str, fuzzy_targets: dict) -> str:
    """
    Apply fuzzy matching only on known noisy words (e.g., banget, lemot).
    fuzzy_targets format:
    {
        "banget": ["bangett", "bangeet"],
        "tolong": ["tolooong"]
    }
    """
    tokens = text.split()
    output = []

    for t in tokens:
        normalized = t
        for canonical, variations in fuzzy_targets.items():
            if fuzz.ratio(t, canonical) >= 85:
                normalized = canonical
                break
        output.append(normalized)

    return " ".join(output)


def remove_punctuation(text: str) -> str:
    """Remove all characters except letters, numbers, and spaces."""
    return re.sub(r"[^a-z0-9\s]", " ", text)


def remove_stopwords(text: str, stopwords: List[str]) -> str:
    """Remove stopwords from token list."""
    tokens = text.split()
    tokens = [t for t in tokens if t not in stopwords]
    return " ".join(tokens)


def drop_lowinfo(text: str) -> str:
    """
    Remove texts that are too short or contain no real information.
    e.g., "ok", "gg", "", "..."
    """
    if len(text.strip()) == 0:
        return ""
    if len(text.split()) < 2:
        return ""
    return text


# Full Cleaning Pipeline
def clean_text(text: str,
               slang: dict,
               stopwords: List[str],
               fuzzy_targets: dict
) -> str:

    if not isinstance(text, str):
        return ""

    text = remove_emoji(text)
    text = normalize_laughter(text)
    text = collapse_repeated_chars(text)
    text = normalize_vowel_stretch(text)

    text = remove_punctuation(text)
    text = normalize_slang(text, slang)
    text = fuzzy_normalize(text, fuzzy_targets)

    text = remove_stopwords(text, stopwords)

    text = " ".join(text.split())
    text = drop_lowinfo(text)

    return text