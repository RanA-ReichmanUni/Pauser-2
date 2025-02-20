import asyncio
import websockets
import ctypes
import time
from datetime import datetime

SERVER_URL = "wss://previous-myrta-fgdsfgd3125243-d6dc9757.koyeb.app/ws"  # Change this to your server's URL

is_playing = False  # Track whether media is currently playing

def send_media_play_pause():
    """Sends a real media play/pause command like a keyboard and then exits."""
    APPCOMMAND_MEDIA_PLAY_PAUSE = 0xE0000
    WM_APPCOMMAND = 0x319

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, APPCOMMAND_MEDIA_PLAY_PAUSE)
    print("✅ Media Play/Pause command sent.")

async def listen():
    """Connect to the WebSocket server and listen for messages."""
    global is_playing

    while True:
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                print("✅ Connected to WebSocket server.")

                while True:
                    message = await websocket.recv()
                    print(f"📩 Message received: {message}")

                    if message == "ping":
                        await websocket.send("pong")  # Respond to keep connection alive
                        print("🔁 Sent pong to server.")
                        continue

                    if message.startswith("resume"):
                        _, minutes = message.split(",")
                        minutes = int(minutes)

                        # Acknowledge receipt even if already playing
                        await websocket.send(f"ack,{minutes}")  
                        print(f"✅ Acknowledged alert for {minutes} minutes.")

                        # Ignore new alerts if already playing
                        if is_playing:
                            print(f"⏳ Ignoring alert for {minutes} minutes (already playing).")
                            continue

                        is_playing = True  # Set playing state
                        send_media_play_pause()
                        print(f"▶️ Resuming media for {minutes} minutes...")
                        await asyncio.sleep(minutes * 60)  # Wait before pausing again
                        send_media_play_pause()
                        print(f"⏸️ Paused after {minutes} minutes.")

                        is_playing = False  # Allow new alerts after playback finishes

        except Exception as e:
            print(f"⚠️ Connection lost: {e}, retrying in 2 seconds...")
            await asyncio.sleep(2)  # Shorter retry delay

if __name__ == "__main__":
    asyncio.run(listen())
