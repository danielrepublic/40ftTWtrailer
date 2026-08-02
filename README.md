# 台式 40 呎貨櫃板台半拖車 / Taiwan 40ft Container Chassis

- 台式雙軸雙胎 40 呎貨櫃板台半拖車模組 / `tw40ch` is a Euro Truck Simulator 2 mod for a Taiwan-style two-axle, dual-tire 40ft container chassis trailer

## 使用者 / User

### 功能 / Features

- 可購買與改裝的自有拖車 / Buyable and customizable owned trailer
- Freight Market 與 Cargo Market / Freight Market and Cargo Market support
- 空車裸骨架、接貨後動態 40 呎貨櫃 / Bare chassis when empty, dynamic 40ft container when loaded
- 雙軸雙胎，基準輪胎 315/70 R22.5 / Two axles with dual tires, based on 315/70 R22.5
- 輪胎、輪圈、輪轂、螺帽、尾燈、牌照與車架配件改裝，部分輪胎種類尚未提供 / Wheel and chassis accessory options; some trailer tire variants are not yet available
- 可自選素色或金屬色車架 / Custom solid or metallic chassis paint

### 已知限制 / Known Limitations

- 拖車部分輪胎種類缺少，輪胎選項目前尚未完整 / Some trailer tire variants are missing; the tire option set is currently incomplete
- ETS2 實際遊戲中的車架 shadow 尚未顯示 / The chassis shadow is not yet visible in live ETS2 gameplay

### 相容性 / Compatibility

- ETS2 `1.60.*`
- 目前版本：`v1.1` 驗證版 / Current release: `v1.1` validation build
- SCS Wheels REWORK V2 為選用模組，可提供額外輪圈外觀 / SCS Wheels REWORK V2 is optional and provides additional wheel visuals

### 安裝 / Installation

1. 從 GitHub Release 下載 `tw40ch_v1.1.scs` / Download `tw40ch_v1.1.scs` from the GitHub Release
2. 複製到 `Documents/Euro Truck Simulator 2/mod/` / Copy it to `Documents/Euro Truck Simulator 2/mod/`
3. 在 Mod Manager 啟用模組 / Enable it in Mod Manager
4. 在車商選擇 `台式 40 呎雙軸` / Select `台式 40 呎雙軸` at the trailer dealer

## 開發者 / Developer

- Canonical source：`40trailer/source/blender/tw40ch_chassis.blend` / Canonical source: `40trailer/source/blender/tw40ch_chassis.blend`
- Runtime 路徑維持 `/vehicle/trailer_owned/tw40ch/chassis.*` / Runtime paths remain `/vehicle/trailer_owned/tw40ch/chassis.*`

### 快速建置 / Quick Build

```powershell
.\setup.ps1
.\setup.ps1 -InstallVendorTools
powershell -ExecutionPolicy Bypass -File .\40trailer\build.ps1
```

### 文件 / Documentation

- [建置指南 / Build Guide](docs/BUILD.md)
- [模型命名 v1.1 / Model Naming v1.1](docs/MODEL_NAMING_V1_1.md)
- [Agent 工作流程 / Agent Workflow](docs/agents/workflow.md)
- [領域背景 / Domain Context](CONTEXT.md)
- [變更記錄 / Changelog](CHANGELOG.md)

## 授權 / License

MIT License。請參閱 [LICENSE](LICENSE) / See [LICENSE](LICENSE).
