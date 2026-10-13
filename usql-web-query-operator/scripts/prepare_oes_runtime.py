"""Fetch pinned official Windows x64 Python/wheels for an offline deployment build."""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

PYTHON_VERSION = "3.13.16"
PYTHON_SHA256 = "97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297"
WHEELS = (
    ("playwright", "1.60.0", "playwright-1.60.0-py3-none-win_amd64.whl"),
    ("openpyxl", "3.1.5", "openpyxl-3.1.5-py2.py3-none-any.whl"),
    ("tzdata", "2026.2", "tzdata-2026.2-py2.py3-none-any.whl"),
    ("greenlet", "3.5.6", "greenlet-3.5.6-cp313-cp313-win_amd64.whl"),
    ("pyee", "13.0.1", "pyee-13.0.1-py3-none-any.whl"),
    ("et-xmlfile", "2.0.0", "et_xmlfile-2.0.0-py3-none-any.whl"),
    ("typing-extensions", "4.16.0", "typing_extensions-4.16.0-py3-none-any.whl"),
)


def fetch(destination: Path) -> dict:
    destination = destination.resolve()
    skills = Path(__file__).resolve().parents[2]
    if destination == skills or skills in destination.parents:
        raise ValueError("Runtime payloads must stay outside the skills repository.")
    destination.mkdir(parents=True, exist_ok=True)
    entries = []

    def download(relative, url, digest):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            temporary = path.with_suffix(path.suffix + ".download")
            urllib.request.urlretrieve(url, temporary)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
                raise ValueError("Official payload checksum mismatch.")
            temporary.replace(path)
        entries.append({"path": relative, "sha256": digest, "source": url})

    archive = f"python-{PYTHON_VERSION}-embed-amd64.zip"
    download(archive, f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{archive}", PYTHON_SHA256)
    for name, version, filename in WHEELS:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as response:
            metadata = json.load(response)
        files = [item for item in metadata["urls"] if item["filename"] == filename and not item.get("yanked")]
        if len(files) != 1 or not files[0]["url"].startswith("https://files.pythonhosted.org/"):
            raise ValueError("Expected pinned official Windows wheel is unavailable.")
        download("wheels/" + filename, files[0]["url"], files[0]["digests"]["sha256"])
    manifest = {"python_version": PYTHON_VERSION, "architecture": "AMD64", "files": entries}
    (destination / "runtime-payload.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"status": "completed", "directory": str(destination), "files": len(entries), "python": PYTHON_VERSION}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    print(json.dumps(fetch(parser.parse_args().output_dir), indent=2))
