"""Shared helpers: build-spec loading, release naming/lookup, constants."""
import functools
import os
import pathlib
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Set

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"


OWNER_REPO = os.environ.get("GITHUB_REPOSITORY", "bjia56/graalpy-wheels")
INDEX_URL = f"https://{OWNER_REPO.split('/')[0]}.github.io/{OWNER_REPO.split('/')[1]}/"


# cibuildwheel platform ids we build, in build order. Packages can restrict
# this with a `platforms:` list in build.yaml.
PLATFORMS = ["manylinux_x86_64", "manylinux_aarch64"]


def tag_for(package: str, version: str, graalpy: str) -> str:
    """One GitHub release per (package, version, graalpy); every platform's
    wheel is attached to the same release."""
    return f"{package}-{version}-{graalpy}"


def parse_tag(tag: str):
    """Inverse of tag_for -> (package, version, graalpy) or None."""
    try:
        rest, graalpy = tag.rsplit("-", 1)
        package, version = rest.rsplit("-", 1)
    except ValueError:
        return None
    return package, version, graalpy


@functools.lru_cache(maxsize=None)
def cibw_graalpy_ids() -> Set[str]:
    """Full GraalPy build ids (e.g. gp312_250-manylinux_aarch64) that the
    installed (pinned) cibuildwheel supports on the platforms we build."""
    archs = ",".join(p.split("_", 1)[1] for p in PLATFORMS)
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, "setup.py").touch()  # cibuildwheel wants a project dir
        env = {**os.environ, "CIBW_BUILD": "gp*"}
        out = subprocess.check_output(
            ["cibuildwheel", "--platform", "linux", "--archs", archs,
             "--enable", "graalpy", "--print-build-identifiers", d],
            env=env, text=True,
        )
    return {line for line in out.split() if line.startswith("gp")}


def fetch_releases():
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/repos/{OWNER_REPO}/releases",
            params={"per_page": 100, "page": page}, headers=headers, timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            return
        yield from batch
        page += 1


def wheel_platform(filename: str):
    """'foo-1-gp-gp-manylinux_2_28_x86_64.manylinux2014_x86_64.whl' -> 'manylinux_x86_64'."""
    m = re.search(r"(x86_64|aarch64)\.whl$", filename)
    return f"manylinux_{m.group(1)}" if m else None


def released_builds() -> Set[tuple]:
    """(package, version, graalpy, platform) tuples that already have a wheel on a release."""
    done = set()
    for rel in fetch_releases():
        parsed = parse_tag(rel["tag_name"])
        if rel.get("draft") or not parsed:
            continue
        for a in rel["assets"]:
            plat = wheel_platform(a["name"]) if a["name"].endswith(".whl") else None
            if plat:
                done.add((*parsed, plat))
    return done


def load_buildspec(package: str) -> Dict[str, Any]:
    with open(PACKAGES_DIR / package / "build.yaml") as f:
        spec = yaml.safe_load(f)
    spec.setdefault("platforms", PLATFORMS)
    for plat in spec["platforms"]:
        if plat not in PLATFORMS:
            raise ValueError(f"{package}: unknown platform {plat!r} (known: {PLATFORMS})")
        for gp in spec.get("graalpy", []):
            if f"{gp}-{plat}" not in cibw_graalpy_ids():
                raise ValueError(
                    f"{package}: build id {gp}-{plat} is not supported by the pinned "
                    f"cibuildwheel (supported: {sorted(cibw_graalpy_ids())})"
                )
    spec.setdefault("cibuildwheel", {})
    return spec


def list_packages() -> List[str]:
    return sorted(p.name for p in PACKAGES_DIR.iterdir() if (p / "build.yaml").is_file())
