from pathlib import Path

EXPECTED = {
    Path("/app/output/summary.txt"):
        "Project: R3 Multi-file Smoke Test\n"
        "Status: complete\n"
        "Files: 3\n",

    Path("/app/output/data/records.csv"):
        "id,name,status\n"
        "1,alpha,ready\n"
        "2,beta,ready\n"
        "3,gamma,ready\n",

    Path("/app/output/config/settings.json"):
        '{\n'
        '  "project": "R3",\n'
        '  "version": 1,\n'
        '  "enabled": true\n'
        '}\n',
}


def test_all_files_exist():
    for path in EXPECTED:
        assert path.is_file(), f"Missing file: {path}"


def test_exact_file_contents():
    for path, content in EXPECTED.items():
        assert path.read_bytes() == content.encode("utf-8"), (
            f"Incorrect content: {path}"
        )


def test_directory_structure():
    assert Path("/app/output").is_dir()
    assert Path("/app/output/data").is_dir()
    assert Path("/app/output/config").is_dir()
