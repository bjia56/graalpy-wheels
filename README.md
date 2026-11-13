# graalpy-wheels

Prebuilt wheels for [GraalPy](https://www.graalvm.org/python/) on Linux (x86_64 and aarch64), hosted as a PyPI-compatible index on GitHub Pages.

```
pip install --extra-index-url https://bjia56.github.io/graalpy-wheels/ <package>
```

## How it works

- `packages/<name>/build.yaml` declares the GraalPy builds (and, optionally, a `platforms:` list; the default is every platform in `scripts/common.py`) (cibuildwheel ids, validated against what the pinned cibuildwheel in `requirements.txt` supports), package versions (`latest` or a list) and per-package cibuildwheel overrides.
- A nightly workflow (`periodic_build_all.yml`) computes which `(package, version, graalpy, platform)` combinations have no wheel on their release yet and builds them serially, each on a native runner (no emulation) with [cibuildwheel](https://cibuildwheel.pypa.io/) from the PyPI sdist.
- Only wheels for the requested package are uploaded; any other wheels produced along the way (e.g. dependencies) are discarded.
- Releases are shared per `(package, version, graalpy id)` and tagged `<package>-<version>-<graalpy id>`. The first platform to finish creates the release; the others attach their wheels to it.
- The index (`scripts/generate_index.py`) is regenerated from release assets on every deploy and published with GitHub Pages; nothing generated is committed.
- Builds resolve their own dependencies against this index (`PIP_EXTRA_INDEX_URL`), so wheels published earlier are reused.

## Adding a package

Create `packages/<name>/build.yaml` (see an existing package for an example). Trigger "Periodic build all" or run "Build and release" manually.
