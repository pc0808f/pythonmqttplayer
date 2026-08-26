主要語言為繁體中文

# CLAUDE.md

此檔案為 Claude Code (claude.ai/code) 在此專案中工作時提供指導。

## 專案概述

🎵 **魔法音樂學院** - 一個具有暖色系小學開學風格和魔法學院感覺的 MQTT 音檔播放控制器，使用 Vue.js 前端和 Flask API 後端。

## 核心架構

應用程式採用多執行緒架構，包含四個主要組件：

1. **Flask API 伺服器** (主執行緒)：提供 RESTful API 和檔案上傳功能
2. **Vue.js 前端** (瀏覽器)：提供魔法學院風格的使用者介面
3. **MQTT 客戶端** (背景執行緒)：訂閱 "puffin-test" 主題，接收播放指令
4. **音訊播放工作執行緒** (背景守護執行緒)：處理音訊播放佇列

### 關鍵組件說明

- **音訊佇列系統**：使用 `queue.Queue()` 實現執行緒安全的播放佇列
- **MQTT 訊息格式**：接收 `name,family` 格式的訊息（如 "001,01"），依序播放 `name/001.wav` → `family/01.wav`
- **檔案儲存**：音訊檔案（.wav）儲存在 `uploads/name/`（姓名）與 `uploads/family/`（家族）兩個子目錄中
- **MQTT Broker**：連接到 "broker.MQTTGO.io:1883"

## 執行指令

### 啟動應用程式

```bash
python app.py
```

應用程式會：

- 在 5000 埠啟動 Flask web 伺服器 (http://0.0.0.0:5000)
- 自動建立 `uploads/` 目錄（如果不存在）
- 啟動音訊播放工作執行緒
- 連接到 MQTT broker 並訂閱 "puffin-test" 主題

### 相依性套件

應用程式需要以下 Python 套件：

- Flask: Web 框架和 API 伺服器
- flask-cors: 跨域資源共享支援 (支援 Vue.js 前端)
- paho-mqtt: MQTT 客戶端函式庫
- werkzeug: Flask 相依性套件（檔案上傳安全性）
- pygame: 音訊播放引擎

可以透過以下指令安裝相依性套件：

```bash
pip install -r requirements.txt
# 或手動安裝：
pip install flask flask-cors paho-mqtt werkzeug pygame
```

### 打包成執行檔（內嵌音效版）

使用 `build.py` 透過 PyInstaller 打包成單一執行檔，會將 `index.html`、`uploads/name/`、`uploads/family/` 內嵌其中：

```bash
python build.py
```

- 產物位於 `dist/魔法音樂學院_完整版.exe`
- 音效資料夾內容會即時抓取，更新音檔後重跑 `build.py` 即可產生新版
- 執行時 `app.py` 的 `get_resource_path()` 會從 PyInstaller 的 `sys._MEIPASS` 臨時目錄讀取內嵌資源

> 轉檔提醒：程式只支援 `.wav`。若音效來源為 `.m4a` 等格式，需先用 ffmpeg 轉檔（例如 `ffmpeg -i in.m4a -ar 44100 -ac 2 -c:a pcm_s16le out.wav`）再放入 `uploads/`。

## 檔案結構

```
pythonmqttplayer/
├── app.py              # 主應用程式檔案 (Flask API 後端)
├── index.html          # Vue.js 魔法學院風格前端 (主界面)
├── build.py            # PyInstaller 打包腳本（產出內嵌音效的單一執行檔）
├── requirements.txt    # Python 相依套件清單
└── uploads/            # 音訊檔案儲存目錄（執行時建立）
    ├── name/           # 姓名音效 (001.wav ~ NNN.wav)
    └── family/         # 家族音效 (01.wav ~ 04.wav)
```

> 注意：`uploads/name/` 與 `uploads/family/` 已在 `.gitignore` 中排除，音效檔不進版控（本機執行時使用磁碟上的檔案）。

## 前端介面

### Vue.js 魔法學院界面

- **訪問路徑**: `http://localhost:5000/` (主頁面)
- **風格**: 暖色系小學開學風格 + 魔法學院元素
- **功能**: 
  - 🎵 音檔上傳 (拖放支援)
  - 📚 魔法音樂圖書館 (檔案列表)
  - ✨ 動畫效果和魔法裝飾
  - 🔄 即時檔案列表更新

### API 端點

- `GET /api/files` - 取得已上傳檔案列表
- `POST /api/upload` - 上傳音檔檔案
- `GET /` - Vue.js 魔法學院主界面

## 開發注意事項

### MQTT 訊息格式

- 主題：`puffin-test`
- 訊息格式：`name,family`（以逗號分隔，對應 `name/name.wav` 與 `family/family.wav`）
- 範例：發送 "001,01" 依序播放 `uploads/name/001.wav` → `uploads/family/01.wav`
- 家族代號對應：`01`=天空、`02`=海洋、`03`=樹居、`04`=大地
- 若某個檔案不存在會自動跳過，只播放存在的檔案

### 安全配置

- 使用 `secure_filename()` 處理檔案上傳安全性
- 限制上傳檔案類型為 .wav 格式
- Flask SECRET_KEY 需要在正式環境中更改

### 偵錯模式

應用程式預設以 debug=True 執行，但使用 use_reloader=False 避免服務重複啟動的問題。

### 前端技術

- **Vue.js 3**: 響應式前端框架
- **Tailwind CSS**: 快速樣式設計
- **Font Awesome**: 圖示庫
- **Google Fonts**: Noto Sans TC + Comic Neue 字體
- **暖色系配色**: 橙色、黃色、粉紅色為主調
- **魔法元素**: 星星、魔法杖、城堡等裝飾

### 客戶端 ID 產生

MQTT 客戶端 ID 使用本機 IP 位址，如果無法取得則使用預設值 "default_client_id_12345"。
