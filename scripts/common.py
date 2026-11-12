"""Shared helpers: build-spec loading, tag naming, constants."""
import functools
import os
import pathlib
import subprocess
import tempfile
from typing import Any, Dict, List, Set

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"


OWNER_REPO = os.environ.get("GITHUB_REPOSITORY", "bjia56/graalpy-wheels")
INDEX_URL = f"https://{OWNER_REPO.split('/')[0]}.github.io/{OWNER_REPO.split('/')[1]}/"


def tag_for(package: str, version: str, graalpy: str) -> str:
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
    """GraalPy build ids the installed (pinned) cibuildwheel supports on manylinux x86_64."""
    with tempfile.TemporaryDirectory() as d:
        pathlib.Path(d, "setup.py").touch()  # cibuildwheel wants a project dir
        env = {**os.environ, "CIBW_BUILD": "gp*-manylinux_x86_64"}
        out = subprocess.check_output(
            ["cibuildwheel", "--platform", "linux", "--archs", "x86_64",
             "--enable", "graalpy", "--print-build-identifiers", d],
            env=env, text=True,
        )
    return {line.split("-", 1)[0] for line in out.split() if line.startswith("gp")}


def load_buildspec(package: str) -> Dict[str, Any]:
    with open(PACKAGES_DIR / package / "build.yaml") as f:
        spec = yaml.safe_load(f)
    for gp in spec.get("graalpy", []):
        if gp not in cibw_graalpy_ids():
            raise ValueError(
                f"{package}: graalpy id {gp!r} is not supported by the pinned cibuildwheel "
                f"(supported: {sorted(cibw_graalpy_ids())})"
            )
    spec.setdefault("cibuildwheel", {})
    return spec


def list_packages() -> List[str]:
    return sorted(p.name for p in PACKAGES_DIR.iterdir() if (p / "build.yaml").is_file())
