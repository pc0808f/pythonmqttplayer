#!/usr/bin/env python3
"""
Python MQTT Player 打包脚本
使用 PyInstaller 将应用程序打包成可执行文件
"""

import os
import subprocess
import sys
import shutil

def run_command(cmd, cwd=None):
    """Execute command and display output"""
    print(f"Running command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=cwd, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False
    except UnicodeDecodeError:
        # Handle encoding issues, retry with gbk encoding
        try:
            result = subprocess.run(cmd, shell=True, check=True, cwd=cwd, 
                                  capture_output=True, text=True, encoding='gbk')
            if result.stdout:
                print(result.stdout)
            return True
        except Exception as e2:
            print(f"Command failed (encoding error): {e2}")
            return False

def build_executable():
    """构建可执行文件"""
    print("Starting build Python MQTT Player executable...")
    
    # 确保当前目录正确
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    # 创建打包所需的参数
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",  # 打包成单个文件
        "--windowed",  # Windows下不显示控制台窗口 (可选)
        "--add-data", "index.html;.",  # 包含前端HTML檔案
        "--hidden-import", "pygame",  # 确保pygame被包含
        "--hidden-import", "paho.mqtt.client",  # 确保paho-mqtt被包含
        "--name", "PythonMQTTPlayer",  # 设置可执行文件名称
        "app.py"
    ]
    
    # 如果是Windows，移除windowed选项以便调试
    if sys.platform.startswith('win'):
        if "--windowed" in pyinstaller_args:
            pyinstaller_args.remove("--windowed")
    
    # 执行PyInstaller命令
    cmd = " ".join(pyinstaller_args)
    if not run_command(cmd):
        print("PyInstaller build failed!")
        return False
    
    # 检查生成的文件
    dist_dir = os.path.join(script_dir, "dist")
    if os.path.exists(dist_dir):
        files = os.listdir(dist_dir)
        print(f"Generated files: {files}")
        
        # 複製 uploads 資料夾到 dist 目錄（如果需要）
        uploads_src = os.path.join(script_dir, "uploads")
        uploads_dst = os.path.join(dist_dir, "uploads")
        if os.path.exists(uploads_src) and not os.path.exists(uploads_dst):
            shutil.copytree(uploads_src, uploads_dst)
            print("Copied uploads folder to dist directory")
    
    print("Build completed!")
    print(f"Executable location: {os.path.join(script_dir, 'dist')}")
    return True

def clean_build():
    """清理构建文件"""
    print("Cleaning build files...")
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    for dirname in dirs_to_remove:
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
            print(f"Removed directory: {dirname}")
    
    import glob
    for pattern in files_to_remove:
        for filename in glob.glob(pattern):
            os.remove(filename)
            print(f"Removed file: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
    else:
        # 先清理，再构建
        clean_build()
        if build_executable():
            print("\\n=== Build Successful! ===")
            print("Executable has been generated in 'dist' directory")
            print("\\nUsage Instructions:")
            print("1. Copy the entire 'dist' directory to target computer")
            print("2. Run PythonMQTTPlayer.exe (Windows) or PythonMQTTPlayer (Linux/Mac)")
            print("3. Access http://localhost:5000 in browser")
        else:
            print("\\n=== Build Failed! ===")
            sys.exit(1)