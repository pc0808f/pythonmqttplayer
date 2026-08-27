# 新增「互動燈光模式」說明(給 Arduino/ESP32 端)

> App 端已完成(v2.4.0 開發中),四顆按鍵與指令已定案,可依本文件實作。

## 背景

裝置目前開機後的行為完全不變,**不要修改**原本這段邏輯:

- 開機連上 WiFi / MQTT(`MQTTGO.io:1883`)
- 進入等待掃 NFC 卡的迴圈
- 掃到卡後,依原本邏輯 publish `"name,family"` 到 `puffin-test` topic(例如 `"001,01"`)

新功能是完全獨立的一塊,靠一個新的 MQTT topic 驅動,平常不觸發時對原本流程沒有任何影響。

## MQTT 指令協定(App 端已定案)

| 動作 | Topic | Payload | 說明 |
|---|---|---|---|
| 主持人按「進入互動模式」 | `puffin-control` | `INTERACTIVE_START` | 燈全暗,進入等待模式一 |
| 主持人按「模式一」 | `puffin-control` | `MODE1_START` | 跑 8 秒燈效 |
| 主持人按「模式二」 | `puffin-control` | `MODE2_START` | 隨機燈光,結束後自動回到待機刷卡 |
| 主持人按「離開互動模式」 | `puffin-control` | `INTERACTIVE_EXIT` | **緊急退出**,不管目前在哪個子狀態都立刻生效,優先權最高 |

## 新增內容

### 1. 訂閱新 topic

除了原本邏輯不變外,額外訂閱:

```
puffin-control
```

(原本裝置應該只有 publish 到 `puffin-test`,沒有訂閱任何 topic,所以這是全新加的訂閱,不會跟舊邏輯衝突)

### 2. 新增一個獨立的狀態機變數

用一個新的變數控制,不要跟 NFC 掃描相關的變數混用:

```cpp
enum InteractiveState {
  STATE_IDLE,          // 一般待機,NFC 正常掃描(目前唯一的狀態)
  STATE_WAITING_MODE1, // 已進入互動模式,燈已關,等待「模式一」指令
  STATE_MODE1_RUNNING, // 模式一動作中(8秒)
  STATE_WAITING_MODE2, // 模式一結束,等待「模式二」指令
  STATE_MODE2_RUNNING  // 模式二動作中(隨機燈光)
};
InteractiveState interactiveState = STATE_IDLE;
```

### 3. 訊息處理邏輯

在 MQTT callback 裡,用 `if (topic == "puffin-control")` 另外分流處理(跟原本處理 `puffin-test` 的邏輯分開寫,不要共用同一段 if/else,避免互相影響):

```cpp
if (String(topic) == "puffin-control") {
  String cmd = String((char*)payload).substring(0, length);

  // INTERACTIVE_EXIT 優先權最高,不管目前是哪個互動子狀態都要立刻生效
  // 所以放在最前面判斷,且不像其他分支一樣檢查目前狀態
  if (cmd == "INTERACTIVE_EXIT") {
    allLedsOff();
    interactiveState = STATE_IDLE;
    nfcScanningEnabled = true;   // 立刻恢復 NFC 掃描,回到開機後的待機模式
  }
  else if (cmd == "INTERACTIVE_START") {
    allLedsOff();
    interactiveState = STATE_WAITING_MODE1;
    // 建議:暫停 NFC 掃描,避免燈光秀進行中有人刷卡誤觸發播放
    nfcScanningEnabled = false;
  }
  else if (cmd == "MODE1_START" && interactiveState == STATE_WAITING_MODE1) {
    interactiveState = STATE_MODE1_RUNNING;
    mode1StartTime = millis();   // 記錄開始時間,用非阻塞方式計時
  }
  else if (cmd == "MODE2_START" && interactiveState == STATE_WAITING_MODE2) {
    interactiveState = STATE_MODE2_RUNNING;
    mode2StartTime = millis();
  }
  // 其餘狀態下收到不該收到的指令,直接忽略即可,不用特別處理
}
```

### 4. 主迴圈 `loop()` 裡處理計時(重要:不要用 `delay()`)

模式一需要跑滿 8 秒,**請用 `millis()` 做非阻塞計時**,不要用 `delay(8000)`。因為 `delay()` 會卡住整個 loop,期間 MQTT client 沒有機會呼叫 `loop()`/`PubSubClient::loop()`,容易造成連線斷線或漏收訊息。

```cpp
void loop() {
  mqttClient.loop();   // 一定要持續呼叫,維持連線與收訊

  switch (interactiveState) {
    case STATE_IDLE:
      // 原本的 NFC 掃描邏輯,完全不變
      if (nfcScanningEnabled) {
        checkNfcAndPublish();
      }
      break;

    case STATE_MODE1_RUNNING:
      runMode1Animation();  // 燈效,逐 frame 更新即可
      if (millis() - mode1StartTime >= 8000) {
        allLedsOff();  // 或維持在某個結束畫面,依設計決定
        interactiveState = STATE_WAITING_MODE2;
      }
      break;

    case STATE_MODE2_RUNNING:
      runMode2RandomLeds();  // 隨機燈光邏輯
      if (mode2Finished()) {  // 自訂結束條件,例如跑滿 N 秒或跑 N 輪
        allLedsOff();
        interactiveState = STATE_IDLE;
        nfcScanningEnabled = true;  // 恢復掃描,回到開機後的待機模式
      }
      break;

    // STATE_WAITING_MODE1 / STATE_WAITING_MODE2:純等待,不用做事
    default:
      break;
  }
}
```

## 注意事項

1. **不要動原本 `puffin-test` 相關的程式碼**,只加新 topic 的訂閱跟新的 if 分支。
2. **狀態檢查很重要**:例如收到 `MODE1_START` 時要先確認 `interactiveState == STATE_WAITING_MODE1` 才動作,不然主持人手滑連點兩次,或訊息重送,會造成燈效重疊/狀態錯亂。
3. **模式二結束後要自動回到 `STATE_IDLE`**,並記得把 NFC 掃描重新打開(`nfcScanningEnabled = true`),這樣才符合「Arduino 自己回到開機後等待刷卡模式」的需求。
4. 全部用 `millis()` 非阻塞寫法,避免 `delay()` 卡住 MQTT loop。
5. Topic 名稱 `puffin-control` 跟指令字串是跟 App 端約定好的協定,**字串要完全一致**(含大小寫)。
6. **`INTERACTIVE_EXIT` 不檢查目前狀態**,任何時候收到都要立刻關燈、reset 回 `STATE_IDLE`、恢復 NFC 掃描,是主持人的緊急退出鍵,判斷順序要放在其他指令前面。
