#!/usr/bin/env python3
"""Populate empty shadPS4 externals submodule dirs from .gitmodules."""
import configparser
import os
import subprocess
import sys


def populate_nested_submodules(target, path):
    if not os.path.exists(os.path.join(target, ".git")):
        return True
    try:
        subprocess.run(
            [
                "git",
                "-C",
                target,
                "submodule",
                "update",
                "--init",
                "--recursive",
                "--depth",
                "1",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as error:
        print(f"[externals] FAILED nested submodules for {path}: {error}", flush=True)
        return False


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
            if not populate_nested_submodules(target, path):
                failed += 1
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
        if not populate_nested_submodules(target, path):
            failed += 1
    print(f"[externals] populated={populated} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
