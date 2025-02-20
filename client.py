import asyncio
import websockets
import ctypes
import time
from datetime import datetime

SERVER_URL = "wss://characteristic-iolande-fgdsfgd3125243-53730f15.koyeb.app/ws"  # Change this to your server's IP

def send_media_play_pause():
    """Sends a real media play/pause command like a keyboard."""
    APPCOMMAND_MEDIA_PLAY_PAUSE = 0xE0000
    WM_APPCOMMAND = 0x319

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, APPCOMMAND_MEDIA_PLAY_PAUSE)
    print("Media Play/Pause command sent.")

async def listen():
    """Connect to the WebSocket server and listen for messages."""
    while True:
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                print("Connected to server.")
                
                while True:
                    message = await websocket.recv()

                    if message == "ping":
                        await websocket.send("pong")  # Respond to keep connection alive
                        continue

                    if message.startswith("resume"):
                        _, minutes = message.split(",")
                        minutes = int(minutes)

                        # Send acknowledgment
                        await websocket.send(f"ack,{minutes}")
                        print(f"Alert received for {minutes} minutes. Sending acknowledgment.")

                        send_media_play_pause()
                        print(f"Resuming media for {minutes} minutes...")
                        await asyncio.sleep(minutes * 60)  # Wait before pausing again
                        send_media_play_pause()
                        print(f"Paused after {minutes} minutes.")
        except Exception as e:
            print(f"Connection lost: {e}, retrying in 2 seconds...")
            await asyncio.sleep(2)  # Shorter retry delay
            

if __name__ == "__main__":
    asyncio.run(listen())
