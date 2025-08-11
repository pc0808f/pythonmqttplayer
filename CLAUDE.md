主要語言為繁體中文

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Python MQTT 音频播放器应用程序，结合了 Flask Web 界面和 MQTT 消息订阅功能。应用程序允许用户通过 Web 界面上传 WAV 音频文件，然后通过 MQTT 消息远程触发音频播放。

## 核心架构

应用程序采用多线程架构，包含三个主要组件：

1. **Flask Web 服务器** (主线程)：提供文件上传界面
2. **MQTT 客户端** (后台线程)：订阅 "puffin-test" 主题，接收播放指令
3. **音频播放工作线程** (后台守护线程)：处理音频播放队列

### 关键组件说明

- **音频队列系统**：使用 `queue.Queue()` 实现线程安全的播放队列
- **MQTT 消息格式**：接收 "playXXX" 格式的消息（如 "play001"），播放对应的 XXX.wav 文件
- **文件存储**：所有上传的音频文件存储在 `uploads/` 目录中
- **MQTT Broker**：连接到 "broker.MQTTGO.io:1883"

## 运行命令

### 启动应用程序

```bash
python app.py
```

应用程序会：

- 在端口 5000 启动 Flask web 服务器 (http://0.0.0.0:5000)
- 自动创建 `uploads/` 目录（如果不存在）
- 启动音频播放工作线程
- 连接到 MQTT broker 并订阅 "puffin-test" 主题

### 依赖项

应用程序需要以下 Python 包：

- Flask: Web 框架
- paho-mqtt: MQTT 客户端库
- playsound: 音频播放库
- werkzeug: Flask 依赖项（文件上传安全性）

可以通过以下命令安装依赖：

```bash
pip install flask paho-mqtt playsound werkzeug
```

## 文件结构

```
pythonmqttplayer/
├── app.py              # 主应用程序文件
├── templates/
│   └── index.html      # Web 界面模板
└── uploads/            # 音频文件存储目录（运行时创建）
```

## 开发注意事项

### MQTT 消息格式

- 主题：`puffin-test`
- 消息格式：`playXXX`（XXX 为数字，对应 XXX.wav 文件）
- 示例：发送 "play001" 播放 "001.wav"

### 安全配置

- 使用 `secure_filename()` 处理文件上传安全性
- 限制上传文件类型为 .wav 格式
- Flask SECRET_KEY 需要在生产环境中更改

### 调试模式

应用程序默认以 debug=True 运行，但使用 use_reloader=False 避免服务重复启动的问题。

### 客户端 ID 生成

MQTT 客户端 ID 使用本机 IP 地址，如果无法获取则使用默认值 "default_client_id_12345"。
