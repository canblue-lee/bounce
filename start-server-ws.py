import asyncio
import os
import websockets
from http import HTTPStatus

# 取得雲端環境分配的 PORT
PORT = int(os.environ.get("PORT", 8080))
clients = set()

async def handle_client(websocket):
    """處理手機與電腦之間的通訊"""
    clients.add(websocket)
    try:
        async for message in websocket:
            if clients:
                # 廣播跳躍指令
                await asyncio.gather(*[client.send(message) for client in clients if client != websocket])
    except: pass
    finally: clients.remove(websocket)

async def process_request(path, request_headers):
    """解決 InvalidUpgrade 錯誤的核心函數：讓伺服器支援讀取 HTML"""
    # 如果標頭包含 upgrade，代表是要建立 WebSocket 連線，不攔截
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 如果是普通瀏覽網頁，回傳 game-ws.html
    target = path.split('?')[0]
    if target == "/" or target == "": target = "/game-ws.html"
    
    file_path = f".{target}"
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": "text/html"}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    # 啟動混合式伺服器
    async with websockets.serve(handle_client, "0.0.0.0", PORT, process_request=process_request):
        print(f"🚀 伺服器已成功啟動於 Port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
