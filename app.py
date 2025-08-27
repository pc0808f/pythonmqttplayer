import os
import sys
import socket
import threading
import queue
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import paho.mqtt.client as mqtt
import pygame

def get_resource_path(relative_path):
    """取得資源檔案的正確路徑，支援 PyInstaller 打包後的執行環境"""
    try:
        # PyInstaller 在打包後會將資源解壓到臨時資料夾
        base_path = sys._MEIPASS
        print(f"PyInstaller 模式，資源基礎路徑: {base_path}")
    except AttributeError:
        # 開發模式或未打包狀態
        base_path = os.path.abspath(".")
        print(f"開發模式，資源基礎路徑: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    print(f"資源路徑轉換: {relative_path} -> {full_path}")
    return full_path

# --- 全域設定 ---
# 存放上傳檔案的資料夾
UPLOAD_FOLDER = get_resource_path('uploads')
# 允許的檔案擴展名
ALLOWED_EXTENSIONS = {'wav'}

# 建立一個執行緒安全的佇列，用於存放待播的音檔路徑
playback_queue = queue.Queue()

# 播放狀態管理
played_files = set()  # 存儲已播放的檔案
play_once_mode = False  # 是否啟用只播放一次模式

# 即時狀態管理
current_playing = None  # 目前播放的檔案
playing_start_time = None  # 播放開始時間
play_queue_list = []  # 播放佇列（用於前端顯示）
mqtt_logs = []  # MQTT 日誌
last_mqtt_command = None  # 最後的 MQTT 指令
last_mqtt_time = None  # 最後 MQTT 指令時間

# --- Flask 應用程式設定 ---
app = Flask(__name__)
CORS(app)  # 啟用 CORS 支援 Vue.js 前端
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flash_messages' # 用於顯示提示訊息

# --- 輔助函式 ---
def allowed_file(filename):
    """檢查檔案是否為允許的格式 (.wav)"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ip_address():
    """取得本機的 IP 位址作為 MQTT Client ID，加入隨機數字避免衝突"""
    import random
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # 加入隨機數字避免多個客戶端衝突
        random_suffix = random.randint(1000, 9999)
        client_id = f"{ip.replace('.', '_')}_{random_suffix}"
        print(f"生成 MQTT 客戶端 ID: {client_id}")
        return client_id
    except Exception:
        random_suffix = random.randint(1000, 9999)
        client_id = f"default_client_{random_suffix}"
        print(f"使用預設 MQTT 客戶端 ID: {client_id}")
        return client_id

def play_audio_file(audio_file_path):
    """播放音頻檔案，支援 wav 格式"""
    try:
        # 直接播放 wav 格式
        pygame.mixer.music.load(audio_file_path)
        pygame.mixer.music.play()
        return True
    except Exception as e:
        print(f"播放音檔失敗: {e} - 檔案: {audio_file_path}")
        return False

# --- 音檔播放執行緒 (消費者) ---
def audio_player_worker():
    """
    這是一個在背景執行的工作執行緒。
    它會不斷地從佇列中取出音檔路徑並播放。
    """
    global current_playing, playing_start_time, play_queue_list
    
    # 初始化pygame mixer
    pygame.mixer.init()
    print("音檔播放執行緒已啟動，等待播放任務...")
    
    while True:
        try:
            # queue.get() 是阻塞操作，如果佇列是空的，它會在這裡等待
            audio_data = playback_queue.get()
            
            # 處理不同的播放格式
            if isinstance(audio_data, tuple) and len(audio_data) == 3 and audio_data[0] == 'sequence':
                # 序列播放模式: ('sequence', [(path1, name1), (path2, name2)], name_for_played_tracking)
                _, files_to_play, name_for_tracking = audio_data
                
                print(f"開始序列播放 {len(files_to_play)} 個檔案")
                
                for i, (audio_file_path, filename) in enumerate(files_to_play):
                    print(f"正在播放 ({i+1}/{len(files_to_play)}): {filename}")
                    
                    # 更新播放狀態
                    current_playing = filename
                    playing_start_time = time.time()
                    
                    # 從佇列列表中移除正在播放的檔案
                    if filename in play_queue_list:
                        play_queue_list.remove(filename)
                    
                    # 播放音檔
                    if not play_audio_file(audio_file_path):
                        # 如果播放失敗，跳過這個檔案繼續下一個
                        continue
                    
                    # 等待播放完畢（更短的檢查間隔）
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.01)  # 縮短檢查間隔從 0.1 秒到 0.01 秒
                    
                    print(f"播放完畢 ({i+1}/{len(files_to_play)}): {filename}")
                    
                    # 如果不是最後一個檔案，立即準備下一個檔案（無延遲）
                    if i < len(files_to_play) - 1:
                        # 預載下一個檔案以減少切換延遲
                        pass  # pygame.mixer.music 一次只能載入一個檔案，所以這裡不能預載
                
                # 序列播放完成
                print(f"序列播放完成")
                
                # 清除播放狀態
                current_playing = None
                playing_start_time = None
                
                # 如果是只播放一次模式，標記 name 為已播放
                if play_once_mode:
                    played_files.add(name_for_tracking)
                    print(f"標記 name={name_for_tracking} 為已播放")
                    print(f"目前已播放檔案: {list(played_files)}")
                    
            elif isinstance(audio_data, tuple) and len(audio_data) == 2:
                # 單一檔案模式: (file_path, filename) 
                audio_file_path, filename = audio_data
                
                print(f"正在播放: {filename}")
                
                # 更新播放狀態
                current_playing = filename
                playing_start_time = time.time()
                
                # 從佇列列表中移除正在播放的檔案
                if filename in play_queue_list:
                    play_queue_list.remove(filename)
                
                # 播放音檔
                if not play_audio_file(audio_file_path):
                    # 如果播放失敗，清除播放狀態並跳過這個檔案
                    current_playing = None
                    playing_start_time = None
                    continue
                
                # 等待播放完畢（更短的檢查間隔）
                while pygame.mixer.music.get_busy():
                    time.sleep(0.01)
                
                print(f"播放完畢: {filename}")
                
                # 清除播放狀態
                current_playing = None
                playing_start_time = None
                
                # 如果是只播放一次模式，標記為已播放
                if play_once_mode:
                    played_files.add(filename)
                    print(f"標記 {filename} 為已播放")
                    
            else:
                # 舊格式: file_path
                audio_file_path = audio_data
                filename = os.path.basename(audio_file_path)
                
                print(f"正在播放: {filename}")
                
                # 更新播放狀態
                current_playing = filename
                playing_start_time = time.time()
                
                # 從佇列列表中移除正在播放的檔案
                if filename in play_queue_list:
                    play_queue_list.remove(filename)
                
                # 播放音檔
                if not play_audio_file(audio_file_path):
                    # 如果播放失敗，清除播放狀態並跳過這個檔案
                    current_playing = None
                    playing_start_time = None
                    continue
                
                # 等待播放完畢（更短的檢查間隔）
                while pygame.mixer.music.get_busy():
                    time.sleep(0.01)
                
                print(f"播放完畢: {filename}")
                
                # 清除播放狀態
                current_playing = None
                playing_start_time = None
                
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
    print("MQTT 連接回調觸發")
    print(f"連接結果碼: {rc}")
    
    if rc == 0:
        print("成功連線到 MQTT Broker")
        try:
            result = client.subscribe("puffin-test")
            print(f"訂閱 puffin-test 結果: {result}")
            if result[0] == 0:
                print("訂閱成功")
            else:
                print(f"訂閱失敗，錯誤碼: {result[0]}")
        except Exception as e:
            print(f"訂閱異常: {str(e)}")
    else:
        print(f"MQTT 連線失敗: {rc}")

def on_message(client, userdata, msg):
    """當收到訂閱主題的訊息時的回呼函式"""
    try:
        payload = msg.payload.decode('utf-8')
        print(f"*** MQTT 訊息接收 ***")
        print(f"主題: {msg.topic}")
        print(f"內容: {payload}")
        print(f"QoS: {msg.qos}")
        
        # 記錄 MQTT 日誌
        global last_mqtt_command, last_mqtt_time, mqtt_logs
        last_mqtt_command = payload
        last_mqtt_time = time.time()
        
        # 添加到 MQTT 日誌
        mqtt_logs.append({
            'timestamp': time.time(),
            'topic': msg.topic,
            'command': payload,
            'status': 'received'
        })
        
        # 限制日誌數量
        if len(mqtt_logs) > 50:
            mqtt_logs = mqtt_logs[-50:]

        # 解析訊息格式 "name,family"，例如 "001,01"
        if ',' in payload:
            try:
                name, family = payload.split(',', 1)
                name = name.strip()
                family = family.strip()
                
                print(f"解析到 name: {name}, family: {family}")
                
                # 檢查只播放一次模式 (基於 name)
                print(f"播放模式檢查: play_once_mode={play_once_mode}, name={name}")
                print(f"目前已播放檔案: {list(played_files)}")
                if play_once_mode and name in played_files:
                    print(f"跳過播放: name={name} (已播放過，只播放一次模式)")
                    mqtt_logs[-1]['status'] = 'skipped'
                    mqtt_logs[-1]['reason'] = 'already_played'
                    return
                
                # 檢查檔案是否存在
                name_file = f"{name}.wav"
                family_file = f"{family}.wav"
                name_path = os.path.join(app.config['UPLOAD_FOLDER'], 'name', name_file)
                family_path = os.path.join(app.config['UPLOAD_FOLDER'], 'family', family_file)
                
                files_to_play = []
                
                # 檢查 name 檔案
                if os.path.exists(name_path):
                    files_to_play.append((name_path, name_file))
                else:
                    print(f"警告: 找不到 name 音檔 {name_file}")
                
                # 檢查 family 檔案
                if os.path.exists(family_path):
                    files_to_play.append((family_path, family_file))
                else:
                    print(f"警告: 找不到 family 音檔 {family_file}")
                
                if files_to_play:
                    # 將檔案序列加入佇列，使用特殊格式表示這是一個組合播放
                    playback_queue.put(('sequence', files_to_play, name))  # 第三個參數是用於記錄已播放的 name
                    print(f"已將 {len(files_to_play)} 個檔案加入播放佇列。目前佇列大小: {playback_queue.qsize()}")
                    
                    # 更新佇列列表
                    global play_queue_list
                    for _, filename in files_to_play:
                        play_queue_list.append(filename)
                    
                    # 記錄成功狀態
                    mqtt_logs[-1]['status'] = 'queued'
                else:
                    print(f"警告: 沒有找到可播放的檔案")
                    mqtt_logs[-1]['status'] = 'files_not_found'
                    
            except ValueError:
                print(f"警告: 無法解析的指令格式 {payload}")
                mqtt_logs[-1]['status'] = 'invalid_format'
        else:
            print(f"警告: 無效的訊息格式，預期 'name,family'，收到: {payload}")
            mqtt_logs[-1]['status'] = 'invalid_format'

    except Exception as e:
        print(f"處理訊息時發生錯誤: {e}")
        if mqtt_logs:
            mqtt_logs[-1]['status'] = 'error'
            mqtt_logs[-1]['error'] = str(e)


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
    try:
        # 使用 get_resource_path 獲取 index.html 的正確路徑
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
        return send_from_directory(base_path, 'index.html')
    except Exception as e:
        print(f"載入首頁時發生錯誤: {e}")
        return f"<h1>魔法音樂學院</h1><p>載入首頁時發生錯誤: {e}</p><p>請確認 index.html 檔案存在。</p>", 500

# --- API 路由 (供 Vue.js 前端使用) ---
@app.route('/api/files', methods=['GET'])
def api_get_files():
    """取得已上傳的檔案列表"""
    result = {'name': [], 'family': [], 'root': []}
    
    # 檢查 name 資料夾
    name_folder = os.path.join(UPLOAD_FOLDER, 'name')
    if os.path.exists(name_folder):
        result['name'] = sorted([f for f in os.listdir(name_folder) if f.endswith('.wav')])
    
    # 檢查 family 資料夾
    family_folder = os.path.join(UPLOAD_FOLDER, 'family')
    if os.path.exists(family_folder):
        result['family'] = sorted([f for f in os.listdir(family_folder) if f.endswith('.wav')])
    
    # 檢查根目錄的檔案（為了向下相容）
    if os.path.exists(UPLOAD_FOLDER):
        all_files = os.listdir(UPLOAD_FOLDER)
        result['root'] = sorted([f for f in all_files if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
    
    # 為了向下相容，保留原有的 API 格式
    all_files_count = len(result['name']) + len(result['family']) + len(result['root'])
    
    return jsonify({
        'files': result['root'],  # 與舊 API 相容
        'count': len(result['root']),  # 與舊 API 相容
        'detailed': result,
        'totalCount': all_files_count
    })

@app.route('/api/upload', methods=['POST'])
def api_upload_files():
    """上傳檔案 API"""
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'message': '請求中沒有檔案部分'}), 400

    files = request.files.getlist('files[]')
    folder_type = request.form.get('folder', 'root')  # 'name', 'family', 或 'root'
    
    uploaded_count = 0
    uploaded_files = []
    
    # 決定上傳目標目錄
    if folder_type == 'name':
        target_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'name')
    elif folder_type == 'family':
        target_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'family')
    else:
        target_folder = app.config['UPLOAD_FOLDER']
    
    for file in files:
        if file.filename == '':
            continue
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(target_folder, filename))
            uploaded_count += 1
            uploaded_files.append(filename)
    
    if uploaded_count > 0:
        return jsonify({
            'success': True, 
            'message': f'成功上傳 {uploaded_count} 個檔案至 {folder_type} 目錄！',
            'uploaded_files': uploaded_files,
            'count': uploaded_count,
            'folder': folder_type
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

@app.route('/api/status', methods=['GET'])
def api_get_status():
    """取得即時播放狀態"""
    global current_playing, playing_start_time, play_queue_list, last_mqtt_command, last_mqtt_time, mqtt_logs
    
    # 更新佇列狀態（移除已播放的）
    if current_playing and current_playing in play_queue_list:
        play_queue_list.remove(current_playing)
    
    # 格式化播放開始時間
    playing_start_formatted = None
    if playing_start_time:
        from datetime import datetime
        playing_start_formatted = datetime.fromtimestamp(playing_start_time).strftime('%H:%M:%S')
    
    # 格式化最後 MQTT 時間
    last_mqtt_formatted = None
    if last_mqtt_time:
        from datetime import datetime
        last_mqtt_formatted = datetime.fromtimestamp(last_mqtt_time).strftime('%H:%M:%S')
    
    return jsonify({
        'currentPlaying': current_playing,
        'playingStartTime': playing_start_formatted,
        'playQueue': play_queue_list.copy(),
        'queueSize': playback_queue.qsize(),
        'lastMqttCommand': last_mqtt_command,
        'lastMqttTime': last_mqtt_formatted,
        'mqttLogs': mqtt_logs[-10:],  # 最近10條日誌
        'isConnected': True  # 簡化版，實際應該檢查 MQTT 連接狀態
    })


# --- 主程式進入點 ---
if __name__ == '__main__':
    print(f"啟動魔法音樂學院...")
    print(f"音效檔基礎路徑: {UPLOAD_FOLDER}")
    
    # 檢查是否在 PyInstaller 環境中
    if hasattr(sys, '_MEIPASS'):
        print("在 PyInstaller 打包環境中執行，音效檔已內嵌")
        # 確認內嵌的音效檔案是否存在
        name_folder = os.path.join(UPLOAD_FOLDER, 'name')
        family_folder = os.path.join(UPLOAD_FOLDER, 'family')
        
        if os.path.exists(name_folder):
            name_files = [f for f in os.listdir(name_folder) if f.endswith('.wav')]
            print(f"發現 {len(name_files)} 個內嵌的 name 音效檔")
        else:
            print(f"警告: 找不到內嵌的 name 資料夾: {name_folder}")
            
        if os.path.exists(family_folder):
            family_files = [f for f in os.listdir(family_folder) if f.endswith('.wav')]
            print(f"發現 {len(family_files)} 個內嵌的 family 音效檔")
        else:
            print(f"警告: 找不到內嵌的 family 資料夾: {family_folder}")
    else:
        print("在開發環境中執行，檢查並建立必要的資料夾...")
        # 確保 uploads 資料夾存在
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            print(f"已建立資料夾: {UPLOAD_FOLDER}")
        
        # 確保 name 和 family 子資料夾存在
        name_folder = os.path.join(UPLOAD_FOLDER, 'name')
        family_folder = os.path.join(UPLOAD_FOLDER, 'family')
        
        if not os.path.exists(name_folder):
            os.makedirs(name_folder)
            print(f"已建立資料夾: {name_folder}")
            
        if not os.path.exists(family_folder):
            os.makedirs(family_folder)
            print(f"已建立資料夾: {family_folder}")

    # 1. 啟動音檔播放工作執行緒
    player_thread = threading.Thread(target=audio_player_worker, daemon=True)
    player_thread.start()

    # 2. 啟動 MQTT 客戶端
    mqtt_client = setup_mqtt_client()
    
    # 3. 啟動 Flask 網頁伺服器
    # use_reloader=False 是必要的，因為 Flask 的自動重載會執行兩次程式，導致服務重複啟動
    print("啟動 Flask 網頁伺服器於 http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

