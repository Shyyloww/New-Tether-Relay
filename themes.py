# themes.py (Full and Complete Code)
class ThemeManager:
    @staticmethod
    def get_stylesheet(theme_name):
        base_style = """
            QWidget { font-family: Segoe UI; font-size: 10pt; }
            QStatusBar { font-size: 9pt; }
            QMenu { padding: 5px; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton { font-weight: bold; padding: 6px; }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }
            QSpinBox { padding-right: 1px; }
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QTableWidget { border: none; }
            QTableWidget::item { padding-left: 10px; padding-right: 10px; padding-top: 8px; padding-bottom: 8px; }
            QHeaderView::section { font-weight: bold; padding: 8px; border: none; }
            QScrollBar:vertical { border: none; width: 8px; margin: 0px 0 0px 0; }
            QScrollBar::handle:vertical { border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QCheckBox::indicator { width: 13px; height: 13px; border-radius: 3px; }
            QPushButton#InteractButton { font-size: 11pt; font-weight: bold; }
            QPushButton#StatusButton { font-size: 9pt; font-weight: bold; border-radius: 4px; padding: 6px 10px; min-width: 70px; }
            QLabel#HeaderStatusLabel { font-size: 10pt; font-weight: bold; border-radius: 4px; padding: 8px; }
            QTabWidget::pane { border: none; padding: 10px; }
            QTabBar::tab { padding: 8px 20px; border-radius: 4px; margin-right: 2px; }
            QDateTimeEdit { padding: 4px; border-radius: 3px; }
            QDateTimeEdit::down-button { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left-width: 1px; border-left-style: solid; border-top-right-radius: 3px; border-bottom-right-radius: 3px; }
            QGroupBox { margin-top: 15px; }
            QGroupBox::title { font-weight: bold; subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
        """
        
        dark_theme = """
            QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QGroupBox { background-color: #3c3c3c; border: 1px solid #555; border-radius: 5px; }
            QGroupBox::title { background-color: #2b2b2b; color: #f0f0f0; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #252525; color: #f0f0f0; border: 1px solid #555; selection-background-color: #555; }
            QDateTimeEdit::down-button { border-left-color: #555; }
            QDateTimeEdit::down-button:hover { background-color: #666; }
            QComboBox QAbstractItemView { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; selection-background-color: #555; }
            QPushButton { background-color: #555; border: 1px solid #666; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #666; } QPushButton:pressed { background-color: #777; }
            QPushButton#InteractButton { color: white; }
            QCheckBox::indicator { border: 1px solid #666; background-color: #252525; } QCheckBox::indicator:checked { background-color: #f0f0f0; }
            QTableWidget { background-color: #3c3c3c; alternate-background-color: #454545; }
            QTableWidget::item { border-bottom: 1px solid #454545; }
            QTableWidget::item:hover { background-color: #454545; }
            QTableWidget::item:selected { background-color: #555; color: #f0f0f0; }
            QHeaderView::section { background-color: #2b2b2b; border-bottom: 2px solid #555; }
            QLabel, QCheckBox { color: #f0f0f0; background-color: transparent;} h2 { color: #66b2ff; }
            QSplitter::handle { background-color: #555; }
            QScrollBar:vertical { background: #3c3c3c; } QScrollBar::handle:vertical { background: #666; }
            QMenu::item:selected { background-color: #666; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #9d2d2d; color: white; border-color: #666; }
            QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
            QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
            QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
            QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
            QTabBar::tab { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; }
            QTabBar::tab:hover { background-color: #4a4a4a; }
            QTabBar::tab:selected { background-color: #555; border: 1px solid #666; }
            DataHarvestPane QListWidget { background-color: #3c3c3c; border: 1px solid #555; }
            DataHarvestPane QListWidget::item { padding: 8px; }
            DataHarvestPane QListWidget::item:selected { background-color: #555; }
            DataHarvestPane QTableWidget { background-color: #252525; border: 1px solid #555; }
            DataHarvestPane QHeaderView::section { background-color: #3c3c3c; border-bottom: 2px solid #555; }
        """

        themes = {
            "Light": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fcfcfc; color: #111; }
                QGroupBox { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; }
                QGroupBox::title { background-color: #fcfcfc; color: #111; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #111; border: 1px solid #ccc; }
                QDateTimeEdit::down-button { border-left-color: #ccc; }
                QDateTimeEdit::down-button:hover { background-color: #e1e1e1; }
                QComboBox QAbstractItemView { background-color: #f0f0f0; color: #111; border: 1px solid #ccc; selection-background-color: #d4d4d4; }
                QPushButton { background-color: #e1e1e1; color: #000; border: 1px solid #adadad; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #cacaca; } QPushButton:pressed { background-color: #b0b0b0; }
                QPushButton#InteractButton { color: #000; }
                QCheckBox::indicator { border: 1px solid #adadad; background-color: #fff; } QCheckBox::indicator:checked { background-color: #555; }
                QTableWidget { background-color: #fff; alternate-background-color: #f5f5f5; color: #000; }
                QTableWidget::item { border-bottom: 1px solid #f0f0f0; }
                QTableWidget::item:hover { background-color: #e6f2fa; }
                QTableWidget::item:selected { background-color: #cde8f9; color: #000; }
                QHeaderView::section { background-color: #fff; border-bottom: 2px solid #ccc; color: #000; }
                QLabel, QCheckBox { color: #111; background-color: transparent;} 
                h2 { color: #005a9e; }
                QSplitter::handle { background-color: #ccc; }
                QScrollBar:vertical { background: #f0f0f0; } QScrollBar::handle:vertical { background: #ccc; }
                QMenu::item:selected { background-color: #d4d4d4; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c82333; color: white; border-color: #bd2130; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #f0f0f0; color: #111; border: 1px solid #ccc; }
                QTabBar::tab:hover { background-color: #e0e0e0; }
                QTabBar::tab:selected { background-color: #ffffff; border: 1px solid #adadad; }
                DataHarvestPane QListWidget { background-color: #f0f0f0; border: 1px solid #ccc; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #cde8f9; color: #111; }
                DataHarvestPane QTableWidget { background-color: #ffffff; border: 1px solid #ccc; color: #111; }
                DataHarvestPane QHeaderView::section { background-color: #f0f0f0; border-bottom: 2px solid #ccc; color: #111; }
            """,
            "Cyber": """
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Lucida Console", Monaco, monospace; background-color: #0d0221; color: #9bf1ff; }
                QGroupBox { background-color: #1a0a38; border: 1px solid #8A2BE2; border-radius: 5px; }
                QGroupBox::title { background-color: #0d0221; color: #ff00ff; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #0d0221; color: #9bf1ff; border: 1px solid #8A2BE2; selection-background-color: #00aaff; }
                QDateTimeEdit::down-button { border-left-color: #8A2BE2; }
                QDateTimeEdit::down-button:hover { background-color: #3c1a7a; }
                QComboBox QAbstractItemView { background-color: #1a0a38; color: #9bf1ff; border: 1px solid #8A2BE2; selection-background-color: #3c1a7a; }
                QPushButton { background-color: #2b0b5a; border: 1px solid #ff00ff; color: #ff00ff; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #3c1a7a; } QPushButton:pressed { background-color: #4c2a9a; }
                QPushButton#InteractButton { color: #ff00ff; }
                QCheckBox::indicator { border: 1px solid #8A2BE2; background-color: #0d0221; } QCheckBox::indicator:checked { background-color: #ff00ff; }
                QTableWidget { background-color: #1a0a38; alternate-background-color: #1f0c4a; }
                QTableWidget::item { border-bottom: 1px solid #2b0b5a; }
                QTableWidget::item:hover { background-color: #2b0b5a; }
                QTableWidget::item:selected { background-color: #4c2a9a; color: #9bf1ff; }
                QHeaderView::section { background-color: #0d0221; border-bottom: 2px solid #ff00ff; color: #9bf1ff; }
                QLabel, QCheckBox { color: #9bf1ff; background-color: transparent;} h2 { color: #00f0ff; }
                QSplitter::handle { background-color: #8A2BE2; }
                QScrollBar:vertical { background: #1a0a38; } QScrollBar::handle:vertical { background: #8A2BE2; }
                QMenu::item:selected { background-color: #3c1a7a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #e11d48; color: white; border-color: #ff00ff; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #1a0a38; color: #9bf1ff; border: 1px solid #8A2BE2; }
                QTabBar::tab:hover { background-color: #2b0b5a; }
                QTabBar::tab:selected { background-color: #3c1a7a; border: 1px solid #ff00ff; }
                DataHarvestPane QListWidget { background-color: #1a0a38; border: 1px solid #8A2BE2; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #4c2a9a; }
                DataHarvestPane QTableWidget { background-color: #0d0221; border: 1px solid #8A2BE2; }
                DataHarvestPane QHeaderView::section { background-color: #1a0a38; border-bottom: 2px solid #ff00ff; }
            """,
            "Matrix": """
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Courier New", monospace; background-color: #000000; color: #39ff14; }
                QGroupBox { background-color: #051a05; border: 1px solid #008F11; border-radius: 5px; }
                QGroupBox::title { background-color: #000000; color: #39ff14; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #000; color: #39ff14; border: 1px solid #008F11; selection-background-color: #39ff14; selection-color: black;}
                QDateTimeEdit::down-button { border-left-color: #008F11; }
                QDateTimeEdit::down-button:hover { background-color: #145414; }
                QComboBox QAbstractItemView { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; selection-background-color: #0f3f0f; }
                QPushButton { background-color: #0a2a0a; border: 1px solid #39ff14; color: #39ff14; padding: 5px; }
                QPushButton:hover { background-color: #0f3f0f; } QPushButton:pressed { background-color: #145414; }
                QPushButton#InteractButton { color: #39ff14; }
                QCheckBox::indicator { border: 1px solid #39ff14; background-color: #000; } QCheckBox::indicator:checked { background-color: #39ff14; }
                QTableWidget { background-color: #051a05; alternate-background-color: #0a2a0a; }
                QTableWidget::item { border-bottom: 1px solid #0f3f0f; }
                QTableWidget::item:hover { background-color: #0f3f0f; }
                QTableWidget::item:selected { background-color: #145414; color: #39ff14; }
                QHeaderView::section { background-color: #000; border-bottom: 2px solid #39ff14; }
                QLabel, QCheckBox { color: #39ff14; background-color: transparent;} h2 { color: #9dff8a; }
                QSplitter::handle { background-color: #008F11; }
                QScrollBar:vertical { background: #051a05; } QScrollBar::handle:vertical { background: #39ff14; }
                QMenu::item:selected { background-color: #0f3f0f; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #8b0000; color: #39ff14; border-color: #39ff14; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: #000; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: #000; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: black; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: black; }
                QTabBar::tab { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; }
                QTabBar::tab:hover { background-color: #0a2a0a; }
                QTabBar::tab:selected { background-color: #0f3f0f; border: 1px solid #39ff14; }
                DataHarvestPane QListWidget { background-color: #051a05; border: 1px solid #008F11; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #145414; }
                DataHarvestPane QTableWidget { background-color: #000000; border: 1px solid #008F11; }
                DataHarvestPane QHeaderView::section { background-color: #051a05; border-bottom: 2px solid #39ff14; }
            """,
            "Sunrise": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fff8e1; color: #4e342e; }
                QGroupBox { background-color: #ffecb3; border: 1px solid #ffca28; border-radius: 5px; }
                QGroupBox::title { background-color: #fff8e1; color: #bf360c; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #4e342e; border: 1px solid #ffca28; }
                QDateTimeEdit::down-button { border-left-color: #ffca28; }
                QDateTimeEdit::down-button:hover { background-color: #ffb74d; }
                QComboBox QAbstractItemView { background-color: #ffecb3; color: #4e342e; border: 1px solid #ffca28; selection-background-color: #ffb74d; }
                QPushButton { background-color: #ffb74d; color: #4e342e; border: 1px solid #ffa726; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ffa726; } QPushButton:pressed { background-color: #ff9800; }
                QPushButton#InteractButton { color: #4e342e; }
                QCheckBox::indicator { border: 1px solid #ffca28; background-color: #fff; } QCheckBox::indicator:checked { background-color: #bf360c; }
                QTableWidget { background-color: #fff; alternate-background-color: #fff8e1; color: #4e342e; }
                QTableWidget::item { border-bottom: 1px solid #ffecb3; }
                QTableWidget::item:hover { background-color: #ffecb3; }
                QTableWidget::item:selected { background-color: #ffcc80; color: #4e342e; }
                QHeaderView::section { background-color: #fff8e1; border-bottom: 2px solid #bf360c; color: #4e342e; }
                QLabel, QCheckBox { color: #4e342e; background-color: transparent;} h2 { color: #d84315; }
                QSplitter::handle { background-color: #ffca28; }
                QScrollBar:vertical { background: #ffecb3; } QScrollBar::handle:vertical { background: #ffca28; }
                QMenu::item:selected { background-color: #ffb74d; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #e53935; color: white; border-color: #d32f2f; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #ffecb3; color: #4e342e; border: 1px solid #ffca28; }
                QTabBar::tab:hover { background-color: #ffb74d; }
                QTabBar::tab:selected { background-color: #ffa726; border: 1px solid #bf360c; }
                DataHarvestPane QListWidget { background-color: #ffecb3; border: 1px solid #ffca28; color: #4e342e; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #ffcc80; }
                DataHarvestPane QTableWidget { background-color: #fff; border: 1px solid #ffca28; color: #4e342e; }
                DataHarvestPane QHeaderView::section { background-color: #ffecb3; border-bottom: 2px solid #bf360c; color: #4e342e; }
            """,
            "Sunset": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #1a182f; color: #fff2cc; }
                QGroupBox { background-color: #3c3a52; border: 1px solid #ff8c42; border-radius: 5px; }
                QGroupBox::title { background-color: #1a182f; color: #ff8c42; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #1a182f; color: #fff2cc; border: 1px solid #ff8c42; selection-background-color: #ff5e57; }
                QDateTimeEdit::down-button { border-left-color: #ff8c42; }
                QDateTimeEdit::down-button:hover { background-color: #ff7b72; }
                QComboBox QAbstractItemView { background-color: #3c3a52; color: #fff2cc; border: 1px solid #ff8c42; selection-background-color: #ff5e57; }
                QPushButton { background-color: #ff5e57; color: #ffffff; border: 1px solid #ff8c42; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ff7b72; } QPushButton:pressed { background-color: #e64a19; }
                QPushButton#InteractButton { color: white; }
                QCheckBox::indicator { border: 1px solid #ff8c42; background-color: #1a182f; } QCheckBox::indicator:checked { background-color: #ff8c42; }
                QTableWidget { background-color: #3c3a52; alternate-background-color: #4a4861; }
                QTableWidget::item { border-bottom: 1px solid #5a5870; }
                QTableWidget::item:hover { background-color: #4a4861; }
                QTableWidget::item:selected { background-color: #ff5e57; color: #fff; }
                QHeaderView::section { background-color: #1a182f; border-bottom: 2px solid #ff5e57; color: #ff8c42; }
                QLabel, QCheckBox { color: #fff2cc; background-color: transparent;} h2 { color: #ff8c42; }
                QSplitter::handle { background-color: #ff8c42; }
                QScrollBar:vertical { background: #3c3a52; } QScrollBar::handle:vertical { background: #ff8c42; }
                QMenu::item:selected { background-color: #ff5e57; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c70039; color: white; border-color: #ff5e57; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #3c3a52; color: #fff2cc; border: 1px solid #ff8c42; }
                QTabBar::tab:hover { background-color: #4a4861; }
                QTabBar::tab:selected { background-color: #ff5e57; border: 1px solid #ff8c42; color: white; }
                DataHarvestPane QListWidget { background-color: #3c3a52; border: 1px solid #ff8c42; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #ff5e57; }
                DataHarvestPane QTableWidget { background-color: #1a182f; border: 1px solid #ff8c42; }
                DataHarvestPane QHeaderView::section { background-color: #3c3a52; border-bottom: 2px solid #ff5e57; }
            """,
            "Jungle": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #344e41; color: #dad7cd; }
                QGroupBox { background-color: #2b4136; border: 1px solid #a3b18a; border-radius: 5px; }
                QGroupBox::title { background-color: #344e41; color: #a3b18a; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #3a5a40; color: #dad7cd; border: 1px solid #588157; selection-background-color: #a3b18a; selection-color: #2b4136;}
                QDateTimeEdit::down-button { border-left-color: #588157; }
                QDateTimeEdit::down-button:hover { background-color: #6a996a; }
                QComboBox QAbstractItemView { background-color: #2b4136; color: #dad7cd; border: 1px solid #a3b18a; selection-background-color: #588157; }
                QPushButton { background-color: #588157; color: #ffffff; border: 1px solid #a3b18a; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #6a996a; } QPushButton:pressed { background-color: #4a714a; }
                QPushButton#InteractButton { color: white; }
                QCheckBox::indicator { border: 1px solid #a3b18a; background-color: #3a5a40; } QCheckBox::indicator:checked { background-color: #a3b18a; }
                QTableWidget { background-color: #3a5a40; alternate-background-color: #3f684c; }
                QTableWidget::item { border-bottom: 1px solid #4a714a; }
                QTableWidget::item:hover { background-color: #4a714a; }
                QTableWidget::item:selected { background-color: #588157; color: #fff; }
                QHeaderView::section { background-color: #344e41; border-bottom: 2px solid #a3b18a; }
                QLabel, QCheckBox { color: #dad7cd; background-color: transparent;} h2 { color: #cde2b4; }
                QSplitter::handle { background-color: #a3b18a; }
                QScrollBar:vertical { background: #2b4136; } QScrollBar::handle:vertical { background: #a3b18a; }
                QMenu::item:selected { background-color: #588157; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #c1440e; color: white; border-color: #a3b18a; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #3a5a40; color: #dad7cd; border: 1px solid #588157; }
                QTabBar::tab:hover { background-color: #4a714a; }
                QTabBar::tab:selected { background-color: #588157; border: 1px solid #a3b18a; color: white; }
                DataHarvestPane QListWidget { background-color: #2b4136; border: 1px solid #588157; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #588157; }
                DataHarvestPane QTableWidget { background-color: #3a5a40; border: 1px solid #588157; }
                DataHarvestPane QHeaderView::section { background-color: #2b4136; border-bottom: 2px solid #a3b18a; }
            """,
            "Ocean": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #020f1c; color: #e0ffff; }
                QGroupBox { background-color: #041c32; border: 1px solid #04294b; border-radius: 5px; }
                QGroupBox::title { background-color: #020f1c; color: #61dafb; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #020f1c; color: #e0ffff; border: 1px solid #04294b; }
                QDateTimeEdit::down-button { border-left-color: #04294b; }
                QDateTimeEdit::down-button:hover { background-color: #0074d9; }
                QComboBox QAbstractItemView { background-color: #041c32; color: #e0ffff; border: 1px solid #04294b; selection-background-color: #0074d9; }
                QPushButton { background-color: #04294b; color: #e0ffff; border: 1px solid #61dafb; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #0074d9; } QPushButton:pressed { background-color: #0060c0; }
                QPushButton#InteractButton { color: white; }
                QCheckBox::indicator { border: 1px solid #61dafb; background-color: #020f1c; } QCheckBox::indicator:checked { background-color: #61dafb; }
                QTableWidget { background-color: #041c32; alternate-background-color: #04233f; }
                QTableWidget::item { border-bottom: 1px solid #04294b; }
                QTableWidget::item:hover { background-color: #04294b; }
                QTableWidget::item:selected { background-color: #0074d9; color: #e0ffff; }
                QHeaderView::section { background-color: #020f1c; border-bottom: 2px solid #61dafb; }
                QLabel, QCheckBox { color: #e0ffff; background-color: transparent;} h2 { color: #bde0ff; }
                QSplitter::handle { background-color: #61dafb; }
                QScrollBar:vertical { background: #041c32; } QScrollBar::handle:vertical { background: #61dafb; }
                QMenu::item:selected { background-color: #0074d9; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #FF4136; color: white; border-color: #61dafb; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #041c32; color: #e0ffff; border: 1px solid #04294b; }
                QTabBar::tab:hover { background-color: #04294b; }
                QTabBar::tab:selected { background-color: #0074d9; border: 1px solid #61dafb; color: white; }
                DataHarvestPane QListWidget { background-color: #041c32; border: 1px solid #04294b; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #0074d9; }
                DataHarvestPane QTableWidget { background-color: #020f1c; border: 1px solid #04294b; }
                DataHarvestPane QHeaderView::section { background-color: #041c32; border-bottom: 2px solid #61dafb; }
            """,
            "Galaxy": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #282a36; color: #f8f8f2; }
                QGroupBox { background-color: #1e1f29; border: 1px solid #bd93f9; border-radius: 5px; }
                QGroupBox::title { background-color: #282a36; color: #ff79c6; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #21222c; color: #f8f8f2; border: 1px solid #6272a4; selection-background-color: #44475a; }
                QDateTimeEdit::down-button { border-left-color: #6272a4; }
                QDateTimeEdit::down-button:hover { background-color: #5a5c72; }
                QComboBox QAbstractItemView { background-color: #1e1f29; color: #f8f8f2; border: 1px solid #bd93f9; selection-background-color: #44475a; }
                QPushButton { background-color: #44475a; border: 1px solid #bd93f9; color: #f8f8f2; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #5a5c72; } QPushButton:pressed { background-color: #343746; }
                QPushButton#InteractButton { color: white; }
                QCheckBox::indicator { border: 1px solid #bd93f9; background-color: #21222c; } QCheckBox::indicator:checked { background-color: #bd93f9; }
                QTableWidget { background-color: #1e1f29; alternate-background-color: #21222c; }
                QTableWidget::item { border-bottom: 1px solid #44475a; }
                QTableWidget::item:hover { background-color: #44475a; }
                QTableWidget::item:selected { background-color: #5a5c72; color: #f8f8f2; }
                QHeaderView::section { background-color: #282a36; border-bottom: 2px solid #bd93f9; }
                QLabel, QCheckBox { color: #f8f8f2; background-color: transparent;} h2 { color: #8be9fd; }
                QSplitter::handle { background-color: #bd93f9; }
                QScrollBar:vertical { background: #1e1f29; } QScrollBar::handle:vertical { background: #bd93f9; }
                QMenu::item:selected { background-color: #44475a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #ff5555; color: #f8f8f2; border-color: #bd93f9; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #21222c; color: #f8f8f2; border: 1px solid #6272a4; }
                QTabBar::tab:hover { background-color: #343746; }
                QTabBar::tab:selected { background-color: #44475a; border: 1px solid #bd93f9; color: white; }
                DataHarvestPane QListWidget { background-color: #1e1f29; border: 1px solid #6272a4; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #44475a; }
                DataHarvestPane QTableWidget { background-color: #21222c; border: 1px solid #6272a4; }
                DataHarvestPane QHeaderView::section { background-color: #1e1f29; border-bottom: 2px solid #bd93f9; }
            """,
            "Candy": """
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fdf6f6; color: #5d5d5d; }
                QGroupBox { background-color: #f7e4f3; border: 1px solid #c9a7c7; border-radius: 5px; }
                QGroupBox::title { background-color: #fdf6f6; color: #8c728a; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #555; border: 1px solid #a3d9e8; selection-background-color: #ffe0b2; }
                QDateTimeEdit::down-button { border-left-color: #a3d9e8; }
                QDateTimeEdit::down-button:hover { background-color: #b3e5fc; }
                QComboBox QAbstractItemView { background-color: #f7e4f3; color: #555; border: 1px solid #c9a7c7; selection-background-color: #b3e5fc; }
                QPushButton { background-color: #c8e6c9; color: #385b38; border: 1px solid #a4d4a5; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #b7e0b8; } QPushButton:pressed { background-color: #a6d9a7; }
                QPushButton#InteractButton { color: #385b38; }
                QCheckBox::indicator { border: 1px solid #c9a7c7; background-color: #fff; } QCheckBox::indicator:checked { background-color: #a3d9e8; }
                QTableWidget { background-color: #fff; alternate-background-color: #f1f8e9; color: #444; }
                QTableWidget::item { border-bottom: 1px solid #e0e0e0; }
                QTableWidget::item:hover { background-color: #f7e4f3; }
                QTableWidget::item:selected { background-color: #b3e5fc; color: #555; }
                QHeaderView::section { background-color: #fdf6f6; border-bottom: 2px solid #c8e6c9; color: #6c6643; }
                QLabel, QCheckBox { color: #5d5d5d; background-color: transparent;} h2 { color: #c2185b; }
                QSplitter::handle { background-color: #c9a7c7; }
                QScrollBar:vertical { background: #f7e4f3; } QScrollBar::handle:vertical { background: #c9a7c7; }
                QMenu::item:selected { background-color: #b3e5fc; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton { background-color: #ffcdd2; color: #b71c1c; border-color: #ef9a9a; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #f7e4f3; color: #5d5d5d; border: 1px solid #c9a7c7; }
                QTabBar::tab:hover { background-color: #f1daec; }
                QTabBar::tab:selected { background-color: #ffffff; border: 1px solid #c9a7c7; }
                DataHarvestPane QListWidget { background-color: #f7e4f3; border: 1px solid #c9a7c7; color: #5d5d5d; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #b3e5fc; }
                DataHarvestPane QTableWidget { background-color: #ffffff; border: 1px solid #a3d9e8; color: #5d5d5d; }
                DataHarvestPane QHeaderView::section { background-color: #f7e4f3; border-bottom: 2px solid #c9a7c7; color: #5d5d5d; }
            """
        }
        
        themes["Dark (Default)"] = dark_theme
        return base_style + themes.get(theme_name, dark_theme)