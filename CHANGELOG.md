# Changelog

## Next Version (Pending)

### 中文

- [ ] 修復 ETS2 遊戲內車架陰影未顯示問題。

### English

- [ ] Fix the chassis shadow not appearing in ETS2 gameplay.

## v1.1 (Validation Release)

### 中文

- 依 20 呎授權參考重建 40 呎 Shadow Model Locator 位置。
- 新增 `eut2.fakeshadow` 車架平面、標準 shadow origin 朝向與版本化 extended-shadow texture。
- 保留 ETS2/SCS runtime Locator 名稱，避免輪胎、掛接、燈光、陰影與碰撞契約破壞。
- 將 Mesh Object 與 Mesh datablock 規格化為語意化英文名稱。

### English

- Rebuilt the 40ft Shadow Model Locator placement from the authorized 20ft reference.
- Added the chassis `eut2.fakeshadow` surface, standard shadow-origin orientation,
  and a versioned extended-shadow texture definition.
- Preserved ETS2/SCS runtime Locator names to protect wheel, hookup, light, shadow, and collision contracts.
- Normalized Mesh Objects and Mesh datablocks to semantic English names.

## v1.0 (V2 Stable Baseline)

- Complete V2 chassis rebuild with I-beam rails, cross beams, and running gear.
- Four Hunyuan3D double-eye leaf springs in iron gray `#625B57`.
- Five SCS Parts: `defaultpart`, `brace_on`, `brace_off`, `cables_on`, `cables_off`.
- Seven collision locators: one Cylinder and six Box locators.
- Four wheel locators at X=+/-0.925 with the two-axle layout.
- Tail lights, mudflap, reflective strips, rear bumper, license plates, and chassis accessories.
- Dynamic container behavior and Cargo/Freight Market definitions.
- Conditional DLC-aware tire, rim, hub, and nut package structure.
