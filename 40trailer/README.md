# tw40ch 模組工程

此目錄包含台式 40 呎雙軸貨櫃骨架半拖車的來源、遊戲資源與建置產物。

| 目錄 | 用途 |
|---|---|
| `source/blender/` | Blender 原始檔 |
| `source/textures/` | 貼圖來源檔 |
| `base/` | SCS Project Base Path 與可封裝遊戲資源 |
| `build/` | 轉換後的暫存收集目錄與建置報告 |
| `dist/` | 最終 `.scs` 封裝輸出 |

執行建置：

建置需要開啟正式 Blender source，並讓其 BlenderMCP server 監聽 `127.0.0.1:9877`。腳本會驗證連線中的檔案為 `source/blender/tw40ch_chassis.blend`，由該 GUI 匯出，再轉換、封裝並部署到 ETS2 `mod` 目錄。

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

若 ETS2 不在預設 Steam 安裝位置，可指定遊戲與 mod 目錄：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Ets2Path 'D:\Steam\steamapps\common\Euro Truck Simulator 2' -ModDirectory 'D:\ETS2\mod'
```

建置會刪除目標 `mod` 目錄中名稱符合 `tw40*.scs` 的舊 package，再部署 `tw40ch_0.2.0-dev.scs`。它不會修改 ETS2 profile 或 Mod Manager 啟用順序。

只清理本專案建置產物：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -CleanOnly
```
