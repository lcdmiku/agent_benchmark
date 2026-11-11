from pathlib import Path

BODY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789XYZ"

EXPECTED = "".join(
    f"R2-{i:04d}|{BODY}\n"
    for i in range(256)
).encode("ascii")


def test_file_exists():
    assert Path("/app/long_input.txt").is_file()


def test_exact_content():
    actual = Path("/app/long_input.txt").read_bytes()
    assert actual == EXPECTED


def test_payload_structure():
    actual = Path("/app/long_input.txt").read_bytes()

    assert len(actual) == 12288
    assert actual.count(b"\n") == 256
    assert actual.endswith(b"\n")
    assert not actual.endswith(b"\n\n")
