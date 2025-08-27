魔法音樂學院 v2.2.0 - 完整內嵌音效版
=============================================

新功能: 音效檔完全內嵌!
--------------------------
本版本的所有音效檔都已完全內嵌到執行檔中，無需額外的音效檔案!

系統需求
----------
- Windows 10/11 (64-bit)
- 網路連接用於 MQTT 通訊

使用方法
----------
1. 雙擊「魔法音樂學院_完整版.exe」啟動程式
2. 程式會自動啟動並載入內嵌音效檔
3. 打開瀏覽器訪問 http://localhost:5000
4. 使用 MQTT 指令控制播放

內嵌音效清單
--------------
- name 音效: 94 個檔案 001.wav ~ 094.wav
- family 音效: 4 個檔案 01.wav ~ 04.wav
- 總計: 98 個完全內嵌的音效檔

MQTT 控制指令
---------------
# 播放 name 音效
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playname001"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playname050"

# 播放 family 音效  
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playfamily01"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playfamily02"

版本特色
----------
- 完全獨立: 無需外部音效檔案
- 一鍵執行: 雙擊即可使用  
- 內嵌完整: 98個音效檔全部內建
- 網路就緒: 內建 MQTT 客戶端
- 魔法界面: Vue.js 魔法學院風格

技術資訊
-----------
- 檔案大小: 約 55-60 MB 包含所有音效
- Python 版本: 3.12+
- 打包工具: PyInstaller
- 音效引擎: Pygame
- 網頁框架: Flask + Vue.js

故障排除
----------
如果程式無法啟動:
1. 確認 Windows Defender 未阻擋執行檔
2. 以系統管理員身份執行
3. 檢查防火牆設定需開放 5000 埠

支援
------
GitHub: https://github.com/pc0808f/pythonmqttplayer
如有問題請建立 Issue 或聯繫開發者

---
使用 Claude Code 協助開發
https://claude.ai/code

© 2024 魔法音樂學院專案