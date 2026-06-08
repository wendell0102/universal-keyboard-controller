import asyncio
import os
import json
import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import our custom modules
from remapper import KeyRemapper
from rgb_controller import RGBManager
from hid_explorer import HIDManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KeyboardController")

app = FastAPI(title="Universal Keyboard Controller API")

# Global instances
remapper = KeyRemapper()
hid_manager = HIDManager()

# WebSocket connections storage
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        # We need a thread-safe way or run in the main event loop
        # Since this might be called from background threads, we will schedule it
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)

ws_manager = ConnectionManager()

# Event loop helper to broadcast from background threads safely
loop = None

def background_broadcast(message: dict):
    try:
        global loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(message), loop)
    except Exception as e:
        logger.error(f"Error broadcasting background message: {e}")

# Register callbacks
remapper.set_callback(
    lambda key, action: background_broadcast({"type": "keypress", "key": key, "action": action})
)

rgb_manager = RGBManager(
    websocket_broadcast_callback=background_broadcast
)

# --- FastAPI Models ---
class MappingModel(BaseModel):
    mappings: dict # e.g. {"CAPS_LOCK": "ESC"}

class RemapperToggleModel(BaseModel):
    active: bool

class RGBEffectModel(BaseModel):
    effect: str
    color: List[int] = [0, 255, 255] # R, G, B
    speed: float = 1.0

class HIDConnectModel(BaseModel):
    path: str

class HIDReportModel(BaseModel):
    report_hex: str # space separated hex bytes, e.g. "01 00 00 ..."

# --- API Endpoints ---

@app.on_event("startup")
def startup_event():
    global loop
    loop = asyncio.get_running_loop()
    logger.info("Starting up controller services...")
    # Start RGB animator
    rgb_manager.start()
    # Remapper starts in inactive state by default
    remapper.start()

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Stopping controller services...")
    remapper.stop()
    rgb_manager.stop()

# WebSocket for real-time events (keypress, RGB updates)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Just keep connection open, handle client disconnects
            data = await websocket.receive_text()
            # If client sends anything, we could echo or handle it
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# 1. Remapping Endpoints
@app.post("/api/remapper/mappings")
def update_mappings(data: MappingModel):
    remapper.update_mappings(data.mappings)
    return {"status": "success", "mappings": data.mappings}

@app.post("/api/remapper/toggle")
def toggle_remapper(data: RemapperToggleModel):
    if data.active:
        remapper.start()
    else:
        remapper.stop()
    return {"status": "success", "active": remapper.active}

@app.get("/api/remapper/status")
def get_remapper_status():
    return {
        "active": remapper.active,
        "mappings": {remapper.VK_REV_MAP.get(k): remapper.VK_REV_MAP.get(v) for k, v in remapper.mappings.items()}
    }

# 2. RGB Control Endpoints
@app.post("/api/rgb/effect")
def set_rgb_effect(data: RGBEffectModel):
    rgb_manager.set_effect(
        effect=data.effect,
        color=(data.color[0], data.color[1], data.color[2]),
        speed=data.speed
    )
    return {"status": "success", "effect": data.effect}

@app.get("/api/rgb/status")
def get_rgb_status():
    return {
        "effect": rgb_manager.active_effect,
        "color": rgb_manager.base_color,
        "speed": rgb_manager.effect_speed,
        "simulated": rgb_manager.client.simulated,
        "devices": rgb_manager.client.devices
    }

# 3. HID/VIA Endpoints
@app.get("/api/hid/devices")
def scan_hid_devices():
    devices = hid_manager.scan_devices()
    return {"status": "success", "devices": devices}

@app.post("/api/hid/connect")
def connect_hid_device(data: HIDConnectModel):
    success = hid_manager.connect_device(data.path)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect to device.")
    return {"status": "success", "device": hid_manager.active_device}

@app.post("/api/hid/send")
def send_hid_report(data: HIDReportModel):
    try:
        # Convert hex string to bytes list
        hex_tokens = [tok for tok in data.report_hex.strip().split() if tok]
        byte_list = [int(tok, 16) for tok in hex_tokens]
        
        if len(byte_list) > 32:
            raise HTTPException(status_code=400, detail="Report size cannot exceed 32 bytes.")
            
        resp_bytes = hid_manager.send_raw_report(byte_list)
        resp_hex = " ".join(f"{b:02X}" for b in resp_bytes)
        return {"status": "success", "response_hex": resp_hex}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid hex string format: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serving UI Static Files
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Mount frontend assets if directory exists
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Universal Keyboard Controller is running. Frontend missing at /frontend/index.html"}

if __name__ == "__main__":
    import uvicorn
    # Run uvicorn server on port 8085
    uvicorn.run("main:app", host="127.0.0.1", port=8085, reload=False)
