"""
scripts/diff_contracts.py

Compares two contracts.json files (before/after) and emits a Markdown
summary suitable for a PR comment.

Usage:
    python scripts/diff_contracts.py before.json after.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


COMPARE_FIELDS = [
    'lives', 'tableName', 'feedType', 'workstream', 'sourceSystem',
    'frequency', 'loadType', 'fileName', 'location', 'productOwner',
    'columnCount', 'status',
]


def load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    arr = json.loads(path.read_text(encoding='utf-8'))
    return {c['dataProduct']: c for c in arr}


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: diff_contracts.py before.json after.json', file=sys.stderr)
        return 2

    before = load(Path(sys.argv[1]))
    after = load(Path(sys.argv[2]))

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    common = set(before) & set(after)

    modified: list[tuple[str, list[tuple[str, str, str]]]] = []
    for name in sorted(common):
        diffs = []
        for f in COMPARE_FIELDS:
            b, a = before[name].get(f), after[name].get(f)
            if b != a:
                diffs.append((f, str(b), str(a)))
        # Schema column changes
        b_cols = {c['Column Name'] for c in before[name].get('columns', [])}
        a_cols = {c['Column Name'] for c in after[name].get('columns', [])}
        col_added = sorted(a_cols - b_cols)
        col_removed = sorted(b_cols - a_cols)
        if col_added:
            diffs.append(('schema', '—', f"added: {', '.join(col_added)}"))
        if col_removed:
            diffs.append(('schema', '—', f"removed: {', '.join(col_removed)}"))
        if diffs:
            modified.append((name, diffs))

    if not (added or removed or modified):
        print('_No contract changes detected._')
        return 0

    if added:
        print(f"### ➕ Added ({len(added)})")
        for name in added:
            c = after[name]
            print(f"- **{name}** — `{c.get('lives','?')}` / `{c.get('tableName','?')}` "
                  f"({c.get('columnCount', 0)} cols)")
        print()

    if removed:
        print(f"### ➖ Removed ({len(removed)})")
        for name in removed:
            print(f"- **{name}**")
        print()

    if modified:
        print(f"### ✏️ Modified ({len(modified)})")
        for name, diffs in modified:
            print(f"<details><summary><b>{name}</b> — {len(diffs)} change(s)</summary>\n")
            print('| Field | Before | After |')
            print('|---|---|---|')
            for field, b, a in diffs:
                print(f"| `{field}` | {b} | {a} |")
            print('\n</details>\n')

    return 0


if __name__ == '__main__':
    sys.exit(main())
