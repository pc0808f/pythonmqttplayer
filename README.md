# 魔法音樂學院 PythonMQTTPlayer

## ⚠️ 大型檔案注意事項

本專案的打包產物 `魔法音樂學院_完整版.exe` 約 **52.8 MB**，已超過 GitHub 建議的單檔 50 MB 上限。

推送時 GitHub 會回傳警告：

```
remote: warning: File PythonMQTTPlayer-EmbeddedAudio-vX.X.X/魔法音樂學院_完整版.exe is 52.79 MB;
        this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: GH001: Large files detected.
```

目前**仍可正常推送**（GitHub 的硬性上限為 100 MB），但每發布一個版本就多存一份 exe，會讓 repo 體積快速膨脹，且 Git 歷史無法輕易縮減。

### 建議做法

1. **改用 GitHub Releases 掛載執行檔**（推薦）
   - 將 `PythonMQTTPlayer-EmbeddedAudio-vX.X.X/` 加入 `.gitignore`
   - 打包後把 exe 上傳到對應版本的 Release 附件
   - 專案內可用 `upload_release.py` 協助上傳

2. **導入 Git LFS**
   ```bash
   git lfs install
   git lfs track "*.exe"
   git add .gitattributes
   ```
   注意：LFS 有免費儲存與流量配額限制。

> 若沿用現況（直接 commit exe），請留意 clone 時間與 repo 容量會持續增加。
