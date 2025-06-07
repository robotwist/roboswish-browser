git clone https://github.com/yourusername/roboswish.git
# RoboSwish

RoboSwish is a productivity launcher for your desktop, combining browser mode presets, a focus timer, and a local AI chat assistant powered by Ollama. Designed for speed, clarity, and privacy, RoboSwish helps you switch contexts, stay focused, and get answers—all from a single, modern interface.

## Features

- **Mode Launcher:** Instantly open sets of browser tabs for different workflows (e.g., Work, Coding, Research, Finance). Modes are fully customizable.
- **Super Focus Burst:** A 5-minute tunnel vision timer to help you concentrate on a single task.
- **Theme Switching:** Visually distinct color schemes for each mode, signaling your brain to switch gears.
- **Ollama Chat:** Local LLM-powered chat assistant (LLaMA or compatible models) for private, fast, and offline AI help.
- **Onboarding & Tour:** Friendly, LLM-style onboarding dialog and guided tour for new users.
- **Settings UI:** Easily configure your browser command, Ollama endpoint/model, and more via a settings dialog. Settings are saved to `.env`.
- **Robust Error Handling:** Clear error messages and logging for connectivity, chat, and configuration issues.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/roboswish-browser.git
cd roboswish-browser
```

### 2. Install Python Dependencies

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install and Run Ollama (for Chat)

Follow instructions at [https://ollama.com/](https://ollama.com/) to install and start Ollama. Download a model (e.g., llama3):

```bash
ollama run llama3
```

### 4. Configure RoboSwish

On first launch, RoboSwish will guide you through onboarding and settings. You can also edit the `.env` file directly to set:

- `BROWSER_COMMAND` (e.g., `google-chrome` or `firefox`)
- `OLLAMA_ENDPOINT` (default: `http://localhost:11434`)
- `OLLAMA_MODEL` (e.g., `llama3`)

## Usage

Run the app:

```bash
python roboswish.py
```

Or use the packaged executable (see Packaging below).

### Main Modes

- **Mode Launcher:** Select or edit modes to launch browser tabs for your workflow.
- **Focus Timer:** Start a 5-minute burst to block distractions.
- **Chat:** Use the sidebar to chat with your local LLM.
- **Settings:** Access via the gear icon to change browser/LLM config.
- **Onboarding/Tour:** Shown on first launch or via the Help menu.

## Packaging & Distribution

You can build a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon public/images/roboswish_angle.png roboswish.py
```

The executable will be in the `dist/` folder. Test it before distribution.

### GitHub Releases

1. Commit and push all changes.
2. Tag a new release:
   ```bash
   git tag v1.1
   git push --tags
   ```
3. Go to your GitHub repo, create a new Release, upload the executable, and add release notes (see below).

## Configuration

Settings are stored in `.env` in the project root. You can edit this file or use the Settings dialog in the app.

Example `.env`:

```
BROWSER_COMMAND=google-chrome
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Troubleshooting

- **Ollama chat not working?**
  - Ensure Ollama is running and the endpoint/model in `.env` are correct.
  - Check the log file (`roboswish_debug.log`) for errors.
- **Browser not launching?**
  - Make sure your `BROWSER_COMMAND` is correct and in your PATH.
- **App won’t start?**
  - Check Python version (3.8+ recommended) and dependencies.
  - Review the log file for details.

## Release Notes

### v1.1 (2025-06-07)
- Async Ollama chat (background thread, non-blocking UI)
- Modern onboarding and tour dialogs with styled HTML/CSS
- Settings dialog for browser/LLM config (saves to `.env`)
- Improved error handling and logging
- Enhanced chat UI formatting (user: green, LLM: glowing blue)
- Fixed icon path and packaging issues
- Expanded README with install, usage, troubleshooting, and release instructions

### v1.0 (2025-05-30)
- Initial public release: mode launcher, focus timer, Ollama chat, basic settings

## License

MIT License. See [LICENSE](LICENSE) for details.

