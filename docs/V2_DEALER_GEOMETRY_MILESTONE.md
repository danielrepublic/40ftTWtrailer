# V2 Dealer Geometry Milestone

## Status

The canonical V2 bare chassis renders as a full three-dimensional model in the ETS2 Trailer Dealer. This resolves the longitudinal flattening defect and establishes the visual baseline for subsequent detail work.

## Accepted Build

| Item | Value |
|---|---|
| Date | 2026-07-29 |
| Package | `40trailer/dist/tw40ch_0.2.0-dev.scs` |
| Package SHA-256 | `72A5279E7E77C4BDF5E0C6B00AE681927E4FB3D1697EBAC4293220444D62ED49` |
| Package size | 50,283,655 bytes |
| Canonical source | `40trailer/source/blender/tw40ch_chassis.blend` |
| Canonical dimensions | 12.393 m x 2.547 m x 1.468 m |
| Core-only status | One local `tw40ch_0.2.0-dev` mod active; Dealer visual accepted |
| Dealer model | Bare chassis only; no owned-body cargo model |
| Conversion Tools | Exit code 0; no warnings or errors |

## Root Cause And Repair

SCS Blender Tools exported each `_UV0` PIM stream with the invalid alias `"_TEXCOORD-1"`. Conversion Tools then omitted the UV semantic from the PMG vertex layout. ETS2 logged `tex_coord_0 / buffer_layout=42` input-layout failures and rendered the complex canonical chassis incorrectly.

`tools/export_v2_chassis.py` now normalizes each exported `_UVn` alias to `"_TEXCOORDn"` before Conversion Tools runs. The accepted build was reverse-decoded from its staged PMG and contains nine converted pieces, each with `_POSITION`, `_NORMAL`, `_UV0`, and `_RGBA`; all nine UV streams retain `"_TEXCOORD0"` and none have an empty alias list.

## Runtime Evidence

The fresh Core-only `game.log.txt` from 2026-07-29 contains zero `tex_coord_0` or `buffer_layout=42` errors. Its only tw40ch-related line is the normal HashFS pool-lookup warning for the local package. A separate traffic error references the base-game `scs_lowbed` chassis, not `tw40ch`.

## Scope Boundary

This milestone verifies Dealer geometry only. Purchase, configurator variants, attachment, physics, cargo/body behavior, lighting, and the Core-plus-Workshop-Wheel-Rework matrix remain unverified and must not be inferred from this result.
