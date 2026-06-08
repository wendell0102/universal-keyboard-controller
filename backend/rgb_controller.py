import socket
import struct
import threading
import time

# OpenRGB SDK Constants
OPENRGB_PORT = 6742
ORGB_MAGIC = b"ORGB"

# SDK Commands
ORGB_REQUEST_CONTROLLER_COUNT = 0
ORGB_REQUEST_CONTROLLER_DATA = 1
ORGB_REQUEST_PROTOCOL_VERSION = 40
ORGB_COMMAND_RESIZE_ZONE = 1000
ORGB_COMMAND_UPDATE_LEDS = 1050
ORGB_COMMAND_UPDATE_ZONE_LEDS = 1051

class OpenRGBClient:
    def __init__(self, host="127.0.0.1", port=OPENRGB_PORT):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.devices = []
        self.simulated = True

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.simulated = False
            print("[OpenRGB] Connected to OpenRGB SDK Server successfully!")
            # Get device count
            self.devices = self._get_devices()
            return True
        except Exception as e:
            self.sock = None
            self.connected = False
            self.simulated = True
            print(f"[OpenRGB] Could not connect to OpenRGB ({e}). Running in SIMULATION MODE.")
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
        self.simulated = True
        self.sock = None

    def _send_packet(self, device_id, command, data):
        if not self.connected or not self.sock:
            return
        # Packet header: Magic (4 bytes) + Device ID (4 bytes) + Command (4 bytes) + Length (4 bytes)
        header = struct.pack("<4sIII", ORGB_MAGIC, device_id, command, len(data))
        try:
            self.sock.sendall(header + data)
        except Exception as e:
            print(f"[OpenRGB] Error sending packet: {e}")
            self.disconnect()

    def _read_packet(self):
        if not self.connected or not self.sock:
            return None, None, None
        try:
            header = self.sock.recv(16)
            if len(header) < 16:
                return None, None, None
            magic, dev_id, command, data_len = struct.unpack("<4sIII", header)
            if magic != ORGB_MAGIC:
                return None, None, None
            data = b""
            while len(data) < data_len:
                chunk = self.sock.recv(data_len - len(data))
                if not chunk:
                    break
                data += chunk
            return dev_id, command, data
        except Exception as e:
            print(f"[OpenRGB] Error reading packet: {e}")
            self.disconnect()
            return None, None, None

    def _get_devices(self):
        if not self.connected:
            return []
        # Query protocol version first (required by OpenRGB)
        protocol_data = struct.pack("<I", 3)  # Client version 3
        self._send_packet(0, ORGB_REQUEST_PROTOCOL_VERSION, protocol_data)
        _, _, resp = self._read_packet() # Protocol response (usually version number)

        # Get controller count
        self._send_packet(0, ORGB_REQUEST_CONTROLLER_COUNT, b"")
        _, _, count_data = self._read_packet()
        if not count_data:
            return []
        count = struct.unpack("<I", count_data[:4])[0]
        
        devices = []
        for i in range(count):
            self._send_packet(i, ORGB_REQUEST_CONTROLLER_DATA, struct.pack("<I", 3)) # Version 3 data request
            _, _, dev_data = self._read_packet()
            if dev_data:
                # Parse basic details (type, name)
                # Structure: type(4 bytes) + name length(2 bytes) + name + description + etc.
                dev_type = struct.unpack("<I", dev_data[:4])[0]
                name_len = struct.unpack("<H", dev_data[4:6])[0]
                dev_name = dev_data[6:6+name_len].decode('utf-8', errors='ignore')
                devices.append({
                    "id": i,
                    "name": dev_name,
                    "type": dev_type, # 0 = Keyboard, 1 = Mouse, etc.
                })
        return devices

    def set_leds(self, device_id, colors):
        """
        colors: list of (r, g, b) tuples matching the size of the keyboard LEDs.
        """
        if self.simulated:
            return
        
        # Command data format:
        # uint32 data size (header handles this)
        # uint16 led count
        # For each led: R (1 byte), G (1 byte), B (1 byte), A (1 byte)
        led_count = len(colors)
        data = struct.pack("<H", led_count)
        for r, g, b in colors:
            data += struct.pack("<BBBB", r, g, b, 0)
        
        self._send_packet(device_id, ORGB_COMMAND_UPDATE_LEDS, data)

class RGBManager:
    def __init__(self, websocket_broadcast_callback=None):
        self.client = OpenRGBClient()
        self.broadcast_callback = websocket_broadcast_callback
        self.active_effect = "static"
        self.base_color = (0, 255, 255) # Cyan default
        self.effect_speed = 1.0
        self.running = False
        self.effect_thread = None
        self.num_keys = 104  # standard layout size

    def start(self):
        self.client.connect()
        self.running = True
        self.effect_thread = threading.Thread(target=self._effect_loop, daemon=True)
        self.effect_thread.start()

    def stop(self):
        self.running = False
        self.client.disconnect()

    def set_effect(self, effect, color=None, speed=1.0):
        self.active_effect = effect
        if color:
            self.base_color = color
        self.effect_speed = speed
        print(f"[RGBManager] Effect set to: {effect}, Color: {self.base_color}, Speed: {speed}")

    def _effect_loop(self):
        tick = 0
        while self.running:
            colors = []
            
            if self.active_effect == "static":
                colors = [self.base_color] * self.num_keys
                
            elif self.active_effect == "rainbow":
                # Cycle hue over key positions
                for i in range(self.num_keys):
                    hue = (tick * self.effect_speed * 5 + i * 3) % 360
                    r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
                    colors.append((r, g, b))
                    
            elif self.active_effect == "breathe":
                # Sine wave brightness modifier
                import math
                brightness = (math.sin(tick * self.effect_speed * 0.1) + 1.0) / 2.0
                r = int(self.base_color[0] * brightness)
                g = int(self.base_color[1] * brightness)
                b = int(self.base_color[2] * brightness)
                colors = [(r, g, b)] * self.num_keys
                
            elif self.active_effect == "wave":
                # A linear wave moving across the keyboard
                import math
                for i in range(self.num_keys):
                    pos_factor = math.sin((i / 10.0) + (tick * self.effect_speed * 0.15))
                    factor = (pos_factor + 1.0) / 2.0
                    r = int(self.base_color[0] * factor)
                    g = int(self.base_color[1] * factor)
                    b = int(self.base_color[2] * factor)
                    colors.append((r, g, b))

            # Send to physical hardware if connected
            if not self.client.simulated and self.client.connected:
                # Find keyboard devices and set colors
                for dev in self.client.devices:
                    if dev["type"] == 0: # 0 is Keyboard in OpenRGB
                        self.client.set_leds(dev["id"], colors)

            # Broadcast to web UI so the virtual keyboard lights up in real-time
            if self.broadcast_callback:
                # Format to hex string list
                hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
                self.broadcast_callback({
                    "type": "rgb_update",
                    "effect": self.active_effect,
                    "simulated": self.client.simulated,
                    "devices": self.client.devices,
                    "colors": hex_colors
                })

            tick += 1
            time.sleep(0.05) # ~20 FPS refresh rate

    def _hsv_to_rgb(self, h, s, v):
        # h: 0-359, s: 0.0-1.0, v: 0.0-1.0
        c = v * s
        x = c * (1 - abs((h / 60.0) % 2 - 1))
        m = v - c
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

if __name__ == "__main__":
    # Test script
    def print_colors(data):
        print(f"Update: {data['colors'][0]}")
    mgr = RGBManager(print_colors)
    mgr.set_effect("rainbow", speed=1.5)
    mgr.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mgr.stop()
