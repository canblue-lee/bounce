import asyncio
import json
import os
import websockets
from http import HTTPStatus

# 取得 Railway 分配的 Port
PORT = int(os.environ.get("PORT", 8080))

clients = set()

# 處理 WebSocket 遊戲邏輯
async def handle_client(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            if clients:
                await asyncio.gather(
                    *[client.send(message) for client in clients if client != websocket]
                )
    except:
        pass
    finally:
        clients.add(websocket)

# 處理 HTTP 請求 (讓網址能顯示網頁)
async def process_request(path, request_headers):
    # 如果路徑是 WebSocket 連線，不攔截
    if "Upgrade" in request_headers.get("Connection", ""):
        return None
    
    # 否則，讀取對應的 HTML 檔案回傳
    path = path.split('?')[0] # 移除參數
    if path == "/": path = "/game-ws.html"
    
    file_path = f".{path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": "text/html"}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    # 同時監聽 HTTP 與 WebSocket
    async with websockets.serve(
        handle_client, 
        "0.0.0.0", 
        PORT, 
        process_request=process_request
    ):
        print(f"🚀 遊戲伺服器已啟動於 Port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
