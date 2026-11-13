#!/usr/bin/env python3
"""Print a JSON build matrix of (package, version, graalpy, platform) with no wheel on its release yet."""
import itertools
import json
import sys

import requests

from common import list_packages, load_buildspec, released_builds

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


def main():
    have = released_builds()
    matrix = []
    for package in list_packages():
        spec = load_buildspec(package)
        if spec.get("disable"):
            continue
        for version, gp, plat in itertools.product(
            package_versions(package, spec), spec["graalpy"], spec["platforms"]
        ):
            if (package, version, gp, plat) not in have:
                matrix.append({"package": package, "version": version, "graalpy": gp, "platform": plat})
    json.dump(matrix[:MAX_JOBS], sys.stdout)


if __name__ == "__main__":
    main()
