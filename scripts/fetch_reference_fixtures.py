"""Acquire public R BE fixture once; offline tests use the resulting CSV."""

import base64
import hashlib
import json
from pathlib import Path

import pyreadr
import requests

target = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
target.mkdir(parents=True, exist_ok=True)
url = "https://api.github.com/repos/cran/BE/git/blobs/f1c5cc184a7e97e87742b5edd43ecaa2a6d4fe0b"
response = requests.get(url, timeout=25)
response.raise_for_status()
payload = base64.b64decode(response.json()["content"])
binary = target / "NCAResult4BE.rda"
binary.write_bytes(payload)
result = pyreadr.read_r(str(binary))["NCAResult4BE"]
result.to_csv(target / "BE_NCAResult4BE.csv", index=False)
print(result.head().to_string(index=False))
print(result.shape, result.dtypes)
metadata = dict(
    source=url,
    source_sha256=hashlib.sha256(payload).hexdigest(),
    expected_source="https://asancpt.github.io/BE/reference/test2x2.html",
    reader="pyreadr 0.5.8",
    note="Public reference PK endpoints; not a synthetic learning study.",
)
(target / "BE_reference_provenance.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
