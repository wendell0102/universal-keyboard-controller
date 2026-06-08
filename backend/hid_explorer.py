import time

# Try to import hid (requires 'pip install hid')
# We will use a soft fallback if the package is missing or no device is connected.
try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

class HIDManager:
    def __init__(self):
        self.devices = []
        self.active_device = None
        self.is_simulated = True
        
        # Mock Keymap: 4 layers, 5 rows, 15 columns of keycodes (stored as uint16)
        # Standard keycodes (like QMK/VIA keycodes: e.g. KC_A = 4, KC_B = 5, etc.)
        self.mock_keymap = {} # (layer, row, col) -> keycode (uint16)
        self._initialize_mock_keymap()

    def _initialize_mock_keymap(self):
        # Initialize Layer 0 with simple mock values (e.g., standard keycodes)
        # Row 0: ESC, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, -, =, BACKSPACE
        row0 = [0x0029, 0x001E, 0x001F, 0x0020, 0x0021, 0x0022, 0x0023, 0x0024, 0x0025, 0x0026, 0x0027, 0x002D, 0x002E, 0x002A]
        for col, kc in enumerate(row0):
            self.mock_keymap[(0, 0, col)] = kc

        # Row 1: TAB, Q, W, E, R, T, Y, U, I, O, P, [, ], \
        row1 = [0x002B, 0x0014, 0x001A, 0x0008, 0x0015, 0x0017, 0x001C, 0x0018, 0x000C, 0x0012, 0x0013, 0x002F, 0x0030, 0x0031]
        for col, kc in enumerate(row1):
            self.mock_keymap[(0, 1, col)] = kc

        # Row 2: CAPS, A, S, D, F, G, H, J, K, L, ;, ', ENTER
        row2 = [0x0039, 0x0004, 0x0016, 0x0007, 0x0009, 0x000A, 0x000B, 0x000D, 0x000E, 0x000F, 0x0033, 0x0034, 0x0028]
        for col, kc in enumerate(row2):
            self.mock_keymap[(0, 2, col)] = kc

        # Row 3: LSHIFT, Z, X, C, V, B, N, M, ,, ., /, RSHIFT
        row3 = [0x00E1, 0x001D, 0x001B, 0x0006, 0x0019, 0x0005, 0x0011, 0x0010, 0x0036, 0x0037, 0x0038, 0x00E5]
        for col, kc in enumerate(row3):
            self.mock_keymap[(0, 3, col)] = kc

    def scan_devices(self):
        devices_list = []
        if HID_AVAILABLE:
            try:
                for dev in hid.enumerate():
                    # Check if QMK/VIA usage page (0xFF60) or standard custom page
                    is_via = (dev.get('usage_page') == 0xFF60)
                    devices_list.append({
                        "vendor_id": dev['vendor_id'],
                        "product_id": dev['product_id'],
                        "path": dev['path'].decode('utf-8', errors='ignore') if isinstance(dev['path'], bytes) else str(dev['path']),
                        "manufacturer": dev['manufacturer_string'] or "Generic",
                        "product": dev['product_string'] or "Keyboard Device",
                        "is_via": is_via
                    })
            except Exception as e:
                print(f"[HID] Enumeration error: {e}")
        
        # Always inject a mock device for simulation
        devices_list.append({
            "vendor_id": 0xFEED,
            "product_id": 0x6060,
            "path": "SIMULATED_KEYBOARD_PATH_01",
            "manufacturer": "Antigravity",
            "product": "Universal QMK/VIA Keyboard Simulator",
            "is_via": True
        })
        self.devices = devices_list
        return devices_list

    def connect_device(self, path):
        if path == "SIMULATED_KEYBOARD_PATH_01":
            self.is_simulated = True
            self.active_device = {"path": path, "product": "Universal QMK/VIA Keyboard Simulator"}
            print("[HID] Connected to SIMULATED VIA device.")
            return True

        if not HID_AVAILABLE:
            return False

        try:
            dev = hid.device()
            dev.open_path(path.encode('utf-8') if isinstance(path, str) else path)
            self.active_device = dev
            self.is_simulated = False
            print(f"[HID] Connected to physical device: {path}")
            return True
        except Exception as e:
            print(f"[HID] Failed to connect: {e}")
            return False

    def send_raw_report(self, data_bytes):
        """
        Sends a 32-byte raw HID report and reads a 32-byte response.
        data_bytes: list of 32 integers representing bytes.
        """
        # Ensure packet size is exactly 32 bytes
        packet = list(data_bytes)
        if len(packet) < 32:
            packet += [0] * (32 - len(packet))
        packet = packet[:32]

        if self.is_simulated:
            return self._simulate_via_transaction(packet)

        if not self.active_device:
            raise Exception("No active HID device connected.")

        try:
            # Under Windows, the report ID (0) must prepended to raw output report if not present
            # so write takes 33 bytes.
            write_packet = [0] + packet
            self.active_device.write(write_packet)
            
            # Read 32 bytes response
            response = self.active_device.read(32, timeout_ms=1000)
            return response
        except Exception as e:
            print(f"[HID] Transaction error: {e}")
            raise e

    def _simulate_via_transaction(self, packet):
        """
        Simulates the standard VIA protocol response.
        VIA commands:
        0x01: Get Protocol Version
        0x11: Get Keymap Value [layer, row, col] -> returns [0x11, layer, row, col, val_msb, val_lsb]
        0x12: Set Keymap Value [layer, row, col, val_msb, val_lsb] -> returns same
        0x18: Dynamic Keymap Reset
        """
        time.sleep(0.02) # Simulate usb bus latency
        cmd = packet[0]
        resp = [0] * 32
        resp[0] = cmd

        if cmd == 0x01:
            # Get Protocol Version -> returns version 9 (0x09)
            resp[1] = 0x09
            resp[2] = 0x00
            
        elif cmd == 0x11:
            # Get Keycode: packet[1] = layer, packet[2] = row, packet[3] = col
            layer = packet[1]
            row = packet[2]
            col = packet[3]
            keycode = self.mock_keymap.get((layer, row, col), 0x0000)
            resp[1] = layer
            resp[2] = row
            resp[3] = col
            resp[4] = (keycode >> 8) & 0xFF  # MSB
            resp[5] = keycode & 0xFF         # LSB

        elif cmd == 0x12:
            # Set Keycode: packet[1] = layer, packet[2] = row, packet[3] = col, packet[4]=msb, packet[5]=lsb
            layer = packet[1]
            row = packet[2]
            col = packet[3]
            keycode = (packet[4] << 8) | packet[5]
            self.mock_keymap[(layer, row, col)] = keycode
            print(f"[VIA Simulator] Key remapped in EEPROM: Layer {layer}, Row {row}, Col {col} -> Keycode 0x{keycode:04X}")
            resp[1] = layer
            resp[2] = row
            resp[3] = col
            resp[4] = packet[4]
            resp[5] = packet[5]

        else:
            # Echo unknown command back with error status
            resp[1] = 0xFF # Command unsupported status

        return resp

if __name__ == "__main__":
    # Test script
    mgr = HIDManager()
    mgr.scan_devices()
    mgr.connect_device("SIMULATED_KEYBOARD_PATH_01")
    
    # Query version (0x01)
    req = [0x01] + [0]*31
    res = mgr.send_raw_report(req)
    print(f"Version Response: {res[:4]}")
    
    # Query key at (0, 0, 1) -> Row 0, Col 1 should be '1' (KC_1 = 0x001E)
    req2 = [0x11, 0, 0, 1] + [0]*28
    res2 = mgr.send_raw_report(req2)
    print(f"Keymap Response: {res2[:6]}")
