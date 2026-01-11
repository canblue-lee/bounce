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
                # 廣播跳躍訊息給其他所有裝置
                await asyncio.gather(*[client.send(message) for client in clients if client != websocket])
    except: pass
    finally: clients.remove(websocket)

async def process_request(path, request_headers):
    """關鍵：解決 InvalidMessage，讓瀏覽器能正常讀取網頁"""
    # 如果是 WebSocket 升級請求，則不攔截，交給 handle_client
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 預設路徑導向 game-ws.html
    target = path.split('?')[0]
    if target == "/" or target == "": target = "/game-ws.html"
    
    file_path = f".{target}"
    
    # 讀取並回傳檔案
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type = "text/html"
        if file_path.endswith(".js"): mime_type = "application/javascript"
        with open(file_path, "rb") as f:
            return HTTPStatus.OK, {"Content-Type": mime_type}, f.read()
    
    return HTTPStatus.NOT_FOUND, {}, b"404 Not Found"

async def main():
    # 啟動混合型伺服器
    async with websockets.serve(handle_client, "0.0.0.0", PORT, process_request=process_request):
        print(f"🚀 混合伺服器已啟動於 Port {PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
