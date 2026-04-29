"""
scripts/audit_stale.py

Scans data/contracts.json for contracts that haven't been verified in 6+ months
and emits a Markdown report.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


STALE_DAYS = 180


def parse_date(s: str):
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    return None


def main():
    contracts = json.loads(Path('data/contracts.json').read_text(encoding='utf-8'))
    threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=STALE_DAYS)

    stale = []
    missing = []
    for c in contracts:
        d = parse_date(c.get('lastVerified', ''))
        if d is None:
            missing.append(c)
        elif d < threshold:
            stale.append((c, d))

    print(f"# 📅 Weekly Inventory Audit\n")
    print(f"_Run: {datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M UTC')}_\n")
    print(f"- Total contracts: **{len(contracts)}**")
    print(f"- Stale (>{STALE_DAYS} days): **{len(stale)}**")
    print(f"- Missing `lastVerified`: **{len(missing)}**\n")

    if stale:
        print(f"## Stale contracts (last verified > {STALE_DAYS} days ago)\n")
        print('| Data Product | Last Verified | Days Stale | Owner |')
        print('|---|---|---|---|')
        for c, d in sorted(stale, key=lambda x: x[1]):
            days = (datetime.now(timezone.utc).replace(tzinfo=None) - d).days
            owner = c.get('productOwner') or '—'
            print(f"| {c['dataProduct']} | {d.strftime('%Y-%m-%d')} | {days} | {owner} |")
        print()

    if missing:
        print(f"## Contracts without `lastVerified` date\n")
        for c in missing:
            owner = c.get('productOwner') or '—'
            print(f"- **{c['dataProduct']}** — owner: {owner}")
        print()

    if not stale and not missing:
        print("✅ All contracts are fresh. Nothing to action this week.")


if __name__ == '__main__':
    main()
