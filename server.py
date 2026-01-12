import asyncio
import json
import os
from aiohttp import web

# 儲存連線的客戶端
rooms = {}

async def handle_websocket(request):
    """處理 WebSocket 連線"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    room_code = None
    client_type = None
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data['type'] == 'join':
                    room_code = data['room']
                    client_type = data['client_type']
                    
                    if room_code not in rooms:
                        rooms[room_code] = {}
                    
                    rooms[room_code][client_type] = ws
                    
                    await ws.send_json({
                        'type': 'connected',
                        'room': room_code,
                        'client_type': client_type
                    })
                    
                    print(f"{client_type} joined room {room_code}")
                    
                    if 'projection' in rooms[room_code] and 'controller' in rooms[room_code]:
                        for client_ws in rooms[room_code].values():
                            if not client_ws.closed:
                                await client_ws.send_json({
                                    'type': 'both_connected',
                                    'room': room_code
                                })
                
                elif data['type'] == 'control':
                    if room_code and room_code in rooms:
                        if 'projection' in rooms[room_code]:
                            projection_ws = rooms[room_code]['projection']
                            if not projection_ws.closed:
                                await projection_ws.send_json(data)
                
                elif data['type'] == 'game_state':
                    if room_code and room_code in rooms:
                        if 'controller' in rooms[room_code]:
                            controller_ws = rooms[room_code]['controller']
                            if not controller_ws.closed:
                                await controller_ws.send_json(data)
            
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    
    except Exception as e:
        print(f'WebSocket exception: {e}')
    
    finally:
        if room_code and room_code in rooms:
            if client_type in rooms[room_code]:
                del rooms[room_code][client_type]
            
            if not rooms[room_code]:
                del rooms[room_code]
            else:
                for client_ws in rooms[room_code].values():
                    if not client_ws.closed:
                        try:
                            await client_ws.send_json({
                                'type': 'peer_disconnected',
                                'room': room_code
                            })
                        except:
                            pass
    
    return ws

async def handle_index(request):
    """首頁"""
    html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投影遊戲系統</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: Arial, sans-serif; min-height: 100vh;
            display: flex; justify-content: center; align-items: center; padding: 20px;
        }
        .container {
            background: white; border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; font-size: 36px; }
        .option {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 15px; margin-bottom: 20px;
            text-decoration: none; display: block; transition: transform 0.2s;
        }
        .option:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .option h2 { font-size: 24px; margin-bottom: 10px; }
        .option p { font-size: 16px; opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 投影遊戲系統</h1>
        <a href="/projection" class="option">
            <h2>📽️ 投影端</h2>
            <p>在投影機或大螢幕上開啟此頁面</p>
        </a>
        <a href="/controller" class="option">
            <h2>🎮 手機手把</h2>
            <p>在手機上開啟此頁面作為控制器</p>
        </a>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type='text/html')

async def handle_projection(request):
    """投影端頁面"""
    # 這裡放你之前的投影端 HTML (太長了,我會在下一個回覆完整給你)
    html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>投影端</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { background: transparent !important; overflow: hidden; }
        #gameCanvas { display: block; width: 100vw; height: 100vh; background: transparent !important; }
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d', { alpha: true });
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
        
        ws.onopen = () => {
            console.log('Connected');
            ws.send(JSON.stringify({
                type: 'join',
                room: 'TEST123',
                client_type: 'projection'
            }));
        };
        
        ws.onmessage = (event) => {
            console.log('Message:', event.data);
        };
        
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#DC143C';
            ctx.fillRect(100, 100, 50, 80);
        }
        
        setInterval(draw, 16);
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type='text/html')

async def handle_controller(request):
    """控制端頁面"""
    html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>手機手把</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               display: flex; justify-content: center; align-items: center; 
               min-height: 100vh; color: white; }
        button { padding: 20px 40px; font-size: 20px; margin: 10px; }
    </style>
</head>
<body>
    <div>
        <h1>🎮 手機手把</h1>
        <button onclick="connect()">連線</button>
        <button onclick="jump()">跳躍</button>
    </div>
    <script>
        let ws;
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
            ws.onopen = () => {
                console.log('Connected');
                ws.send(JSON.stringify({
                    type: 'join',
                    room: 'TEST123',
                    client_type: 'controller'
                }));
            };
        }
        function jump() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'control', action: 'jump' }));
            }
        }
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type='text/html')

def main():
    """主程式入口"""
    app = web.Application()
    
    # 路由
    app.router.add_get('/', handle_index)
    app.router.add_get('/projection', handle_projection)
    app.router.add_get('/controller', handle_controller)
    app.router.add_get('/ws', handle_websocket)
    
    # 啟動伺服器
    PORT = int(os.environ.get('PORT', 10000))
    print(f"🚀 Server starting on port {PORT}")
    
    web.run_app(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
