#!/usr/bin/env python3
"""Populate empty shadPS4 externals submodule dirs from .gitmodules.

The committed runtime/sources/shadps4 tree ships without .git, so
`git submodule update --init` cannot work. This clones every externals/*
entry from its .gitmodules URL (branch HEAD, shallow) when the directory
is still empty. Already-populated dirs (aacdec, gcn, stb, ...) are kept.
"""
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
    populated = 0
    for sec in cp.sections():
        path = cp[sec].get("path", "")
        url = cp[sec].get("url", "")
        branch = cp[sec].get("branch") or "HEAD"
        if not url or not path.startswith("externals/"):
            continue
        target = os.path.join(root, path)
        if os.path.isdir(target) and os.listdir(target):
            continue
        print(f"[externals] cloning {url} ({branch}) -> {path}")
        subprocess.run(
            ["git", "clone", "--depth", "1", "-b", branch, url, target],
            check=True,
        )
        populated += 1
    print(f"[externals] populated {populated} dir(s)")

if __name__ == "__main__":
    main()
