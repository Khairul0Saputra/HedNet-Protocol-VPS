#!/usr/bin/env python3
import requests
import websocket
import json
import time
import logging
import threading
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HedNetVPS")

class HedNetVPSNode:
    def __init__(self, access_token: str):
        self.base_url = "https://api.hednetio.ovh"
        self.ws_url = "wss://api.hednetio.ovh/websocket"  # Diperkirakan
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "HedNet-VPS-Node/1.0"
        })
        
        # Bandwidth simulation
        self.bandwidth_urls = [
            "https://job.hednetio.ovh/500MB-CZIPtestfile.org.zip",
            "https://job.hednetio.ovh/500MB-CZIPtestfilea.org.zip"
        ]
        self.current_url_index = 0
        self.is_running = False
        self.total_bytes = 0
        self.session_points = 0
        
    def authenticate(self) -> bool:
        """Test authentication dengan ping endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/device/ext/ping")
            if response.status_code == 200:
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def start_bandwidth_simulation(self):
        """Simulasi bandwidth sharing seperti di ekstensi"""
        self.is_running = True
        logger.info("Starting bandwidth simulation...")
        
        def bandwidth_worker():
            while self.is_running:
                try:
                    url = self.bandwidth_urls[self.current_url_index]
                    logger.info(f"Testing bandwidth with: {url}")
                    
                    response = self.session.get(url, stream=True)
                    chunk_size = 1024 * 1024  # 1MB chunks
                    bytes_downloaded = 0
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if not self.is_running:
                            break
                            
                        if chunk:
                            bytes_downloaded += len(chunk)
                            self.total_bytes += len(chunk)
                            
                            # Simulate bandwidth usage reporting
                            if bytes_downloaded % (100 * 1024 * 1024) == 0:  # Every 100MB
                                self.report_bandwidth_usage()
                            
                            # Small delay to simulate real usage
                            time.sleep(0.1)
                    
                    # Switch to next URL
                    self.current_url_index = (self.current_url_index + 1) % len(self.bandwidth_urls)
                    
                    # Report after each complete download
                    self.report_bandwidth_usage()
                    
                    # Idle period like in extension (1 hour)
                    if self.is_running:
                        logger.info("Simulating idle period (1 hour)")
                        for _ in range(3600):  # 1 hour in seconds
                            if not self.is_running:
                                break
                            time.sleep(1)
                            
                except Exception as e:
                    logger.error(f"Bandwidth simulation error: {e}")
                    time.sleep(60)  # Wait before retry
        
        # Start bandwidth simulation in separate thread
        self.bandwidth_thread = threading.Thread(target=bandwidth_worker, daemon=True)
        self.bandwidth_thread.start()
    
    def report_bandwidth_usage(self):
        """Report bandwidth usage to HedNet API"""
        try:
            # Calculate points based on bandwidth (10 points per hour as in extension)
            points_earned = 10 / 3600  # Points per second
            
            payload = {
                "added_point": points_earned,
                "total_bytes": self.total_bytes
            }
            
            response = self.session.post(
                f"{self.base_url}/device/ext/bandwidth_point",
                json=payload
            )
            
            if response.status_code == 200:
                self.session_points += points_earned
                logger.info(f"Bandwidth reported successfully. Total points: {self.session_points:.2f}")
            else:
                logger.warning(f"Bandwidth report failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error reporting bandwidth: {e}")
    
    def connect_websocket(self):
        """Connect to HedNet WebSocket for real-time updates"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                logger.info(f"WebSocket message: {data}")
                
                # Handle different message types
                if data.get('type') == 'bandwidth_update':
                    self.handle_bandwidth_update(data)
                elif data.get('type') == 'node_config':
                    self.handle_node_config(data)
                    
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON WebSocket message: {message}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            # Attempt reconnect after delay
            time.sleep(10)
            self.connect_websocket()
        
        def on_open(ws):
            logger.info("WebSocket connection established")
            # Send authentication
            auth_message = {
                "type": "auth",
                "token": self.access_token
            }
            ws.send(json.dumps(auth_message))
        
        # Connect to WebSocket
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Run WebSocket in separate thread
        def run_websocket():
            ws.run_forever()
        
        self.ws_thread = threading.Thread(target=run_websocket, daemon=True)
        self.ws_thread.start()
    
    def handle_bandwidth_update(self, data):
        """Handle bandwidth update messages"""
        logger.info(f"Bandwidth update: {data}")
    
    def handle_node_config(self, data):
        """Handle node configuration updates"""
        logger.info(f"Node config update: {data}")
    
    def start(self):
        """Start the HedNet VPS node"""
        if not self.authenticate():
            logger.error("Cannot start node: Authentication failed")
            return False
        
        logger.info("HedNet VPS Node starting...")
        
        # Start bandwidth simulation
        self.start_bandwidth_simulation()
        
        # Connect to WebSocket
        self.connect_websocket()
        
        logger.info("HedNet VPS Node is now running")
        return True
    
    def stop(self):
        """Stop the HedNet VPS node"""
        logger.info("Stopping HedNet VPS Node...")
        self.is_running = False
        
        # Final bandwidth report
        if self.session_points > 0:
            self.report_bandwidth_usage()

def main():
    # Anda perlu mendapatkan access_token dari ekstensi Chrome
    # Cara: 
    # 1. Jalankan ekstensi di browser
    # 2. Buka Developer Tools -> Application -> Local Storage
    # 3. Cari token akses
    access_token = "YOUR_ACCESS_TOKEN_HERE"
    
    if access_token == "YOUR_ACCESS_TOKEN_HERE":
        logger.error("Please set your access token in the script")
        return
    
    node = HedNetVPSNode(access_token)
    
    try:
        if node.start():
            # Keep the main thread alive
            while True:
                time.sleep(1)
        else:
            logger.error("Failed to start node")
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        node.stop()
        logger.info("HedNet VPS Node stopped")

if __name__ == "__main__":
    main()"""

@app.route("/")
def home():
    return HTML_UI

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        # Ganti sesuai URL internal ekstensi Anda
        driver.get("chrome-extension://jgmekddkhffanioefjcgfaggjpokifpi/index.html")
        time.sleep(3)

        # Ganti selector sesuai UI ekstensi
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()

        return f"✅ Login sukses untuk {username}"
    except Exception as e:
        return f"❌ Gagal login: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
