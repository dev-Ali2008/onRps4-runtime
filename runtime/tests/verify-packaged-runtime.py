#!/usr/bin/env python3
"""Verify packaged runtime.zip ↔ manifest.json consistency.

Mirrors app RuntimeInstaller rules:
  - exact 1:1 set match between manifest.files and zip entries
  - per-file size + sha256 match
  - optional --no-vortek: fail if any vortek artifact slipped in
"""
import hashlib
import json
import sys
import zipfile

def main():
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <assets-dir> [--no-vortek]", file=sys.stderr)
        return 64
    assets = sys.argv[1]
    no_vortek = "--no-vortek" in sys.argv

    with open(f"{assets}/manifest.json", "rb") as f:
        manifest = json.loads(f.read())
    zf = zipfile.ZipFile(f"{assets}/runtime.zip")

    zip_names = {n for n in zf.namelist() if not n.endswith("/")}
    man_names = {f["path"] for f in manifest["files"]}

    errors = []
    for name in sorted(zip_names - man_names):
        errors.append(f"zip entry missing from manifest: {name}")
    for name in sorted(man_names - zip_names):
        errors.append(f"manifest entry missing from zip: {name}")

    for f in manifest["files"]:
        info = zf.getinfo(f["path"])
        data = zf.read(f["path"])
        if info.file_size != f["size"]:
            errors.append(f"size mismatch: {f['path']} ({info.file_size} != {f['size']})")
        digest = hashlib.sha256(data).hexdigest()
        if digest != f["sha256"]:
            errors.append(f"sha256 mismatch: {f['path']}")

    if no_vortek:
        offenders = sorted(n for n in zip_names | man_names if "vortek" in n.lower())
        errors.extend(f"vortek artifact present: {n}" for n in offenders)

    if errors:
        print("FAIL")
        for e in errors:
            print(" ", e)
        return 1

    print(f"OK: {len(man_names)} files, manifest↔zip consistent, hashes valid"
          + (", no vortek" if no_vortek else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
