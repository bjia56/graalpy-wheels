#!/usr/bin/env python3
"""Keep only the wheels belonging to <package> in <dir>; delete everything else.

Usage: filter_wheels.py <package> <dir>
Fails if no wheel for <package> remains.
"""
import pathlib
import sys

from normalize import normalize


def main(package: str, directory: str) -> int:
    want = normalize(package)
    kept = []
    for whl in sorted(pathlib.Path(directory).glob("*.whl")):
        dist = whl.name.split("-", 1)[0]
        if normalize(dist) == want:
            kept.append(whl.name)
        else:
            print(f"dropping unrelated wheel: {whl.name}")
            whl.unlink()
    if not kept:
        print(f"error: no wheel for {package} in {directory}", file=sys.stderr)
        return 1
    print("keeping: " + ", ".join(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
