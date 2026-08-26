"""
魔法音樂學院 - 打包腳本

使用 PyInstaller 把 app.py 打包成單一執行檔，並將以下資源內嵌：
  - index.html            (Vue.js 前端，送檔時從 _MEIPASS 根目錄讀取)
  - uploads/name/*.wav    (姓名音效)
  - uploads/family/*.wav  (家族音效)

執行方式：
    python build.py

產物會出現在 dist/ 目錄下。
音效資料夾內容會即時抓取，所以更新音檔後只要重跑本腳本即可。
"""

import os
import sys
import subprocess

# Windows 主控台預設 cp950，無法輸出 emoji / 部分字元，強制改用 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

APP_NAME = "魔法音樂學院_完整版"
ENTRY = "app.py"

# PyInstaller 的 --add-data 在 Windows 用 ';' 分隔，其他平台用 ':'
SEP = ";" if os.name == "nt" else ":"

# 要內嵌的資源： (來源路徑, 打包後在 bundle 內的目標路徑)
DATA = [
    ("index.html", "."),
    ("uploads/name", "uploads/name"),
    ("uploads/family", "uploads/family"),
]


def count_wav(folder):
    if not os.path.isdir(folder):
        return 0
    return len([f for f in os.listdir(folder) if f.lower().endswith(".wav")])


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # --- 前置檢查 ---
    if not os.path.exists(ENTRY):
        sys.exit(f"❌ 找不到進入點 {ENTRY}")

    name_count = count_wav("uploads/name")
    family_count = count_wav("uploads/family")
    print("=" * 50)
    print(f"🎵 準備打包 {APP_NAME}")
    print(f"   name   音效: {name_count} 個")
    print(f"   family 音效: {family_count} 個")
    print(f"   合計:       {name_count + family_count} 個")
    print("=" * 50)

    if name_count == 0 and family_count == 0:
        print("⚠️  警告：uploads/name 與 uploads/family 皆為空，將打包出沒有音效的執行檔。")

    missing = [src for src, _ in DATA if not os.path.exists(src)]
    if missing:
        print(f"⚠️  警告：以下資源不存在，會被略過：{missing}")

    # --- 組裝 PyInstaller 指令 ---
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--name", APP_NAME,
    ]
    for src, dest in DATA:
        if os.path.exists(src):
            cmd += ["--add-data", f"{src}{SEP}{dest}"]
    cmd.append(ENTRY)

    print("執行指令：")
    print("  " + " ".join(cmd))
    print("-" * 50)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"❌ 打包失敗，PyInstaller 回傳碼 {result.returncode}")

    exe_path = os.path.join("dist", APP_NAME + (".exe" if os.name == "nt" else ""))
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("-" * 50)
        print(f"✅ 打包完成：{exe_path}  ({size_mb:.1f} MB)")
    else:
        sys.exit("❌ 打包指令結束但找不到產物，請檢查上方輸出。")


if __name__ == "__main__":
    main()
