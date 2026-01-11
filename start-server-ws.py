#!/usr/bin/env python3
"""
投影遊戲 - WebSocket 即時同步伺服器 (Railway 優化版)
"""

import asyncio
import json
import os
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ 缺少 websockets 套件，請確保根目錄有 requirements.txt 並寫入 websockets")
    exit(1)

# Railway 會透過環境變數提供 PORT，若沒提供則預設使用 8080
WS_PORT = int(os.environ.get("PORT", 8080))

# 儲存所有連線的客戶端
clients = set()

async def handle_client(websocket):
    """處理 WebSocket 連線"""
    # 加入新客戶端
    clients.add(websocket)
    print(f"📱 新連線加入 (目前總數: {len(clients)})")
    
    try:
        async for message in websocket:
            # 收到訊息後，廣播給所有「其他」客戶端
            data = json.loads(message)
            print(f"📩 收到訊息: {data.get('type')}")
            
            # 廣播訊息
            if clients:
                await asyncio.gather(
                    *[client.send(message) for client in clients if client != websocket]
                )
    except websockets.exceptions.ConnectionClosed:
        print("📴 連線已關閉")
    finally:
        # 移除斷開的客戶端
        clients.remove(websocket)
        print(f"📉 連線移除 (目前總數: {len(clients)})")

async def main():
    """啟動 WebSocket 伺服器"""
    print("=" * 60)
    print(f"🚀 Railway 部署環境偵測成功")
    print(f"🔌 WebSocket 伺服器將執行在 Port: {WS_PORT}")
    print("=" * 60)
    
    # 在 Railway 必須監聽 0.0.0.0
    async with websockets.serve(handle_client, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # 永遠執行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 伺服器停止")