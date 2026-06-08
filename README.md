# Antigravity Universal Keyboard Hub

Um painel desktop moderno e integrado para remapeamento global de teclas, controle de iluminação RGB e simulação de protocolo USB HID (QMK/VIA).

## 🚀 Funcionalidades

1. **Remapeamento Global (Software):** 
   - Intercepta teclas fisicamente no nível do sistema operacional.
   - **Windows**: Implementado usando hooks nativos Win32 de baixo nível (`SetWindowsHookExW`).
   - **Linux**: Implementado via subsistema `evdev` de leitura e emulação de teclado virtual no kernel (`uinput`).
2. **Controle RGB (Iluminação):**
   - Conectividade automática com o daemon do **OpenRGB** (porta `6742`).
   - Fallback para simulador visual integrado com efeitos clássicos: Estático, Ondas Neon, Respiração e Arco-íris.
3. **USB HID & Terminal VIA:**
   - Scanner de portas USB para detectar teclados compatíveis com QMK/VIA.
   - Console terminal interativo para codificar/decodificar comandos hexadecimais brutos de 32 bytes (gravação na EEPROM).
   - Emulador de firmware VIA integrado para fins educacionais e testes.

---

## 🛠️ Arquitetura

O sistema é dividido em duas partes principais:
- **Backend (Python 3.14+)**: Executa o servidor FastAPI, lida com threads de pooling de inputs e conexões SDK/HID.
- **Frontend (Web Dashboard)**: Construído com HTML, CSS Vanilla com design Glassmorphism responsivo, e JavaScript com WebSockets assíncronos.

---

## 💻 Instalação & Execução

### Pré-requisitos
- Python 3.10 ou superior instalado.

### 1. Clonando e Instalando Dependências
```bash
pip install fastapi uvicorn pynput
```
*(No Linux, instale também a biblioteca `evdev`: `pip install evdev`)*

### 2. Executando o Servidor

#### No Windows:
Abra o prompt de comando como **Administrador** (necessário para registrar hooks globais no Windows) e execute:
```bash
python backend/main.py
```

#### No Linux:
Execute com privilégios de superusuário (necessário para abrir `/dev/input/` e gravar em `/dev/uinput`):
```bash
sudo python backend/main.py
```

### 3. Acessando a Interface
Abra o navegador no endereço:
👉 **http://127.0.0.1:8085**
