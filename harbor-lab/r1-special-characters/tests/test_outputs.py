from pathlib import Path

EXPECTED_TEXT = (
    "第一行：你好，DSH！\n"
    '第二行：双引号 "你好" 与单引号 \'你好\'\n'
    "第三行：反斜杠 \\ 和美元符号 $HOME\n"
    "第四行：Emoji：🐳 🚀\n"
)


def test_file_exists():
    assert Path("/app/special.txt").is_file()


def test_exact_utf8_content():
    actual = Path("/app/special.txt").read_bytes()
    expected = EXPECTED_TEXT.encode("utf-8")

    assert actual == expected
