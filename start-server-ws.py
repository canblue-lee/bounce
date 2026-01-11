import asyncio
import json
import os
import websockets
from http import HTTPStatus

# 取得 Railway 分配的 Port
PORT = int(os.environ.get("PORT", 8080))

# 儲存連線中的手機與電腦
clients = set()

async def handle_websocket(websocket):
    """處理遊戲連線邏輯"""
    clients.add(websocket)
    print(f"📱 新裝置連線 (目前總數: {len(clients)})")
    try:
        async for message in websocket:
            # 廣播訊息給其他所有裝置
            if clients:
                await asyncio.gather(
                    *[client.send(message) for client in clients if client != websocket]
                )
    except Exception as e:
        print(f"⚠️ 連線異常: {e}")
    finally:
        clients.remove(websocket)
        print(f"📉 裝置離開 (目前總數: {len(clients)})")

async def process_request(path, request_headers):
    """處理瀏覽器 HTTP 請求 (讓網址能顯示網頁)"""
    # 如果是 WebSocket 握手請求，交給 handle_websocket 處理
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 否則，讀取並回傳 HTML 網頁
    # 預設路徑導向 game-ws.html
    target_path = path.split('?')[0]
    if target_path == "/" or target_path == "":
        target_path = "/game-ws.html"
    
    file_path = f".{target_path}"
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type = "text/html"
        if file_path.endswith(".js"): mime_type = "application/javascript"
        elif file_path.endswith(".css"): mime_type = "text/css"
        
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": mime_type}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    print(f"🚀 雲端伺服器啟動中...")
    print(f"📍 監聽埠號: {PORT}")
    
    # 啟動混合型伺服器 (HTTP + WebSocket)
    async with websockets.serve(
        handle_websocket, 
        "0.0.0.0", 
        PORT, 
        process_request=process_request
    ):
        await asyncio.Future() # 永久執行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
