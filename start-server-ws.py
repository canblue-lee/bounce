import asyncio
import os
import websockets
from http import HTTPStatus

# 自動獲取雲端環境分配的 PORT
PORT = int(os.environ.get("PORT", 8080))
clients = set()

async def handle_client(websocket):
    """處理遊戲連線廣播"""
    clients.add(websocket)
    try:
        async for message in websocket:
            if clients:
                # 將手機的跳躍指令傳給電腦
                await asyncio.gather(*[client.send(message) for client in clients if client != websocket])
    except: pass
    finally: clients.remove(websocket)

async def process_request(path, request_headers):
    """【關鍵修復】解決 missing Connection header 錯誤"""
    # 如果標頭包含 upgrade，代表是要連線玩遊戲，交給 handle_client
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 如果只是普通瀏覽網頁，我們主動回傳 game-ws.html
    target = path.split('?')[0]
    if target == "/" or target == "": target = "/game-ws.html"
    
    file_path = f".{target}"
    
    # 檢查檔案是否存在並回傳
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type = "text/html"
        if file_path.endswith(".js"): mime_type = "application/javascript"
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": mime_type}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    # 啟動混合型伺服器 (HTTP + WebSocket)
    async with websockets.serve(handle_client, "0.0.0.0", PORT, process_request=process_request):
        print(f"🚀 混合伺服器已啟動於 Port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
