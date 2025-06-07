# Onboarding, settings, and .env support
import sys
import json
import subprocess
import requests  # for Ollama API calls
import threading
import logging
import os
from PyQt5.QtGui import QIcon
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup debug logging
logging.basicConfig(
    filename="roboswish_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QHBoxLayout, QTextEdit, QLineEdit, QMessageBox, QSizePolicy, QSplitter, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal


# Update config loading
MODES_FILE = "modes.json"
BROWSER_COMMAND = os.environ.get("BROWSER_COMMAND", "google-chrome")
FOCUS_BURST_SECONDS = 5 * 60
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")

# Define color themes for modes
THEMES = {
    "RoboSwish Default": {"bg": "#0F1419", "fg": "#00FF88"},
    "Focus Mode": {"bg": "#1E1E1E", "fg": "#E0E0E0"},
    "Super Focus Burst": {"bg": "#0F1419", "fg": "#00FF88"},
}

# --- Async Chat Worker ---

class OllamaWorker(QThread):
    result = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": self.prompt}
                ]
            }
            logging.debug(f"Sending to Ollama: {payload}")
            r = requests.post(OLLAMA_API_URL, json=payload, timeout=60, stream=True)
            r.raise_for_status()
            full_content = ""
            last_data = None
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode('utf-8'))
                    last_data = data
                    logging.debug(f"[Ollama API stream] {data}")
                    if "error" in data:
                        self.error.emit(f"[Ollama error: {data['error']}]\nRaw: {data}")
                        return
                    if "message" in data and data["message"].get("content"):
                        full_content += data["message"]["content"]
                except Exception as e:
                    logging.error(f"[Error parsing Ollama stream: {e}")
            if full_content.strip():
                self.result.emit(full_content.strip())
            elif last_data:
                self.error.emit(f"[No valid response from Ollama]\nRaw: {last_data}")
            else:
                self.error.emit("[No response from Ollama]")
        except Exception as e:
            logging.error(f"[Error calling Ollama API: {e}")
            self.error.emit(f"[Error calling Ollama API: {e}]")


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to RoboSwish!")
        self.setMinimumWidth(420)
        icon_path = os.path.join(os.path.dirname(__file__), "public/images/roboswish_angle.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        # Styled label
        label = QLabel("""
            <div style='font-size:22px; font-weight:bold; color:#00FF88; margin-bottom:10px;'>🤖 Welcome to RoboSwish!</div>
            <div style='font-size:15px; color:#B3E5FC; text-shadow:0 0 8px #4FC3F7;'>
                I'm your fairly smart sidebar copilot.<br>Would you like a quick tour of the features?
            </div>
        """)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Button styles
        btn_style = (
            "QPushButton { background-color: #15232e; color: #00FF88; font-weight: bold; padding: 10px 18px; border-radius: 8px; font-size: 15px; }"
            "QPushButton:hover { background-color: #00FF88; color: #0F1419; }"
        )

        self.tour_btn = QPushButton("Show me the tour!")
        self.tour_btn.setStyleSheet(btn_style)
        self.tour_btn.clicked.connect(self.show_tour)
        self.skip_btn = QPushButton("Skip for now")
        self.skip_btn.setStyleSheet(btn_style)
        self.skip_btn.clicked.connect(self.reject)
        btns = QHBoxLayout()
        btns.addWidget(self.tour_btn)
        btns.addWidget(self.skip_btn)
        layout.addLayout(btns)

        # Set dialog background and border
        self.setStyleSheet("""
            QDialog {
                background-color: #0F1419;
                color: #00FF88;
                border: 2px solid #00FF88;
                border-radius: 16px;
            }
        """)
        self.setLayout(layout)

    def show_tour(self):
        # Custom styled tour dialog
        tour = QDialog(self)
        tour.setWindowTitle("RoboSwish Tour")
        tour.setMinimumWidth(420)
        tour.setStyleSheet("""
            QDialog {
                background-color: #0F1419;
                color: #00FF88;
                border: 2px solid #00FF88;
                border-radius: 16px;
            }
            QLabel { color: #B3E5FC; font-size: 15px; }
        """)
        vbox = QVBoxLayout()
        vbox.setContentsMargins(30, 30, 30, 30)
        vbox.setSpacing(16)
        msg = QLabel("""
            <div style='font-size:18px; color:#00FF88; font-weight:bold; margin-bottom:10px;'>🚀 RoboSwish Tour</div>
            <ul style='font-size:15px; color:#B3E5FC; text-shadow:0 0 8px #4FC3F7;'>
                <li><b>Mode Launcher:</b> Launches browser tabs for your favorite workflows.</li>
                <li><b>Super Focus Burst:</b> 5-minute tunnel vision timer.</li>
                <li><b>Theme Switching:</b> Visually unique color schemes.</li>
                <li><b>AI Chat:</b> Local LLM assistant in the sidebar.</li>
                <li><b>Settings:</b> Click the gear icon to change browser, model, or API endpoint!</li>
            </ul>
            <div style='margin-top:10px; color:#00FF88; font-style:italic;'>Ready to boost your productivity? 🚀</div>
        """)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignLeft)
        vbox.addWidget(msg)
        ok_btn = QPushButton("Let's go!")
        ok_btn.setStyleSheet(
            "QPushButton { background-color: #00FF88; color: #0F1419; font-weight: bold; padding: 10px 18px; border-radius: 8px; font-size: 15px; }"
            "QPushButton:hover { background-color: #15232e; color: #00FF88; }"
        )
        ok_btn.clicked.connect(tour.accept)
        vbox.addWidget(ok_btn, alignment=Qt.AlignCenter)
        tour.setLayout(vbox)
        tour.exec_()
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, parent, browser_cmd, ollama_url, ollama_model):
        super().__init__(parent)
        self.setWindowTitle("RoboSwish Settings")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        self.browser_input = QLineEdit(browser_cmd)
        self.ollama_url_input = QLineEdit(ollama_url)
        self.ollama_model_input = QLineEdit(ollama_model)
        layout.addWidget(QLabel("Browser Command:"))
        layout.addWidget(self.browser_input)
        layout.addWidget(QLabel("Ollama API URL:"))
        layout.addWidget(self.ollama_url_input)
        layout.addWidget(QLabel("Ollama Model Name:"))
        layout.addWidget(self.ollama_model_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_settings(self):
        return self.browser_input.text(), self.ollama_url_input.text(), self.ollama_model_input.text()

class ChatSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")
        self.layout = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #181818; color: #e0e0e0; padding: 5px;")
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask RoboSwish...")
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        # Add a close button for the sidebar
        self.close_btn = QPushButton("Close Chat")
        self.close_btn.clicked.connect(self.close_sidebar)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)

        self.layout.addWidget(QLabel("🤖 RoboSwish Chat Assistant"))
        self.layout.addWidget(self.chat_history)
        self.layout.addLayout(input_layout)
        self.layout.addWidget(self.close_btn)
        self.setLayout(self.layout)

        self.worker = None

    def close_sidebar(self):
        self.setVisible(False)


    def send_message(self):
        user_text = self.chat_input.text().strip()
        if not user_text:
            return
        self.append_message("You", user_text)
        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self.chat_input.setEnabled(False)
        self.append_message("Robo", "<i>Thinking...</i>")
        try:
            self.worker = OllamaWorker(user_text)
            self.worker.result.connect(self.handle_result)
            self.worker.error.connect(self.handle_error)
            self.worker.start()
        except Exception as e:
            self.append_message("Robo", f"<span style='color:red;'>[Failed to start chat worker: {e}]</span>")
            QMessageBox.critical(self, "Chat Error", f"Failed to start chat worker thread.\n{e}")

    def handle_result(self, message):
        # Remove last "Thinking..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove newline
        self.chat_history.setTextCursor(cursor)
        self.append_message("Robo", message)
        self.send_btn.setEnabled(True)
        self.chat_input.setEnabled(True)

    def handle_error(self, message):
        # Remove last "Thinking..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove newline
        self.chat_history.setTextCursor(cursor)
        self.append_message("Robo", f"<span style='color:red;'>{message}</span>")
        self.send_btn.setEnabled(True)
        self.chat_input.setEnabled(True)
        # Also show a popup for critical errors
        QMessageBox.critical(self, "Ollama Chat Error", message)

    def handle_result(self, message):
        # Remove last "Thinking..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove newline
        self.chat_history.setTextCursor(cursor)
        self.append_message("Robo", message)
        self.send_btn.setEnabled(True)
        self.chat_input.setEnabled(True)

    def append_message(self, sender, message):
        if sender == "You":
            # Bright green for user
            self.chat_history.append(
                "<div style='margin:8px 0;'><b style='color:#00FF88;'>You:</b> "
                "<span style='color:#00FF88;font-weight:bold;'>{}</span></div>".format(message)
            )
        else:
            # Glowing light blue for LLM (Robo)
            self.chat_history.append(
                "<div style='margin:8px 0;'><b style='color:#4FC3F7;text-shadow:0 0 8px #B3E5FC;'>Robo:</b> "
                "<span style='color:#4FC3F7;text-shadow:0 0 8px #B3E5FC;font-weight:bold;'>{}</span></div>".format(message)
            )
class ModeEditorDialog(QDialog):
    def __init__(self, parent, modes):
        super().__init__(parent)
        self.setWindowTitle("Edit Modes")
        self.resize(400, 300)
        self.modes = modes.copy()
        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.populate()
        self.list_widget.itemDoubleClicked.connect(self.edit_mode)

        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Mode")
        add_btn.clicked.connect(self.add_mode)
        del_btn = QPushButton("Delete Mode")
        del_btn.clicked.connect(self.delete_mode)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        self.layout.insertLayout(1, btn_layout)

        # Add a note for browser theming limitation
        self.layout.addWidget(QLabel("<i>Note: Browser theming/profile support is limited. See README.</i>"))

    def populate(self):
        self.list_widget.clear()
        for mode, urls in self.modes.items():
            item = QListWidgetItem(f"{mode}: {', '.join(urls)}")
            item.setData(Qt.UserRole, mode)
            self.list_widget.addItem(item)

    def add_mode(self):
        name, ok = QInputDialog.getText(self, "Add Mode", "Mode name:")
        if ok and name:
            urls, ok2 = QInputDialog.getText(self, "Add URLs", "Comma-separated URLs:")
            if ok2:
                self.modes[name] = [u.strip() for u in urls.split(",") if u.strip()]
                self.populate()

    def edit_mode(self, item):
        mode = item.data(Qt.UserRole)
        urls, ok = QInputDialog.getText(self, "Edit URLs", f"Edit URLs for {mode} (comma-separated):", text=", ".join(self.modes[mode]))
        if ok:
            self.modes[mode] = [u.strip() for u in urls.split(",") if u.strip()]
            self.populate()

    def delete_mode(self):
        item = self.list_widget.currentItem()
        if item:
            mode = item.data(Qt.UserRole)
            del self.modes[mode]
            self.populate()

    def get_modes(self):
        return self.modes


def check_ollama_available(model_name="llama2"):
    """Check if Ollama API is reachable and the model is available."""
    try:
        # Try a simple /api/tags call to see if Ollama is up
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        tags = r.json().get("models", [])
        if not any(model_name in m.get("name", "") for m in tags):
            return False, f"Model '{model_name}' not found in Ollama. Run: ollama pull {model_name}"
        return True, None
    except Exception as e:
        return False, f"Ollama API not reachable: {e}"


class RoboSwish(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RoboSwish")
        self.resize(800, 500)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setMinimumSize(600, 400)
        self.current_theme = "RoboSwish Default"
        self.focus_timer = None
        self.time_left = FOCUS_BURST_SECONDS

        icon_path = os.path.join(os.path.dirname(__file__), "public/images/roboswish_angle.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Onboarding dialog
        if not os.path.exists(".roboswish_onboarded"):
            dlg = OnboardingDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                with open(".roboswish_onboarded", "w") as f:
                    f.write("onboarded\n")

        self.initUI()
        self.load_modes()
        self.apply_theme()
        self.check_ollama_status()
        # Settings button
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        self.left_layout.addWidget(self.settings_btn)

    def open_settings(self):
        dlg = SettingsDialog(self, BROWSER_COMMAND, OLLAMA_API_URL, OLLAMA_MODEL)
        if dlg.exec_() == QDialog.Accepted:
            browser, url, model = dlg.get_settings()
            # Save to .env
            with open(".env", "w") as f:
                f.write(f"BROWSER_COMMAND={browser}\nOLLAMA_API_URL={url}\nOLLAMA_MODEL={model}\n")
            QMessageBox.information(self, "Settings Saved", "Restart RoboSwish to apply new settings.")

    def check_ollama_status(self):
        def do_check():
            ok, msg = check_ollama_available()
            if not ok:
                def show():
                    QMessageBox.warning(self, "Ollama Not Available", f"RoboSwish AI chat will not work.\n\n{msg}")
                QTimer.singleShot(0, show)
        threading.Thread(target=do_check, daemon=True).start()

    def initUI(self):
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # Left side: Mode buttons and focus timer
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)

        self.title_label = QLabel("🚀 RoboSwish: Mode Launcher")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.left_layout.addWidget(self.title_label)

        self.mode_buttons = []
        self.modes = {}

        # Mode editor button
        self.edit_modes_btn = QPushButton("Edit Modes")
        self.edit_modes_btn.clicked.connect(self.open_mode_editor)
        self.left_layout.addWidget(self.edit_modes_btn)

        self.left_layout.addStretch()

        # Focus burst controls
        self.focus_btn = QPushButton("Start 5-Minute Super Focus Burst")
        self.focus_btn.clicked.connect(self.start_focus_burst)
        self.left_layout.addWidget(self.focus_btn)

        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.left_layout.addWidget(self.timer_label)

        # Theme switcher buttons (for demonstration)
        self.left_layout.addWidget(QLabel("Switch Theme:"))
        for theme_name in THEMES.keys():
            btn = QPushButton(theme_name)
            btn.clicked.connect(lambda checked, t=theme_name: self.switch_theme(t))
            self.left_layout.addWidget(btn)

        self.left_layout.addStretch()

        # Right side: Chat sidebar
        self.chat_sidebar = ChatSidebar()

        # Splitter to allow resizing between left panel and chat
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.chat_sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.main_layout.addWidget(splitter)

    def load_modes(self):
        try:
            with open(MODES_FILE, "r") as f:
                self.modes = json.load(f)
        except Exception as e:
            self.left_layout.addWidget(QLabel(f"Error loading modes: {e}"))
            self.modes = {}

        # Create buttons for each mode
        # Remove old mode buttons
        for btn in getattr(self, 'mode_buttons', []):
            self.left_layout.removeWidget(btn)
            btn.deleteLater()
        self.mode_buttons = []
        insert_at = 2  # After title and edit button
        for mode_name, urls in self.modes.items():
            btn = QPushButton(mode_name)
            btn.clicked.connect(lambda checked, u=urls: self.launch_mode(u))
            self.left_layout.insertWidget(insert_at, btn)
            self.mode_buttons.append(btn)
            insert_at += 1
    def open_mode_editor(self):
        dlg = ModeEditorDialog(self, self.modes)
        if dlg.exec_() == QDialog.Accepted:
            self.modes = dlg.get_modes()
            # Save to file
            try:
                with open(MODES_FILE, "w") as f:
                    json.dump(self.modes, f, indent=2)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save modes: {e}")
            self.load_modes()

    def apply_theme(self):
        theme = THEMES.get(self.current_theme, THEMES["RoboSwish Default"])
        bg = theme["bg"]
        fg = theme["fg"]

        self.setStyleSheet(f"background-color: {bg}; color: {fg};")
        self.title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {fg};")

        for btn in self.mode_buttons + [self.focus_btn]:
            btn.setStyleSheet(f"background-color: #15232e; color: {fg}; padding: 10px;")

        self.timer_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {fg};")

        # Also style chat sidebar colors dynamically
        self.chat_sidebar.setStyleSheet(f"background-color: {bg}; color: {fg};")
        self.chat_sidebar.chat_history.setStyleSheet(f"background-color: #181818; color: {fg}; padding: 5px;")
        self.chat_sidebar.chat_input.setStyleSheet(f"background-color: #222; color: {fg}; padding: 5px;")
        self.chat_sidebar.send_btn.setStyleSheet(f"background-color: #004d2e; color: {fg}; padding: 5px;")

    def switch_theme(self, theme_name):
        self.current_theme = theme_name
        self.apply_theme()

    def launch_mode(self, urls):
        if not urls or self.focus_timer:
            return
        command = [BROWSER_COMMAND, "--new-window"] + urls
        try:
            subprocess.Popen(command)
        except Exception as e:
            print(f"Failed to launch browser: {e}")

    def start_focus_burst(self):
        if self.focus_timer:
            return  # Already running

        self.time_left = FOCUS_BURST_SECONDS
        self.update_timer_label()
        self.focus_btn.setEnabled(False)
        for btn in self.mode_buttons:
            btn.setEnabled(False)

        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self.tick)
        self.focus_timer.start(1000)

    def tick(self):
        self.time_left -= 1
        self.update_timer_label()
        if self.time_left <= 0:
            self.focus_timer.stop()
            self.focus_timer = None
            self.timer_label.setText("")
            self.focus_btn.setEnabled(True)
            for btn in self.mode_buttons:
                btn.setEnabled(True)
            QMessageBox.information(self, "Focus Burst Complete", "5 minutes of super focus is up! Time for a break or next burst.")

    def update_timer_label(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f"⏱️  Focus Time Left: {minutes:02d}:{seconds:02d}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    swish = RoboSwish()
    swish.show()
    sys.exit(app.exec_())
