# 🐧 Tutorial de Configuração e Uso no Linux

Este guia detalha o passo a passo completo para configurar, instalar e executar o **Universal Keyboard Controller Hub** em sistemas operacionais baseados em Linux (como Ubuntu, Debian, Fedora, Arch Linux, Mint, etc.).

---

## 🛠️ Passo 1: Preparar o Sistema e Clonar o Código

Abra o seu terminal no Linux e siga os passos abaixo:

1. Atualize a lista de pacotes do sistema:
   ```bash
   sudo apt update
   ```
2. Certifique-se de ter o Git, o Python 3 e o instalador de pacotes `pip` instalados:
   ```bash
   sudo apt install git python3 python3-pip python3-venv -y
   ```
3. Clone o seu repositório do GitHub (Substitua pelo link correto do seu repo):
   ```bash
   git clone https://github.com/wendell0102/universal-keyboard-controller.git
   cd universal-keyboard-controller
   ```

---

## 📦 Passo 2: Configurar o Ambiente Virtual (Recomendado)

Criar um ambiente virtual isola os pacotes do projeto para não interferir com outras aplicações do sistema:

1. Crie o ambiente virtual:
   ```bash
   python3 -m venv .venv
   ```
2. Ative o ambiente virtual:
   ```bash
   source .venv/bin/activate
   ```
   *(Você verá `.venv` antes do prompt do terminal, indicando que ele está ativo).*

---

## 💾 Passo 3: Instalar as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias para rodar o servidor FastAPI, capturar entradas de hardware e interagir com o kernel Linux:

```bash
pip install fastapi uvicorn pynput evdev
```

---

## 🚀 Passo 4: Executar o Servidor (Com Acesso de Root)

No Linux, a leitura de inputs do teclado físico (`/dev/input/`) e a simulação de teclas virtuais via módulo `uinput` exigem privilégios de superusuário.

1. **Inicie o servidor utilizando o Python do seu ambiente virtual com `sudo`**:
   ```bash
   sudo .venv/bin/python backend/main.py
   ```
2. O terminal exibirá mensagens de inicialização do Uvicorn parecidas com esta:
   ```text
   INFO:     Started server process [12345]
   INFO:     Waiting for application startup.
   INFO:KeyboardController:Starting up controller services...
   [Remapper] Linux Evdev Service started.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8085 (Press CTRL+C to quit)
   ```

3. Abra o seu navegador web no Linux e acesse o endereço:
   👉 **[http://127.0.0.1:8085](http://127.0.0.1:8085)**

---

## ⚙️ Passo 5: Configurações Opcionais (Udev Rules)

### Para rodar o VIA HID Scanner sem travar permissões USB
Para que o backend consiga se comunicar com o seu teclado mecânico físico compatível com VIA sem dar erro de permissão negada na porta USB:

1. Crie um arquivo de regras `udev`:
   ```bash
   sudo nano /etc/udev/rules.d/99-via.rules
   ```
2. Cole a seguinte linha dentro do arquivo:
   ```text
   KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666", TAG+="uaccess"
   ```
3. Salve o arquivo (no nano: pressione `Ctrl+O`, `Enter`, depois `Ctrl+X`).
4. Atualize as regras do sistema:
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
5. Desplugue e plugue o seu teclado físico novamente na porta USB.

---

## 🛑 Como parar o servidor?
No terminal onde o servidor está rodando, pressione **`Ctrl + C`**. Os recursos de entrada do teclado físico serão liberados de volta ao sistema operacional automaticamente.
