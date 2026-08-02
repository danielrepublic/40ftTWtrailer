# Project Context: 40ft Trailer Modification

## Domain Glossary

- **Mesh Object**: A static model component exported as geometry. Its Blender
  Object name and Mesh datablock name must match the canonical semantic name.
- **Model Locator**: An SCS locator whose runtime name can be consumed by the
  ETS2 engine to place another model or hookup. Runtime names are contracts and
  are preserved in v1.1.
- **Collision Locator**: An SCS physics primitive exported to the collision
  asset. The 40ft chassis has one Cylinder `adv_cpling1` and six Box locators
  `cl` through `cl.005`, all in `cables_on`.
- **Shadow Model Locator**: The pair `shadow_x_crn` and `shadow_x_ori` used by
  the game shadow system. Their runtime names are preserved; their positions
  are rebuilt from complete static Mesh bounds using the 20ft reference rule.
  `shadow_x_ori` uses the standard downward orientation, and the chassis also
  contains a downward-facing `eut2.fakeshadow` surface plus an extended shadow
  texture.
- **SCS Part**: A runtime variant contract. The five Part IDs are
  `defaultpart`, `brace_on`, `brace_off`, `cables_on`, and `cables_off`.
- **Runtime Path**: The game resource path `/vehicle/trailer_owned/tw40ch/chassis.*`.

## Current Understanding

- The canonical source is `40trailer/source/blender/tw40ch_chassis.blend`.
- The current version is `1.1`, and the release package is
  `tw40ch_v1.1.scs`.
- The 20ft Blender model is the structural reference for SCS locator types and
  the Shadow Model Locator pair; current 40ft geometry determines positions.
- The world shadow uses `/vehicle/trailer_owned/tw40ch/shadow.tobj` and the
  `shadow_surface` Mesh. The shadow surface is excluded from chassis bounds.
- Vehicle coordinates use `Y > 0` for the kingpin/gooseneck end and `Y < 0`
  for the rear. `X < 0` is vehicle left and `X > 0` is vehicle right.
- Landing gear and leaf springs are visual/static geometry, not collision
  boundaries.
- A successful conversion is not an ETS2 gameplay validation.

## Naming Rule

Mesh names are semantic English `snake_case`, with category first, and the Mesh
datablock matches the Object name. SCS runtime Locator names are not renamed;
their semantic meanings are documented in `docs/MODEL_NAMING_V1_1.md`.

## Maintenance State

- Blender naming and Shadow migration has been applied with a timestamped backup.
- The active scene contains 46 Objects, 19 active Mesh datablocks, and seven Materials.
- Known issue: v1.1 gameplay still does not display the chassis shadow; defer further investigation to the next version.
- The v1.1 build pipeline, source documentation cleanup, and automated/package
  validation are complete; the next work is the deferred shadow investigation.
- Generated Blender mid-format files are temporary build artifacts under
  `40trailer/build/mid-format/tw40ch/`; `40trailer/base/` remains the authored
  runtime source tree.
