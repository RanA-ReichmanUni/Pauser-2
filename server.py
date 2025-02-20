from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Store active WebSocket clients
clients = set()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Homepage with instructions and alert links."""
    return """
    <html>
        <head>
            <title>FastAPI Alert Server</title>
            <style>
                body { text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f4; }
                .container { margin-top: 100px; }
                .button { display: inline-block; padding: 10px 20px; margin: 10px; font-size: 20px;
                          background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
                .button:hover { background-color: #45a049; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to the FastAPI Alert Server</h2>
                <p>Click a button to send an alert to the client:</p>
                <a href="/alert/1" class="button">1 Minute</a>
                <a href="/alert/2" class="button">2 Minutes</a>
                <a href="/alert/5" class="button">5 Minutes</a>
                <a href="/alert/10" class="button">10 Minutes</a>
            </div>
        </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections from clients."""
    await websocket.accept()
    clients.add(websocket)
    print("Client connected.")

    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except:
        clients.remove(websocket)
        print("Client disconnected.")

@app.get("/alert/{minutes}", response_class=HTMLResponse)
async def send_alert(minutes: int):
    """Send an alert to all connected clients and return a confirmation page."""
    if minutes not in [1, 2, 5, 10]:  # Added 2 minutes option
        return HTMLResponse(
            content="<h2 style='color:red;'>Invalid duration! Choose 1, 2, 5, or 10 minutes.</h2>",
            status_code=400,
        )

    # Send alert to connected WebSocket clients
    message = f"resume,{minutes}"
    for client in clients:
        await client.send_text(message)

    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Request Received</title>
                <style>
                    body {{ text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f4; }}
                    .container {{ margin-top: 100px; }}
                    .icon {{ font-size: 80px; color: #4CAF50; }}
                    h2 {{ color: #333; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✔️</div>
                    <h2>Request received for {minutes} minutes</h2>
                    <p>The media will resume accordingly.</p>
                    <p><a href="/" style="color:blue;">Go back</a></p>
                </div>
            </body>
        </html>
        """
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
