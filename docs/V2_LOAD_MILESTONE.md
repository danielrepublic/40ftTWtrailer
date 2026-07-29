# V2 Load Milestone

## Scope

This milestone proves that the V2 Taiwan 40 ft skeletal trailer can be built reproducibly, loaded by ETS2, purchased, configured, and attached. It is not a release-completion claim.

## Build Contract

- Canonical editable source: `40trailer/source/blender/tw40ch_chassis.blend`.
- The source must be open in Blender GUI with BlenderMCP at `127.0.0.1:9877`.
- `40trailer/build.ps1` verifies that MCP is connected to the canonical source, performs a read-only export, runs Conversion Tools, validates the V2 model contract, packages `tw40ch_0.2.0-dev.scs`, and deploys it to ETS2's `mod` directory.
- The build bootstraps ignored official effect definitions from the locally installed ETS2 archives into `40trailer/build/tool-cache/`; official game assets are never committed or packaged.
- Build success requires zero Blender MCP/export and Conversion Tools warnings or errors.
- SCS Tools may emit `Warning: 1 x Draw window and swap: <milliseconds>` during GUI redraw. This is a variable UI timing measurement, not an SCS diagnostic, and does not appear in its `WARNING SUMMARY`; the build rejects all formal `WARNING -` and `ERROR -` diagnostics.

## Static Contract

- PIM, PIT, and PIC each declare exactly: `defaultpart`, `brace_on`, `brace_off`, `cables_on`, `cables_off`.
- Collision is seven `defaultpart` locators: one cylinder and six boxes.
- PIT contains `eut2.truckpaint`, `eut2.dif.spec`, and the base-game `vehicle_reflection` resource; it must not fall back to a default/empty effect.
- Converted `chassis.pmd`, `chassis.pmg`, and `chassis.pmc` must be present in the package.
- Each build writes an ignored package-content manifest with entry hashes. Repeating a build with identical formal inputs must reproduce that manifest exactly.

## Wheel Rework Behavior

- The package is standalone and does not require Wheel Rework.
- No WR-only 315/60 tire definition is included.
- If Steam Workshop `SCS wheels REWORK` (ID `3015167743`) is enabled above the base game, its replacement assets at shared SCS disc, hub, and nut paths naturally apply to the trailer.
- Without WR, the same trailer resolves those paths from ETS2 base assets.

## Test Matrix

| Configuration | Required result |
|---|---|
| Core only: `tw40ch_0.2.0-dev.scs` | Dealer/configurator can select every brace and cable variant; trailer can be purchased and attached; no tw40-related `ERROR` in the fresh game log. |
| Core plus Workshop WR ID `3015167743` | Same purchase, variant, and attachment checks; shared wheel assets display through WR; no tw40-related `ERROR` in the fresh game log. |

## Version Evidence

- Support target: ETS2 `1.60.*`.
- Verified versions: pending the test matrix.
- Local test candidate: ETS2 `1.60.1.7`, Steam build `23966373`.

## Dealer Geometry Baseline

- The V2 canonical bare chassis passed a Core-only Dealer visual check on 2026-07-29.
- The accepted package, root cause, runtime evidence, and remaining scope are recorded in `docs/V2_DEALER_GEOMETRY_MILESTONE.md`.
