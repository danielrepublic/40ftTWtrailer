# Issue tracker: GitHub

Issues and specs (you may know a spec as a PRD) for this repo live in GitHub Issues.

## Conventions

- Issues are created and managed via the `gh` CLI
- PRs are not currently used as a request surface for triage

## When a skill says "publish to the issue tracker"

Run `gh issue create` in this repo. The repo must have a GitHub remote configured.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number>` or `gh issue list` as appropriate. The user will normally pass the issue number or title directly.
