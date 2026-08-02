# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

Single-context repo: one `CONTEXT.md` plus `docs/adr/` at the repo root.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root.
- **`docs/MODEL_NAMING_V1_1.md`** before changing model names or locators.
- **`docs/BUILD.md`** before changing build or conversion behavior.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If these files don't exist, proceed silently. Don't flag their absence or suggest creating them upfront. The `/domain-modeling` skill creates them lazily when terms or decisions actually get resolved.

## File structure

```text
/
|-- CONTEXT.md
|-- docs/
|   `-- adr/
|       |-- 0001-example-decision.md
|       `-- 0002-another-decision.md
`-- src/
```

## Use the glossary's vocabulary

When your output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, either you're inventing language the project doesn't use or there is a real gap to note for `/domain-modeling`.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding it.
