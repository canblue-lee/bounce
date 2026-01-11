#!/usr/bin/env python3
"""
投影遊戲 - 本地伺服器啟動腳本
"""

import http.server
import socketserver
import socket
import os
from pathlib import Path

PORT = 8000

def get_local_ip():
    """取得本機 IP 位址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 允許跨域請求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # 取得當前目錄
    current_dir = Path.cwd()
    
    print("=" * 60)
    print("🎮 投影遊戲系統 - 本地伺服器")
    print("=" * 60)
    print(f"\n📁 伺服器目錄: {current_dir}")
    print(f"🌐 伺服器連接埠: {PORT}")
    
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print("📱 連線網址:")
    print("=" * 60)
    
    print(f"\n💻 筆電 (投影顯示):")
    print(f"   http://localhost:{PORT}/dual-device-game-sync.html?mode=display")
    
    print(f"\n📱 手機 (控制器):")
    print(f"   http://{local_ip}:{PORT}/dual-device-game-sync.html?mode=controller")
    
    print("\n" + "=" * 60)
    print("📖 使用說明:")
    print("=" * 60)
    print("1. 確保手機和筆電在同一個 WiFi")
    print("2. 筆電打開上面的「投影顯示」網址")
    print("3. 手機打開上面的「控制器」網址")
    print("4. 在手機上點擊跳躍按鈕!")
    print("5. 按 Ctrl+C 停止伺服器")
    print("=" * 60)
    print("\n🚀 伺服器啟動中...\n")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ 伺服器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ 錯誤: 連接埠 {PORT} 已被占用")
            print(f"請執行: lsof -ti:{PORT} | xargs kill -9")
        else:
            print(f"\n❌ 錯誤: {e}")

if __name__ == "__main__":
    main()
