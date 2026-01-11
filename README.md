# 🎮 投影遊戲系統 - 手機控制器版

讓手機變成遊戲控制器,投影機顯示遊戲畫面的互動系統!

## 📁 檔案說明

```
game/
├── index.html              # 主遊戲檔案
├── start-server.py         # 伺服器啟動腳本
├── README.md              # 本說明文件
└── QR-codes/              # QR Code 圖片 (稍後生成)
```

## 🚀 快速開始

### 方法 1: 單機測試 (最簡單)

**不需要伺服器,直接測試跨視窗通訊**

1. 用瀏覽器打開 `index.html`
2. 選擇「📱 手機控制器」或「🖥️ 投影顯示」
3. 或直接開兩個視窗:

```
視窗 1 (投影): file:///Users/xingqimac01/Downloads/game/index.html?mode=display
視窗 2 (控制): file:///Users/xingqimac01/Downloads/game/index.html?mode=controller
```

4. 在控制器視窗點擊跳躍按鈕
5. 投影視窗的角色會跳起來!

---

### 方法 2: 手機 + 筆電測試

**需要手機和筆電在同一個 WiFi**

#### Step 1: 啟動伺服器

```bash
cd /Users/xingqimac01/Downloads/game
python3 start-server.py
```

#### Step 2: 連線

終端會顯示連線網址,例如:

```
💻 筆電 (投影顯示):
   http://localhost:8000/index.html?mode=display

📱 手機 (控制器):
   http://192.168.1.100:8000/index.html?mode=controller
```

#### Step 3: 連接投影機

- 筆電用 HDMI 或 AirPlay 連接投影機
- 投影機會鏡像顯示筆電畫面
- 手機變成遊戲控制器!

---

## 🎯 系統架構

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │         │              │         │             │
│   手機      │ ──控制─→ │ localStorage │ ──同步─→ │  投影機     │
│  (控制器)   │         │   (橋接)     │         │  (顯示)     │
│             │ ←─狀態── │              │ ←─更新── │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

### 技術細節

- **通訊方式**: localStorage + StorageEvent
- **延遲**: < 50ms
- **同步頻率**: 每 100ms 更新狀態
- **支援功能**: 觸控震動、防重複跳躍

---

## 🎮 遊戲玩法

1. **跳躍**: 點擊控制器的大按鈕
2. **收集禮物**: 角色碰到禮物 +50 分
3. **平台跳躍**: 每次跳躍 +10 分
4. **自動移動**: 角色會左右擺動

---

## 🔧 故障排除

### 問題 1: 跨視窗不同步

**解決方案**:
- 確保兩個視窗都是相同的瀏覽器 (Chrome/Safari)
- 嘗試重新整理兩個視窗
- 檢查 Console (F12) 是否有錯誤訊息

### 問題 2: 手機連不上伺服器

**解決方案**:
```bash
# 檢查 Mac 的防火牆設定
# 系統偏好設定 > 安全性與隱私 > 防火牆

# 或暫時關閉防火牆測試
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### 問題 3: 伺服器連接埠被占用

**解決方案**:
```bash
# 查看並關閉占用 8000 埠的程序
lsof -ti:8000 | xargs kill -9

# 或修改 start-server.py 中的 PORT = 8000 改成其他數字
```

### 問題 4: 投影畫面延遲

**解決方案**:
- 使用有線 HDMI 連接 (比無線快)
- 關閉其他占用 CPU 的程式
- 降低投影機解析度

---

## 📊 效能建議

### 筆電設定 (投影顯示)
- ✅ 關閉其他不必要的程式
- ✅ 使用有線網路或穩定的 WiFi
- ✅ 插上電源供應器
- ✅ 關閉省電模式

### 手機設定 (控制器)
- ✅ 電量充足 (> 50%)
- ✅ 關閉背景 App
- ✅ 使用相同 WiFi (5GHz 更佳)

---

## 🎨 自訂設定

可以修改 `index.html` 中的變數:

```javascript
// 遊戲難度
gameState.gravity = 0.8;      // 重力 (越大越難)
gameState.jumpForce = -18;    // 跳躍力量 (負數越大跳越高)

// 視覺效果
character.size = 80;          // 角色大小
```

---

## 📱 行動裝置優化

- ✅ 響應式設計 (支援各種螢幕尺寸)
- ✅ 觸控優化 (大按鈕設計)
- ✅ 震動回饋 (支援的裝置)
- ✅ 防止誤觸 (禁用長按選取)

---

## 🚀 進階功能 (未來擴充)

- [ ] WebSocket 即時同步 (更低延遲)
- [ ] 多人對戰模式
- [ ] 關卡編輯器
- [ ] 遊戲紀錄儲存
- [ ] 音效與背景音樂
- [ ] 更多角色與場景

---

## 💡 靈感來源

這個專案受到以下概念啟發:
- 任天堂 Switch 的 Joy-Con 分離設計
- Jackbox Party Pack 的手機控制器
- Web AR 投影互動展覽

---

## 📞 需要協助?

如果遇到問題:
1. 查看瀏覽器 Console (F12)
2. 檢查 `start-server.py` 的終端輸出
3. 確認所有檔案都在正確的資料夾內

---

## 🎉 開始遊戲吧!

```bash
cd /Users/xingqimac01/Downloads/game
python3 start-server.py
```

祝你玩得開心! 🎮✨
