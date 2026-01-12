import asyncio
import websockets
import json
import os
from aiohttp import web

# 儲存連線的客戶端
rooms = {}

async def handle_websocket(websocket, path):
    room_code = None
    client_type = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data['type'] == 'join':
                room_code = data['room']
                client_type = data['client_type']
                
                if room_code not in rooms:
                    rooms[room_code] = {}
                
                rooms[room_code][client_type] = websocket
                
                await websocket.send(json.dumps({
                    'type': 'connected',
                    'room': room_code,
                    'client_type': client_type
                }))
                
                print(f"{client_type} joined room {room_code}")
                
                if 'projection' in rooms[room_code] and 'controller' in rooms[room_code]:
                    for ws in rooms[room_code].values():
                        if ws.open:
                            await ws.send(json.dumps({
                                'type': 'both_connected',
                                'room': room_code
                            }))
            
            elif data['type'] == 'control':
                if room_code and room_code in rooms:
                    if 'projection' in rooms[room_code]:
                        projection_ws = rooms[room_code]['projection']
                        if projection_ws.open:
                            await projection_ws.send(json.dumps(data))
            
            elif data['type'] == 'game_state':
                if room_code and room_code in rooms:
                    if 'controller' in rooms[room_code]:
                        controller_ws = rooms[room_code]['controller']
                        if controller_ws.open:
                            await controller_ws.send(json.dumps(data))
    
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for {client_type} in room {room_code}")
    finally:
        if room_code and room_code in rooms:
            if client_type in rooms[room_code]:
                del rooms[room_code][client_type]
            
            if not rooms[room_code]:
                del rooms[room_code]
            else:
                for ws in rooms[room_code].values():
                    if ws.open:
                        await ws.send(json.dumps({
                            'type': 'peer_disconnected',
                            'room': room_code
                        }))

# HTTP 處理器
async def handle_projection(request):
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投影遊戲 - 透明背景</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; overflow: hidden; font-family: Arial, sans-serif; }
        #gameCanvas { display: block; width: 100vw; height: 100vh; background: transparent; }
        #connectionStatus {
            position: fixed; top: 20px; left: 20px;
            background: rgba(0, 0, 0, 0.7); color: white;
            padding: 15px 25px; border-radius: 10px;
            font-size: 18px; z-index: 1000;
        }
        .status-dot {
            display: inline-block; width: 12px; height: 12px;
            border-radius: 50%; margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .status-connecting { background: #ffa500; }
        .status-connected { background: #00ff00; }
        .status-disconnected { background: #ff0000; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        #roomCode {
            position: fixed; top: 20px; right: 20px;
            background: rgba(0, 0, 0, 0.7); color: white;
            padding: 15px 25px; border-radius: 10px;
            font-size: 24px; font-weight: bold; z-index: 1000;
        }
        #score {
            position: fixed; top: 80px; right: 20px;
            background: rgba(0, 0, 0, 0.7); color: white;
            padding: 15px 25px; border-radius: 10px;
            font-size: 20px; z-index: 1000;
        }
        #gameOver {
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9); color: white;
            padding: 40px 60px; border-radius: 20px;
            text-align: center; display: none; z-index: 2000;
        }
        #gameOver h1 { font-size: 48px; margin-bottom: 20px; }
        #gameOver p { font-size: 24px; margin: 10px 0; }
    </style>
</head>
<body>
    <div id="connectionStatus">
        <span class="status-dot status-connecting"></span>
        <span id="statusText">等待連線...</span>
    </div>
    <div id="roomCode">房間: <span id="roomCodeText">----</span></div>
    <div id="score">分數: <span id="scoreText">0</span></div>
    <div id="gameOver">
        <h1>遊戲結束!</h1>
        <p>最終分數: <span id="finalScore">0</span></p>
        <p style="font-size: 18px; margin-top: 20px;">請從手機重新開始</p>
    </div>
    <canvas id="gameCanvas"></canvas>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d', { alpha: true });
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        let gameState = 'waiting';
        let score = 0;
        let ws = null;
        let roomCode = '';
        
        const player = {
            x: 100, y: canvas.height - 150, width: 50, height: 80,
            velocityY: 0, velocityX: 0, isJumping: false,
            speed: 5, jumpPower: 15, gravity: 0.8
        };
        
        let obstacles = [];
        let gifts = [];
        let obstacleSpeed = 5;
        let frameCount = 0;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host);
            
            ws.onopen = () => {
                console.log('WebSocket 連線成功');
                updateStatus('connecting', '等待房間代碼...');
                roomCode = 'ROOM' + Math.floor(Math.random() * 10000).toString().padStart(4, '0');
                document.getElementById('roomCodeText').textContent = roomCode;
                ws.send(JSON.stringify({
                    type: 'join',
                    room: roomCode,
                    client_type: 'projection'
                }));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'connected') {
                    console.log('已加入房間:', data.room);
                    updateStatus('connecting', '等待手機連線...');
                }
                if (data.type === 'both_connected') {
                    console.log('手機已連線!');
                    updateStatus('connected', '已連線');
                    startGame();
                }
                if (data.type === 'control') {
                    handleControl(data);
                }
                if (data.type === 'peer_disconnected') {
                    updateStatus('disconnected', '手機已斷線');
                    pauseGame();
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket 錯誤:', error);
                updateStatus('disconnected', '連線錯誤');
            };
            
            ws.onclose = () => {
                console.log('WebSocket 連線關閉');
                updateStatus('disconnected', '連線中斷');
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        function updateStatus(status, text) {
            const dot = document.querySelector('.status-dot');
            dot.className = 'status-dot status-' + status;
            document.getElementById('statusText').textContent = text;
        }
        
        function handleControl(data) {
            if (gameState !== 'playing') return;
            switch(data.action) {
                case 'left': player.velocityX = -player.speed; break;
                case 'right': player.velocityX = player.speed; break;
                case 'jump':
                    if (!player.isJumping) {
                        player.velocityY = -player.jumpPower;
                        player.isJumping = true;
                    }
                    break;
                case 'jump_high':
                    if (!player.isJumping) {
                        player.velocityY = -player.jumpPower * 1.5;
                        player.isJumping = true;
                    }
                    break;
                case 'stop_horizontal': player.velocityX = 0; break;
                case 'pause': pauseGame(); break;
                case 'resume': resumeGame(); break;
                case 'exit': endGame(); break;
            }
        }
        
        function startGame() {
            gameState = 'playing';
            score = 0;
            obstacles = [];
            gifts = [];
            player.x = 100;
            player.y = canvas.height - 150;
            player.velocityY = 0;
            player.velocityX = 0;
            player.isJumping = false;
            document.getElementById('gameOver').style.display = 'none';
            gameLoop();
        }
        
        function pauseGame() {
            if (gameState === 'playing') gameState = 'paused';
        }
        
        function resumeGame() {
            if (gameState === 'paused') {
                gameState = 'playing';
                gameLoop();
            }
        }
        
        function endGame() {
            gameState = 'gameover';
            document.getElementById('finalScore').textContent = score;
            document.getElementById('gameOver').style.display = 'block';
        }
        
        function drawPlayer() {
            ctx.save();
            ctx.fillStyle = '#DC143C';
            ctx.fillRect(player.x, player.y + 30, player.width, 50);
            ctx.fillStyle = '#FFD6A5';
            ctx.beginPath();
            ctx.arc(player.x + player.width/2, player.y + 20, 20, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#DC143C';
            ctx.beginPath();
            ctx.moveTo(player.x + player.width/2 - 15, player.y + 5);
            ctx.lineTo(player.x + player.width/2 + 15, player.y + 5);
            ctx.lineTo(player.x + player.width/2, player.y - 20);
            ctx.closePath();
            ctx.fill();
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(player.x + player.width/2, player.y - 20, 5, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = 'white';
            ctx.fillRect(player.x + player.width/2 - 15, player.y + 5, 30, 5);
            ctx.fillStyle = 'white';
            ctx.fillRect(player.x + player.width/2 - 10, player.y + 25, 20, 10);
            ctx.fillStyle = '#000';
            ctx.fillRect(player.x, player.y + 50, player.width, 8);
            ctx.fillStyle = '#FFD700';
            ctx.fillRect(player.x + player.width/2 - 8, player.y + 48, 16, 12);
            ctx.fillStyle = '#000';
            ctx.fillRect(player.x + 5, player.y + 80, 15, 8);
            ctx.fillRect(player.x + 30, player.y + 80, 15, 8);
            ctx.restore();
        }
        
        function drawObstacles() {
            ctx.fillStyle = '#333';
            obstacles.forEach(obs => {
                ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
            });
        }
        
        function drawGifts() {
            gifts.forEach(gift => {
                ctx.fillStyle = '#DC143C';
                ctx.fillRect(gift.x, gift.y, gift.width, gift.height);
                ctx.fillStyle = '#FFD700';
                ctx.fillRect(gift.x + gift.width/2 - 2, gift.y, 4, gift.height);
                ctx.fillRect(gift.x, gift.y + gift.height/2 - 2, gift.width, 4);
                ctx.fillStyle = '#FFD700';
                ctx.beginPath();
                ctx.arc(gift.x + gift.width/2 - 8, gift.y, 6, 0, Math.PI * 2);
                ctx.arc(gift.x + gift.width/2 + 8, gift.y, 6, 0, Math.PI * 2);
                ctx.fill();
            });
        }
        
        function spawnObstacle() {
            const height = 30 + Math.random() * 50;
            obstacles.push({
                x: canvas.width,
                y: canvas.height - height - 50,
                width: 40,
                height: height
            });
        }
        
        function spawnGift() {
            gifts.push({
                x: canvas.width,
                y: canvas.height - 150 - Math.random() * 200,
                width: 30,
                height: 30
            });
        }
        
        function checkCollision(rect1, rect2) {
            return rect1.x < rect2.x + rect2.width &&
                   rect1.x + rect1.width > rect2.x &&
                   rect1.y < rect2.y + rect2.height &&
                   rect1.y + rect1.height > rect2.y;
        }
        
        function update() {
            if (gameState !== 'playing') return;
            player.x += player.velocityX;
            player.y += player.velocityY;
            player.velocityY += player.gravity;
            if (player.x < 0) player.x = 0;
            if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;
            const ground = canvas.height - 50;
            if (player.y + player.height >= ground) {
                player.y = ground - player.height;
                player.velocityY = 0;
                player.isJumping = false;
            }
            frameCount++;
            if (frameCount % 120 === 0) spawnObstacle();
            if (frameCount % 200 === 0) spawnGift();
            obstacles = obstacles.filter(obs => {
                obs.x -= obstacleSpeed;
                if (checkCollision(player, obs)) {
                    endGame();
                    return false;
                }
                return obs.x + obs.width > 0;
            });
            gifts = gifts.filter(gift => {
                gift.x -= obstacleSpeed;
                if (checkCollision(player, gift)) {
                    score += 10;
                    document.getElementById('scoreText').textContent = score;
                    return false;
                }
                return gift.x + gift.width > 0;
            });
            if (frameCount % 600 === 0) obstacleSpeed += 0.5;
        }
        
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, canvas.height - 50);
            ctx.lineTo(canvas.width, canvas.height - 50);
            ctx.stroke();
            drawPlayer();
            drawObstacles();
            drawGifts();
        }
        
        function gameLoop() {
            if (gameState === 'playing') {
                update();
                draw();
                requestAnimationFrame(gameLoop);
            }
        }
        
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
        
        connectWebSocket();
    </script>
</body>
</html>
"""
    return web.Response(text=html_content, content_type='text/html')

async def handle_controller(request):
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>遊戲手把</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: Arial, sans-serif; overflow: hidden; touch-action: none; }
        #connectionPanel {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.95); display: flex;
            flex-direction: column; justify-content: center; align-items: center; z-index: 10000;
        }
        #connectionPanel h1 { color: white; font-size: 32px; margin-bottom: 30px; }
        #roomCodeInput {
            width: 300px; padding: 15px; font-size: 24px; text-align: center;
            border: 3px solid #667eea; border-radius: 10px; background: white; margin-bottom: 20px;
        }
        #connectBtn {
            width: 300px; padding: 15px; font-size: 20px;
            background: #667eea; color: white; border: none;
            border-radius: 10px; cursor: pointer; font-weight: bold;
        }
        #connectBtn:active { background: #5568d3; }
        #connectionStatus { color: white; font-size: 16px; margin-top: 20px; }
        .status-dot {
            display: inline-block; width: 10px; height: 10px;
            border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;
        }
        .status-connecting { background: #ffa500; }
        .status-connected { background: #00ff00; }
        .status-disconnected { background: #ff0000; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        #controller { display: none; width: 100vw; height: 100vh; padding: 20px; }
        #topBar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        #roomInfo {
            background: rgba(255, 255, 255, 0.2); padding: 10px 20px;
            border-radius: 20px; color: white; font-size: 18px; font-weight: bold;
        }
        #exitBtn {
            background: rgba(255, 0, 0, 0.7); color: white; border: none;
            padding: 10px 20px; border-radius: 20px; font-size: 16px; font-weight: bold;
        }
        #controlArea {
            height: calc(100vh - 100px); display: grid;
            grid-template-columns: 1fr 1fr; gap: 20px;
        }
        #leftSide, #rightSide {
            display: flex; flex-direction: column;
            justify-content: center; align-items: center;
        }
        #dpad { position: relative; width: 180px; height: 180px; margin-bottom: 20px; }
        .dpad-btn {
            position: absolute; background: rgba(255, 255, 255, 0.9);
            border: 3px solid #333; width: 60px; height: 60px;
            display: flex; justify-content: center; align-items: center;
            font-size: 28px; cursor: pointer; user-select: none;
        }
        .dpad-btn:active { background: #667eea; color: white; }
        #dpad-up { top: 0; left: 60px; border-radius: 15px 15px 0 0; }
        #dpad-down { bottom: 0; left: 60px; border-radius: 0 0 15px 15px; }
        #dpad-left { left: 0; top: 60px; border-radius: 15px 0 0 15px; }
        #dpad-right { right: 0; top: 60px; border-radius: 0 15px 15px 0; }
        #dpad-center { left: 60px; top: 60px; background: #333; border-radius: 50%; pointer-events: none; }
        #actionBtns { display: flex; gap: 30px; margin-bottom: 20px; }
        .action-btn {
            width: 80px; height: 80px; border-radius: 50%;
            border: 4px solid #333; background: rgba(255, 255, 255, 0.9);
            font-size: 32px; font-weight: bold; color: #333;
            cursor: pointer; user-select: none;
            display: flex; justify-content: center; align-items: center;
        }
        .action-btn:active { background: #DC143C; color: white; }
        #btnA { background: rgba(255, 100, 100, 0.9); }
        #btnB { background: rgba(255, 200, 100, 0.9); }
        #pauseBtn {
            width: 120px; padding: 15px;
            background: rgba(255, 255, 255, 0.9);
            border: 3px solid #333; border-radius: 25px;
            font-size: 18px; font-weight: bold;
            cursor: pointer; user-select: none;
        }
        #pauseBtn:active { background: #FFD700; }
        .label { color: white; font-size: 14px; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <div id="connectionPanel">
        <h1>🎮 遊戲手把</h1>
        <input type="text" id="roomCodeInput" placeholder="輸入房間代碼" maxlength="8">
        <button id="connectBtn">連線</button>
        <div id="connectionStatus">
            <span class="status-dot status-disconnected"></span>
            <span id="statusText">未連線</span>
        </div>
    </div>
    <div id="controller">
        <div id="topBar">
            <div id="roomInfo">房間: <span id="currentRoom">----</span></div>
            <button id="exitBtn">退出</button>
        </div>
        <div id="controlArea">
            <div id="leftSide">
                <div id="dpad">
                    <div class="dpad-btn" id="dpad-up">▲</div>
                    <div class="dpad-btn" id="dpad-down">▼</div>
                    <div class="dpad-btn" id="dpad-left">◀</div>
                    <div class="dpad-btn" id="dpad-right">▶</div>
                    <div class="dpad-btn" id="dpad-center"></div>
                </div>
                <div class="label">方向鍵</div>
            </div>
            <div id="rightSide">
                <div id="actionBtns">
                    <div class="action-btn" id="btnB">B</div>
                    <div class="action-btn" id="btnA">A</div>
                </div>
                <div class="label">A: 跳躍 | B: 高跳</div>
                <div style="margin-top: 40px;">
                    <button id="pauseBtn">⏸ 暫停</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        let ws = null;
        let roomCode = '';
        let isConnected = false;
        let isPaused = false;
        
        const connectionPanel = document.getElementById('connectionPanel');
        const controller = document.getElementById('controller');
        const roomCodeInput = document.getElementById('roomCodeInput');
        const connectBtn = document.getElementById('connectBtn');
        const statusText = document.getElementById('statusText');
        const statusDot = document.querySelector('.status-dot');
        const currentRoom = document.getElementById('currentRoom');
        
        connectBtn.addEventListener('click', () => {
            roomCode = roomCodeInput.value.trim().toUpperCase();
            if (roomCode.length < 4) {
                alert('請輸入有效的房間代碼');
                return;
            }
            connectWebSocket();
        });
        
        function connectWebSocket() {
            updateStatus('connecting', '連線中...');
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host);
            
            ws.onopen = () => {
                console.log('WebSocket 連線成功');
                ws.send(JSON.stringify({
                    type: 'join',
                    room: roomCode,
                    client_type: 'controller'
                }));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'connected') {
                    console.log('已加入房間:', data.room);
                    updateStatus('connecting', '等待投影端...');
                }
                if (data.type === 'both_connected') {
                    console.log('投影端已連線!');
                    updateStatus('connected', '已連線');
                    isConnected = true;
                    showController();
                }
                if (data.type === 'peer_disconnected') {
                    updateStatus('disconnected', '投影端已斷線');
                    isConnected = false;
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket 錯誤:', error);
                updateStatus('disconnected', '連線錯誤');
            };
            
            ws.onclose = () => {
                console.log('WebSocket 連線關閉');
                updateStatus('disconnected', '連線中斷');
                isConnected = false;
            };
        }
        
        function updateStatus(status, text) {
            statusDot.className = 'status-dot status-' + status;
            statusText.textContent = text;
        }
        
        function showController() {
            connectionPanel.style.display = 'none';
            controller.style.display = 'block';
            currentRoom.textContent = roomCode;
        }
        
        function sendControl(action) {
            if (ws && ws.readyState === WebSocket.OPEN && isConnected) {
                ws.send(JSON.stringify({
                    type: 'control',
                    action: action,
                    timestamp: Date.now()
                }));
            }
        }
        
        const dpadBtns = {
            'dpad-up': 'up',
            'dpad-down': 'down',
            'dpad-left': 'left',
            'dpad-right': 'right'
        };
        
        Object.keys(dpadBtns).forEach(id => {
            const btn = document.getElementById(id);
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                sendControl(dpadBtns[id]);
            });
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                if (id === 'dpad-left' || id === 'dpad-right') {
                    sendControl('stop_horizontal');
                }
            });
            btn.addEventListener('mousedown', () => {
                sendControl(dpadBtns[id]);
            });
            btn.addEventListener('mouseup', () => {
                if (id === 'dpad-left' || id === 'dpad-right') {
                    sendControl('stop_horizontal');
                }
            });
        });
        
        document.getElementById('btnA').addEventListener('touchstart', (e) => {
            e.preventDefault();
            sendControl('jump');
        });
        document.getElementById('btnA').addEventListener('mousedown', () => {
            sendControl('jump');
        });
        
        document.getElementById('btnB').addEventListener('touchstart', (e) => {
            e.preventDefault();
            sendControl('jump_high');
        });
        document.getElementById('btnB').addEventListener('mousedown', () => {
            sendControl('jump_high');
        });
        
        document.getElementById('pauseBtn').addEventListener('click', () => {
            isPaused = !isPaused;
            const btn = document.getElementById('pauseBtn');
            if (isPaused) {
                btn.textContent = '▶ 繼續';
                sendControl('pause');
            } else {
                btn.textContent = '⏸ 暫停';
                sendControl('resume');
            }
        });
        
        document.getElementById('exitBtn').addEventListener('click', () => {
            if (confirm('確定要退出遊戲嗎?')) {
                sendControl('exit');
                if (ws) ws.close();
                location.reload();
            }
        });
        
        document.body.addEventListener('touchmove', (e) => {
            e.preventDefault();
        }, { passive: false });
    </script>
</body>
</html>
"""
    return web.Response(text=html_content, content_type='text/html')

async def handle_index(request):
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投影遊戲系統</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 36px;
        }
        .option {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-decoration: none;
            display: block;
            transition: transform 0.2s;
        }
        .option:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .option h2 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .option p {
            font-size: 16px;
            opacity: 0.9;
        }
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
</html>
"""
    return web.Response(text=html_content, content_type='text/html')

async def init_app():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/projection', handle_projection)
    app.router.add_get('/controller', handle_controller)
    return app

async def main():
    # 啟動 HTTP 伺服器
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    PORT = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"HTTP Server running on port {PORT}")
    
    # 啟動 WebSocket 伺服器 (使用相同的 port)
    print(f"WebSocket Server running on port {PORT}")
    async with websockets.serve(handle_websocket, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
