# Changelog

## Next Version (Pending)

### 中文

- [ ] 修復 ETS2 遊戲內車架陰影未顯示問題。v1.1 的匯出、轉換與封裝驗證已通過，但實際遊戲顯示仍未確認成功，延後至下一版本重新調查。

### English

- [ ] Fix the chassis shadow not appearing in ETS2 gameplay. The v1.1 export,
  conversion, and packaging checks pass, but the in-game result remains
  unresolved and is deferred to the next version.

## v1.1 (Validation Release)

### 中文

- 依 20 呎授權參考重建 40 呎 Shadow Model Locator 位置。
- 新增 `eut2.fakeshadow` 車架平面、標準 shadow origin 朝向與版本化 extended-shadow texture。
- 保留 ETS2/SCS runtime Locator 名稱，避免輪胎、掛接、燈光、陰影與碰撞契約破壞。
- 將 Mesh Object 與 Mesh datablock 規格化為語意化英文名稱。
- 清理無主施工 Mesh datablock 與一次性 V2/V5 修復工具。
- 重寫可重現建置流程：Python 3.12、PowerShell 5.1 入口、結構化報告與單元測試。
- 使用官方 Conversion Tools 2.21、PIM/PIT/PIC contract、reverse validation 與 GitHub Release 流程。

### English

- Rebuilt the 40ft Shadow Model Locator placement from the authorized 20ft reference.
- Added the chassis `eut2.fakeshadow` surface, standard shadow-origin orientation,
  and a versioned extended-shadow texture definition.
- Preserved ETS2/SCS runtime Locator names to protect wheel, hookup, light, shadow, and collision contracts.
- Normalized Mesh Objects and Mesh datablocks to semantic English names.
- Removed unowned construction Mesh datablocks and one-off V2/V5 repair scripts.
- Rebuilt the reproducible pipeline around Python 3.12, a PowerShell 5.1 entry point,
  structured reports, and unit tests.
- Kept official Conversion Tools 2.21 with PIM/PIT/PIC contracts, reverse validation,
  and GitHub Release packaging.

## v1.0 (V2 Stable Baseline)

- Complete V2 chassis rebuild with I-beam rails, cross beams, and running gear.
- Four Hunyuan3D double-eye leaf springs in iron gray `#625B57`.
- Five SCS Parts: `defaultpart`, `brace_on`, `brace_off`, `cables_on`, `cables_off`.
- Seven collision locators: one Cylinder and six Box locators.
- Four wheel locators at X=+/-0.925 with the two-axle layout.
- Tail lights, mudflap, reflective strips, rear bumper, license plates, and chassis accessories.
- Dynamic container behavior and Cargo/Freight Market definitions.
- Conditional DLC-aware tire, rim, hub, and nut package structure.
- Traditional Chinese localization and a reproducible build pipeline.
