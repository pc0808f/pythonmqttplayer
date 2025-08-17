# 🎵 魔法音樂學院 - Python MQTT 音檔播放器

一個具有暖色系小學開學風格和魔法學院感覺的 MQTT 音檔播放控制器，使用 Vue.js 前端和 Flask API 後端。

![魔法音樂學院](https://img.shields.io/badge/魔法音樂學院-Vue.js+Flask-orange)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ 功能特色

- 🎵 **音檔上傳與管理**：支援拖放上傳 WAV 音檔
- 📚 **魔法音樂圖書館**：美麗的檔案列表顯示界面
- 🔊 **MQTT 遠程控制**：透過 MQTT 指令遠程播放音檔
- 🎨 **魔法學院風格界面**：暖色系設計配合動畫效果
- ⚡ **即時監控**：播放狀態與 MQTT 指令即時顯示
- 🔄 **播放佇列管理**：支援播放佇列與只播放一次模式

## 🚀 快速安裝

### 方法一：下載預編譯執行檔（推薦）

1. 前往 [Releases](https://github.com/yourusername/pythonmqttplayer/releases) 頁面
2. 下載最新版本的 `PythonMQTTPlayer-vX.X.X.zip`
3. 解壓縮到任意資料夾
4. 執行 `PythonMQTTPlayer.exe`
5. 開啟瀏覽器訪問 http://localhost:5000

### 方法二：從原始碼安裝

#### 系統需求

- Python 3.8 或更高版本
- Windows、macOS 或 Linux

#### 安裝步驟

1. **克隆專案**
   ```bash
   git clone https://github.com/yourusername/pythonmqttplayer.git
   cd pythonmqttplayer
   ```

2. **安裝相依性套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **啟動應用程式**
   ```bash
   python app.py
   ```

4. **開啟瀏覽器**
   
   訪問 http://localhost:5000 即可使用魔法音樂學院界面

## 🎯 使用說明

### 基本操作

1. **上傳音檔**：
   - 拖放 WAV 檔案到上傳區域
   - 或點擊「選擇檔案」按鈕

2. **MQTT 遠程播放**：
   - 應用程式會自動連接到 `broker.MQTTGO.io:1883`
   - 訂閱主題：`puffin-test`
   - 發送指令格式：`playXXX`（例如：`play001` 播放 `001.wav`）

3. **監控功能**：
   - 即時播放狀態顯示
   - MQTT 指令歷史記錄
   - 播放佇列管理

### MQTT 指令範例

```bash
# 播放 001.wav 檔案
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "play001"

# 播放 002.wav 檔案
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "play002"
```

## 🛠️ 開發者資訊

### 核心架構

應用程式採用多執行緒架構，包含四個主要組件：

1. **Flask API 伺服器**（主執行緒）：提供 RESTful API 和檔案上傳功能
2. **Vue.js 前端**（瀏覽器）：提供魔法學院風格的使用者介面
3. **MQTT 客戶端**（背景執行緒）：訂閱 "puffin-test" 主題，接收播放指令
4. **音訊播放工作執行緒**（背景守護執行緒）：處理音訊播放佇列

### 技術棧

**後端**：
- Flask - Web 框架
- paho-mqtt - MQTT 客戶端
- pygame - 音訊播放引擎
- flask-cors - 跨域支援

**前端**：
- Vue.js 3 - 響應式前端框架
- Tailwind CSS - 樣式框架
- Font Awesome - 圖示庫

### 專案結構

```
pythonmqttplayer/
├── app.py              # 主應用程式檔案
├── index.html          # Vue.js 前端界面
├── requirements.txt    # Python 相依性套件
├── build.py           # 打包腳本
├── build.bat          # Windows 打包批次檔
├── PythonMQTTPlayer.spec # PyInstaller 配置
└── uploads/           # 音訊檔案儲存目錄
```

### API 端點

- `GET /` - Vue.js 魔法學院主界面
- `GET /api/files` - 取得已上傳檔案列表
- `POST /api/upload` - 上傳音檔檔案
- `GET /api/status` - 取得播放狀態
- `POST /api/play-once-mode` - 設定只播放一次模式

### 從原始碼建立執行檔

如果您想要自己建立執行檔：

```bash
# 安裝相依性套件
pip install -r requirements.txt

# Windows 使用者
build.bat

# 或直接使用 Python 腳本
python build.py
```

建立完成後，執行檔會在 `dist/` 資料夾中。

## 🔧 配置說明

### MQTT 設定

預設 MQTT 配置：
- **Broker**: broker.MQTTGO.io
- **埠號**: 1883
- **主題**: puffin-test
- **Client ID**: 使用本機 IP 位址

### 檔案限制

- 支援格式：WAV 音檔
- 檔案大小：無特別限制
- 儲存位置：`uploads/` 資料夾

## 🐛 疑難排解

### 常見問題

**Q: 執行檔無法啟動**
A: 確保 Windows Defender 或防毒軟體沒有阻擋執行檔

**Q: 無法播放音檔**
A: 確認系統已安裝音訊輸出設備，並且音檔為有效的 WAV 格式

**Q: MQTT 連線失敗**
A: 檢查網路連線，確保能連接到 broker.MQTTGO.io

**Q: 網頁無法開啟**
A: 確認 5000 埠沒有被其他程式佔用

### 日誌查看

執行檔會在控制台顯示詳細的運行日誌，包括：
- MQTT 連線狀態
- 音檔播放狀態
- 錯誤訊息

## 📄 授權條款

本專案採用 MIT 授權條款。詳情請見 [LICENSE](LICENSE) 檔案。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📞 支援與聯絡

如果您遇到問題或有建議，請：
- 提交 [Issue](https://github.com/yourusername/pythonmqttplayer/issues)
- 發送 Email：your.email@example.com

---

<div align="center">
  <p>✨ 用魔法讓音樂更精彩！✨</p>
  <p>Made with ❤️ by 魔法音樂學院開發團隊</p>
</div>