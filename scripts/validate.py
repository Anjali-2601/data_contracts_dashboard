"""
scripts/validate.py

Validates data/contracts.json against data/schema.json plus integrity rules
that JSON Schema can't easily express.

Exits with non-zero status on any failure so CI fails the PR.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator


CONTRACTS_PATH = Path('data/contracts.json')
SCHEMA_PATH = Path('data/schema.json')


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> int:
    if not CONTRACTS_PATH.exists():
        print(f"ERROR: {CONTRACTS_PATH} not found", file=sys.stderr)
        return 1
    if not SCHEMA_PATH.exists():
        print(f"ERROR: {SCHEMA_PATH} not found", file=sys.stderr)
        return 1

    contracts = load_json(CONTRACTS_PATH)
    schema = load_json(SCHEMA_PATH)

    # 1. JSON Schema validation
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(contracts), key=lambda e: e.path)
    if schema_errors:
        print("\n✗ JSON Schema violations:\n")
        for err in schema_errors:
            loc = '/'.join(str(p) for p in err.absolute_path) or '(root)'
            print(f"  - [{loc}] {err.message}")
        return 1

    # 2. Integrity rules
    failures: list[str] = []

    # 2a. No duplicate dataProduct names
    name_counts = Counter(c['dataProduct'] for c in contracts)
    dupes = {n: count for n, count in name_counts.items() if count > 1}
    if dupes:
        failures.append(f"Duplicate dataProduct names: {dupes}")

    # 2b. No duplicate numPrefix values
    prefix_counts = Counter(c.get('numPrefix') for c in contracts if c.get('numPrefix'))
    dupe_prefixes = {n: count for n, count in prefix_counts.items() if count > 1}
    if dupe_prefixes:
        failures.append(f"Duplicate numPrefix values: {dupe_prefixes}")

    # 2c. Schema columns should equal columnCount
    for c in contracts:
        if len(c.get('columns', [])) != c.get('columnCount', -1):
            failures.append(
                f"{c['dataProduct']}: columnCount={c['columnCount']} but "
                f"len(columns)={len(c.get('columns', []))}"
            )

    # 2d. Every contract has either a fileName or a tableName
    for c in contracts:
        if not c.get('fileName') and not c.get('tableName'):
            failures.append(f"{c['dataProduct']}: missing both fileName and tableName")

    if failures:
        print("\n✗ Integrity check failures:\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    # Success summary
    print(f"✓ {len(contracts)} contracts validated successfully")
    print(f"  Schema errors: 0")
    print(f"  Integrity errors: 0")
    print(f"  Total schema columns: {sum(c['columnCount'] for c in contracts)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
