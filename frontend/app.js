// Frontend Logic for Universal Keyboard Controller Hub

// List of available keys for mapping dropdowns
const AVAILABLE_KEYS = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", 
    "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", 
    "6", "7", "8", "9", "ENTER", "ESC", "BACKSPACE", "TAB", "SPACE", "CAPS_LOCK", 
    "LEFT_CTRL", "LEFT_SHIFT", "LEFT_ALT", "RIGHT_CTRL", "RIGHT_SHIFT", "RIGHT_ALT",
    "UP", "DOWN", "LEFT", "RIGHT", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", 
    "F9", "F10", "F11", "F12"
];

// Layout definition for a standard 60% keyboard (5 rows, 61 keys total)
// Each row represents keys with a label, key vk-name (matches backend), class modifier, and an rgbIndex
const KEYBOARD_LAYOUT = [
    // Row 0
    [
        { label: "Esc", vk: "ESC", rgbIndex: 0 },
        { label: "1", vk: "1", rgbIndex: 1 },
        { label: "2", vk: "2", rgbIndex: 2 },
        { label: "3", vk: "3", rgbIndex: 3 },
        { label: "4", vk: "4", rgbIndex: 4 },
        { label: "5", vk: "5", rgbIndex: 5 },
        { label: "6", vk: "6", rgbIndex: 6 },
        { label: "7", vk: "7", rgbIndex: 7 },
        { label: "8", vk: "8", rgbIndex: 8 },
        { label: "9", vk: "9", rgbIndex: 9 },
        { label: "0", vk: "0", rgbIndex: 10 },
        { label: "-", vk: "MINUS", rgbIndex: 11 }, // Fallback to index if mapping not in backend dictionary
        { label: "=", vk: "EQUAL", rgbIndex: 12 },
        { label: "Bksp", vk: "BACKSPACE", class: "key-2", rgbIndex: 13 }
    ],
    // Row 1
    [
        { label: "Tab", vk: "TAB", class: "key-1-5", rgbIndex: 14 },
        { label: "Q", vk: "Q", rgbIndex: 15 },
        { label: "W", vk: "W", rgbIndex: 16 },
        { label: "E", vk: "E", rgbIndex: 17 },
        { label: "R", vk: "R", rgbIndex: 18 },
        { label: "T", vk: "T", rgbIndex: 19 },
        { label: "Y", vk: "Y", rgbIndex: 20 },
        { label: "U", vk: "U", rgbIndex: 21 },
        { label: "I", vk: "I", rgbIndex: 22 },
        { label: "O", vk: "O", rgbIndex: 23 },
        { label: "P", vk: "P", rgbIndex: 24 },
        { label: "[", vk: "LBRACKET", rgbIndex: 25 },
        { label: "]", vk: "RBRACKET", rgbIndex: 26 },
        { label: "\\", vk: "BACKSLASH", class: "key-1-5", rgbIndex: 27 }
    ],
    // Row 2
    [
        { label: "Caps", vk: "CAPS_LOCK", class: "key-1-75", rgbIndex: 28 },
        { label: "A", vk: "A", rgbIndex: 29 },
        { label: "S", vk: "S", rgbIndex: 30 },
        { label: "D", vk: "D", rgbIndex: 31 },
        { label: "F", vk: "F", rgbIndex: 32 },
        { label: "G", vk: "G", rgbIndex: 33 },
        { label: "H", vk: "H", rgbIndex: 34 },
        { label: "J", vk: "J", rgbIndex: 35 },
        { label: "K", vk: "K", rgbIndex: 36 },
        { label: "L", vk: "L", rgbIndex: 37 },
        { label: ";", vk: "SEMICOLON", rgbIndex: 38 },
        { label: "'", vk: "QUOTE", rgbIndex: 39 },
        { label: "Enter", vk: "ENTER", class: "key-2-25", rgbIndex: 40 }
    ],
    // Row 3
    [
        { label: "Shift", vk: "LEFT_SHIFT", class: "key-2-25", rgbIndex: 41 },
        { label: "Z", vk: "Z", rgbIndex: 42 },
        { label: "X", vk: "X", rgbIndex: 43 },
        { label: "C", vk: "C", rgbIndex: 44 },
        { label: "V", vk: "V", rgbIndex: 45 },
        { label: "B", vk: "B", rgbIndex: 46 },
        { label: "N", vk: "N", rgbIndex: 47 },
        { label: "M", vk: "M", rgbIndex: 48 },
        { label: ",", vk: "COMMA", rgbIndex: 49 },
        { label: ".", vk: "PERIOD", rgbIndex: 50 },
        { label: "/", vk: "SLASH", rgbIndex: 51 },
        { label: "Shift", vk: "RIGHT_SHIFT", class: "key-2-75", rgbIndex: 52 }
    ],
    // Row 4
    [
        { label: "Ctrl", vk: "LEFT_CTRL", class: "key-1-25", rgbIndex: 53 },
        { label: "Win", vk: "LEFT_WIN", class: "key-1-25", rgbIndex: 54 },
        { label: "Alt", vk: "LEFT_ALT", class: "key-1-25", rgbIndex: 55 },
        { label: "Spacebar", vk: "SPACE", class: "key-6-25", rgbIndex: 56 },
        { label: "Alt", vk: "RIGHT_ALT", class: "key-1-25", rgbIndex: 57 },
        { label: "Win", vk: "RIGHT_WIN", class: "key-1-25", rgbIndex: 58 },
        { label: "Menu", vk: "MENU", class: "key-1-25", rgbIndex: 59 },
        { label: "Ctrl", vk: "RIGHT_CTRL", class: "key-1-25", rgbIndex: 60 }
    ]
];

// App State
let ws = null;
let currentMappings = {};
let selectedDevicePath = "";

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    renderKeyboard();
    setupDropdowns();
    setupTabNavigation();
    connectWebSocket();
    fetchInitialState();
    setupEventListeners();
});

// Render the 60% mechanical keyboard grid
function renderKeyboard() {
    const grid = document.getElementById("keyboard-grid");
    grid.innerHTML = "";

    KEYBOARD_LAYOUT.forEach(row => {
        const rowEl = document.createElement("div");
        rowEl.className = "keyboard-row";
        
        row.forEach(key => {
            const keyEl = document.createElement("div");
            keyEl.className = `key ${key.class || ""}`;
            keyEl.dataset.vk = key.vk;
            keyEl.dataset.rgbIndex = key.rgbIndex;
            
            const labelEl = document.createElement("span");
            labelEl.innerText = key.label;
            
            keyEl.appendChild(labelEl);
            rowEl.appendChild(keyEl);
        });

        grid.appendChild(rowEl);
    });
}

// Populate dropdown selectors for remapping
function setupDropdowns() {
    const srcSelect = document.getElementById("src-key");
    const tgtSelect = document.getElementById("tgt-key");

    srcSelect.innerHTML = "";
    tgtSelect.innerHTML = "";

    AVAILABLE_KEYS.forEach(key => {
        const opt1 = document.createElement("option");
        opt1.value = key;
        opt1.text = key;
        srcSelect.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = key;
        opt2.text = key;
        tgtSelect.appendChild(opt2);
    });

    // Set some default selections
    srcSelect.value = "CAPS_LOCK";
    tgtSelect.value = "ESC";
}

// Sidebar Tab switching
function setupTabNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const panels = document.querySelectorAll(".control-panel");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            navButtons.forEach(b => b.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const tabName = btn.dataset.tab;
            document.getElementById(`panel-${tabName}`).classList.add("active");
            logToConsole(`[SYSTEM] Switched panel view to: ${tabName}`);
        });
    });
}

// Connect WebSocket to Python backend for real-time alerts
function connectWebSocket() {
    const wsStatusDot = document.querySelector("#ws-status .status-dot");
    const wsStatusText = document.getElementById("ws-text");

    // Establish websocket connection
    const wsUrl = `ws://${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        wsStatusDot.className = "status-dot connected";
        wsStatusText.innerText = "Connected";
        logToConsole("[SYSTEM] WebSocket connected to controller daemon.");
    };

    ws.onclose = () => {
        wsStatusDot.className = "status-dot disconnected";
        wsStatusText.innerText = "Disconnected";
        logToConsole("[SYSTEM] WebSocket disconnected. Retrying in 3 seconds...", "error");
        setTimeout(connectWebSocket, 3000);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
}

// Handle real-time WebSocket payloads
function handleWebSocketMessage(data) {
    if (data.type === "keypress") {
        // Physical keypress captured
        const keyEl = document.querySelector(`.key[data-vk="${data.key}"]`);
        if (keyEl) {
            if (data.action === "down") {
                keyEl.classList.add("pressed");
            } else {
                keyEl.classList.remove("pressed");
            }
        }
    } else if (data.type === "rgb_update") {
        // RGB synchronization packet received from OpenRGB/Simulator
        updateKeyboardRGB(data);
    }
}

// Colorize keys on visual visualizer
function updateKeyboardRGB(data) {
    const rgbStatusDot = document.querySelector("#rgb-status .status-dot");
    const rgbStatusText = document.getElementById("rgb-text");
    
    // Update header status
    if (data.simulated) {
        rgbStatusDot.className = "status-dot simulated";
        rgbStatusText.innerText = "Simulated";
    } else {
        rgbStatusDot.className = "status-dot connected";
        rgbStatusText.innerText = `Connected (${data.devices.length} Devices)`;
    }

    // Color keys
    const keys = document.querySelectorAll(".key");
    keys.forEach(keyEl => {
        const rgbIdx = parseInt(keyEl.dataset.rgbIndex, 10);
        if (data.colors && rgbIdx < data.colors.length) {
            const hexColor = data.colors[rgbIdx];
            // Update key color border and glowing shadow
            keyEl.style.border = `1px solid ${hexColor}`;
            keyEl.style.boxShadow = `inset 0 0 8px ${hexColor}33, 0 0 6px ${hexColor}22`;
            // Subtle indicator overlay
            keyEl.style.background = `rgba(${hexToRgb(hexColor)}, 0.08)`;
        }
    });
}

function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
}

// Fetch initial remapper and RGB configurations
async function fetchInitialState() {
    try {
        const remapperResp = await fetch("/api/remapper/status");
        const remapperData = await remapperResp.json();
        
        document.getElementById("remapper-toggle").checked = remapperData.active;
        currentMappings = remapperData.mappings;
        renderMappingList();

        const rgbResp = await fetch("/api/rgb/status");
        const rgbData = await rgbResp.json();
        document.getElementById("rgb-effect").value = rgbData.effect;
        document.getElementById("rgb-speed-slider").value = rgbData.speed;
        document.querySelector(".range-val").innerText = `${rgbData.speed.toFixed(1)}x`;

        // Load hex color
        const hex = rgbToHex(rgbData.color[0], rgbData.color[1], rgbData.color[2]);
        document.getElementById("rgb-color").value = hex;
        document.querySelector(".color-hex-label").innerText = hex;
        
        // Scan for HID
        scanHIDDevices();
    } catch (err) {
        console.error("Error loading initial state:", err);
    }
}

// Binds actions and buttons
function setupEventListeners() {
    // 1. Remapper Toggle
    document.getElementById("remapper-toggle").addEventListener("change", async (e) => {
        const active = e.target.checked;
        const resp = await fetch("/api/remapper/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ active })
        });
        const res = await resp.json();
        logToConsole(`[REMAPPER] Service state changed. Active: ${res.active}`, res.active ? "success" : "system");
    });

    // 2. Add Key Mapping
    document.getElementById("add-mapping-btn").addEventListener("click", async () => {
        const src = document.getElementById("src-key").value;
        const tgt = document.getElementById("tgt-key").value;

        if (src === tgt) {
            logToConsole("[REMAPPER] Error: Cannot map a key to itself.", "error");
            return;
        }

        currentMappings[src] = tgt;
        const resp = await fetch("/api/remapper/mappings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mappings: currentMappings })
        });
        const res = await resp.json();
        
        logToConsole(`[REMAPPER] Added mapping: ${src} -> ${tgt}`, "success");
        renderMappingList();
    });

    // 3. RGB controls changes
    document.getElementById("rgb-effect").addEventListener("change", updateRGBBackend);
    document.getElementById("rgb-color").addEventListener("input", (e) => {
        document.querySelector(".color-hex-label").innerText = e.target.value;
        updateRGBBackend();
    });
    document.getElementById("rgb-speed-slider").addEventListener("input", (e) => {
        document.querySelector(".range-val").innerText = `${parseFloat(e.target.value).toFixed(1)}x`;
        updateRGBBackend();
    });

    // Show/hide color picker dynamic
    document.getElementById("rgb-effect").addEventListener("change", (e) => {
        const group = document.getElementById("color-picker-group");
        if (e.target.value === "rainbow") {
            group.style.display = "none";
        } else {
            group.style.display = "flex";
        }
    });

    // 4. HID Explorer buttons
    document.getElementById("scan-hid-btn").addEventListener("click", scanHIDDevices);
    document.getElementById("hid-device-select").addEventListener("change", connectHIDDevice);
    document.getElementById("send-hex-btn").addEventListener("click", sendRawHexPacket);
    document.getElementById("clear-console-btn").addEventListener("click", () => {
        document.getElementById("console-log").innerHTML = "";
    });

    // Quick Command Helpers
    document.getElementById("cmd-version").addEventListener("click", () => {
        document.getElementById("hex-input").value = "01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00";
        sendRawHexPacket();
    });
    
    document.getElementById("cmd-get-key").addEventListener("click", () => {
        // Command 0x11, Layer 0, Row 0, Col 1
        document.getElementById("hex-input").value = "11 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00";
        sendRawHexPacket();
    });

    document.getElementById("cmd-set-key").addEventListener("click", () => {
        // Command 0x12, Layer 0, Row 0, Col 1, Keycode Backspace (0x002A -> MSB 0x00, LSB 0x2A)
        document.getElementById("hex-input").value = "12 00 00 01 00 2A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00";
        sendRawHexPacket();
    });
}

// Call backend to update active RGB variables
async function updateRGBBackend() {
    const effect = document.getElementById("rgb-effect").value;
    const colorHex = document.getElementById("rgb-color").value;
    const speed = parseFloat(document.getElementById("rgb-speed-slider").value);
    
    // Convert hex to rgb list
    const r = parseInt(colorHex.slice(1, 3), 16);
    const g = parseInt(colorHex.slice(3, 5), 16);
    const b = parseInt(colorHex.slice(5, 7), 16);

    await fetch("/api/rgb/effect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            effect,
            color: [r, g, b],
            speed
        })
    });
}

// Render active mapping cards in remapping view
function renderMappingList() {
    const list = document.getElementById("active-mappings-list");
    list.innerHTML = "";

    const keys = Object.keys(currentMappings);
    if (keys.length === 0) {
        list.innerHTML = '<div class="empty-list-msg">No active mappings.</div>';
        return;
    }

    keys.forEach(src => {
        const tgt = currentMappings[src];
        const item = document.createElement("div");
        item.className = "mapping-item";
        item.innerHTML = `
            <span><code>${src}</code> &rarr; <code>${tgt}</code></span>
            <button class="mapping-remove-btn" data-src="${src}">&times;</button>
        `;
        
        item.querySelector(".mapping-remove-btn").addEventListener("click", async (e) => {
            const keyToRemove = e.target.dataset.src;
            delete currentMappings[keyToRemove];
            
            await fetch("/api/remapper/mappings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mappings: currentMappings })
            });
            logToConsole(`[REMAPPER] Removed mapping for ${keyToRemove}`, "system");
            renderMappingList();
        });

        list.appendChild(item);
    });
}

// Call backend to scan HID USB Devices
async function scanHIDDevices() {
    logToConsole("[HID] Scanning USB HID endpoints...");
    try {
        const resp = await fetch("/api/hid/devices");
        const res = await resp.json();
        
        const select = document.getElementById("hid-device-select");
        select.innerHTML = '<option value="">-- Choose Keyboard --</option>';

        if (res.devices && res.devices.length > 0) {
            res.devices.forEach(dev => {
                const opt = document.createElement("option");
                opt.value = dev.path;
                opt.text = `${dev.manufacturer} - ${dev.product} ${dev.is_via ? "[VIA]" : ""}`;
                select.appendChild(opt);
            });
            
            // Auto connect to simulator by default for demonstration
            const simDev = res.devices.find(d => d.path.includes("SIMULATED"));
            if (simDev) {
                select.value = simDev.path;
                connectHIDDevice({ target: { value: simDev.path } });
            }
        }
    } catch (err) {
        logToConsole(`[HID] Scan failed: ${err.message}`, "error");
    }
}

// Connect to selected USB Device
async function connectHIDDevice(e) {
    const path = e.target.value;
    if (!path) return;

    try {
        const resp = await fetch("/api/hid/connect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path })
        });
        const res = await resp.json();

        if (res.status === "success") {
            selectedDevicePath = path;
            const text = res.device.product;
            document.getElementById("device-text").innerText = text;
            logToConsole(`[HID] Device Connected: ${text}`, "success");
        }
    } catch (err) {
        logToConsole(`[HID] Connection error: ${err.message}`, "error");
    }
}

// Send custom hex packet from input line to backend
async function sendRawHexPacket() {
    const inputEl = document.getElementById("hex-input");
    const rawVal = inputEl.value.trim();
    if (!rawVal) return;

    if (!selectedDevicePath) {
        logToConsole("[HID] Error: Connect a keyboard device first.", "error");
        return;
    }

    logToConsole(`[TX] ${rawVal}`, "tx");

    try {
        const resp = await fetch("/api/hid/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ report_hex: rawVal })
        });
        const res = await resp.json();

        if (resp.ok) {
            logToConsole(`[RX] ${res.response_hex}`, "rx");
        } else {
            logToConsole(`[HID] Error response: ${res.detail}`, "error");
        }
    } catch (err) {
        logToConsole(`[HID] Transmit failed: ${err.message}`, "error");
    }
}

// Print log messages to visual scrolling logger
function logToConsole(message, type = "system") {
    const logEl = document.getElementById("console-log");
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    
    const timeStr = new Date().toLocaleTimeString();
    line.innerText = `[${timeStr}] ${message}`;
    
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight; // Autoscroll
}

// Utility formatting converters
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}
