# 🎵 魔法音樂學院 v2.2.0 - 完整內嵌音效版

## ✨ 新功能特色
- **🎶 音效檔完全內嵌**: 所有 99 個音效檔都已內嵌到執行檔中，無需外部音效檔案！
- **🚀 一鍵執行**: 雙擊即可使用，完全獨立運行
- **🔧 編碼問題修正**: 解決了打包腳本的編碼顯示問題
- **📦 單一檔案**: 52.8 MB 包含完整功能和所有音效

## 🎶 內嵌音效清單
- **name 音效**: 95 個檔案 (001.wav ~ 094.wav)
- **family 音效**: 4 個檔案 (01.wav ~ 04.wav)
- **總計**: 99 個完全內嵌的音效檔

## 🚀 使用方法
1. 下載 `魔法音樂學院_完整版.exe`
2. 雙擊執行檔啟動程式
3. 打開瀏覽器訪問 http://localhost:5000
4. 享受魔法學院風格的 Vue.js 界面
5. 使用 MQTT 指令控制播放

## 📡 MQTT 控制指令範例
```bash
# 組合播放 (name + family)
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "001,01"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "050,02"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "094,04"
```

**指令格式說明：**
- 使用 `"name,family"` 格式，例如 `"001,01"`
- 會依序播放 `name/001.wav` → `family/01.wav`
- 如果某個檔案不存在會跳過，繼續播放存在的檔案

## 💻 系統需求
- Windows 10/11 (64-bit)
- 網路連接 (用於 MQTT 通訊)
- 約 100 MB 可用磁碟空間

## 🛠️ 技術資訊
- **Python 版本**: 3.12+
- **打包工具**: PyInstaller
- **音效引擎**: Pygame
- **網頁框架**: Flask + Vue.js
- **檔案大小**: 52.8 MB (包含所有音效)
- **架構**: 多執行緒 (Flask API + MQTT 客戶端 + 音訊播放工作執行緒)

## 🎨 界面特色
- 🏰 魔法學院風格設計
- 🌅 暖色系小學開學風格
- ✨ Vue.js 3 響應式界面
- 🎵 拖放檔案上傳支援
- 📚 魔法音樂圖書館管理

## 🔧 故障排除
如果程式無法啟動：
1. 確認 Windows Defender 未阻擋執行檔
2. 以系統管理員身份執行
3. 檢查防火牆設定 (需開放 5000 埠)

## 📞 支援與回饋
- **GitHub**: https://github.com/pc0808f/pythonmqttplayer
- **Issues**: 如有問題請建立 Issue
- **開發工具**: 使用 [Claude Code](https://claude.ai/code) 協助開發

---
**© 2024 魔法音樂學院專案** | 🤖 Generated with Claude Code