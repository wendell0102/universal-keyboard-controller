import threading
import time
import platform
import os

# Universal Key Names
KEY_NAMES = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
    "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "ENTER", "ESC", "BACKSPACE", "TAB", "SPACE", "CAPS_LOCK",
    "LEFT_CTRL", "LEFT_SHIFT", "LEFT_ALT", "RIGHT_CTRL", "RIGHT_SHIFT", "RIGHT_ALT",
    "UP", "DOWN", "LEFT", "RIGHT", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
    "F9", "F10", "F11", "F12"
]

class KeyRemapper:
    def __init__(self):
        self.mappings = {}  # key_name -> key_name
        self.active = False
        self.listener_thread = None
        self.on_key_event_callback = None
        self.system = platform.system()
        
        # Windows Hook Specifics
        self.win_hook_id = None
        self.win_hook_fn = None
        
        # Linux Evdev Specifics
        self.linux_device = None
        self.linux_uinput = None

    def set_callback(self, callback):
        self.on_key_event_callback = callback

    def update_mappings(self, new_mappings):
        """
        Expects a dictionary like: {"CAPS_LOCK": "ESC"}
        """
        self.mappings = {k: v for k, v in new_mappings.items() if k in KEY_NAMES and v in KEY_NAMES}
        print(f"[Remapper] Mappings updated: {self.mappings}")

    def start(self):
        if self.active:
            return
        self.active = True
        
        if self.system == "Windows":
            self.listener_thread = threading.Thread(target=self._run_windows_hook, daemon=True)
            self.listener_thread.start()
            print("[Remapper] Windows Hook Service started.")
        elif self.system == "Linux":
            self.listener_thread = threading.Thread(target=self._run_linux_evdev, daemon=True)
            self.listener_thread.start()
            print("[Remapper] Linux Evdev Service started.")
        else:
            print(f"[Remapper] OS {self.system} is not supported for global remapping.")
            self.active = False

    def stop(self):
        if not self.active:
            return
        self.active = False
        
        if self.system == "Windows" and self.win_hook_id:
            import ctypes
            ctypes.windll.user32.UnhookWindowsHookEx(self.win_hook_id)
            self.win_hook_id = None
            print("[Remapper] Windows Hook Service stopped.")
            
        elif self.system == "Linux":
            # Stopping is handled by the thread breaking the loop on self.active = False
            # but we can trigger a dummy event if needed to break evdev blocking read.
            # Usually, thread termination on shutdown is sufficient.
            print("[Remapper] Linux Evdev Service stopped.")

    # ================= WINDOWS IMPLEMENTATION =================
    def _run_windows_hook(self):
        import ctypes
        from ctypes import wintypes
        
        # Win32 Constants
        WH_KEYBOARD_LL = 13
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105

        # Windows Virtual Key Codes Map
        VK_MAP = {
            "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
            "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E,
            "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
            "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5A,
            "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35, "6": 0x36,
            "7": 0x37, "8": 0x38, "9": 0x39,
            "ENTER": 0x0D, "ESC": 0x1B, "BACKSPACE": 0x08, "TAB": 0x09, "SPACE": 0x20,
            "CAPS_LOCK": 0x14, "LEFT_CTRL": 0xA2, "LEFT_SHIFT": 0xA0, "LEFT_ALT": 0xA4,
            "RIGHT_CTRL": 0xA3, "RIGHT_SHIFT": 0xA1, "RIGHT_ALT": 0xA5,
            "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
            "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
        }
        VK_REV_MAP = {v: k for k, v in VK_MAP.items()}

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", ctypes.c_ulong),
                ("scanCode", ctypes.c_ulong),
                ("flags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_ulonglong)
            ]

        # Declare API Signatures
        ctypes.windll.user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        ctypes.windll.user32.SetWindowsHookExW.restype = ctypes.c_void_p
        ctypes.windll.user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        ctypes.windll.user32.UnhookWindowsHookEx.restype = ctypes.c_int
        ctypes.windll.user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ulonglong, ctypes.c_ulonglong]
        ctypes.windll.user32.CallNextHookEx.restype = ctypes.c_longlong
        ctypes.windll.kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        ctypes.windll.kernel32.GetModuleHandleW.restype = ctypes.c_void_p

        # Mappings list internally converted to VK codes
        def get_active_vk_mappings():
            vk_maps = {}
            for src, tgt in self.mappings.items():
                s_vk = VK_MAP.get(src)
                t_vk = VK_MAP.get(tgt)
                if s_vk and t_vk:
                    vk_maps[s_vk] = t_vk
            return vk_maps

        def hook_callback(nCode, wParam, lParam):
            if nCode >= 0:
                kbd = KBDLLHOOKSTRUCT.from_address(lParam)
                vk = kbd.vkCode
                flags = kbd.flags
                injected = bool(flags & 0x00000010)

                is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                is_up = wParam in (WM_KEYUP, WM_SYSKEYUP)

                # Broadcast to UI
                if self.on_key_event_callback and not injected:
                    key_name = VK_REV_MAP.get(vk, f"0x{vk:02X}")
                    self.on_key_event_callback(key_name, "down" if is_down else "up")

                if injected:
                    return ctypes.windll.user32.CallNextHookEx(self.win_hook_id, nCode, wParam, lParam)

                active_vk_maps = get_active_vk_mappings()
                if vk in active_vk_maps:
                    target_vk = active_vk_maps[vk]
                    if is_down:
                        ctypes.windll.user32.keybd_event(target_vk, 0, 0, 0)
                    elif is_up:
                        ctypes.windll.user32.keybd_event(target_vk, 0, 2, 0)
                    return 1  # Swallow event

            return ctypes.windll.user32.CallNextHookEx(self.win_hook_id, nCode, wParam, lParam)

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, ctypes.c_ulonglong, ctypes.c_ulonglong)
        self.win_hook_fn = CMPFUNC(hook_callback)

        h_mod = ctypes.windll.kernel32.GetModuleHandleW(None)
        self.win_hook_id = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self.win_hook_fn,
            h_mod,
            0
        )

        if not self.win_hook_id:
            err = ctypes.windll.kernel32.GetLastError()
            print(f"[Remapper] Windows Hook failed to install. Error code: {err}")
            self.active = False
            return

        msg = wintypes.MSG()
        while self.active:
            r = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            if r <= 0:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    # ================= LINUX IMPLEMENTATION =================
    def _run_linux_evdev(self):
        try:
            import evdev
            from evdev import ecodes, UInput
        except ImportError:
            print("[Remapper] Error: 'evdev' python package is not installed. Run: pip install evdev")
            self.active = False
            return

        # Linux Evdev Code Maps
        EV_MAP = {
            "A": ecodes.KEY_A, "B": ecodes.KEY_B, "C": ecodes.KEY_C, "D": ecodes.KEY_D,
            "E": ecodes.KEY_E, "F": ecodes.KEY_F, "G": ecodes.KEY_G, "H": ecodes.KEY_H,
            "I": ecodes.KEY_I, "J": ecodes.KEY_J, "K": ecodes.KEY_K, "L": ecodes.KEY_L,
            "M": ecodes.KEY_M, "N": ecodes.KEY_N, "O": ecodes.KEY_O, "P": ecodes.KEY_P,
            "Q": ecodes.KEY_Q, "R": ecodes.KEY_R, "S": ecodes.KEY_S, "T": ecodes.KEY_T,
            "U": ecodes.KEY_U, "V": ecodes.KEY_V, "W": ecodes.KEY_W, "X": ecodes.KEY_X,
            "Y": ecodes.KEY_Y, "Z": ecodes.KEY_Z,
            "0": ecodes.KEY_0, "1": ecodes.KEY_1, "2": ecodes.KEY_2, "3": ecodes.KEY_3,
            "4": ecodes.KEY_4, "5": ecodes.KEY_5, "6": ecodes.KEY_6, "7": ecodes.KEY_7,
            "8": ecodes.KEY_8, "9": ecodes.KEY_9,
            "ENTER": ecodes.KEY_ENTER, "ESC": ecodes.KEY_ESC, "BACKSPACE": ecodes.KEY_BACKSPACE,
            "TAB": ecodes.KEY_TAB, "SPACE": ecodes.KEY_SPACE, "CAPS_LOCK": ecodes.KEY_CAPSLOCK,
            "LEFT_CTRL": ecodes.KEY_LEFTCTRL, "LEFT_SHIFT": ecodes.KEY_LEFTSHIFT, "LEFT_ALT": ecodes.KEY_LEFTALT,
            "RIGHT_CTRL": ecodes.KEY_RIGHTCTRL, "RIGHT_SHIFT": ecodes.KEY_RIGHTSHIFT, "RIGHT_ALT": ecodes.KEY_RIGHTALT,
            "UP": ecodes.KEY_UP, "DOWN": ecodes.KEY_DOWN, "LEFT": ecodes.KEY_LEFT, "RIGHT": ecodes.KEY_RIGHT,
            "F1": ecodes.KEY_F1, "F2": ecodes.KEY_F2, "F3": ecodes.KEY_F3, "F4": ecodes.KEY_F4,
            "F5": ecodes.KEY_F5, "F6": ecodes.KEY_F6, "F7": ecodes.KEY_F7, "F8": ecodes.KEY_F8,
            "F9": ecodes.KEY_F9, "F10": ecodes.KEY_F10, "F11": ecodes.KEY_F11, "F12": ecodes.KEY_F12,
        }
        EV_REV_MAP = {v: k for k, v in EV_MAP.items()}

        # 1. Search for physical keyboard
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        kbd_dev = None
        for dev in devices:
            caps = dev.capabilities()
            if ecodes.EV_KEY in caps:
                # Check if it looks like a standard keyboard (has A and Enter keys)
                if ecodes.KEY_A in caps[ecodes.EV_KEY] and ecodes.KEY_ENTER in caps[ecodes.EV_KEY]:
                    # Ignore virtual uinput devices we created ourselves
                    if "Virtual" not in dev.name and "uinput" not in dev.name.lower():
                        kbd_dev = dev
                        break
        
        if not kbd_dev:
            print("[Remapper] Error: No physical keyboard detected on /dev/input/*")
            self.active = False
            return

        print(f"[Remapper] Linux detected Keyboard: {kbd_dev.name} [{kbd_dev.path}]")
        self.linux_device = kbd_dev
        
        try:
            # Grab keyboard exclusively
            kbd_dev.grab()
            
            # Create a virtual uinput device to write keys
            # Copy capabilities of the original keyboard so it mimics it exactly
            self.linux_uinput = UInput.from_device(kbd_dev, name="Antigravity Universal Virtual Keyboard")
            
            # Read input loop
            for event in kbd_dev.read_loop():
                if not self.active:
                    break

                if event.type == ecodes.EV_KEY:
                    code = event.code
                    val = event.value # 0 = UP, 1 = DOWN, 2 = HOLD
                    
                    # Convert to our standardized key names for callback
                    if self.on_key_event_callback:
                        key_name = EV_REV_MAP.get(code, f"KEY_CODE_{code}")
                        self.on_key_event_callback(key_name, "down" if val in (1, 2) else "up")

                    # Translate mappings
                    # Map internally: source_code -> target_code
                    active_ev_maps = {}
                    for src, tgt in self.mappings.items():
                        s_code = EV_MAP.get(src)
                        t_code = EV_MAP.get(tgt)
                        if s_code and t_code:
                            active_ev_maps[s_code] = t_code

                    if code in active_ev_maps:
                        target_code = active_ev_maps[code]
                        self.linux_uinput.write(ecodes.EV_KEY, target_code, val)
                        self.linux_uinput.syn()
                    else:
                        # Pass key through unmodified
                        self.linux_uinput.write(ecodes.EV_KEY, code, val)
                        self.linux_uinput.syn()
                else:
                    # Pass through non-keyboard events (like sync, relative movement if any)
                    self.linux_uinput.write(event.type, event.code, event.value)
                    self.linux_uinput.syn()

        except Exception as e:
            print(f"[Remapper] Linux evdev error: {e}")
            print("[Remapper] Note: This script must be run as ROOT (sudo) to access /dev/input/*")
        finally:
            # Clean up and release the keyboard!
            try:
                kbd_dev.ungrab()
            except:
                pass
            if self.linux_uinput:
                self.linux_uinput.close()
            self.active = False
            print("[Remapper] Linux evdev resources released.")

if __name__ == "__main__":
    # Test script
    remapper = KeyRemapper()
    remapper.update_mappings({"CAPS_LOCK": "ESC", "A": "B"})
    remapper.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        remapper.stop()
