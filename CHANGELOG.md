# Changelog

## Next Version / 下一版本 (Pending)

- [ ] 修復 ETS2 遊戲內車架陰影未顯示問題。 / Fix the chassis shadow not appearing in ETS2 gameplay.

## v1.1 (Validation Release / 驗證版)

- 依 20 呎授權參考重建 40 呎 Shadow Model Locator 位置。 / Rebuilt the 40ft Shadow Model Locator placement from the authorized 20ft reference.
- 新增 `eut2.fakeshadow` 車架平面、標準 shadow origin 朝向與版本化 extended-shadow texture。 / Added the chassis `eut2.fakeshadow` surface, standard shadow-origin orientation, and a versioned extended-shadow texture definition.
- 保留 ETS2/SCS runtime Locator 名稱，避免輪胎、掛接、燈光、陰影與碰撞契約破壞。 / Preserved ETS2/SCS runtime Locator names to protect wheel, hookup, light, shadow, and collision contracts.
- 將 Mesh Object 與 Mesh datablock 規格化為語意化英文名稱。 / Normalized Mesh Objects and Mesh datablocks to semantic English names.
