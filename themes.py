# themes.py

class ThemeManager:
    """ A central place to store and retrieve theme stylesheets (QSS). """
    @staticmethod
    def get_stylesheet(theme_name):
        base_style = """
            QWidget { font-family: Segoe UI; font-size: 10pt; }
            QStatusBar { font-size: 9pt; }
            QMenu { padding: 5px; }
            QGroupBox::title { font-weight: bold; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton { font-weight: bold; padding: 6px; }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }
            QSpinBox { padding-right: 1px; }
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QTableWidget { border: none; }
            QTableWidget::item { padding-left: 10px; padding-right: 10px; padding-top: 8px; padding-bottom: 8px; }
            QHeaderView::section {
                font-weight: bold;
                padding: 8px;
                border: none; 
            }
            QScrollBar:vertical { border: none; width: 8px; margin: 0px 0 0px 0; }
            QScrollBar::handle:vertical { border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QCheckBox::indicator { width: 13px; height: 13px; border-radius: 3px; }
            QPushButton#InteractButton { font-size: 11pt; font-weight: bold; }
            QLabel#StatusLabel {
                font-size: 10pt;
                font-weight: bold;
                border-radius: 4px;
                padding: 12px 8px;
            }
        """
        themes = {
            "Light": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fcfcfc; color: #111; }
                QGroupBox { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #f0f0f0; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #fff; color: #111; border: 1px solid #ccc; border-radius: 3px; padding: 4px; }
                QComboBox QAbstractItemView { background-color: #f0f0f0; color: #111; border: 1px solid #ccc; selection-background-color: #d4d4d4; }
                QPushButton { background-color: #e1e1e1; color: #000; border: 1px solid #adadad; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #cacaca; } QPushButton:pressed { background-color: #b0b0b0; }
                QCheckBox::indicator { border: 1px solid #adadad; background-color: #fff; } QCheckBox::indicator:checked { background-color: #555; }
                QTableWidget { background-color: #fff; alternate-background-color: #f5f5f5; color: #000; }
                QTableWidget::item { border-bottom: 1px solid #f0f0f0; }
                QTableWidget::item:hover { background-color: #e6f2fa; }
                QTableWidget::item:selected { background-color: #cde8f9; color: #000; }
                QHeaderView::section { background-color: #fff; border-bottom: 2px solid #ccc; color: #000; }
                QLabel, QCheckBox { color: #111; background-color: transparent;} h2 { color: #005a9e; }
                QSplitter::handle { background-color: #ccc; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #f0f0f0; } QScrollBar::handle:vertical { background: #ccc; }
                QMenu::item:selected { background-color: #d4d4d4; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c82333; color: white; border-color: #bd2130; }
                QPushButton#InteractButton { background-color: #d4d4d4; border: 1px solid #adadad; } QPushButton#InteractButton:hover { background-color: #c0c0c0; }
                QLabel#StatusLabel[status="online"] { background-color: #d4edda; color: #155724; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #f8d7da; color: #721c24; border: none; }
            """,
            "Cyber": """
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Lucida Console", Monaco, monospace; background-color: #0d0221; color: #9bf1ff; }
                QGroupBox { background-color: #1a0a38; border: 1px solid #8A2BE2; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #ff00ff; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #1a0a38; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #0d0221; color: #9bf1ff; border: 1px solid #8A2BE2; border-radius: 3px; padding: 4px; selection-background-color: #00aaff; }
                QComboBox QAbstractItemView { background-color: #1a0a38; color: #9bf1ff; border: 1px solid #8A2BE2; selection-background-color: #3c1a7a; }
                QPushButton { background-color: #2b0b5a; border: 1px solid #ff00ff; color: #ff00ff; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #3c1a7a; } QPushButton:pressed { background-color: #4c2a9a; }
                QCheckBox::indicator { border: 1px solid #8A2BE2; background-color: #0d0221; } QCheckBox::indicator:checked { background-color: #ff00ff; }
                QTableWidget { background-color: #1a0a38; alternate-background-color: #1f0c4a; }
                QTableWidget::item { border-bottom: 1px solid #2b0b5a; }
                QTableWidget::item:hover { background-color: #2b0b5a; }
                QTableWidget::item:selected { background-color: #4c2a9a; color: #9bf1ff; }
                QHeaderView::section { background-color: #0d0221; border-bottom: 2px solid #ff00ff; color: #9bf1ff; }
                QLabel, QCheckBox { color: #9bf1ff; background-color: transparent;} h2 { color: #00f0ff; }
                QSplitter::handle { background-color: #8A2BE2; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #1a0a38; } QScrollBar::handle:vertical { background: #8A2BE2; }
                QMenu::item:selected { background-color: #3c1a7a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #e11d48; color: white; border-color: #ff00ff; }
                QPushButton#InteractButton { background-color: #3c1a7a; } QPushButton#InteractButton:hover { background-color: #4c2a9a; }
                QLabel#StatusLabel[status="online"] { background-color: #00f0ff; color: #0d0221; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #e11d48; color: white; border: none; }
            """,
            "Matrix": """
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Courier New", monospace; background-color: #000000; color: #39ff14; }
                QGroupBox { background-color: #051a05; border: 1px solid #008F11; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #39ff14; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #051a05;}
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #000; color: #39ff14; border: 1px solid #008F11; padding: 4px; selection-background-color: #39ff14; selection-color: black;}
                QComboBox QAbstractItemView { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; selection-background-color: #0f3f0f; }
                QPushButton { background-color: #0a2a0a; border: 1px solid #39ff14; color: #39ff14; padding: 5px; }
                QPushButton:hover { background-color: #0f3f0f; } QPushButton:pressed { background-color: #145414; }
                QCheckBox::indicator { border: 1px solid #39ff14; background-color: #000; } QCheckBox::indicator:checked { background-color: #39ff14; }
                QTableWidget { background-color: #051a05; alternate-background-color: #0a2a0a; }
                QTableWidget::item { border-bottom: 1px solid #0f3f0f; }
                QTableWidget::item:hover { background-color: #0f3f0f; }
                QTableWidget::item:selected { background-color: #145414; color: #39ff14; }
                QHeaderView::section { background-color: #000; border-bottom: 2px solid #39ff14; }
                QLabel, QCheckBox { color: #39ff14; background-color: transparent;} h2 { color: #9dff8a; }
                QSplitter::handle { background-color: #008F11; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #051a05; } QScrollBar::handle:vertical { background: #39ff14; }
                QMenu::item:selected { background-color: #0f3f0f; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #8b0000; color: #39ff14; border-color: #39ff14; }
                QPushButton#InteractButton { background-color: #0f3f0f; } QPushButton#InteractButton:hover { background-color: #145414; }
                QLabel#StatusLabel[status="online"] { background-color: #39ff14; color: #000; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #ff0000; color: #000; border: none; }
            """,
            "Sunrise": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fff8e1; color: #4e342e; }
                QGroupBox { background-color: #ffecb3; border: 1px solid #ffca28; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #bf360c; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #ffecb3; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #fff; color: #4e342e; border: 1px solid #ffca28; border-radius: 3px; padding: 4px; }
                QComboBox QAbstractItemView { background-color: #ffecb3; color: #4e342e; border: 1px solid #ffca28; selection-background-color: #ffb74d; }
                QPushButton { background-color: #ffb74d; color: #4e342e; border: 1px solid #ffa726; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ffa726; } QPushButton:pressed { background-color: #ff9800; }
                QCheckBox::indicator { border: 1px solid #ffca28; background-color: #fff; } QCheckBox::indicator:checked { background-color: #bf360c; }
                QTableWidget { background-color: #fff; alternate-background-color: #fff8e1; color: #4e342e; }
                QTableWidget::item { border-bottom: 1px solid #ffecb3; }
                QTableWidget::item:hover { background-color: #ffecb3; }
                QTableWidget::item:selected { background-color: #ffcc80; color: #4e342e; }
                QHeaderView::section { background-color: #fff8e1; border-bottom: 2px solid #bf360c; color: #4e342e; }
                QLabel, QCheckBox { color: #4e342e; background-color: transparent;} h2 { color: #d84315; }
                QSplitter::handle { background-color: #ffca28; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #ffecb3; } QScrollBar::handle:vertical { background: #ffca28; }
                QMenu::item:selected { background-color: #ffb74d; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #e53935; color: white; border-color: #d32f2f; }
                QPushButton#InteractButton { background-color: #ffcc80; color: #4e342e; border: 1px solid #ffa726; } QPushButton#InteractButton:hover { background-color: #ffb74d; }
                QLabel#StatusLabel[status="online"] { background-color: #8bc34a; color: white; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #e53935; color: white; border: none; }
            """,
            "Sunset": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #1a182f; color: #fff2cc; }
                QGroupBox { background-color: #3c3a52; border: 1px solid #ff8c42; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #ff8c42; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #3c3a52; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #1a182f; color: #fff2cc; border: 1px solid #ff8c42; border-radius: 3px; padding: 4px; selection-background-color: #ff5e57; }
                QComboBox QAbstractItemView { background-color: #3c3a52; color: #fff2cc; border: 1px solid #ff8c42; selection-background-color: #ff5e57; }
                QPushButton { background-color: #ff5e57; color: #ffffff; border: 1px solid #ff8c42; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ff7b72; } QPushButton:pressed { background-color: #e64a19; }
                QCheckBox::indicator { border: 1px solid #ff8c42; background-color: #1a182f; } QCheckBox::indicator:checked { background-color: #ff8c42; }
                QTableWidget { background-color: #3c3a52; alternate-background-color: #4a4861; }
                QTableWidget::item { border-bottom: 1px solid #5a5870; }
                QTableWidget::item:hover { background-color: #4a4861; }
                QTableWidget::item:selected { background-color: #ff5e57; color: #fff; }
                QHeaderView::section { background-color: #1a182f; border-bottom: 2px solid #ff5e57; color: #ff8c42; }
                QLabel, QCheckBox { color: #fff2cc; background-color: transparent;} h2 { color: #ff8c42; }
                QSplitter::handle { background-color: #ff8c42; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #3c3a52; } QScrollBar::handle:vertical { background: #ff8c42; }
                QMenu::item:selected { background-color: #ff5e57; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c70039; color: white; border-color: #ff5e57; }
                QPushButton#InteractButton { background-color: #e64a19; } QPushButton#InteractButton:hover { background-color: #ff7b72; }
                QLabel#StatusLabel[status="online"] { background-color: #ffab40; color: #1a182f; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #c70039; color: #fff2cc; border: none; }
            """,
            "Jungle": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #344e41; color: #dad7cd; }
                QGroupBox { background-color: #2b4136; border: 1px solid #a3b18a; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #a3b18a; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #2b4136;}
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #3a5a40; color: #dad7cd; border: 1px solid #588157; border-radius: 3px; padding: 4px; selection-background-color: #a3b18a; selection-color: #2b4136;}
                QComboBox QAbstractItemView { background-color: #2b4136; color: #dad7cd; border: 1px solid #a3b18a; selection-background-color: #588157; }
                QPushButton { background-color: #588157; color: #ffffff; border: 1px solid #a3b18a; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #6a996a; } QPushButton:pressed { background-color: #4a714a; }
                QCheckBox::indicator { border: 1px solid #a3b18a; background-color: #3a5a40; } QCheckBox::indicator:checked { background-color: #a3b18a; }
                QTableWidget { background-color: #3a5a40; alternate-background-color: #3f684c; }
                QTableWidget::item { border-bottom: 1px solid #4a714a; }
                QTableWidget::item:hover { background-color: #4a714a; }
                QTableWidget::item:selected { background-color: #588157; color: #fff; }
                QHeaderView::section { background-color: #344e41; border-bottom: 2px solid #a3b18a; }
                QLabel, QCheckBox { color: #dad7cd; background-color: transparent;} h2 { color: #cde2b4; }
                QSplitter::handle { background-color: #a3b18a; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #2b4136; } QScrollBar::handle:vertical { background: #a3b18a; }
                QMenu::item:selected { background-color: #588157; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c1440e; color: white; border-color: #a3b18a; }
                QPushButton#InteractButton { background-color: #4a714a; } QPushButton#InteractButton:hover { background-color: #6a996a; }
                QLabel#StatusLabel[status="online"] { background-color: #a3b18a; color: #2b4136; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #c1440e; color: white; border: none; }
            """,
            "Ocean": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #020f1c; color: #e0ffff; }
                QGroupBox { background-color: #041c32; border: 1px solid #04294b; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #61dafb; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #041c32;}
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #020f1c; color: #e0ffff; border: 1px solid #04294b; border-radius: 3px; padding: 4px; }
                QComboBox QAbstractItemView { background-color: #041c32; color: #e0ffff; border: 1px solid #04294b; selection-background-color: #0074d9; }
                QPushButton { background-color: #04294b; color: #e0ffff; border: 1px solid #61dafb; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #0074d9; } QPushButton:pressed { background-color: #0060c0; }
                QCheckBox::indicator { border: 1px solid #61dafb; background-color: #020f1c; } QCheckBox::indicator:checked { background-color: #61dafb; }
                QTableWidget { background-color: #041c32; alternate-background-color: #04233f; }
                QTableWidget::item { border-bottom: 1px solid #04294b; }
                QTableWidget::item:hover { background-color: #04294b; }
                QTableWidget::item:selected { background-color: #0074d9; color: #e0ffff; }
                QHeaderView::section { background-color: #020f1c; border-bottom: 2px solid #61dafb; }
                QLabel, QCheckBox { color: #e0ffff; background-color: transparent;} h2 { color: #bde0ff; }
                QSplitter::handle { background-color: #61dafb; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #041c32; } QScrollBar::handle:vertical { background: #61dafb; }
                QMenu::item:selected { background-color: #0074d9; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #FF4136; color: white; border-color: #61dafb; }
                QPushButton#InteractButton { background-color: #0060c0; } QPushButton#InteractButton:hover { background-color: #0074d9; }
                QLabel#StatusLabel[status="online"] { background-color: #7fdbff; color: #020f1c; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #FF4136; color: white; border: none; }
            """,
            "Galaxy": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #282a36; color: #f8f8f2; }
                QGroupBox { background-color: #1e1f29; border: 1px solid #bd93f9; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #ff79c6; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #1e1f29; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #21222c; color: #f8f8f2; border: 1px solid #6272a4; border-radius: 3px; padding: 4px; selection-background-color: #44475a; }
                QComboBox QAbstractItemView { background-color: #1e1f29; color: #f8f8f2; border: 1px solid #bd93f9; selection-background-color: #44475a; }
                QPushButton { background-color: #44475a; border: 1px solid #bd93f9; color: #f8f8f2; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #5a5c72; } QPushButton:pressed { background-color: #343746; }
                QCheckBox::indicator { border: 1px solid #bd93f9; background-color: #21222c; } QCheckBox::indicator:checked { background-color: #bd93f9; }
                QTableWidget { background-color: #1e1f29; alternate-background-color: #21222c; }
                QTableWidget::item { border-bottom: 1px solid #44475a; }
                QTableWidget::item:hover { background-color: #44475a; }
                QTableWidget::item:selected { background-color: #5a5c72; color: #f8f8f2; }
                QHeaderView::section { background-color: #282a36; border-bottom: 2px solid #bd93f9; }
                QLabel, QCheckBox { color: #f8f8f2; background-color: transparent;} h2 { color: #8be9fd; }
                QSplitter::handle { background-color: #bd93f9; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #1e1f29; } QScrollBar::handle:vertical { background: #bd93f9; }
                QMenu::item:selected { background-color: #44475a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #ff5555; color: #f8f8f2; border-color: #bd93f9; }
                QPushButton#InteractButton { background-color: #343746; } QPushButton#InteractButton:hover { background-color: #5a5c72; }
                QLabel#StatusLabel[status="online"] { background-color: #8be9fd; color: #282a36; border: none; }
                QLabel#StatusLabel[status="offline"] { background-color: #ff5555; color: #f8f8f2; border: none; }
            """,
            "Candy": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fdf6f6; color: #5d5d5d; }
                QGroupBox { background-color: #f7e4f3; border: 1px solid #c9a7c7; border-radius: 5px; margin-top: 1ex; }
                QGroupBox::title { color: #8c728a; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #f7e4f3; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #fff; color: #555; border: 1px solid #a3d9e8; border-radius: 3px; padding: 4px; selection-background-color: #ffe0b2; }
                QComboBox QAbstractItemView { background-color: #f7e4f3; color: #555; border: 1px solid #c9a7c7; selection-background-color: #b3e5fc; }
                QPushButton { background-color: #c8e6c9; color: #385b38; border: 1px solid #a4d4a5; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #b7e0b8; } QPushButton:pressed { background-color: #a6d9a7; }
                QCheckBox::indicator { border: 1px solid #c9a7c7; background-color: #fff; } QCheckBox::indicator:checked { background-color: #a3d9e8; }
                QTableWidget { background-color: #fff; alternate-background-color: #f1f8e9; color: #444; }
                QTableWidget::item { border-bottom: 1px solid #e0e0e0; }
                QTableWidget::item:hover { background-color: #f7e4f3; }
                QTableWidget::item:selected { background-color: #b3e5fc; color: #555; }
                QHeaderView::section { background-color: #fdf6f6; border-bottom: 2px solid #c8e6c9; color: #6c6643; }
                QLabel, QCheckBox { color: #5d5d5d; background-color: transparent;} h2 { color: #c2185b; }
                QSplitter::handle { background-color: #c9a7c7; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
                QScrollBar:vertical { background: #f7e4f3; } QScrollBar::handle:vertical { background: #c9a7c7; }
                QMenu::item:selected { background-color: #b3e5fc; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #ffcdd2; color: #b71c1c; border-color: #ef9a9a; }
                QPushButton#InteractButton { background-color: #b3e5fc; color: #555; border: 1px solid #a3d9e8; } QPushButton#InteractButton:hover { background-color: #a2d4eb; }
                QLabel#StatusLabel[status="online"] { background-color: #c8e6c9; color: #385b38; border: 1px solid #a4d4a5; }
                QLabel#StatusLabel[status="offline"] { background-color: #ffcdd2; color: #b71c1c; border: 1px solid #ef9a9a; }
            """
        }
        dark_theme = """
            QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QGroupBox { background-color: #3c3c3c; border: 1px solid #555; border-radius: 5px; margin-top: 1ex; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #3c3c3c;}
            QLineEdit, QTextEdit, QComboBox, QSpinBox { background-color: #252525; color: #f0f0f0; border: 1px solid #555; border-radius: 3px; padding: 4px; selection-background-color: #555; }
            QComboBox QAbstractItemView { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; selection-background-color: #555; }
            QPushButton { background-color: #555; border: 1px solid #666; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #666; } QPushButton:pressed { background-color: #777; }
            QCheckBox::indicator { border: 1px solid #666; background-color: #252525; } QCheckBox::indicator:checked { background-color: #f0f0f0; }
            QTableWidget { background-color: #3c3c3c; alternate-background-color: #454545; }
            QTableWidget::item { border-bottom: 1px solid #454545; }
            QTableWidget::item:hover { background-color: #454545; }
            QTableWidget::item:selected { background-color: #555; color: #f0f0f0; }
            QHeaderView::section { background-color: #2b2b2b; border-bottom: 2px solid #555; }
            QLabel, QCheckBox { color: #f0f0f0; background-color: transparent;} h2 { color: #66b2ff; }
            QSplitter::handle { background-color: #555; } QSplitter::handle:horizontal { width: 1px; } QSplitter::handle:vertical { height: 1px; }
            QScrollBar:vertical { background: #3c3c3c; } QScrollBar::handle:vertical { background: #666; }
            QMenu::item:selected { background-color: #666; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #9d2d2d; color: white; border-color: #666; }
            QPushButton#InteractButton { background-color: #666; } QPushButton#InteractButton:hover { background-color: #777; }
            QLabel#StatusLabel[status="online"] { background-color: #66b2ff; color: #2b2b2b; border: none; }
            QLabel#StatusLabel[status="offline"] { background-color: #9d2d2d; color: #f0f0f0; border: none; }
        """
        return base_style + themes.get(theme_name, dark_theme)