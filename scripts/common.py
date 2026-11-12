"""Shared helpers: build-spec loading, tag naming, constants."""
import os
import pathlib
from typing import Any, Dict, List

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"

# Pinned to the two newest GraalPy releases cibuildwheel supports on
# manylinux_x86_64. Bump together with the pinned cibuildwheel version.
SUPPORTED_GRAALPY = ["gp312_250", "gp313_253"]
CIBUILDWHEEL_VERSION = "4.3.5"

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


def load_buildspec(package: str) -> Dict[str, Any]:
    with open(PACKAGES_DIR / package / "build.yaml") as f:
        spec = yaml.safe_load(f)
    for gp in spec.get("graalpy", []):
        if gp not in SUPPORTED_GRAALPY:
            raise ValueError(f"{package}: unsupported graalpy id {gp!r}")
    spec.setdefault("cibuildwheel", {})
    return spec


def list_packages() -> List[str]:
    return sorted(p.name for p in PACKAGES_DIR.iterdir() if (p / "build.yaml").is_file())
