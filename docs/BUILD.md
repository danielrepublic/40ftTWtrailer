# 建置與封裝

## 固定識別

| 項目 | 值 |
|---|---|
| Mod ID / SII namespace | `tw40ch` |
| SCS Project Base Path | `40trailer/base/` |
| Conversion Tools | `tools/conversion_tools_2_21/` |
| Conversion mount | `tools/conversion_tools_2_21/tw40ch/` |
| Converted cache | `tools/conversion_tools_2_21/rsrc/tw40ch/@cache/` |
| 收集目錄 | `40trailer/build/staging/` |
| 封裝輸出 | `40trailer/dist/tw40ch_0_1_0_dev.scs` |

## 建置命令

從 `40trailer/` 執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

流程依序執行：

1. 僅清理本專案受控的舊建置產物。
2. 將 `base/` 複製到 Conversion Tools 的 `tw40ch` 暫存 mount。
3. 執行 Conversion Tools 2.21。
4. 從 `rsrc/tw40ch/@cache/` 收集轉換結果至 `staging/base/`。
5. 將 metadata 留在套件根目錄，並將 DLC wrapper 分配至 `dlc_goodyear/`、`dlc_michelin/`、`dlc_rims/`。
6. 驗證條件式檔案沒有殘留於 `base/`，根目錄也沒有散落遊戲內容。
7. 使用 deflate ZIP 建立 `.scs`。
8. 將結束代碼、錯誤數、時間與套件大小寫入 `build/build_report.txt`。

## 條件式 DLC 結構

ETS2 1.48+ 會依玩家持有的 DLC 自動掛載對應區段：

```text
manifest.sii
mod_description.txt
mod_description.zh_tw.txt
base/
dlc_goodyear/
dlc_michelin/
dlc_rims/
```

- `base/`：拖車本體、SCS 原版雙胎與原版輪端 wrapper。
- `dlc_goodyear/`：2 個 Goodyear 雙胎 wrapper。
- `dlc_michelin/`：10 個 Michelin 雙胎 wrapper。
- `dlc_rims/`：6 個輪圈、2 個輪轂、6 個螺帽 wrapper。
- `manifest.sii` 不宣告硬性 `dlc_dependencies[]`；缺少 DLC 時只略過該區段。

## 安全清理

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -CleanOnly
```

腳本只會清理：

- `40trailer/build/`
- `40trailer/dist/tw40ch_0_1_0_dev.scs`
- `tools/conversion_tools_2_21/tw40ch/`
- `tools/conversion_tools_2_21/rsrc/tw40ch/`

每個清理路徑都會先確認位於預期的受控根目錄下。

## 不封裝內容

- `source/` 下的 Blender 與貼圖來源檔。
- `build/`、`dist/` 與 Conversion Tools 暫存資料。
- `.blend1`、`.blend2`、`.psd`、`.kra`、`.xcf`、`.tmp`、`.bak`、`.log`。
- 開發用 `.md`、`.ps1`、`.py` 與點號開頭檔案。
- 擷取出的原版遊戲資料。

## 日誌檢查

Conversion Tools 日誌會收集至：

```text
40trailer/build/mass_convert.log
```

若已有隔離測試產生的 `game.log.txt`，可重新建置並一併計數：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -GameLogPath "<path>\game.log.txt"
```

報告中的 `mod_error_count` 只計算同時包含 `<ERROR>` 與 `tw40ch` 的行；仍應人工檢視前後文，避免漏掉未直接帶模組 ID 的關聯錯誤。

提供 `-GameLogPath` 時，腳本也會將該日誌保存至 `40trailer/build/game.log.txt`。

## 隔離遊戲驗證

測試使用獨立 `-homedir`，避免修改正式玩家設定檔：

```text
eurotrucks2.exe -homedir <test_root> -nointro -nosplash -unlimitedlog -noworkshop -force_mods
```

`-homedir` 會在 `<test_root>/Euro Truck Simulator 2/` 建立遊戲使用者目錄，測試套件須放在其 `mod/` 子目錄。`-noworkshop` 可避免 `-force_mods` 同時啟用已訂閱的 Workshop 模組。

2026-07-16 最小模組驗證結果：

```text
[mods] Active 1 mods (local: 1, workshop: 0)
[mods] Active local mod tw40ch_0_1_0_dev
[mod_package_manager] Mod "台式 40 呎貨櫃版台" has been mounted.
```

結果為 `game_error_count=0`、`mod_error_count=0`。唯一警告是輸入裝置偵測耗時，與本模組無關。
