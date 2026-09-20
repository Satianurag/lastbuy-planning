"""Deterministic source package; excludes credentials, local state and evidence."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--export", action="store_true")
args = parser.parse_args()
folder = "export_functions" if args.export else "functions"
label = "lastbuy-export" if args.export else "lastbuy-functions"
files = [
    (root / folder / name, name)
    for name in ("function_app.py", "host.json", "requirements.txt")
]
files += [
    (p, p.relative_to(root).as_posix())
    for directory in (("lastbuy",) if args.export else ("lastbuy", "web"))
    for p in sorted((root / directory).rglob("*"))
    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
]
target = root / f"evidence/releases/{label}.zip"
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    for path, name in files:
        info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, path.read_bytes())
sha = hashlib.sha256(target.read_bytes()).hexdigest()
frozen = target.with_name(f"{label}-{sha[:16]}.zip")
frozen.write_bytes(target.read_bytes())
record = {
    "archive": str(frozen.relative_to(root)),
    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "files": len(files),
}
(root / f"evidence/{folder}-source-release.json").write_text(
    json.dumps(record, indent=2)
)
print(json.dumps(record))
