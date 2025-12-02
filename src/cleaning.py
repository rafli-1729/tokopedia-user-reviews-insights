import re
import string
from rapidfuzz import fuzz
from fuzzywuzzy import process
from typing import List
import unicodedata


def remove_email_and_link(text: str, regex: str=r"http\S+|www\.\S+|\S+@\S+"):
    return re.sub(regex, " ", text)


def handle_word_number(text: str):
    def process_token(tok):
        # Case reduplikasi → akhiran 2
        m = re.match(r"^([A-Za-z]+)2$", tok)
        if m:
            word = m.group(1)
            return f"{word} {word}"

        # Case huruf + angka → ambil hurufnya
        m = re.match(r"^([A-Za-z]+)\d+$", tok)
        if m:
            return m.group(1)

        # Case angka + huruf + angka → ambil hurufnya
        m = re.match(r"^\d+([A-Za-z]+)\d*$", tok)
        if m:
            return m.group(1)

        # Case huruf + angka + huruf (rare but possible)
        m = re.match(r"^([A-Za-z]+)\d+([A-Za-z]+)$", tok)
        if m:
            return m.group(1) + m.group(2)

        # default → tok apa adanya
        return tok

    tokens = text.split()
    tokens = [process_token(t) for t in tokens]
    return " ".join(tokens)


def normalize_unicode(text: str) -> str:
    """Normalize unicode anomalies (italic unicode, etc)."""
    return unicodedata.normalize("NFKC", text)


def map_emoji(text: str, emoji_dict: dict, fallback="[EMOJI_MISC]"):
    """
    Replace emoji using emoji_map.json.
    Unmapped emoji will be replaced with a fallback token.
    """
    emoji_all = (
        "["
        "\U0001F000-\U0001FAFF"
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F900-\U0001F9FF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]"
    )
    pattern = re.compile(emoji_all)

    def replace_emoji(m):
        char = m.group(0)
        if char in emoji_dict:
            return " " + emoji_dict[char] + " "
        else:
            return " " + fallback + " "

    return pattern.sub(replace_emoji, text)


def is_laughter(word: str, whitelist) -> bool:
    if len(word) < 3:
        return False

    if word in whitelist:
        return False

    # must contain laughter sequence
    if any(seq in word for seq in LAUGHTER_SEQS):
        return True

    # chaotic patterns like awokawok, wkwkwkw, hahahhaha
    if (
        len(word) >= 4 and
        sum(char in "hawkow" for char in word) >= (len(word) * 0.7)
    ):
        return True

    return False


def normalize_laughter(word: str) -> str:
    if "wk" in word or "kw" in word:
        return "wkwk"

    if "ha" in word or "he" in word or "hi" in word:
        return "haha"

    return "haha"


def normalize_laughter_word(word: str, whitelist: list[str]) -> str:
    if is_laughter(word, whitelist):
        return normalize_laughter(word)
    return word


def remove_punctuation(text: str) -> str:
    """Replace punctuation with whitespace, keep emoji intact."""
    pattern = "[" + re.escape(string.punctuation) + "]"
    return re.sub(pattern, " ", text)


def reduce_to_two(word: str):
    return re.sub(r"(.)\1{2,}", r"\1\1", word.lower())


def reduce_to_one(word: str):
    return re.sub(r"(.)\1+", r"\1", word.lower())


def longest_prefix_whitelist(word: str, whitelist: set):
    w = word.lower()
    for i in range(len(w), 2, -1):
        pref = w[:i]
        if pref in whitelist:
            return pref
    return None


def should_segment(word):
    if re.search(r"(.)\1{2,}", word):
        return True

    if any(x in word for x in ["ga", "gk", "pls"]):
        return True

    if re.search(r"\d+[A-Za-z]", word):
        return True
    return False


def normalize_stretch(word: str, whitelist: set, slang: dict):
    w = word.lower()

    if w in slang:
        return slang[w]
    if w in whitelist:
        return w

    step2 = reduce_to_two(w)

    # exact match whitelist/slang
    if step2 in slang:
        return slang[step2]
    if step2 in whitelist:
        return step2

    step1 = reduce_to_one(step2)

    # exact match whitelist/slang
    if step1 in slang:
        return slang[step1]
    if step1 in whitelist:
        return step1

    if should_segment(word):
        pref2 = longest_prefix_whitelist(step2, whitelist)
        if pref2:
            return pref2

        pref1 = longest_prefix_whitelist(step1, whitelist)
        if pref1:
            return pref1

    return step2


def normalize_typos(text: str, typo_map: dict) -> str:
    tokens = text.split()
    out = [typo_map.get(t, t) for t in tokens]
    return " ".join(out)


def normalize_slang(text: str, slang_dict: dict) -> str:
    """Replace slang words using dictionary mapping."""
    tokens = text.split()
    out = [slang_dict.get(t, t) for t in tokens]
    return " ".join(out)


def fuzzy_normalize(text: str, fuzzy_targets: dict, whitelist: set) -> str:
    tokens = text.split()
    output = []

    # Build noisy → canonical mapping
    noisy_map = {}
    for canonical, variations in fuzzy_targets.items():
        for var in variations:
            noisy_map[var] = canonical

    for t in tokens:
        t_clean = t.lower()

        # skip whitelist
        if t_clean in whitelist:
            output.append(t_clean)
            continue

        normalized = t_clean
        best_score = 0
        best_match = None

        # fuzzy only to noisy variations
        for noisy_var, canonical in noisy_map.items():
            score = fuzz.ratio(t_clean, noisy_var)
            if score > best_score:
                best_score = score
                best_match = canonical

        if best_score >= 85:  # threshold aman
            normalized = best_match

        output.append(normalized)

    return " ".join(output)


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


class Cleaner:
    """
    Industry-grade text cleaning pipeline.
    Tiga mode cleaning disediakan:
        - clean_for_tokenizer: minimal cleaning tanpa semantic changes
        - clean_for_analysis: moderate cleaning untuk EDA / TF-IDF / topics
        - clean_for_model: full semantic normalization untuk NLP modeling
    """

    def __init__(
        self,
        slang: dict,
        typo: dict,
        whitelist: set,
        fuzzy_targets: dict,
        prefix_suffix: dict,
        emoji_map: dict,
        laughter_list: list,
        negation_list: list,
        stopwords: set,
        pos_lexicon: dict,
    ):
        """
        Load seluruh assets untuk cleaning pipeline.

        - slang           : peta slang -> kata baku
        - typo            : peta typo -> pembenaran
        - whitelist       : kata yang tidak boleh dihapus/diubah
        - fuzzy_targets   : mapping fuzzy noisy variations -> canonical form
        - prefix_suffix   : aturan pemotongan gabungan kata
        - emoji_map       : mapping emoji -> kategori / token
        - laughter_list   : daftar bentuk ketawa untuk deteksi
        - negation_list   : daftar kata negasi (tidak, nggak, gk, dll.)
        - stopwords       : stopword list opsional untuk modeling
        - pos_lexicon     : kamus POS (optional untuk advanced cleaning)
        """

        self.slang = slang
        self.typo = typo
        self.whitelist = whitelist
        self.fuzzy_targets = fuzzy_targets
        self.prefix_suffix = prefix_suffix
        self.emoji_map = emoji_map
        self.laughter_list = laughter_list
        self.negation_list = negation_list
        self.stopwords = stopwords
        self.pos_lexicon = pos_lexicon


    def _normalize_unicode(self, text: str) -> str:
        """Perbaiki unicode anomali, hilangkan karakter aneh."""
        pass


    def _lowercase(self, text: str) -> str:
        """Ubah semua huruf menjadi lowercase."""
        pass


    def _remove_email_and_link(self, text: str) -> str:
        """Hilangkan URL, email, teks copy-paste yang tidak relevan."""
        pass


    def _remove_emoji(self, text: str) -> str:
        """Hilangkan emoji (untuk tokenizer/analysis) ATAU mapping emoji ke token (untuk model)."""
        pass


    def _split_number_word(self, text: str) -> str:
        """Pisahkan angka dan huruf (2hari -> 2 hari) & reduplikasi angka (hari2 -> hari hari)."""
        pass


    def _remove_punctuation(self, text: str) -> str:
        """Hilangkan tanda baca, simpan hanya huruf + angka + spasi."""
        pass


    def _normalize_stretch(self, word: str) -> str:
        """Hilangkan huruf berulang (lamaaaaa -> lamaa -> lama), hormati whitelist & slang."""
        pass


    def _normalize_laughter(self, word: str) -> str:
        """Deteksi bentuk ketawa (wkwkw, awokawok, haha), mapping jadi 1 bentuk standar."""
        pass


    def _apply_prefix_suffix_split(self, word: str) -> str:
        """Gunakan aturan prefix/suffix untuk memisahkan kata gabungan (harusdijual -> harus dijual)."""
        pass


    def _normalize_slang(self, word: str) -> str:
        """Ubah slang menjadi bentuk baku berdasarkan slang.json."""
        pass


    def _normalize_typo(self, word: str) -> str:
        """Ubah typo ke bentuk benar berdasarkan typo.json."""
        pass


    def _apply_negation(self, word: str) -> str:
        """Normalisasi kata negasi (gk, nggak, gk, ga) -> tidak / nggak."""
        pass


    def _apply_fuzzy(self, word: str) -> str:
        """Fuzzy match kata yang mirip dengan target canonical (gkjls -> gak jelas)."""
        pass


    def _remove_stopwords(self, tokens: list[str]) -> list[str]:
        """Hapus stopwords (opsional, hanya di modeling)."""
        pass


    def _apply_whitelist_guard(self, word: str) -> str:
        """Jangan ubah kata yang ada di whitelist."""
        pass


    def _normalize_whitespace(self, text: str) -> str:
        """Hilangkan whitespace berlebih (  banyak   spasi  -> 1 spasi )."""
        pass


    def clean_for_tokenizer(self, text: str) -> str:
        """
        Minimal cleaning.
        Digunakan untuk:
            - training SentencePiece
            - EDA asli (melihat bahasa user apa adanya)
        Tidak boleh mengubah makna:
            - NO slang/typo correction
            - NO fuzzy matching
            - NO stopwords removal
            - NO semantic mapping
        """
        pass


    def clean_for_analysis(self, text: str) -> str:
        """
        Medium cleaning untuk analisis:
            - TF-IDF
            - clustering
            - topic modeling
        Boleh hilangkan noise, tapi tidak boleh ubah makna.
        Langkah:
            - semua clean_for_tokenizer
            - laughter normalize
            - stretch normalize
            - emoji → kategori (bukan token)
            - prefix/suffix splitting
        """
        pass


    def clean_for_model(self, text: str) -> str:
        """
        Full semantic normalization untuk ML model input.
        Hasil harus:
            - rapi
            - konsisten
            - bebas typo & slang
            - bebas noise
            - under single semantic form
        Langkah:
            - semua clean_for_analysis
            - slang normalization
            - typo normalization
            - fuzzy normalization
            - negation normalization
            - emoji → [EMOJI_SAD]
            - laughter → [LAUGH]
            - remove stopwords (optional)
        """
        pass
