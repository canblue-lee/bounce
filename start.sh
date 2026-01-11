#!/bin/bash

# 投影遊戲系統 - 快速啟動腳本

echo "=================================="
echo "🎮 投影遊戲系統 - 快速啟動"
echo "=================================="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "index.html" ]; then
    echo "❌ 錯誤: 找不到 index.html"
    echo "請確保在 game 資料夾內執行此腳本"
    exit 1
fi

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 找不到 Python 3"
    echo "請先安裝 Python 3: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ 檔案檢查完成"
echo ""

# 詢問啟動模式
echo "請選擇啟動模式:"
echo "1) 啟動伺服器 (手機+筆電測試)"
echo "2) 在瀏覽器開啟 (單機測試)"
echo ""
read -p "請輸入選項 (1 或 2): " choice

case $choice in
    1)
        echo ""
        echo "🚀 啟動伺服器中..."
        python3 start-server.py
        ;;
    2)
        echo ""
        echo "🌐 在瀏覽器開啟遊戲..."
        
        # 取得當前目錄的完整路徑
        CURRENT_DIR=$(pwd)
        
        # 開啟投影顯示
        open "file://${CURRENT_DIR}/index.html?mode=display" &
        sleep 1
        
        # 開啟控制器
        open "file://${CURRENT_DIR}/index.html?mode=controller" &
        
        echo "✅ 已在瀏覽器開啟兩個視窗"
        echo "   - 投影顯示 (遊戲畫面)"
        echo "   - 控制器 (手機介面)"
        ;;
    *)
        echo "❌ 無效的選項"
        exit 1
        ;;
esac
