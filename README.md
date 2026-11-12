# graalpy-wheels

Prebuilt wheels for [GraalPy](https://www.graalvm.org/python/) on Linux x86_64, hosted as a PyPI-compatible index on GitHub Pages.

```
pip install --extra-index-url https://bjia56.github.io/graalpy-wheels/ cryptography grpcio
```

## How it works

- `packages/<name>/build.yaml` declares the GraalPy builds (pinned cibuildwheel ids), package versions (`latest` or a list) and per-package cibuildwheel overrides.
- A nightly workflow (`periodic_build_all.yml`) computes which `(package, version, graalpy)` combinations have no git tag yet and builds them serially with [cibuildwheel](https://cibuildwheel.pypa.io/) from the PyPI sdist.
- Each build is published as a GitHub Release tagged `<package>-<version>-<graalpy id>`.
- The index (`scripts/generate_index.py`) is regenerated from release assets on every deploy and published with GitHub Pages; nothing generated is committed.
- Builds resolve their own dependencies against this index (`PIP_EXTRA_INDEX_URL`), so wheels published earlier are reused.

## Adding a package

Create `packages/<name>/build.yaml` (see `packages/grpcio`). Trigger "Periodic build all" or run "Build and release" manually.
