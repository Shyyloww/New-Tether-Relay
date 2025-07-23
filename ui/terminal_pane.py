# ui/terminal_pane.py (Definitive, Interactive Terminal Widget)

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class TerminalPane(QWidget):
    command_entered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setFont(QFont("Consolas", 11))
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter command...")
        self.input_line.returnPressed.connect(self.on_command_entered)

        layout.addWidget(self.output_view)
        layout.addWidget(self.input_line)

    def on_command_entered(self):
        command = self.input_line.text().strip()
        if command:
            self.append_output(f"> {command}\n")
            self.command_entered.emit(command)
            self.input_line.clear()

    def append_output(self, text):
        self.output_view.moveCursor(Qt.TextCursor.MoveOperation.End)
        self.output_view.insertPlainText(text)
        self.output_view.moveCursor(Qt.TextCursor.MoveOperation.End)

    def clear_output(self):
        self.output_view.clear()