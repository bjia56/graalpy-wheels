#!/usr/bin/env python3
"""Emit a cibuildwheel config (TOML) for a package to stdout."""
import json
import shlex
import sys

from common import INDEX_URL, load_buildspec


def graalpy_patch_cmd(package: str, version: str) -> str:
    """Apply GraalPy's own sdist patches (autopatch_capi + metadata.toml rules).

    GraalPy's patched pip does this when it unpacks an sdist, but cibuildwheel
    builds from an already-unpacked tree, so we invoke the same entry point.
    The filename is only parsed for the package name and version.
    """
    py = (
        "import logging; logging.basicConfig(level=logging.INFO); "
        "import graalpy_pip_extensions as g; "
        f"g.apply_graalpy_patches({f'{package}-{version}.tar.gz'!r}, '.')"
    )
    return f"python -c {shlex.quote(py)}"


def main(package: str, version: str):
    cfg = load_buildspec(package)["cibuildwheel"]
    # Self-reference: dependencies resolve against our own index first-class,
    # so earlier builds (e.g. cffi for cryptography) are reused.
    env = {
        "PIP_EXTRA_INDEX_URL": INDEX_URL,
        "PIP_PREFER_BINARY": "1",
        **cfg.get("environment", {}),
    }
    lines = ["[tool.cibuildwheel]"]
    lines.append('enable = ["graalpy"]')
    lines.append('manylinux-x86_64-image = "manylinux_2_28"')
    lines.append('manylinux-aarch64-image = "manylinux_2_28"')
    # `patch` is needed to apply GraalPy's package patches
    before_all = "command -v patch >/dev/null || yum install -y patch"
    if cfg.get("before_all"):
        before_all += "\n" + cfg["before_all"].strip()
    lines.append(f"before-all = {json.dumps(before_all)}")
    before_build = graalpy_patch_cmd(package, version)
    if cfg.get("before_build"):
        before_build += "\n" + cfg["before_build"].strip()
    lines.append(f"before-build = {json.dumps(before_build)}")
    for key in ("test_command", "test_requires"):
        if key in cfg:
            lines.append(f'{key.replace("_", "-")} = {json.dumps(cfg[key])}')
    # json.dumps yields valid TOML basic strings; a table keeps the env readable
    lines.append("")
    lines.append("[tool.cibuildwheel.environment]")
    for k, v in env.items():
        lines.append(f"{k} = {json.dumps(str(v))}")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
