#!/usr/bin/env python3
import asyncio
import json
import os
from pathlib import Path

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("請安裝 websockets: pip install websockets")
    exit(1)

# 環境變數取得 Port (Render 會提供)
PORT = int(os.environ.get("PORT", 8080))

# 儲存連線的客戶端
clients = set()

async def handle_websocket(websocket):
    """處理 WebSocket 連線"""
    clients.add(websocket)
    client_ip = websocket.remote_address[0] if hasattr(websocket, 'remote_address') else 'unknown'
    client_role = 'unknown'
    print(f"🔌 新裝置連線: {client_ip} (目前 {len(clients)} 個裝置)")
    
    try:
        async for message in websocket:
            # 解析訊息
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                # 記錄客戶端角色
                if msg_type == 'register':
                    client_role = data.get('role', 'unknown')
                    print(f"📝 裝置註冊: {client_ip} 角色={client_role}")
                
                # 相機畫面只記錄統計,不輸出完整內容
                if msg_type == 'cameraFrame':
                    data_size = len(message) / 1024  # KB
                    print(f"📸 相機畫面: {data_size:.1f}KB 來自 {client_ip}")
                else:
                    print(f"📨 收到訊息: {msg_type} 來自 {client_ip} ({client_role})")
                
                # 廣播給其他客戶端
                if clients:
                    others = clients - {websocket}
                    if others:
                        await asyncio.gather(
                            *[client.send(message) for client in others],
                            return_exceptions=True
                        )
                        
                        # 只在非相機畫面時顯示廣播訊息
                        if msg_type != 'cameraFrame':
                            print(f"📤 已廣播給 {len(others)} 個裝置")
                            
            except json.JSONDecodeError:
                print(f"⚠️ 無效的訊息格式")
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    finally:
        if websocket in clients:
            clients.remove(websocket)
        print(f"🔌 裝置離線: {client_ip} ({client_role}) - 剩餘 {len(clients)} 個裝置")

async def handle_http(path, request_headers):
    """處理 HTTP 請求,提供靜態檔案"""
    # WebSocket 連線直接返回 None,交給 WebSocket handler
    if "upgrade" in request_headers.get("connection", "").lower():
        return None
    
    # 處理 HTTP 檔案請求
    if path == "/" or path == "":
        path = "/game-ws.html"
    
    # 移除查詢參數
    file_path = path.split('?')[0].lstrip('/')
    
    # 檢查檔案是否存在
    if Path(file_path).exists() and Path(file_path).is_file():
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 判斷 Content-Type
            content_type = 'text/html; charset=utf-8'
            if file_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif file_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            
            print(f"✅ 提供檔案: {file_path}")
            return 200, {"Content-Type": content_type}, content
        except Exception as e:
            print(f"❌ 讀取檔案失敗: {e}")
            return 500, {}, b"Internal Server Error"
    
    print(f"❌ 檔案不存在: {file_path}")
    return 404, {}, b"404 Not Found"

async def main():
    """啟動伺服器"""
    print("=" * 60)
    print("🎮 投影遊戲系統 - WebSocket 伺服器")
    print("=" * 60)
    print(f"🌐 Port: {PORT}")
    print(f"📁 工作目錄: {Path.cwd()}")
    print("=" * 60)
    
    # 列出可用檔案
    print("\n📂 可用檔案:")
    for file in Path('.').glob('*.html'):
        print(f"   - {file.name}")
    print()
    
    async with serve(
        handle_websocket,
        "0.0.0.0",
        PORT,
        process_request=handle_http
    ):
        print("🚀 伺服器啟動成功!")
        print(f"🔗 請訪問: https://your-app.onrender.com/game-ws.html")
        print("=" * 60)
        await asyncio.Future()  # 持續運行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✅ 伺服器已停止")
