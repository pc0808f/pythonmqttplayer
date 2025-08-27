#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔法音樂學院 - 內嵌音效檔執行檔打包腳本
使用 PyInstaller 打包包含內嵌音效檔的獨立執行檔
"""

import os
import sys
import shutil
import subprocess

def build_embedded_executable():
    """執行打包程序，確保音效檔正確內嵌"""
    print("開始打包魔法音樂學院（內嵌音效版）...")
    
    # 檢查必要檔案和目錄
    required_files = ['app.py', 'index.html']
    required_dirs = ['uploads/name', 'uploads/family']
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"錯誤：找不到必要檔案 {file}")
            return False
    
    for dir in required_dirs:
        if not os.path.exists(dir):
            print(f"錯誤：找不到必要目錄 {dir}")
            return False
    
    # 統計音效檔數量
    name_files = [f for f in os.listdir('uploads/name') if f.endswith('.wav')]
    family_files = [f for f in os.listdir('uploads/family') if f.endswith('.wav')]
    print(f"準備內嵌 {len(name_files)} 個 name 音效檔")
    print(f"準備內嵌 {len(family_files)} 個 family 音效檔")
    
    # 清理舊的 build 和 dist 目錄
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"清理舊的 {dir_name} 目錄")
            shutil.rmtree(dir_name)
    
    # 執行 PyInstaller 使用詳細的 --add-data 參數
    try:
        print("正在執行 PyInstaller（內嵌音效版）...")
        
        # 建構 PyInstaller 命令
        cmd = [
            'pyinstaller',
            '--onefile',  # 單一執行檔
            '--console',  # 顯示控制台（便於除錯）
            '--name=MagicMusicAcademy_Embedded',  # 執行檔名稱
            '--add-data=index.html;.',  # 網頁檔案
            '--clean',  # 清理暫存
            '--noconfirm',  # 不確認覆蓋
        ]
        
        # 加入所有 name 音效檔
        for filename in name_files:
            source_path = f"uploads/name/{filename}"
            cmd.append(f"--add-data={source_path};uploads/name")
        
        # 加入所有 family 音效檔  
        for filename in family_files:
            source_path = f"uploads/family/{filename}"
            cmd.append(f"--add-data={source_path};uploads/family")
        
        # 加入隱含匯入
        hidden_imports = [
            'flask', 'flask_cors', 'paho.mqtt.client', 'pygame', 
            'werkzeug', 'werkzeug.utils', 'pydub'
        ]
        for module in hidden_imports:
            cmd.append(f"--hidden-import={module}")
        
        # 主程式檔案
        cmd.append('app.py')
        
        print(f"執行指令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        
        print("打包成功！")
        exe_path = "dist/MagicMusicAcademy_Embedded.exe"
        print(f"執行檔位置：{exe_path}")
        
        # 檢查檔案大小
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"執行檔大小：{size_mb:.1f} MB")
            print(f"內嵌音效檔數量：{len(name_files) + len(family_files)} 個")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"打包失敗：{e}")
        if e.stderr:
            print("錯誤輸出：", e.stderr)
        return False
    except Exception as e:
        print(f"執行錯誤：{e}")
        return False

def create_embedded_release():
    """創建內嵌音效版 Release"""
    exe_path = "dist/MagicMusicAcademy_Embedded.exe"
    if not os.path.exists(exe_path):
        print("找不到執行檔，請先執行打包")
        return False
    
    # 創建 release 目錄
    release_dir = "PythonMQTTPlayer-EmbeddedAudio-v2.1.0"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    
    os.makedirs(release_dir)
    
    # 複製執行檔並重新命名
    shutil.copy2(exe_path, f"{release_dir}/魔法音樂學院_完整版.exe")
    
    # 創建說明文件
    readme_content = """🎵 魔法音樂學院 v2.1.0 - 完整內嵌音效版
=============================================

✨ 新功能：音效檔完全內嵌！
--------------------------
本版本的所有音效檔都已完全內嵌到執行檔中，無需額外的音效檔案！

📋 系統需求
----------
- Windows 10/11 (64-bit)
- 網路連接（用於 MQTT 通訊）

🚀 使用方法
----------
1. 雙擊「魔法音樂學院_完整版.exe」啟動程式
2. 程式會自動啟動並載入內嵌音效檔
3. 打開瀏覽器訪問 http://localhost:5000
4. 使用 MQTT 指令控制播放

🎶 內嵌音效清單
--------------
- name 音效：094 個檔案（001.wav ~ 094.wav）
- family 音效：4 個檔案（01.wav ~ 04.wav）
- 總計：98 個完全內嵌的音效檔

📡 MQTT 控制指令
---------------
# 播放 name 音效
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playname001"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playname050"

# 播放 family 音效  
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playfamily01"
mosquitto_pub -h broker.MQTTGO.io -p 1883 -t puffin-test -m "playfamily02"

✅ 版本特色
----------
- ✅ 完全獨立：無需外部音效檔案
- ✅ 一鍵執行：雙擊即可使用  
- ✅ 內嵌完整：98個音效檔全部內建
- ✅ 網路就緒：內建 MQTT 客戶端
- ✅ 魔法界面：Vue.js 魔法學院風格

🛠️ 技術資訊
-----------
- 檔案大小：約 55-60 MB（包含所有音效）
- Python 版本：3.12+
- 打包工具：PyInstaller
- 音效引擎：Pygame
- 網頁框架：Flask + Vue.js

🔧 故障排除
----------
如果程式無法啟動：
1. 確認 Windows Defender 未阻擋執行檔
2. 以系統管理員身份執行
3. 檢查防火牆設定（需開放 5000 埠）

📞 支援
------
GitHub: https://github.com/pc0808f/pythonmqttplayer
如有問題請建立 Issue 或聯繫開發者

---
🤖 使用 Claude Code 協助開發
https://claude.ai/code

© 2024 魔法音樂學院專案"""
    
    with open(f"{release_dir}/README_內嵌版說明.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"內嵌音效版 Release 已創建：{release_dir}/")
    print("包含檔案：")
    print("   - 魔法音樂學院_完整版.exe（內嵌 98 個音效檔）")
    print("   - README_內嵌版說明.txt")
    
    return True

if __name__ == "__main__":
    print("魔法音樂學院 - 內嵌音效版打包程式")
    print("=" * 60)
    
    if build_embedded_executable():
        print("\n打包完成！")
        create_embedded_release()
        print("\n內嵌音效版 Release 準備完成！")
    else:
        print("\n打包失敗，請檢查錯誤訊息")
        sys.exit(1)