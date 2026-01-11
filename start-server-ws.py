#!/usr/bin/env python3
import asyncio
import json
import os
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ 缺少 websockets 套件")
    exit(1)

# Railway 自動分配的 Port
PORT = int(os.environ.get("PORT", 8080))

# 儲存連線中的客戶端
clients = set()

async def handle_client(websocket):
    clients.add(websocket)
    print(f"📱 新連線加入 (目前總數: {len(clients)})")
    try:
        async for message in websocket:
            # 收到訊息後，廣播給所有其他連線者
            if clients:
                await asyncio.gather(
                    *[client.send(message) for client in clients if client != websocket]
                )
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        print(f"📉 連線移除 (目前總數: {len(clients)})")

async def main():
    print(f"🚀 伺服器啟動在 Port: {PORT}")
    # 在雲端必須使用 0.0.0.0 才能接收外部連線
    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
