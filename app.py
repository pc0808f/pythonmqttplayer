import os
import socket
import threading
import queue
import time
from flask import Flask, request, render_template, flash, redirect, url_for
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

# --- Flask 應用程式設定 ---
app = Flask(__name__)
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
            audio_file_path = playback_queue.get()
            print(f"正在播放: {os.path.basename(audio_file_path)}")
            
            # 使用pygame播放音檔
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            
            # 等待播放完畢
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print(f"播放完畢: {os.path.basename(audio_file_path)}")
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
                    # 將待播的音檔路徑放入佇列
                    playback_queue.put(file_path)
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
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 檢查是否有檔案在請求中
        if 'files[]' not in request.files:
            flash('請求中沒有檔案部分')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        uploaded_count = 0
        for file in files:
            # 如果使用者沒有選擇檔案，瀏覽器可能會送出一個沒有檔名的空檔案
            if file.filename == '':
                continue
            
            if file and allowed_file(file.filename):
                # 使用 secure_filename 確保檔名安全
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_count += 1
        
        if uploaded_count > 0:
            flash(f'成功上傳 {uploaded_count} 個檔案！')
        else:
            flash('沒有選擇任何有效的 .wav 檔案。')
        return redirect(url_for('upload_file'))

    # 顯示目前已上傳的檔案列表
    if os.path.exists(UPLOAD_FOLDER):
        uploaded_files = sorted(os.listdir(UPLOAD_FOLDER))
    else:
        uploaded_files = []
        
    return render_template('index.html', uploaded_files=uploaded_files)

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

