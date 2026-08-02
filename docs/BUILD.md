# Build Guide

## Requirements

- Windows PowerShell 5.1
- Python 3.12
- Blender 3.6.23 with SCS Blender Tools 2.4.1
- A canonical Blender GUI with Blender MCP on `127.0.0.1:9876`
- Official Conversion Tools 2.21, compatible with ETS2 1.58+
- SCS Game Archive Extractor 1.55 and ConverterPIX
- ETS2 1.60.1.7 for effect resources and later gameplay validation

The ignored `reference/` tree is for human research and model authoring only. It
is not a build input; normal builds must remain valid when that tree is absent.

Conversion Tools 2.21 is the latest official version listed by the SCS Modding
Wiki for the target game range. Do not replace it with an unverified build.

## First Setup

From the repository root, run PowerShell as administrator because the selected
setup uses a machine-scope winget installation:

```powershell
.\setup.ps1
.\setup.ps1 -InstallVendorTools
```

The setup script creates `.venv`, checks Blender prerequisites, and prepares
the ignored `tools/vendor/` directory. It does not install Blender or its SCS
addon automatically.

Copy `build.config.example.json` to `build.config.json` and set local ETS2 and
Mod directory paths when the defaults do not apply.

## Build

Open the canonical `.blend` in Blender 3.6 and run
`tools/blender/start_blender_mcp.py` through the Blender Text Editor. Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\40trailer\build.ps1
```

Optional overrides remain compatible with the previous entry point:

```powershell
powershell -ExecutionPolicy Bypass -File .\40trailer\build.ps1 `
  -Ets2Path "D:\Steam\Euro Truck Simulator 2" `
  -ModDirectory "D:\ETS2\mod" `
  -GameLogPath "D:\Documents\Euro Truck Simulator 2\game.log.txt"
```

The output is `40trailer/dist/tw40ch_v1.1.scs` and is copied to the configured
ETS2 Mod directory. Older `tw40*.scs` files in those two managed directories
are removed at the start of each build by design, so a failed build cannot
leave an older package looking like the current build.

## Clean

```powershell
powershell -ExecutionPolicy Bypass -File .\40trailer\build.ps1 -CleanOnly
```

Clean only removes managed generated directories, old package files, and
conversion mounts. It never removes source, documentation, reference assets,
or vendor tools.

## Verification Stages

The build runs, in order:

1. Managed workspace cleanup and stale package removal.
2. VERSION, source metadata, and external input checks.
3. Blender MCP preflight and SCS mid-format export.
4. PIM/PIT/PIC contract checks, including one Cylinder and six Box collision locators.
5. Conversion Tools 2.21 conversion and package staging.
6. ConverterPIX reverse validation and source contract validation.
7. Versioned archive creation, optional game-log validation, and deployment.

Reports are written to the ignored `40trailer/build/` directory. A successful
build is not proof that ETS2 gameplay is correct; wheel, hook, lights, shadow,
landing gear, cargo, and game log behavior still require in-game validation.

Generated Blender mid-format files are collected in
`40trailer/build/mid-format/tw40ch/`. SCS Blender Tools requires a temporary
export inside `40trailer/base/.generated/`; the build copies those files into
the managed build directory and removes the temporary export afterward.
Reusable ETS2 effect definitions are cached in the ignored
`tools/vendor/tool-cache/` directory so repeated builds do not extract the full
game archive again.

## Shared v1.1 Contract

`tools/build/chassis_contract.py` is the shared source for v1.1 runtime
invariants used by the build and validation tools. It covers SCS Parts, runtime
Model and Collision Locator expectations, wheel and loading-area positions,
guardrail slots, and shadow rules. It does not replace the canonical Blender
source or the SII runtime definitions; those remain the authored and runtime
authorities respectively.
