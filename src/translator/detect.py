import re


def direction(text: str) -> str:
    """Return 'zh→en' if text is mostly Chinese, otherwise 'auto→zh'.

    Threshold: ≥30% of characters are CJK Unified Ideographs.
    """
    if not text or text.isspace():
        return "auto→zh"
    chinese = sum(1 for c in text if "一" <= c <= "鿿")
    return "zh→en" if chinese / len(text) >= 0.3 else "auto→zh"


_SINGLE_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'-]{0,39}$")


def is_single_word(text: str) -> bool:
    """Return True if `text` looks like a single English word.

    Accepts 1-40 ASCII letters with optional apostrophes/hyphens inside.
    Surrounding whitespace is stripped before matching.
    """
    return bool(_SINGLE_WORD_RE.fullmatch(text.strip()))
