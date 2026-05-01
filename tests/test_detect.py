from translator.detect import direction


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
