def direction(text: str) -> str:
    """Return 'zh→en' if text is mostly Chinese, otherwise 'auto→zh'.

    Threshold: ≥30% of characters are CJK Unified Ideographs.
    """
    if not text or text.isspace():
        return "auto→zh"
    chinese = sum(1 for c in text if "一" <= c <= "鿿")
    return "zh→en" if chinese / len(text) >= 0.3 else "auto→zh"
