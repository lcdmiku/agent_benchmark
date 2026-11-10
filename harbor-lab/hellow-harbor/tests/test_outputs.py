from pathlib import Path


def test_hello_file_exists():
    """The agent must create hello.txt."""
    output = Path("/app/hello.txt")

    assert output.is_file(), "hello.txt does not exist"


def test_hello_file_content():
    """The file must contain the exact expected content."""
    output = Path("/app/hello.txt")

    assert output.read_text(encoding="utf-8") == "Hello from DSH\n"
