import asyncio
import json
import os
import websockets
from http import HTTPStatus

# 取得 Railway 分配的 Port
PORT = int(os.environ.get("PORT", 8080))

# 儲存連線中的客戶端
clients = set()

async def handle_websocket(websocket):
    """處理遊戲控制通訊"""
    clients.add(websocket)
    print(f"📱 新連線加入 (總數: {len(clients)})")
    try:
        async for message in websocket:
            # 廣播訊息給其他連線者
            if clients:
                await asyncio.gather(
                    *[client.send(message) for client in clients if client != websocket]
                )
    except:
        pass
    finally:
        clients.remove(websocket)
        print(f"📉 連線移除")

async def process_request(path, request_headers):
    """處理瀏覽器讀取網頁請求 (讓網址能打開 HTML)"""
    # 如果是 WebSocket 握手請求，交給 handle_websocket 處理
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 預設導向 game-ws.html
    target_path = path.split('?')[0]
    if target_path == "/" or target_path == "":
        target_path = "/game-ws.html"
    
    file_path = f".{target_path}"
    
    # 讀取並回傳 HTML 檔案
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type = "text/html"
        if file_path.endswith(".js"): mime_type = "application/javascript"
        elif file_path.endswith(".css"): mime_type = "text/css"
        
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": mime_type}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    print(f"🚀 伺服器啟動中，監聽埠號: {PORT}")
    # 同時開啟 HTTP 與 WebSocket 支援
    async with websockets.serve(
        handle_websocket, 
        "0.0.0.0", 
        PORT, 
        process_request=process_request
    ):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
