#!/usr/bin/env python3
"""Print a JSON build matrix of (package, version, graalpy) not yet released."""
import itertools
import json
import subprocess
import sys

import requests

from common import list_packages, load_buildspec, tag_for

MAX_JOBS = 15


def package_versions(package: str, spec: dict):
    v = spec["package"]["versions"]
    if isinstance(v, list):
        return [str(x) for x in v]
    if v == "latest":
        r = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=30)
        r.raise_for_status()
        return [r.json()["info"]["version"]]
    return [str(v)]


def existing_tags():
    out = subprocess.check_output(["git", "tag", "-l"], text=True)
    return set(out.split())


def main():
    have = existing_tags()
    matrix = []
    for package in list_packages():
        spec = load_buildspec(package)
        if spec.get("disable"):
            continue
        for version, gp in itertools.product(package_versions(package, spec), spec["graalpy"]):
            if tag_for(package, version, gp) not in have:
                matrix.append({"package": package, "version": version, "graalpy": gp})
    json.dump(matrix[:MAX_JOBS], sys.stdout)


if __name__ == "__main__":
    main()
