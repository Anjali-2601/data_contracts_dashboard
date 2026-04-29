# IBU Omnichannel Data Inventory — Contributor Guide

This repo is the source of truth for the IBU Omnichannel data contracts dashboard
deployed at `https://<org>.github.io/<repo>/`.

## Repo layout

```
.
├── index.html                     # Dashboard template (placeholders for JSON + version)
├── assets/                        # CSS / JS / images
├── data/
│   ├── contracts.json             # Generated — DO NOT edit by hand
│   └── schema.json                # Validation schema
├── source/
│   └── Current_State_Data_Inventory.xlsb   # SOURCE OF TRUTH — edit this
├── scripts/
│   ├── extract.py                 # Reads Excel → writes contracts.json
│   ├── validate.py                # JSON-Schema + integrity checks
│   ├── diff_contracts.py          # Generates PR change summary
│   ├── audit_stale.py             # Weekly staleness audit
│   ├── build.py                   # Bundles dashboard for deploy
│   └── requirements.txt
├── .github/
│   ├── workflows/
│   │   ├── pr-extract-and-validate.yml
│   │   ├── deploy.yml
│   │   └── weekly-audit.yml
│   ├── CODEOWNERS
│   └── pull_request_template.md
└── CHANGELOG.md
```

## How to make a change (the only workflow)

1. **Branch** from `main` using a descriptive name:
   - `omnichannel/add-medscape-feed`
   - `latam/update-lilly360-schema`
   - `payer/retire-formulary-positioning`
2. **Edit `source/Current_State_Data_Inventory.xlsb`** in Excel — this is the source of truth.
3. **Commit and push** the workbook. *Don't touch `data/contracts.json`* — the bot will regenerate it.
4. **Open a PR.** Within ~3 minutes, the `pr-extract-and-validate` workflow will:
   - Re-run `extract.py` against your Excel changes
   - Push the regenerated `data/contracts.json` to your PR branch
   - Validate the JSON against `schema.json`
   - Post a Markdown comment on the PR showing exactly which contracts were added / removed / modified
5. **Review the bot's diff comment** to confirm the JSON change matches what you intended.
6. **Get team approvals.** CODEOWNERS auto-requests reviewers based on the paths you touched. The Excel and JSON files require approval from all three teams; everything else from `data-platform-leads`.
7. **Merge.** GitHub Pages auto-deploys within 2–3 minutes.

### Why is the Excel the source and not the JSON?

Three reasons:
- Stakeholders already maintain the inventory in Excel; we don't break their workflow.
- Schema definitions live alongside the contract metadata in the same sheet, so editing them together keeps consistency.
- The bot regenerating JSON enforces a **single, deterministic transformation** — no team can hand-edit JSON and drift from Excel.

## Versioning

We use **semantic versioning** adapted for data inventories:

| Bump | When |
|------|------|
| **Major** (e.g. 1.x → 2.0.0) | Breaking schema changes — renamed/dropped JSON fields, restructured layout, removed required attributes |
| **Minor** (e.g. 1.2.x → 1.3.0) | New contract added, new optional field added, new workstream/category |
| **Patch** (e.g. 1.2.3 → 1.2.4) | Corrected table name, fixed typo, updated frequency, refreshed `lastVerified` dates |

After merging, tag the release:
```bash
git checkout main && git pull
git tag v1.3.0
git push origin v1.3.0
```
The `deploy.yml` workflow reads the tag via `git describe --tags` and bakes it into the dashboard's version pill (`v1.3.0 · READ`).

## CHANGELOG.md

Every user-visible change must be recorded. Format:
```
## [1.3.0] - 2026-04-30
### Added
- 7 LATAM data products (#26-#32)
### Changed
- Header text revised
### Deprecated
- (none)
### Removed
- (none)
### Fixed
- (none)
```

## Branch protection (configure in GitHub settings)

Recommended settings on `main`:
- Require pull request reviews before merging — **2 approvals**, dismiss stale on new commits
- Require review from CODEOWNERS
- Require status checks: `extract-and-validate`
- Require branches to be up to date before merging
- Restrict who can push to matching branches: leads only

## Working with the Excel file in 3 teams

The `.xlsb` file is binary — Git can store it but **conflicts cannot be auto-merged**.

- **Coordinate large structural changes** in your team channel before branching (e.g., "I'm refactoring the Hierarchy sheet on Tuesday").
- **Keep PRs short-lived.** The longer a branch lives, the more likely the Excel diverges from `main`. Merge within 1–2 working days.
- **For unavoidable conflicts:** the team that branched second re-applies their changes on top of the latest `main` Excel and force-pushes. The bot will regenerate JSON automatically.
- **Per-sheet ownership** is informally encoded in CODEOWNERS — Omnichannel owns hierarchy/CAP/EDB sheets; LATAM owns the `Latam - *` sheets; Payer owns `Formulary *` sheets. Teams shouldn't edit each other's sheets without coordinating.

## Local dev

```bash
pip install -r scripts/requirements.txt

# Regenerate contracts.json from your local Excel changes
python scripts/extract.py

# Validate
python scripts/validate.py

# See what would change vs main
git stash && git checkout main -- data/contracts.json && cp data/contracts.json /tmp/before.json
git stash pop && python scripts/extract.py
python scripts/diff_contracts.py /tmp/before.json data/contracts.json

# Build the deployable dashboard
python scripts/build.py
# Open dist/index.html
```
