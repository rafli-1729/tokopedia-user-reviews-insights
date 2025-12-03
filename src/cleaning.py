import re
import string
from rapidfuzz import fuzz
from fuzzywuzzy import process
from typing import List
import unicodedata

class CleaningPipeline:
    def __init__(
        self,
        slang: Dict[str, str],
        typo: Dict[str, str],
        whitelist: Set[str],
        prefix_suffix: Dict[str, str],
        emoji_map: Dict[str, str],
        laughter_list: List[str],
        negation_list: List[str],
        stopwords: Set[str],
        pos_lexicon: Dict[str, str],
    ):
        self.slang = slang
        self.typo = typo
        self.whitelist = set(whitelist)
        self.prefix_suffix = prefix_suffix
        self.emoji_map = emoji_map
        self.laughter_list = set(laughter_list)
        self.negation_list = set(negation_list)
        self.stopwords = set(stopwords)
        self.pos_lexicon = pos_lexicon

    # ---------------------- BASIC HELPERS ---------------------- #

    def _remove_email_and_link(
        self, text: str, regex: str = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ) -> str:
        return re.sub(regex, " ", text)

    def _handle_word_number(self, text: str):
        text = re.sub(r"(\d)([A-Za-z])", r"\1 \2", text)   # 2hari → 2 hari
        text = re.sub(r"([A-Za-z])(\d)", r"\1 \2", text)   # hari2 → hari 2

        text = re.sub(r"\b([A-Za-z]+) 2\b", r"\1 \1", text)
        text = re.sub(r"\b([A-Za-z]+) \d+\b", r"\1", text)

        return text

    def _normalize_unicode(self, text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    # ---------------------- EMOJI HANDLER ---------------------- #

    def _map_emoji(self, text: str, fallback: str = "[EMOJI_MISC]") -> str:
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

        def replace(m):
            ch = m.group(0)
            return " " + self.emoji_map.get(ch, fallback) + " "

        return pattern.sub(replace, text)

    # ---------------------- LAUGHTER DETECTION ---------------------- #

    def _is_laughter(self, word: str) -> bool:
        w = word.lower()

        if len(w) < 3:
            return False
        if w in self.whitelist or w in self.slang:
            return False
        if w in self.laughter_list:
            return True
        if any(l in w for l in self.laughter_list):
            return True
        if re.search(r"(wk|kw|wok|awok|okaw)+", w):
            return True
        if sum(c in "hahehihuhu" for c in w) >= len(w) * 0.6:
            return True
        if re.search(r"(x[aiueo]){2,}", w):
            return True
        if w.startswith(("lol", "lmao", "rofl")):
            return True
        if "ngak" in w:
            return True

        return False

    def _normalize_laugh(self, word: str):
        w = word.lower()
        if any(p in w for p in ["wk", "kw", "awok", "kekw", "ngak"]):
            return "wkwk"
        return "haha"

    def _tokenize(self, text: str):
        return re.findall(r"\w+|[^\w\s]", text)

    def _normalize_laughter(self, text: str) -> str:
        toks = self._tokenize(text)
        out = []

        for t in toks:
            if self._is_laughter(t):
                out.append(self._normalize_laugh(t))
            else:
                out.append(t)

        result = ""
        for tok in out:
            if tok.isalnum():
                result += tok + " "
            else:
                result += tok

        return result.strip()

    # ---------------------- PUNCTUATION & STRETCH ---------------------- #

    def _remove_punctuation(self, text: str) -> str:
        pattern = "[" + re.escape(string.punctuation) + "]"
        return re.sub(pattern, " ", text)

    def _reduce_to_two(self, word: str):
        return re.sub(r"(.)\1{2,}", r"\1\1", word.lower())

    def _reduce_to_one(self, word: str):
        return re.sub(r"(.)\1+", r"\1", word.lower())

    def _longest_prefix_whitelist(self, word: str):
        w = word.lower()
        for i in range(len(w), 2, -1):
            pref = w[:i]
            if pref in self.whitelist:
                return pref
        return None

    def _should_segment(self, word: str):
        if re.search(r"(.)\1{2,}", word):
            return True
        if any(x in word for x in ["ga", "gk", "pls"]):
            return True
        if re.search(r"\d+[A-Za-z]", word):
            return True
        return False

    def _normalize_stretch(self, word: str):
        if word.startswith("[") and word.endswith("]"):
            return word

        w = word.lower()
        original = w

        step2 = self._reduce_to_two(w)
        step1 = self._reduce_to_one(step2)

        if step1 == original:
            return w

        # Setelah ini baru coba mapping
        if step1 in self.slang:
            return self.slang[step1]
        if step1 in self.typo:
            return self.typo[step1]
        if step1 in self.whitelist:
            return step1
        if step1 in self.negation_list:
            return step1

        # prefix segmentation
        if self._should_segment(w):
            pref2 = self._longest_prefix_whitelist(step2)
            if pref2:
                return pref2
            pref1 = self._longest_prefix_whitelist(step1)
            if pref1:
                return pref1

        return step1

    # ---------------------- TYPO, SLANG, STOPWORDS ---------------------- #

    def _normalize_typos(self, text: str) -> str:
        return " ".join(self.typo.get(t, t) for t in text.split())

    def _normalize_slang(self, text: str) -> str:
        return " ".join(self.slang.get(t, t) for t in text.split())

    def _remove_stopwords(self, text: str) -> str:
        return " ".join(t for t in text.split() if t not in self.stopwords)

    def _drop_lowinfo(self, text: str):
        if len(text.strip()) == 0:
            return ""
        if len(text.split()) < 2:
            return ""
        return text

    def _normalize_whitespace(self, text: str):
        return " ".join(text.split())

    # ---------------------- TYPO, SLANG, STOPWORDS ---------------------- #

    def explain(self, text: str):
        original = text
        log = []

        def step(name, fn, inp):
            out = fn(inp)

            # # ignore whitespace-only changes
            if inp.split() == out.split():
                return out

            log.append((name, inp, out))
            return out

        # ===== PIPELINE ORDER ===== #
        text = step("Normalize Unicode", self._normalize_unicode, text)
        text = step("Lowercase", lambda x: x.lower(), text)
        text = step("Remove Links", self._remove_email_and_link, text)
        text = step("Remove Punctuation", self._remove_punctuation, text)
        text = step("Handle Word Number", self._handle_word_number, text)
        text = step("Normalize Laughter", self._normalize_laughter, text)
        text = step("Map Emoji", self._map_emoji, text)

        # stretch per-token
        def stretch_all(t):
            return " ".join(self._normalize_stretch(tok) for tok in t.split())
        text = step("Normalize Stretch", stretch_all, text)

        text = step("Normalize Typos", self._normalize_typos, text)
        text = step("Normalize Slang", self._normalize_slang, text)
        text = step("Remove Stopwords", self._remove_stopwords, text)
        text = step("Normalize Whitespace", self._normalize_whitespace, text)
        text = step("Drop Lowinfo", self._drop_lowinfo, text)

        # ===== PRINT RESULT ===== #
        print("=== EXPLAIN CLEANING PIPELINE ===")
        print("Input:", original)
        print("---------------------------------")

        if not log:
            print("(No changes occurred — text is already normalized!)")
            return text

        for name, before, after in log:
            print(f"[{name}]")
            print(f"  before: {before}")
            print(f"  after : {after}")
            print("---------------------------------")

        return text