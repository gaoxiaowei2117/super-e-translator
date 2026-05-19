from translator.detect import direction, is_single_word


def test_pure_english():
    assert direction("Hello world") == "auto→zh"


def test_pure_chinese():
    assert direction("你好世界") == "zh→en"


def test_mixed_below_threshold():
    # "hello 你好 there" — 14 chars, 2 chinese = 14% < 30%
    assert direction("hello 你好 there") == "auto→zh"


def test_mixed_above_threshold():
    # "hi 你好世界 ok" — 10 chars, 4 chinese = 40% > 30%
    assert direction("hi 你好世界 ok") == "zh→en"


def test_empty():
    assert direction("") == "auto→zh"


def test_whitespace_only():
    assert direction("   \n\t") == "auto→zh"


# ----- is_single_word -----

def test_single_word_plain():
    assert is_single_word("hello") is True


def test_single_word_uppercase():
    assert is_single_word("Hello") is True


def test_single_word_with_hyphen():
    assert is_single_word("well-known") is True


def test_single_word_with_apostrophe():
    assert is_single_word("don't") is True


def test_single_letter():
    assert is_single_word("a") is True


def test_strips_surrounding_whitespace():
    assert is_single_word("  run  \n") is True


def test_rejects_multiple_words():
    assert is_single_word("hello world") is False


def test_rejects_chinese():
    assert is_single_word("你好") is False


def test_rejects_starts_with_digit():
    assert is_single_word("3d") is False


def test_rejects_punctuation():
    assert is_single_word("hello!") is False


def test_rejects_empty():
    assert is_single_word("") is False


def test_rejects_whitespace_only():
    assert is_single_word("   ") is False


def test_rejects_too_long():
    # 41 chars exceeds the 40-char cap
    assert is_single_word("a" * 41) is False


def test_accepts_at_length_limit():
    # exactly 40 chars
    assert is_single_word("a" * 40) is True
