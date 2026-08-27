# 🎵 魔法音樂學院 PythonMQTTPlayer

一個具有暖色系小學開學風格、魔法學院感覺的 MQTT 音檔播放控制器。專為**台北市和平實驗小學「家族儀式」**活動開發：現場司儀（或裝置）透過 MQTT 送出指令，伺服器依序播放對應的姓名 / 家族音效，並提供 Web 介面上傳音檔、監看播放狀態、管理補送名單、以及觸發互動燈光模式。

> 給下一位維護者：這份 README 除了說明「現在長怎樣」，也記錄「為什麼長成這樣」以及「明年開學前要做什麼」。詳細規格文件另外放在 `doc/`、`archives/`，重大功能的設計脈絡建議先看本檔案的〈開發歷程〉一節。

## 這個專案在做什麼

典型使用情境（畢業/開學典禮，小朋友上台刷卡）：

1. 小朋友刷 NFC 卡，Arduino/ESP32 裝置解析卡片，透過 MQTT 送出 `"姓名代號,家族代號"`（例如 `"001,01"`）到 `puffin-test` 主題。
2. 本專案的 Flask 後端訂閱該主題，依序播放 `uploads/name/001.wav` → `uploads/family/01.wav`。
3. 現場工作人員可透過瀏覽器開啟的 Vue.js 介面，即時看到播放狀態、上傳/管理音檔。
4. 若卡片刷卡失敗或漏播，工作人員可到「補送名單頁」(`/sup`) 手動補送指定的姓名/家族音效。
5. 司儀也可以在補送名單頁觸發「互動燈光模式」，透過另一個 MQTT 主題 (`puffin-control`) 控制裝置上的 LED 燈效（進入互動模式 / 模式一 / 模式二 / 離開互動模式）。

## 核心架構

多執行緒 Flask 應用，四個主要組件：

1. **Flask API 伺服器**（主執行緒）— RESTful API、檔案上傳、Vue.js/補送名單頁面路由
2. **Vue.js 前端**（瀏覽器）— 主頁 `index.html`（上傳/監控）與補送名單頁 `supplement.html`
3. **MQTT 客戶端**（背景執行緒）— 訂閱 `puffin-test`（播放指令）並發布 `puffin-control`（燈光控制）
4. **音訊播放工作執行緒**（背景守護執行緒）— 從 `queue.Queue()` 取出待播序列，用 pygame 依序播放

詳細技術規則（訊息格式、API 端點、打包方式）請見 `CLAUDE.md`。

## 檔案結構

```
pythonmqttplayer/
├── app.py                              # Flask 後端主程式（MQTT 訂閱、播放佇列、API）
├── index.html                          # Vue.js 主頁（音檔上傳、即時播放狀態監控）
├── supplement.html                     # 補送名單頁 + 互動燈光模式控制（/sup 路由）
├── build.py                            # PyInstaller 打包腳本（內嵌 index.html / supplement.html / uploads）
├── 魔法音樂學院_完整版.spec             # PyInstaller spec 檔（build.py 優先使用）
├── upload_release.py                   # 協助把打包產物上傳到 GitHub Release
├── requirements.txt                    # Python 相依套件
├── uploads/                             # 音效檔（.gitignore 排除，不進版控）
│   ├── name/                            # 姓名音效 001.wav ~ NNN.wav
│   └── family/                          # 家族音效 01~04.wav（01=天空、02=海洋、03=樹居、04=大地）
├── doc/
│   └── Arduino互動燈光模式說明.md        # 給 Arduino/ESP32 端的燈光模式協定規格
├── archives/                            # 歷史部署說明等文件
└── 魔法音樂學院_使用說明書_v2.3.0.md     # 給現場工作人員看的操作手冊
```

## 執行與打包

```bash
pip install -r requirements.txt
python app.py          # http://0.0.0.0:5000，主頁 /，補送名單頁 /sup
```

打包成單一執行檔（會把 index.html、supplement.html、uploads/name、uploads/family 全部內嵌進 exe）：

```bash
python build.py
```

> 音效資料夾內容是打包當下即時抓取的，**改完音檔一定要重新執行 `build.py`** 才會反映到新的 exe。

## 開發歷程（重大功能演進）

依 git log 由舊到新整理，方便新接手的人快速抓到「為什麼會有這段程式碼」：

| 版本/主題 | 做了什麼 | 為什麼 |
|---|---|---|
| 初始版本 | 純 Python + MQTT + pygame 的音檔播放器 | 最基本的刷卡播放需求 |
| 前端重構 | 改為 Vue.js 3 + Tailwind「魔法學院」風格介面 | 提升現場操作體驗，取代陽春介面 |
| 即時播放監控 | 新增播放佇列、目前播放中檔案、MQTT 收訊日誌的 API 與前端顯示 | 現場工作人員需要即時確認裝置有沒有正確送出指令、有沒有卡音效 |
| 「只播放一次」模式 | 依 `name` 記錄已播放清單，避免重複刷卡重複播放 | 典禮上小朋友可能重複刷卡，需要防止洗版 |
| 執行檔打包（內嵌音效） | 導入 `build.py` + PyInstaller，把 uploads 音效內嵌進單一 exe | 現場電腦不一定有 Python 環境，需要單檔可直接執行 |
| v2.3.0 補送名單頁 (`/sup`) | 新增查詢「已播放/未播放」名單、可手動重送單一姓名或家族音效 | 刷卡裝置訊號不穩或卡片故障時，需要人工補救播放 |
| MQTT broker 統一為 `MQTTGO.io` | 修正先前 broker 位址不一致的問題 | 確保裝置端與伺服器端連到同一個 broker |
| 回報真實 MQTT 連線狀態 | 移除前端假造的「已連線」顯示，改用 `on_connect`/`on_disconnect` 回呼更新真實狀態 | 先前介面會顯示連線正常，但實際上 broker 沒連上，造成現場誤判 |
| build.py 內嵌 supplement.html | 修正打包後 `/sup` 頁面 404 的問題 | 一開始 `build.py` 只內嵌了 `index.html`，忘記把補送名單頁也加進去 |
| v2.4.0 互動燈光模式 | 補送名單頁新增「進入互動模式／模式一／模式二／離開互動模式」四顆按鈕，發布指令到新主題 `puffin-control`；新增 `doc/Arduino互動燈光模式說明.md` 給硬體端實作 | 典禮中除了播音效，也想讓 Arduino 端的 LED 燈條配合演出，且完全不影響原本刷卡播放邏輯（新協定走獨立 topic） |
| 進入互動模式可重複補送 | `INTERACTIVE_START` 刻意設計成不檢查目前狀態，允許重複發送 | MQTT 沒有送達保證，主持人按下「進入互動模式」但裝置沒收到時，可以直接再按一次而不會出錯 |

> **互動燈光模式的協定是「App 端已定案」**，若要修改燈光時間長度、指令字串、topic 名稱，務必同步更新 `doc/Arduino互動燈光模式說明.md` 並跟硬體端確認，因為 App 與 Arduino 是兩份獨立程式碼，靠字串協定溝通，沒有型別檢查。

## ⚠️ 大型檔案注意事項

本專案的打包產物 `魔法音樂學院_完整版.exe` 約 **52.8 MB**，已超過 GitHub 建議的單檔 50 MB 上限。

推送時 GitHub 會回傳警告：

```
remote: warning: File PythonMQTTPlayer-EmbeddedAudio-vX.X.X/魔法音樂學院_完整版.exe is 52.79 MB;
        this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: GH001: Large files detected.
```

目前**仍可正常推送**（GitHub 的硬性上限為 100 MB），但每發布一個版本就多存一份 exe，會讓 repo 體積快速膨脹，且 Git 歷史無法輕易縮減。

### 建議做法

1. **改用 GitHub Releases 掛載執行檔**（推薦）
   - 將 `PythonMQTTPlayer-EmbeddedAudio-vX.X.X/` 加入 `.gitignore`
   - 打包後把 exe 上傳到對應版本的 Release 附件
   - 專案內可用 `upload_release.py` 協助上傳

2. **導入 Git LFS**
   ```bash
   git lfs install
   git lfs track "*.exe"
   git add .gitattributes
   ```
   注意：LFS 有免費儲存與流量配額限制。

> 若沿用現況（直接 commit exe），請留意 clone 時間與 repo 容量會持續增加。

## 給下一位開發者：如何快速上手

1. **先讀 `CLAUDE.md`**：訊息格式、API 端點、打包指令、目錄結構等「規則性」資訊都寫在那裡，這份 README 著重「脈絡」與「為什麼」。
2. **`app.py` 是唯一的後端檔案**，所有 API、MQTT 邏輯、播放佇列都在裡面，沒有拆成多個 module——改動前建議先搜尋 `mqtt_logs`、`play_queue_list`、`played_files` 這幾個全域變數，弄清楚狀態怎麼流動。
3. **兩個前端頁面是獨立的靜態 HTML**（`index.html` 主頁、`supplement.html` 補送名單頁），都是單檔 Vue.js（CDN 版，非建置流程），改完不需要跑 build 工具，重新整理瀏覽器就會生效；但**打包成 exe 時兩個檔案都要記得加進 `build.py` 的 `DATA` 清單**（先前就漏掉 `supplement.html` 導致 `/sup` 404，見上方開發歷程）。
4. **MQTT 有兩個主題，職責分離**：`puffin-test` 是原本的刷卡播放指令（不要更動格式），`puffin-control` 是後來新增的燈光控制指令，兩者互不影響。若要新增更多裝置端功能，優先考慮再開新 topic，而不是把邏輯塞進既有格式。
5. **改動燈光模式協定前，先看 `doc/Arduino互動燈光模式說明.md`**，那份文件是跟硬體端的契約（topic 名稱、指令字串、狀態機），App 端跟 Arduino 端是分開的程式碼庫，只靠字串約定，改一邊沒改另一邊會直接壞掉且不會有編譯期錯誤。
6. **`uploads/` 目錄不進版控**，本機開發或現場佈署都是直接放檔案到磁碟上；音檔只支援 `.wav`，其他格式（如 `.m4a`）要先用 ffmpeg 轉檔。
7. **每學年開學前的例行工作**（目前 116 學年度尚未做）：
   - 更新補送名單頁 `supplement.html` 內的姓名/家族名單為當學年度新生名單
   - 更新 `uploads/name/`、`uploads/family/` 音效檔，並重新執行 `python build.py` 產生新的 exe
   - 明年可評估：MQTT 訊息是否能只帶「姓名代號」、改成直接查詢補送名單頁的名單來決定播放內容，取代目前 `name,family` 雙代碼格式，簡化維護負擔
