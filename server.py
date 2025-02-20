from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio

app = FastAPI()

clients = set()
confirmations = {}  # Store alert confirmation status
pending_alerts = {}  # Store active alert sending tasks

@app.get("/", response_class=HTMLResponse)
async def home():
    """Homepage with instructions and alert links."""
    return HTMLResponse(content=f"""
    <html>
        <head>
            <title>FastAPI Alert Server</title>
            <style>
                body {{ text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f4; }}
                .container {{ margin-top: 100px; }}
                .button {{ display: inline-block; padding: 10px 20px; margin: 10px; font-size: 20px;
                          background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
                .button:hover {{ background-color: #45a049; }}
                #status {{ font-weight: bold; font-size: 24px; }}
                #confirmation_icon {{ font-size: 100px; }}
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
                <p>Last Alert Status:</p>
                <div id="confirmation_icon">❌</div>
                <p id="status">No alerts sent yet.</p>
            </div>
            <script>
                async function checkStatus() {{
                    let response = await fetch('/status');
                    let data = await response.json();
                    document.getElementById("status").innerText = data.message;

                    if (data.confirmed) {{
                        document.getElementById("confirmation_icon").innerText = "✔️";
                    }} else {{
                        document.getElementById("confirmation_icon").innerText = "❌";
                    }}
                }}
                setInterval(checkStatus, 2000);
            </script>
        </body>
    </html>
    """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections from clients."""
    await websocket.accept()
    clients.add(websocket)
    print("✅ Client connected.")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"📩 Received message: {message}")

            if message.startswith("ack"):
                _, minutes = message.split(",")
                confirmations[minutes] = True  # Mark alert as acknowledged
                print(f"✅ Client acknowledged alert for {minutes} minutes.")

                # Cancel remaining alerts for this duration
                if minutes in pending_alerts:
                    pending_alerts[minutes].cancel()
                    print(f"🛑 Stopped remaining alerts for {minutes} minutes.")

            elif message == "pong":
                print("🔁 Pong received, connection is alive.")

    except Exception as e:
        print(f"⚠️ Client disconnected: {e}")
        clients.remove(websocket)


@app.get("/alert/{minutes}", response_class=HTMLResponse)
async def send_alert(minutes: int):
    """Send an alert to all connected clients (up to 10 times, 1 second apart, but stop if acknowledged)."""
    if minutes not in [1, 2, 5, 10]:
        return HTMLResponse(
            content="<h2 style='color:red;'>Invalid duration! Choose 1, 2, 5, or 10 minutes.</h2>",
            status_code=400,
        )

    confirmations[minutes] = False  # Reset confirmation status

    async def send_multiple_alerts():
        """Send the alert 10 times, but stop if the client acknowledges."""
        for i in range(10):
            if confirmations.get(str(minutes), False):  # Stop if already acknowledged
                print(f"✅ Stopping alert sequence for {minutes} minutes (client confirmed).")
                break

            message = f"resume,{minutes}"
            for client in clients:
                try:
                    await client.send_text(message)
                    print(f"📢 Sent alert {i + 1}/10 for {minutes} minutes.")
                except:
                    print("❌ Failed to send alert to a client, removing...")
                    clients.remove(client)

            await asyncio.sleep(1)

    # Start sending alerts in the background and store the task
    task = asyncio.create_task(send_multiple_alerts())
    pending_alerts[str(minutes)] = task  # Track the running task

    return HTMLResponse(content=f"""
        <html>
            <head>
                <title>Request Sent</title>
                <style>
                    body {{ text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f4; }}
                    .container {{ margin-top: 100px; }}
                    .icon {{ font-size: 100px; color: #4CAF50; }}
                    h2 {{ color: #333; }}
                    #status {{ font-weight: bold; font-size: 24px; }}
                    #confirmation_icon {{ font-size: 100px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Request sent for {minutes} minutes</h2>
                    <p>Waiting for client confirmation...</p>
                    <div id="confirmation_icon">❌</div>
                    <p id="status">Pending confirmation...</p>
                    <p><a href="/" style="color:blue;">Go back</a></p>
                </div>
                <script>
                    async function checkStatus() {{
                        let response = await fetch('/status');
                        let data = await response.json();
                        document.getElementById("status").innerText = data.message;

                        if (data.confirmed) {{
                            document.getElementById("confirmation_icon").innerText = "✔️";
                        }} else {{
                            document.getElementById("confirmation_icon").innerText = "❌";
                        }}
                    }}
                    setInterval(checkStatus, 2000);
                </script>
            </body>
        </html>
    """)


@app.get("/status")
async def status():
    """Returns the last alert confirmation status."""
    confirmed = False
    message = "No alerts sent."
    for minutes, status in confirmations.items():
        if status:
            confirmed = True
            message = f"✅ Alert for {minutes} minutes was received by the client."
        else:
            message = f"⌛ Alert for {minutes} minutes is waiting for confirmation."

    return {"message": message, "confirmed": confirmed}


# Periodically send pings to clients
async def ping_clients():
    while True:
        for client in list(clients):
            try:
                await client.send_text("ping")
            except:
                clients.remove(client)
                print("⚠️ Client removed due to disconnection.")
        await asyncio.sleep(30)


# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ping_clients())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
