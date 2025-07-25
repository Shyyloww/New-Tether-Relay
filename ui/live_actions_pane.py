# ui/live_actions_pane.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QLabel
from PyQt6.QtCore import pyqtSignal

class LiveActionsPane(QWidget):
    """
    A widget containing buttons for common C2 actions like taking screenshots
    and listing processes, along with a view to show text-based results.
    """
    screenshot_requested = pyqtSignal()
    pslist_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 20, 10, 10)

        # --- Action Buttons ---
        actions_group = QGroupBox("Remote Actions")
        actions_layout = QHBoxLayout(actions_group)

        self.screenshot_button = QPushButton("Take Screenshot")
        self.screenshot_button.clicked.connect(self.screenshot_requested.emit)
        actions_layout.addWidget(self.screenshot_button)

        self.pslist_button = QPushButton("List Processes")
        self.pslist_button.clicked.connect(self.pslist_requested.emit)
        actions_layout.addWidget(self.pslist_button)
        
        main_layout.addWidget(actions_group)

        # --- Results View ---
        results_group = QGroupBox("Action Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_view = QTextEdit()
        self.results_view.setReadOnly(True)
        results_layout.addWidget(self.results_view)
        
        main_layout.addWidget(results_group, 1) # Give results view more space

    def display_result(self, text):
        """Appends text results (like a process list) to the results view."""
        self.results_view.append(text)

    def clear_results(self):
        """Clears the results view for a new session."""
        self.results_view.clear()