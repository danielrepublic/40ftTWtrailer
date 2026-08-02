# Repository Workflow

## Scope

This is a Windows ETS2 mod project. The canonical source is
`40trailer/source/blender/tw40ch_chassis.blend`. The game runtime path remains

## Before editing

- Read `CONTEXT.md`, `docs/MODEL_NAMING_V1_1.md`, and `docs/BUILD.md` for the area being changed.
- Inspect the filesystem, Blender scene, and current scripts before asking the user for facts.
- Ask one focused decision at a time with the recommended answer when a choice is required.
- Do not modify Blender, source, or build files until the user has confirmed the shared understanding.

## Blender rules

- Use Blender MCP on `127.0.0.1:9876` with the canonical Blender GUI.
- Treat SCS runtime Locator names as contracts. Do not rename `wheel_r_*`,
  `hook`, `rlights`, `r_mudflap`, `shadow_x_*`, `adv_cpling1`, `cl*`, or other
  Model Locators without explicit research and game validation.
- Mesh Objects and Mesh datablocks use the same canonical semantic name.
- Run the naming migration tool only against a saved, clean source; it creates
  a timestamped backup before changing anything.

## Build rules

- Run `setup.ps1` once, then `40trailer/build.ps1` for normal builds.
- Do not commit `.venv`, `build.config.json`, vendor tools, references, logs,
  generated SCS assets, or `.scs` files to the source tree.
- A successful conversion is not an ETS2 gameplay validation. State this
  distinction explicitly in reports and handoffs.
- Never revert unrelated dirty worktree changes from another session.

## Verification

- Run Python unit tests before the full build.
- Require Blender preflight, PIM/PIT/PIC contract checks, Conversion Tools,
  reverse validation, source contract validation, and package inventory checks.
- Record failures in `40trailer/build/logs/` and retain the structured report.
