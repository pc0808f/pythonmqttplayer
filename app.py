import os
import socket
import threading
import queue
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import paho.mqtt.client as mqtt
import pygame

# --- 全域設定 ---
# 存放上傳檔案的資料夾
UPLOAD_FOLDER = 'uploads'
# 允許的檔案擴展名
ALLOWED_EXTENSIONS = {'wav'}

# 建立一個執行緒安全的佇列，用於存放待播的音檔路徑
playback_queue = queue.Queue()

# 播放狀態管理
played_files = set()  # 存儲已播放的檔案
play_once_mode = False  # 是否啟用只播放一次模式

# --- Flask 應用程式設定 ---
app = Flask(__name__)
CORS(app)  # 啟用 CORS 支援 Vue.js 前端
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flash_messages' # 用於顯示提示訊息

# --- 輔助函式 ---
def allowed_file(filename):
    """檢查檔案是否為允許的 .wav 格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ip_address():
    """取得本機的 IP 位址作為 MQTT Client ID"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "default_client_id_12345"

# --- 音檔播放執行緒 (消費者) ---
def audio_player_worker():
    """
    這是一個在背景執行的工作執行緒。
    它會不斷地從佇列中取出音檔路徑並播放。
    """
    # 初始化pygame mixer
    pygame.mixer.init()
    print("音檔播放執行緒已啟動，等待播放任務...")
    
    while True:
        try:
            # queue.get() 是阻塞操作，如果佇列是空的，它會在這裡等待
            audio_data = playback_queue.get()
            
            # 處理新格式：(file_path, filename) 或舊格式：file_path
            if isinstance(audio_data, tuple):
                audio_file_path, filename = audio_data
            else:
                audio_file_path = audio_data
                filename = os.path.basename(audio_file_path)
            
            print(f"正在播放: {filename}")
            
            # 使用pygame播放音檔
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            
            # 等待播放完畢
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print(f"播放完畢: {filename}")
            
            # 如果是只播放一次模式，標記為已播放
            if play_once_mode:
                played_files.add(filename)
                print(f"標記 {filename} 為已播放")
            
            # 標示任務完成
            playback_queue.task_done()
        except Exception as e:
            print(f"播放時發生錯誤: {e}")
            # 即使出錯，也要標示任務完成，以免卡住佇列
            playback_queue.task_done()


# --- MQTT 客戶端設定 (生產者) ---
def on_connect(client, userdata, flags, rc, properties=None):
    """當成功連線到 MQTT Broker 時的回呼函式"""
    if rc == 0:
        print("成功連線到 MQTT Broker!")
        # 訂閱指定的主題
        client.subscribe("puffin-test")
        print("已訂閱主題: puffin-test")
    else:
        print(f"連線失敗，返回碼: {rc}")

def on_message(client, userdata, msg):
    """當收到訂閱主題的訊息時的回呼函式"""
    try:
        payload = msg.payload.decode('utf-8')
        print(f"收到訊息 - 主題: {msg.topic}, 內容: {payload}")

        # 解析訊息，例如 "play001" -> "001"
        if payload.startswith("play"):
            file_number = payload[4:]
            if file_number.isdigit():
                filename = f"{file_number}.wav"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # 檢查檔案是否存在
                if os.path.exists(file_path):
                    # 檢查只播放一次模式
                    if play_once_mode and filename in played_files:
                        print(f"跳過播放: {filename} (已播放過，只播放一次模式)")
                        return
                    
                    # 將待播的音檔路徑放入佇列
                    playback_queue.put((file_path, filename))  # 同時傳遞路徑和檔名
                    print(f"已將 {filename} 加入播放佇列。目前佇列大小: {playback_queue.qsize()}")
                else:
                    print(f"警告: 找不到音檔 {filename}")
            else:
                print(f"警告: 無法解析的指令 {payload}")

    except Exception as e:
        print(f"處理訊息時發生錯誤: {e}")


def setup_mqtt_client():
    """設定並啟動 MQTT 客戶端"""
    client_id = get_ip_address()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("正在嘗試連線到 MQTT Broker...")
        client.connect("broker.MQTTGO.io", 1883, 60)
        # client.loop_start() 會在背景執行緒中處理網路迴圈，不會阻塞主程式
        client.loop_start()
        return client
    except Exception as e:
        print(f"無法連線到 MQTT Broker: {e}")
        return None

# --- Flask 網頁路由 ---
@app.route('/')
def vue_app():
    """Vue.js 魔法音樂學院前端頁面 (主頁面)"""
    return send_from_directory('.', 'index.html')

# --- API 路由 (供 Vue.js 前端使用) ---
@app.route('/api/files', methods=['GET'])
def api_get_files():
    """取得已上傳的檔案列表"""
    if os.path.exists(UPLOAD_FOLDER):
        uploaded_files = sorted(os.listdir(UPLOAD_FOLDER))
    else:
        uploaded_files = []
    
    return jsonify({
        'files': uploaded_files,
        'count': len(uploaded_files)
    })

@app.route('/api/upload', methods=['POST'])
def api_upload_files():
    """上傳檔案 API"""
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'message': '請求中沒有檔案部分'}), 400

    files = request.files.getlist('files[]')
    uploaded_count = 0
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploaded_count += 1
            uploaded_files.append(filename)
    
    if uploaded_count > 0:
        return jsonify({
            'success': True, 
            'message': f'成功上傳 {uploaded_count} 個檔案！',
            'uploaded_files': uploaded_files,
            'count': uploaded_count
        })
    else:
        return jsonify({
            'success': False, 
            'message': '沒有選擇任何有效的 .wav 檔案。'
        }), 400

@app.route('/api/play-mode', methods=['POST'])
def api_set_play_mode():
    """設定播放模式"""
    global play_once_mode, played_files
    
    data = request.get_json()
    play_once_mode = data.get('playOnceMode', False)
    
    # 如果關閉只播放一次模式，清空已播放列表
    if not play_once_mode:
        played_files.clear()
    
    return jsonify({
        'success': True,
        'playOnceMode': play_once_mode,
        'message': f'播放模式已設定為: {"只播放一次" if play_once_mode else "可重複播放"}'
    })

@app.route('/api/played-files', methods=['GET'])
def api_get_played_files():
    """取得已播放檔案列表"""
    return jsonify({
        'playedFiles': list(played_files),
        'playOnceMode': play_once_mode
    })

@app.route('/api/reset-played', methods=['POST'])
def api_reset_played():
    """重置已播放檔案"""
    global played_files
    
    data = request.get_json()
    filename = data.get('filename')
    
    if filename:
        # 重置單個檔案
        if filename in played_files:
            played_files.remove(filename)
            return jsonify({
                'success': True,
                'message': f'檔案 {filename} 已重置'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'檔案 {filename} 尚未播放'
            })
    else:
        # 重置全部檔案
        played_files.clear()
        return jsonify({
            'success': True,
            'message': '所有檔案已重置'
        })


# --- 主程式進入點 ---
if __name__ == '__main__':
    # 確保 uploads 資料夾存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"已建立資料夾: {UPLOAD_FOLDER}")

    # 1. 啟動音檔播放工作執行緒
    player_thread = threading.Thread(target=audio_player_worker, daemon=True)
    player_thread.start()

    # 2. 啟動 MQTT 客戶端
    mqtt_client = setup_mqtt_client()
    
    # 3. 啟動 Flask 網頁伺服器
    # use_reloader=False 是必要的，因為 Flask 的自動重載會執行兩次程式，導致服務重複啟動
    print("啟動 Flask 網頁伺服器於 http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

