from pathlib import Path

OUTPUT = Path("/app/output")

EXPECTED_RESULT = (
    "Recovered after one retry\n"
).encode("utf-8")

EXPECTED_ATTEMPTS = (
    "attempt=1 status=transient_failure\n"
    "attempt=2 status=success\n"
).encode("utf-8")


def test_result_exists():
    assert (OUTPUT / "result.txt").is_file()


def test_attempt_log_exists():
    assert (OUTPUT / "attempts.log").is_file()


def test_result_exact_content():
    actual = (OUTPUT / "result.txt").read_bytes()
    assert actual == EXPECTED_RESULT


def test_exactly_one_recovery():
    actual = (OUTPUT / "attempts.log").read_bytes()
    assert actual == EXPECTED_ATTEMPTS


def test_directory_structure():
    assert OUTPUT.is_dir()
