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

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

只清理本專案建置產物：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -CleanOnly
```
