async def handle_projection(request):
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投影遊戲 - 透明背景</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        html {
            background: transparent !important;
        }
        
        body { 
            background: transparent !important;
            overflow: hidden; 
            font-family: Arial, sans-serif;
        }
        
        #gameCanvas { 
            display: block; 
            width: 100vw; 
            height: 100vh; 
            background: transparent !important;
        }
        
        #connectionStatus {
            position: fixed; 
            top: 20px; 
            left: 20px;
            background: rgba(0, 0, 0, 0.7); 
            color: white;
            padding: 15px 25px; 
            border-radius: 10px;
            font-size: 18px; 
            z-index: 1000;
        }
        
        .status-dot {
            display: inline-block; 
            width: 12px; 
            height: 12px;
            border-radius: 50%; 
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        
        .status-connecting { background: #ffa500; }
        .status-connected { background: #00ff00; }
        .status-disconnected { background: #ff0000; }
        
        @keyframes pulse { 
            0%, 100% { opacity: 1; } 
            50% { opacity: 0.5; } 
        }
        
        #roomCode {
            position: fixed; 
            top: 20px; 
            right: 20px;
            background: rgba(0, 0, 0, 0.7); 
            color: white;
            padding: 15px 25px; 
            border-radius: 10px;
            font-size: 24px; 
            font-weight: bold; 
            z-index: 1000;
        }
        
        #score {
            position: fixed; 
            top: 80px; 
            right: 20px;
            background: rgba(0, 0, 0, 0.7); 
            color: white;
            padding: 15px 25px; 
            border-radius: 10px;
            font-size: 20px; 
            z-index: 1000;
        }
        
        #gameOver {
            position: fixed; 
            top: 50%; 
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9); 
            color: white;
            padding: 40px 60px; 
            border-radius: 20px;
            text-align: center; 
            display: none; 
            z-index: 2000;
        }
        
        #gameOver h1 { 
            font-size: 48px; 
            margin-bottom: 20px; 
        }
        
        #gameOver p { 
            font-size: 24px; 
            margin: 10px 0; 
        }
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
        
        // 設定 canvas 大小
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        let gameState = 'waiting';
        let score = 0;
        let ws = null;
        let roomCode = '';
        
        const player = {
            x: 100, 
            y: canvas.height - 150, 
            width: 50, 
            height: 80,
            velocityY: 0, 
            velocityX: 0, 
            isJumping: false,
            speed: 5, 
            jumpPower: 15, 
            gravity: 0.8
        };
        
        let obstacles = [];
        let gifts = [];
        let obstacleSpeed = 5;
        let frameCount = 0;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
            
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
                case 'left': 
                    player.velocityX = -player.speed; 
                    break;
                case 'right': 
                    player.velocityX = player.speed; 
                    break;
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
                case 'stop_horizontal': 
                    player.velocityX = 0; 
                    break;
                case 'pause': 
                    pauseGame(); 
                    break;
                case 'resume': 
                    resumeGame(); 
                    break;
                case 'exit': 
                    endGame(); 
                    break;
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
            
            // 身體 (紅色)
            ctx.fillStyle = '#DC143C';
            ctx.fillRect(player.x, player.y + 30, player.width, 50);
            
            // 頭部 (膚色)
            ctx.fillStyle = '#FFD6A5';
            ctx.beginPath();
            ctx.arc(player.x + player.width/2, player.y + 20, 20, 0, Math.PI * 2);
            ctx.fill();
            
            // 聖誕帽
            ctx.fillStyle = '#DC143C';
            ctx.beginPath();
            ctx.moveTo(player.x + player.width/2 - 15, player.y + 5);
            ctx.lineTo(player.x + player.width/2 + 15, player.y + 5);
            ctx.lineTo(player.x + player.width/2, player.y - 20);
            ctx.closePath();
            ctx.fill();
            
            // 帽子球球
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(player.x + player.width/2, player.y - 20, 5, 0, Math.PI * 2);
            ctx.fill();
            
            // 白色帽邊
            ctx.fillStyle = 'white';
            ctx.fillRect(player.x + player.width/2 - 15, player.y + 5, 30, 5);
            
            // 白鬍子
            ctx.fillStyle = 'white';
            ctx.fillRect(player.x + player.width/2 - 10, player.y + 25, 20, 10);
            
            // 黑帶子
            ctx.fillStyle = '#000';
            ctx.fillRect(player.x, player.y + 50, player.width, 8);
            
            // 金色帶扣
            ctx.fillStyle = '#FFD700';
            ctx.fillRect(player.x + player.width/2 - 8, player.y + 48, 16, 12);
            
            // 腳
            ctx.fillStyle = '#000';
            ctx.fillRect(player.x + 5, player.y + 80, 15, 8);
            ctx.fillRect(player.x + 30, player.y + 80, 15, 8);
            
            ctx.restore();
        }
        
        function drawObstacles() {
            obstacles.forEach(obs => {
                // 障礙物 - 深灰色方塊
                ctx.fillStyle = '#444';
                ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
                
                // 加個邊框讓它更明顯
                ctx.strokeStyle = '#222';
                ctx.lineWidth = 2;
                ctx.strokeRect(obs.x, obs.y, obs.width, obs.height);
            });
        }
        
        function drawGifts() {
            gifts.forEach(gift => {
                // 禮物盒 - 紅色
                ctx.fillStyle = '#DC143C';
                ctx.fillRect(gift.x, gift.y, gift.width, gift.height);
                
                // 金色絲帶 - 垂直
                ctx.fillStyle = '#FFD700';
                ctx.fillRect(gift.x + gift.width/2 - 2, gift.y, 4, gift.height);
                
                // 金色絲帶 - 水平
                ctx.fillRect(gift.x, gift.y + gift.height/2 - 2, gift.width, 4);
                
                // 蝴蝶結
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
            
            // 更新玩家位置
            player.x += player.velocityX;
            player.y += player.velocityY;
            player.velocityY += player.gravity;
            
            // 邊界限制
            if (player.x < 0) player.x = 0;
            if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;
            
            // 地面檢測
            const ground = canvas.height - 50;
            if (player.y + player.height >= ground) {
                player.y = ground - player.height;
                player.velocityY = 0;
                player.isJumping = false;
            }
            
            // 生成障礙物和禮物
            frameCount++;
            if (frameCount % 120 === 0) spawnObstacle();
            if (frameCount % 200 === 0) spawnGift();
            
            // 更新障礙物
            obstacles = obstacles.filter(obs => {
                obs.x -= obstacleSpeed;
                if (checkCollision(player, obs)) {
                    endGame();
                    return false;
                }
                return obs.x + obs.width > 0;
            });
            
            // 更新禮物
            gifts = gifts.filter(gift => {
                gift.x -= obstacleSpeed;
                if (checkCollision(player, gift)) {
                    score += 10;
                    document.getElementById('scoreText').textContent = score;
                    return false;
                }
                return gift.x + gift.width > 0;
            });
            
            // 增加難度
            if (frameCount % 600 === 0) obstacleSpeed += 0.5;
        }
        
        function draw() {
            // 完全清除 canvas - 不填充任何顏色
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // 只繪製遊戲元素,不繪製任何背景
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
