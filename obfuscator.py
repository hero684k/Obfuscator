import sys
import os
import re
import base64
import random
import string
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QGroupBox, QFrame,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QSize, QTimer
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QBrush
)

LANG = "RU"

TEXTS = {
    "RU": {
        "title": "OBFUSCATOR v1.0",
        "source": "Источник",
        "paste": "Вставить код",
        "browse": "Выбрать файл",
        "mode": "Режим",
        "universal": "Универсальный",
        "by_type": "По типу",
        "type_label": "Тип",
        "level": "Уровень",
        "easy": "🟢 Лёгкий",
        "medium": "🟡 Средний",
        "hard": "🟠 Сложный",
        "maximum": "🔴 Максимальный",
        "obfuscate": "ОБФУСЦИРОВАТЬ",
        "result": "Результат",
        "save": "Сохранить как...",
        "placeholder_input": "Вставьте код сюда...",
        "placeholder_output": "Результат появится здесь...",
        "error_no_code": "Введите код или выберите файл!",
        "error_no_result": "Нет результата для сохранения!",
        "saved": "Сохранено",
    },
    "EN": {
        "title": "OBFUSCATOR v1.0",
        "source": "Source",
        "paste": "Paste Code",
        "browse": "Choose File",
        "mode": "Mode",
        "universal": "Universal",
        "by_type": "By Type",
        "type_label": "Type",
        "level": "Level",
        "easy": "🟢 Easy",
        "medium": "🟡 Medium",
        "hard": "🟠 Hard",
        "maximum": "🔴 Maximum",
        "obfuscate": "OBFUSCATE",
        "result": "Result",
        "save": "Save As...",
        "placeholder_input": "Paste your code here...",
        "placeholder_output": "Result will appear here...",
        "error_no_code": "Enter code or select a file!",
        "error_no_result": "No result to save!",
        "saved": "Saved",
    }
}

def t(key):
    return TEXTS[LANG].get(key, key)


class NoWhiteBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(QBrush(QColor("#A78BFA")))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QBrush(QColor("#3D3D5A")))
        else:
            painter.setBrush(QBrush(QColor("#1A1A2E")))

        painter.drawRoundedRect(QRect(option.rect.adjusted(2, 1, -2, -1)), 8, 8)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QColor("#FFFFFF"))
        else:
            painter.setPen(QColor("#EDF2F7"))

        font = painter.font()
        font.setPixelSize(13)
        painter.setFont(font)
        painter.drawText(
            QRect(option.rect.adjusted(12, 0, -12, 0)),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            index.data()
        )
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(0, 32)


class CodeObfuscator:
    def __init__(self, code, lang="universal", level="medium"):
        self.code = code
        self.lang = lang
        self.level = level
        self.var_map = {}
        self.func_map = {}

    def run(self):
        code = self.code
        code = self.remove_comments(code)
        code = self.minify(code)
        if self.level in ("medium", "hard", "maximum") and self.lang != "universal":
            code = self.rename_variables(code)
            code = self.rename_functions(code)
        if self.level in ("hard", "maximum"):
            code = self.encrypt_strings(code)
        if self.level == "maximum":
            code = self.split_strings_to_chr(code)
            code = self.xor_numbers(code)
            code = self.add_dead_code(code)
        return code

    def remove_comments(self, code):
        patterns = {
            "python":   [(r'#.*', ''), (r'""".*?"""', lambda m: m.group(0)), (r"'''.*?'''", lambda m: m.group(0))],
            "java":     [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "kotlin":   [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "js":       [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "ts":       [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "lua":      [(r'--.*', ''), (r'--\[\[.*?\]\]', '', re.DOTALL)],
            "cs":       [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "c":        [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "cpp":      [(r'//.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "php":      [(r'//.*', ''), (r'#.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
            "ruby":     [(r'#.*', ''), (r'=begin.*?=end', '', re.DOTALL)],
            "universal":[(r'//.*', ''), (r'#.*', ''), (r'--.*', ''), (r'/\*.*?\*/', '', re.DOTALL)],
        }
        for pattern, repl, *flags in patterns.get(self.lang, patterns["universal"]):
            flag = flags[0] if flags else 0
            if callable(repl):
                code = re.sub(pattern, repl, code, flags=flag)
            else:
                code = re.sub(pattern, repl, code, flags=flag)
        return code

    def minify(self, code):
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        return '\n'.join(lines)

    def rename_variables(self, code):
        var_patterns = {
            "python": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?!=)',
            "java":   r'\b(?:int|float|double|String|boolean|char|long|short|byte)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "kotlin": r'\b(?:val|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "js":     r'\b(?:let|var|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            "ts":     r'\b(?:let|var|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            "lua":    r'\b(?:local\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
            "cs":     r'\b(?:int|float|double|string|bool|char|long|short|byte|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "c":      r'\b(?:int|float|double|char|long|short|void)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "cpp":    r'\b(?:int|float|double|char|long|short|void|bool|auto)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "php":    r'\$([a-zA-Z_][a-zA-Z0-9_]*)',
            "ruby":   r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
        }
        pattern = var_patterns.get(self.lang)
        if not pattern:
            return code
        def replacer(match):
            var_name = match.group(1)
            if var_name not in self.var_map:
                self.var_map[var_name] = '_' + ''.join(random.choices(string.ascii_lowercase, k=8))
            return match.group(0).replace(var_name, self.var_map[var_name], 1)
        return re.sub(pattern, replacer, code)

    def rename_functions(self, code):
        func_patterns = {
            "python": r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "java":   r'\b(?:public|private|protected)?\s*(?:static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            "kotlin": r'\b(?:fun)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "js":     r'\b(?:function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            "ts":     r'\b(?:function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            "lua":    r'\b(?:function)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "cs":     r'\b(?:public|private|protected)?\s*(?:static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "c":      r'\b\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            "cpp":    r'\b\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            "php":    r'\b(?:function)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            "ruby":   r'\b(?:def)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        }
        pattern = func_patterns.get(self.lang)
        if not pattern:
            return code
        def replacer(match):
            func_name = match.group(1)
            if func_name not in self.func_map:
                self.func_map[func_name] = '_f' + ''.join(random.choices(string.ascii_lowercase, k=6))
            return match.group(0).replace(func_name, self.func_map[func_name], 1)
        return re.sub(pattern, replacer, code)

    def encrypt_strings(self, code):
        def encrypt(match):
            s = match.group(1)
            encoded = base64.b64encode(s.encode()).decode()
            return f'__decode__("{encoded}")'
        return re.sub(r'"([^"]*)"', encrypt, code)

    def split_strings_to_chr(self, code):
        def splitter(match):
            s = match.group(1)
            parts = [f'chr({ord(c)})' for c in s]
            return '+'.join(parts)
        code = re.sub(r'__decode__\("([^"]*)"\)', splitter, code)
        code = re.sub(r'"([^"]*)"', splitter, code)
        return code

    def xor_numbers(self, code):
        def mask(match):
            num = int(match.group(1))
            key = random.randint(1, 255)
            return f'({num ^ key}^{key})'
        return re.sub(r'\b(\d+)\b', mask, code)

    def add_dead_code(self, code):
        lines = code.split('\n')
        result = []
        counter = 0
        for line in lines:
            if random.random() < 0.2:
                result.append(f'_dc{counter} = {random.randint(0, 999)}; ' + line)
                counter += 1
            else:
                result.append(line)
        return '\n'.join(result)


class ObfuscatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        global LANG
        LANG = "RU"
        self.setWindowTitle("Obfuscator v1.0 — by hero684k")
        self.setMinimumSize(920, 720)
        self.setFixedSize(920, 720)
        self.current_file = None
        self.init_ui()
        self.apply_theme()
        self.animate_in()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(20, 20, 20, 20)

        top_bar = QHBoxLayout()
        logo_label = QLabel("⚡")
        logo_label.setFont(QFont("Segoe UI", 26))
        logo_label.setStyleSheet("color: #A78BFA; margin-right: 8px;")
        top_bar.addWidget(logo_label)

        title_label = QLabel("OBFUSCATOR v1.0")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Black))
        title_label.setStyleSheet("color: #A78BFA; letter-spacing: 1px;")
        top_bar.addWidget(title_label)
        top_bar.addStretch()

        author_label = QLabel("by hero684k")
        author_label.setFont(QFont("Segoe UI", 10))
        author_label.setStyleSheet("color: #8B90A0; margin-right: 12px;")
        top_bar.addWidget(author_label)

        self.lang_btn = QPushButton("RU")
        self.lang_btn.setFixedSize(60, 32)
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #A78BFA, stop:1 #60A5FA);
                color: white; border: none; border-radius: 10px; font-weight: 800; font-size: 12px; padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C4B5FD, stop:1 #93C5FD);
            }
        """)
        self.lang_btn.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_btn)
        main_layout.addLayout(top_bar)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #A78BFA, stop:0.5 #60A5FA, stop:1 #A78BFA); border: none; border-radius: 1px;")
        main_layout.addWidget(line)

        src_group = QGroupBox(t("source"))
        src_layout = QVBoxLayout(src_group)
        src_layout.setSpacing(8)

        radio_layout = QHBoxLayout()
        self.src_group = QButtonGroup(self)
        self.rb_paste = QRadioButton(t("paste"))
        self.rb_file = QRadioButton(t("browse"))
        self.rb_paste.setChecked(True)
        self.src_group.addButton(self.rb_paste, 1)
        self.src_group.addButton(self.rb_file, 2)
        radio_layout.addWidget(self.rb_paste)
        radio_layout.addWidget(self.rb_file)
        radio_layout.addStretch()

        self.btn_browse = QPushButton(t("browse"))
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self.browse_file)
        radio_layout.addWidget(self.btn_browse)
        src_layout.addLayout(radio_layout)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText(t("placeholder_input"))
        src_layout.addWidget(self.input_edit)
        main_layout.addWidget(src_group)

        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(16)

        mode_group = QGroupBox(t("mode"))
        mode_lay = QVBoxLayout(mode_group)
        self.mode_group = QButtonGroup(self)
        self.rb_universal = QRadioButton(t("universal"))
        self.rb_typed = QRadioButton(t("by_type"))
        self.rb_universal.setChecked(True)
        self.mode_group.addButton(self.rb_universal, 1)
        self.mode_group.addButton(self.rb_typed, 2)
        mode_lay.addWidget(self.rb_universal)
        mode_lay.addWidget(self.rb_typed)
        settings_layout.addWidget(mode_group)

        self.type_group = QGroupBox(t("type_label"))
        type_lay = QVBoxLayout(self.type_group)
        self.type_combo = QComboBox()
        self.type_combo.setItemDelegate(NoWhiteBorderDelegate())
        self.type_combo.addItems(["python", "java", "kotlin", "js", "ts", "lua", "cs", "c", "cpp", "php", "ruby"])
        type_lay.addWidget(self.type_combo)
        self.type_group.setVisible(False)
        settings_layout.addWidget(self.type_group)

        level_group = QGroupBox(t("level"))
        level_lay = QVBoxLayout(level_group)
        self.level_combo = QComboBox()
        self.level_combo.setItemDelegate(NoWhiteBorderDelegate())
        level_lay.addWidget(self.level_combo)
        settings_layout.addWidget(level_group)
        main_layout.addLayout(settings_layout)

        self.rb_universal.toggled.connect(lambda checked: self.animate_type_group(not checked))
        self.rb_typed.toggled.connect(lambda checked: self.animate_type_group(checked))

        self.btn_obfuscate = QPushButton(t("obfuscate"))
        self.btn_obfuscate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_obfuscate.clicked.connect(self.animate_obfuscate)
        self.btn_obfuscate.setMinimumHeight(50)
        main_layout.addWidget(self.btn_obfuscate)

        result_group = QGroupBox(t("result"))
        result_layout = QVBoxLayout(result_group)
        result_layout.setSpacing(8)

        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText(t("placeholder_output"))
        self.output_edit.setReadOnly(True)
        result_layout.addWidget(self.output_edit)

        save_layout = QHBoxLayout()
        self.btn_save = QPushButton(t("save"))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_result)
        save_layout.addStretch()
        save_layout.addWidget(self.btn_save)
        result_layout.addLayout(save_layout)
        main_layout.addWidget(result_group)

        self.update_texts()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #06060E, stop:0.3 #0A0A16, stop:0.7 #0E0E1A, stop:1 #06060E);
            }
            QLabel { color: #E2E8F0; font-size: 13px; }
            QGroupBox {
                color: #A0AEC0;
                border: 1px solid #252540;
                border-radius: 14px;
                margin-top: 16px;
                padding: 22px 18px 14px 18px;
                font-weight: 700;
                font-size: 12px;
                background: rgba(16, 16, 30, 0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 10px;
                color: #A78BFA;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #252540, stop:1 #353560);
                color: #EDF2F7;
                border: 1px solid #3D3D5A;
                border-radius: 10px;
                padding: 10px 22px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3D3D5A, stop:1 #5A5A7A);
                border-color: #A78BFA;
            }
            QPushButton#obfuscateBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A78BFA, stop:0.3 #8B5CF6, stop:0.7 #7C3AED, stop:1 #60A5FA);
                color: white;
                border: none;
                font-size: 16px;
                font-weight: 800;
                letter-spacing: 3px;
                border-radius: 14px;
            }
            QPushButton#obfuscateBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #C4B5FD, stop:0.3 #A78BFA, stop:0.7 #8B5CF6, stop:1 #93C5FD);
            }
            QTextEdit {
                background: rgba(12, 12, 24, 0.9);
                color: #E2E8F0;
                border: 1px solid #252540;
                border-radius: 12px;
                padding: 14px;
                font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
                font-size: 12px;
                selection-background-color: #A78BFA;
            }
            QComboBox {
    background: #1A1A2E;
    color: #EDF2F7;
    border: 1px solid #3D3D5A;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    min-width: 130px;
    min-height: 20px;
}
QComboBox:hover { border-color: #A78BFA; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: none; border: none; }
QComboBox QAbstractItemView {
    background: #1A1A2E;
    color: #EDF2F7;
    border: 1px solid #3D3D5A;
    border-radius: 10px;
    padding: 4px;
    outline: none;
    selection-background-color: transparent;
}
            QComboBox:hover { border-color: #A78BFA; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView {
    background: #1A1A2E;
    color: #EDF2F7;
    border: 1px solid #3D3D5A;
    border-radius: 10px;
    outline: none;
    selection-background-color: transparent;
}
            QRadioButton { color: #E2E8F0; font-size: 12px; spacing: 10px; }
            QRadioButton::indicator {
                width: 18px; height: 18px;
                border-radius: 9px;
                border: 2px solid #4A4A6A;
                background: transparent;
            }
            QRadioButton::indicator:checked {
                border-color: #A78BFA;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.45,
                    fx:0.5, fy:0.5,
                    stop:0 #C4B5FD, stop:0.6 #A78BFA, stop:1 #1A1A2E);
            }
        """)
        self.btn_obfuscate.setObjectName("obfuscateBtn")

    def update_texts(self):
        self.setWindowTitle("Obfuscator v1.0 — by hero684k")
        for grp in self.findChildren(QGroupBox):
            for key in ["source", "mode", "type_label", "level", "result"]:
                if grp.title() in [TEXTS["RU"][key], TEXTS["EN"][key]]:
                    grp.setTitle(t(key))
        self.rb_paste.setText(t("paste"))
        self.rb_file.setText(t("browse"))
        self.btn_browse.setText(t("browse"))
        self.rb_universal.setText(t("universal"))
        self.rb_typed.setText(t("by_type"))
        self.btn_obfuscate.setText(t("obfuscate"))
        self.btn_save.setText(t("save"))
        self.input_edit.setPlaceholderText(t("placeholder_input"))
        self.output_edit.setPlaceholderText(t("placeholder_output"))
        self.level_combo.clear()
        self.level_combo.addItems([t("easy"), t("medium"), t("hard"), t("maximum")])
        self.level_combo.setCurrentIndex(3)
        self.level_combo.setItemDelegate(NoWhiteBorderDelegate())

    def toggle_language(self):
        global LANG
        LANG = "EN" if LANG == "RU" else "RU"
        self.lang_btn.setText("EN" if LANG == "EN" else "RU")
        self.update_texts()

    def animate_in(self):
        self.setWindowOpacity(0)
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(400)
        fade.setStartValue(0)
        fade.setEndValue(1)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start()

    def animate_type_group(self, visible):
        if visible:
            self.type_group.setVisible(True)
            self.type_group.setMaximumHeight(0)
            anim = QPropertyAnimation(self.type_group, b"maximumHeight", self)
            anim.setDuration(250)
            anim.setStartValue(0)
            anim.setEndValue(100)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
        else:
            anim = QPropertyAnimation(self.type_group, b"maximumHeight", self)
            anim.setDuration(200)
            anim.setStartValue(self.type_group.height())
            anim.setEndValue(0)
            anim.setEasingCurve(QEasingCurve.Type.InCubic)
            anim.finished.connect(lambda: self.type_group.setVisible(False))
            anim.start()

    def animate_obfuscate(self):
        self.btn_obfuscate.setEnabled(False)
        self.btn_obfuscate.setText("...")
        self.output_edit.setStyleSheet(self.output_edit.styleSheet() + "QTextEdit { border-color: #A78BFA; border-width: 2px; }")
        QTimer.singleShot(300, self._do_obfuscate)

    def _do_obfuscate(self):
        self.obfuscate()
        self.btn_obfuscate.setEnabled(True)
        self.btn_obfuscate.setText(t("obfuscate"))
        self.output_edit.setStyleSheet(self.output_edit.styleSheet().replace("border-color: #A78BFA;", "").replace("border-width: 2px;", ""))

    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, t("browse"), "",
            "Code files (*.py *.java *.kt *.js *.ts *.lua *.cs *.c *.cpp *.h *.php *.rb *.txt);;All files (*.*)")
        if filepath:
            self.current_file = filepath
            with open(filepath, "r", encoding="utf-8") as f:
                self.input_edit.setText(f.read())
            self.rb_file.setChecked(True)

    def obfuscate(self):
        if self.rb_paste.isChecked():
            code = self.input_edit.toPlainText()
        elif self.current_file:
            with open(self.current_file, "r", encoding="utf-8") as f:
                code = f.read()
        else:
            code = self.input_edit.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Error", t("error_no_code"))
            return
        lang = "universal" if self.rb_universal.isChecked() else self.type_combo.currentText()
        level_map = {t("easy"): "easy", t("medium"): "medium", t("hard"): "hard", t("maximum"): "maximum"}
        level = level_map[self.level_combo.currentText()]
        obf = CodeObfuscator(code, lang, level)
        result = obf.run()
        self.output_edit.setText(result)
        self.output_edit.setStyleSheet(self.output_edit.styleSheet() + "QTextEdit { border-color: #3FB950; border-width: 2px; }")
        QTimer.singleShot(800, lambda: self.output_edit.setStyleSheet(
            self.output_edit.styleSheet().replace("border-color: #3FB950;", "").replace("border-width: 2px;", "")))

    def save_result(self):
        result = self.output_edit.toPlainText()
        if not result.strip():
            QMessageBox.warning(self, "Error", t("error_no_result"))
            return
        lang = "universal" if self.rb_universal.isChecked() else self.type_combo.currentText()
        ext_map = {"python": ".py", "java": ".java", "kotlin": ".kt", "js": ".js", "ts": ".ts", "lua": ".lua", "cs": ".cs", "c": ".c", "cpp": ".cpp", "php": ".php", "ruby": ".rb", "universal": ".txt"}
        ext = ext_map.get(lang, ".txt")
        filepath, _ = QFileDialog.getSaveFileName(self, t("save"), f"obfuscated{ext}", f"Code files (*{ext});;All files (*.*)")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result)
            QMessageBox.information(self, t("saved"), f"{t('saved')}: {filepath}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ObfuscatorGUI()
    window.show()
    sys.exit(app.exec())