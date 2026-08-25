# MANUS PLAN — onRps4 runtime CI build (Kytyps4)

Goal: make the GitHub Actions workflow `build-runtime` succeed and produce
`runtime-assets` artifact = runtime.zip + manifest.json.

## CURRENT STATUS
- Workflow runs inside `debian:trixie` container, installs deps via
  `runtime/scripts/install-debian-runtime-deps.sh`, then runs
  `runtime/scripts/build-runtime-debian.sh`.
- FAILING STEP: "Populate shadPS4 externals submodules".
  Error: `git clone -b HEAD ...` → "Remote branch HEAD not found".

## FIX 1 — populate-shadps4-submodules.py (REPLACE ENTIRE FILE)
Problem: `.gitmodules` entries with no branch were cloned with `-b HEAD`,
which most remotes reject. Never pass `-b HEAD`; clone the remote default
branch instead. Also never crash the whole run on one bad submodule — log
and continue (CMake will tell us if something essential is missing).

Replace runtime/scripts/populate-shadps4-submodules.py with:

```python
#!/usr/bin/env python3
"""Populate empty shadPS4 externals submodule dirs from .gitmodules."""
import configparser
import os
import subprocess
import sys

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "runtime/sources/shadps4"
    gitmodules = os.path.join(root, ".gitmodules")
    if not os.path.exists(gitmodules):
        raise SystemExit(f"missing {gitmodules}")
    cp = configparser.ConfigParser(strict=False)
    cp.read(gitmodules)
    populated = failed = 0
    for sec in cp.sections():
        path = cp[sec].get("path", "")
        url = cp[sec].get("url", "")
        branch = (cp[sec].get("branch") or "").strip()
        if not url or not path.startswith("externals/"):
            continue
        target = os.path.join(root, path)
        if os.path.isdir(target) and os.listdir(target):
            continue
        print(f"[externals] cloning {url} ({branch or 'default'}) -> {path}", flush=True)
        cmd = ["git", "clone", "--depth", "1"]
        # only pass -b for a real branch name; HEAD/main fall back to default
        use_branch = branch not in ("", "HEAD", "main")
        if use_branch:
            cmd += ["-b", branch]
        cmd += [url, target]
        try:
            subprocess.run(cmd, check=True)
            populated += 1
        except subprocess.CalledProcessError as error:
            # retry once without any -b (remote default branch)
            subprocess.run(["rm", "-rf", target], check=False)
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, target], check=True
                )
                populated += 1
            except subprocess.CalledProcessError:
                failed += 1
                print(f"[externals] FAILED to clone {path}: {error}", flush=True)
                continue
    print(f"[externals] populated={populated} failed={failed}", flush=True)

if __name__ == "__main__":
    main()
```

## FIX 2 — clean half-cloned dirs before rerun
Add a step BEFORE the populate step in the workflow:

```yaml
      - name: Clean partial submodule clones
        run: |
          find runtime/sources/shadps4/externals -maxdepth 1 -type d -empty -delete || true
          rm -rf runtime/sources/shadps4/externals/zlib-ng
```

(The previous run left a broken/partial zlib-ng clone behind; empty dirs
are safe to delete since the script only fills empty ones.)

## NOTES / RULES
- Do NOT touch anything else in the repo.
- Keep the workflow order: deps install → clean → populate submodules →
  build-runtime-debian.sh → verify → upload-artifact.
- If a later step fails, capture the FULL log of that step; do not guess-fix
  other files.
