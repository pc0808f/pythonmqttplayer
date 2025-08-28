#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json

def upload_to_github_release():
    """
    上傳執行檔到 GitHub Release v2.2.1
    """
    # GitHub 設定
    repo_owner = "pc0808f"
    repo_name = "pythonmqttplayer"
    release_tag = "v2.2.1"
    
    # 檔案設定
    file_path = r"C:\git\pythonmqttplayer\dist\MagicMusicAcademy_Embedded.exe"
    file_name = "魔法音樂學院_v2.2.1_完整版.exe"
    
    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    # 取得檔案大小
    file_size = os.path.getsize(file_path)
    print(f"📁 檔案: {file_name}")
    print(f"📊 大小: {file_size / 1024 / 1024:.1f} MB")
    
    # 獲取 GitHub Token (需要設定環境變數)
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ 請設定 GITHUB_TOKEN 環境變數")
        print("💡 可以在 GitHub Settings > Developer settings > Personal access tokens 生成")
        return False
    
    # 設定 API headers
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Upload-Script"
    }
    
    try:
        # 1. 獲取 release 資訊
        print(f"🔍 查找 release {release_tag}...")
        release_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{release_tag}"
        
        response = requests.get(release_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ 找不到 release {release_tag}: {response.status_code}")
            print(f"回應: {response.text}")
            return False
        
        release_data = response.json()
        release_id = release_data['id']
        upload_url = release_data['upload_url'].replace('{?name,label}', '')
        
        print(f"✅ 找到 release: {release_data['name']}")
        print(f"📤 上傳 URL: {upload_url}")
        
        # 2. 上傳檔案
        print(f"⬆️  開始上傳檔案...")
        upload_headers = headers.copy()
        upload_headers["Content-Type"] = "application/octet-stream"
        
        upload_params = {
            "name": file_name,
            "label": f"魔法音樂學院 v2.2.1 完整版執行檔 (含 99 個內嵌音效檔)"
        }
        
        with open(file_path, 'rb') as f:
            upload_response = requests.post(
                upload_url,
                headers=upload_headers,
                params=upload_params,
                data=f
            )
        
        if upload_response.status_code == 201:
            asset_data = upload_response.json()
            download_url = asset_data['browser_download_url']
            print(f"🎉 上傳成功!")
            print(f"📥 下載連結: {download_url}")
            print(f"📦 檔案大小: {asset_data['size'] / 1024 / 1024:.1f} MB")
            return True
        else:
            print(f"❌ 上傳失敗: {upload_response.status_code}")
            print(f"回應: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 上傳過程發生錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 開始上傳魔法音樂學院執行檔到 GitHub Release...")
    success = upload_to_github_release()
    
    if success:
        print("\n✅ 上傳完成!")
        print("🎵 魔法音樂學院 v2.2.1 已可供下載!")
    else:
        print("\n❌ 上傳失敗!")
        print("💡 請檢查網路連線和 GitHub Token 設定")