"""
scripts/build.py

Assembles the deployable dashboard:
- Reads the index.html template
- Injects data/contracts.json into the page
- Injects the current git tag/SHA as the version label
- Writes everything to dist/

This separates source (HTML + JSON) from artifact (single bundled HTML).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def get_version() -> str:
    """Return the current git tag if HEAD is tagged, else short SHA."""
    try:
        tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--exact-match'],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return tag
    except subprocess.CalledProcessError:
        sha = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return f"dev-{sha}"


def main():
    src_html = Path('index.html').read_text(encoding='utf-8')
    contracts = json.loads(Path('data/contracts.json').read_text(encoding='utf-8'))
    version = get_version()

    # Replace placeholders. The HTML template should contain:
    #   __CONTRACTS_JSON__   (in a <script> tag, replaced by inline JSON)
    #   __VERSION_TAG__      (in the version pill, e.g. "v1.0 · READ")
    out_html = (
        src_html
        .replace('__CONTRACTS_JSON__', json.dumps(contracts))
        .replace('__VERSION_TAG__', f"{version} · READ")
    )

    dist = Path('dist')
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir()

    (dist / 'index.html').write_text(out_html, encoding='utf-8')

    # Copy any static assets if they exist
    for d in ('assets',):
        if Path(d).exists():
            shutil.copytree(d, dist / d)

    # Also publish the raw JSON so external consumers can fetch it
    (dist / 'contracts.json').write_text(
        json.dumps(contracts, indent=2), encoding='utf-8'
    )

    print(f"✓ Built dist/ with version {version} ({len(contracts)} contracts)")


if __name__ == '__main__':
    main()
