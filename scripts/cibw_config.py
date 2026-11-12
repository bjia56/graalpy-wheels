#!/usr/bin/env python3
"""Emit a cibuildwheel config (TOML) for a package to stdout."""
import json
import sys

from common import INDEX_URL, load_buildspec


def main(package: str):
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
    for key in ("before_all", "before_build", "test_command", "test_requires"):
        if key in cfg:
            lines.append(f'{key.replace("_", "-")} = {json.dumps(cfg[key])}')
    # json.dumps yields valid TOML basic strings; a table keeps the env readable
    lines.append("")
    lines.append("[tool.cibuildwheel.environment]")
    for k, v in env.items():
        lines.append(f"{k} = {json.dumps(str(v))}")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
