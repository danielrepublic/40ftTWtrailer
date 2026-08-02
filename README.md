# 台式 40 呎貨櫃板台半拖車 / Taiwan 40ft Container Chassis

`tw40ch` is an Euro Truck Simulator 2 mod for a Taiwan-style two-axle,
dual-tire 40ft container chassis trailer.

## 使用者 / User

### 功能 / Features

- 可購買與改裝的自有拖車 / Buyable and customizable owned trailer
- Freight Market 與 Cargo Market / Freight Market and Cargo Market support
- 空車裸骨架、接貨後動態 40 呎貨櫃 / Bare chassis when empty, dynamic 40ft container when loaded
- 雙軸雙胎，基準輪胎 315/70 R22.5 / Two axles with dual tires, based on 315/70 R22.5
- 輪胎、輪圈、輪轂、螺帽、尾燈、牌照與車架配件改裝 / Wheel and chassis accessory options
- 可自選素色或金屬色車架 / Custom solid or metallic chassis paint

### 相容性 / Compatibility

- ETS2 `1.60.*`
- Current release: `v1.1` validation build
- SCS Wheels REWORK V2 is optional and provides additional wheel visuals.

### 安裝 / Installation

1. Download `tw40ch_v1.1.scs` from the GitHub Release.
2. Copy it to `Documents/Euro Truck Simulator 2/mod/`.
3. Enable it in Mod Manager.
4. Select `台式 40 呎雙軸` at the trailer dealer.

## 開發者 / Developer

The canonical source is `40trailer/source/blender/tw40ch_chassis.blend`.
Runtime paths remain `/vehicle/trailer_owned/tw40ch/chassis.*`.

### Quick Build

```powershell
.\setup.ps1
.\setup.ps1 -InstallVendorTools
powershell -ExecutionPolicy Bypass -File .\40trailer\build.ps1
```

### Documentation

- [Build Guide](docs/BUILD.md)
- [Model Naming v1.1](docs/MODEL_NAMING_V1_1.md)
- [Agent Workflow](docs/agents/workflow.md)
- [Domain Context](CONTEXT.md)
- [Changelog](CHANGELOG.md)

## License

MIT License. See [LICENSE](LICENSE).
