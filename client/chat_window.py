
import sys
import requests
import socketio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QTextEdit, QPushButton, 
    QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QFrame,
    QMessageBox, QScrollArea, QInputDialog, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QListWidgetItem, QMenu, QAction, QStackedWidget
)



from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor


from styles import STYLE_SHEET
from animated_logo import AnimatedLogoWidget

# Socket Connection
sio = socketio.Client()

class ChatWindow(QWidget):
    message_received_signal = pyqtSignal(dict)
    typing_received_signal = pyqtSignal(dict)
    online_status_signal = pyqtSignal(list)

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.current_friend = "AI Assistant"
        self.avatars = {}
        self.avatar_paths = {}
        self.unread_counts = {}
        
        # Connect Socket
        try:
            sio.connect('http://127.0.0.1:5555')
            sio.emit('user_connected', {"username": self.username})
        except:
            print("Could not connect to server")

        self.setWindowTitle(f"NexusChat - {username}")
        self.resize(1100, 750)
        self.setup_ui()
        
        # Load Initial Data
        self.load_chat_history()
        self.update_status()
        
        # Connect Signals
        self.message_received_signal.connect(self.handle_receive_message)
        self.typing_received_signal.connect(self.handle_receive_typing)
        self.online_status_signal.connect(self.handle_update_online_status)

        # Socket Listeners (Emitting signals to safely update GUI)
        sio.on('private_message', lambda data: self.message_received_signal.emit(data))
        sio.on('online_users', lambda users: self.online_status_signal.emit(users))
        sio.on('typing', lambda data: self.typing_received_signal.emit(data))

        # Fade-in animation
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()

    def apply_glow(self, widget, color="#6366f1", blur_radius=20):
        glow = QGraphicsDropShadowEffect(widget)
        glow.setBlurRadius(blur_radius)
        glow.setColor(QColor(color))
        glow.setOffset(0, 0)
        widget.setGraphicsEffect(glow)

    def get_avatar_url(self, username):
        if username in self.avatars:
            return self.avatars[username]
        try:
            r = requests.get(f"http://127.0.0.1:5555/user/{username}", timeout=1)
            url = r.json().get('avatar_url', "")
            self.avatars[username] = url
            return url
        except:
            return ""

    def get_avatar_local_path(self, username):
        if username in self.avatar_paths:
            return self.avatar_paths[username]
            
        url = self.get_avatar_url(username)
        if not url: return ""
        import tempfile, os
        temp_dir = tempfile.gettempdir()
        path = os.path.join(temp_dir, f"avatar_{username}.jpg")
        if os.path.exists(path):
            self.avatar_paths[username] = path
            return path
        try:
            data = requests.get(url, timeout=1).content
            with open(path, "wb") as f:
                f.write(data)
            self.avatar_paths[username] = path
            return path
        except:
            return ""

    def get_avatar_icon(self, url):
        if not url:
            pix = QPixmap(40, 40)
            pix.fill(QColor("#334155"))
            return QIcon(pix)
        try:
            data = requests.get(url, timeout=1).content
            pix = QPixmap()
            pix.loadFromData(data)
            return QIcon(pix)
        except:
            pix = QPixmap(40, 40)
            pix.fill(QColor("#334155"))
            return QIcon(pix)

    def setup_ui(self):
        self.setStyleSheet(STYLE_SHEET)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar_stack = QStackedWidget()
        sidebar_layout.addWidget(self.sidebar_stack)

        # 1. Main Sidebar View
        main_sidebar_widget = QWidget()
        main_sidebar_layout = QVBoxLayout(main_sidebar_widget)
        main_sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Animated Logo
        logo = AnimatedLogoWidget()
        # Scale it down slightly for the sidebar if needed, but 300x150 should fit
        main_sidebar_layout.addWidget(logo, alignment=Qt.AlignCenter)
        
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(5, 5, 5, 5)
        profile_layout.setSpacing(10)
        
        self.user_avatar = QLabel()
        self.user_avatar.setFixedSize(40, 40)
        self.user_avatar.setStyleSheet("border-radius: 20px; background-color: #1e293b;")
        url = self.get_avatar_url(self.username)
        self.user_avatar.setPixmap(self.get_avatar_icon(url).pixmap(40, 40))
        
        self.user_profile = QLabel(self.username)
        self.user_profile.setStyleSheet("font-weight: bold; font-size: 16px; color: #6366f1;")
        
        profile_layout.addWidget(self.user_avatar)
        profile_layout.addWidget(self.user_profile)
        profile_layout.addStretch()
        
        self.settings_btn = QPushButton("Settings ⚙️")
        self.settings_btn.setObjectName("icon_button")
        self.settings_btn.setStyleSheet("color: #94a3b8; font-size: 13px; text-align: left;")
        self.settings_btn.clicked.connect(lambda: self.sidebar_stack.setCurrentIndex(1))

        self.chat_list = QListWidget()
        self.chat_list.setIconSize(QSize(30, 30))
        
        # Load contacts
        try:
            r = requests.get(f"http://127.0.0.1:5555/contacts/{self.username}")
            friends = r.json().get('contacts', [])
        except:
            friends = ["AI Assistant", "Rahul", "Priya", "Aman", "Sarah"]
            
        for friend in friends:
            self.create_contact_item(friend)
            
        self.chat_list.itemClicked.connect(self.change_chat)
        
        self.create_group_btn = QPushButton("Create Group")
        self.create_group_btn.setObjectName("icon_button")
        self.create_group_btn.setStyleSheet("color: #3b82f6; font-size: 13px; text-align: left;")
        self.create_group_btn.clicked.connect(self.create_group)
        
        self.add_contact_btn = QPushButton("Add Contact")
        self.add_contact_btn.setObjectName("icon_button")
        self.add_contact_btn.setStyleSheet("color: #6366f1; font-size: 13px; text-align: left;")
        self.add_contact_btn.clicked.connect(self.add_contact)
        
        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search contacts...")
        self.search_input.textChanged.connect(self.filter_contacts)
        self.apply_glow(self.search_input, "#4f46e5", 10)

        main_sidebar_layout.addLayout(profile_layout)
        main_sidebar_layout.addWidget(self.settings_btn)
        main_sidebar_layout.addWidget(self.add_contact_btn)
        main_sidebar_layout.addWidget(self.create_group_btn)
        main_sidebar_layout.addWidget(QLabel("CHATS"))
        main_sidebar_layout.addWidget(self.search_input)
        main_sidebar_layout.addWidget(self.chat_list)
        
        self.sidebar_stack.addWidget(main_sidebar_widget)
        
        # 2. Settings Sidebar View
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(15, 20, 15, 20)
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("icon_button")
        back_btn.setStyleSheet("color: #e2e8f0; font-weight: bold; text-align: left; font-size: 14px;")
        back_btn.clicked.connect(lambda: self.sidebar_stack.setCurrentIndex(0))
        
        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        
        self.my_contacts_btn = QPushButton("My Contacts")
        self.my_contacts_btn.setObjectName("icon_button")
        self.my_contacts_btn.setStyleSheet("color: #3b82f6; font-size: 14px; text-align: left;")
        self.my_contacts_btn.clicked.connect(lambda: QMessageBox.information(self, "My Contacts", f"You have {self.chat_list.count()} saved contacts."))
        
        self.change_avatar_btn = QPushButton("Change Profile Photo")
        self.change_avatar_btn.setObjectName("icon_button")
        self.change_avatar_btn.setStyleSheet("color: #10b981; font-size: 14px; text-align: left;")
        self.change_avatar_btn.clicked.connect(self.change_avatar)
        
        self.blocked_btn = QPushButton("Blocked Contacts")
        self.blocked_btn.setObjectName("icon_button")
        self.blocked_btn.setStyleSheet("color: #f59e0b; font-size: 14px; text-align: left;")
        self.blocked_btn.clicked.connect(self.view_blocked_contacts)
        
        self.share_profile_btn = QPushButton("Share Profile / Invite Friends")
        self.share_profile_btn.setObjectName("icon_button")
        self.share_profile_btn.setStyleSheet("color: #a855f7; font-size: 14px; text-align: left;")
        self.share_profile_btn.clicked.connect(self.share_profile)
        
        self.switch_account_btn = QPushButton("Sign Out")
        self.switch_account_btn.setObjectName("icon_button")
        self.switch_account_btn.setStyleSheet("color: #f43f5e; font-size: 14px; text-align: left;")
        self.switch_account_btn.clicked.connect(self.switch_account)
        
        settings_layout.addWidget(back_btn)
        settings_layout.addWidget(settings_title)
        settings_layout.addSpacing(20)
        settings_layout.addWidget(self.my_contacts_btn)
        settings_layout.addWidget(self.change_avatar_btn)
        settings_layout.addWidget(self.blocked_btn)
        settings_layout.addWidget(self.share_profile_btn)
        settings_layout.addWidget(self.switch_account_btn)
        settings_layout.addStretch()
        
        self.sidebar_stack.addWidget(settings_widget)

        
        # --- Chat Area ---
        chat_container = QFrame()
        
        # Add opacity effect for smooth transitions
        self.chat_opacity_effect = QGraphicsOpacityEffect()
        chat_container.setGraphicsEffect(self.chat_opacity_effect)
        
        chat_layout = QVBoxLayout(chat_container)
        
        # Stories Bar
        self.stories_frame = QFrame()
        self.stories_frame.setFixedHeight(100)
        self.stories_frame.setStyleSheet("background-color: #0f172a; border-bottom: 1px solid #334155;")
        self.stories_layout = QHBoxLayout(self.stories_frame)
        self.stories_layout.setAlignment(Qt.AlignLeft)
        
        # Load Stories
        self.refresh_stories()
        
        # Chat Header
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("background-color: #1e293b; border-bottom: 1px solid #334155;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignVCenter)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(2)
        
        self.header_avatar = QLabel()
        self.header_avatar.setFixedSize(45, 45)
        self.header_avatar.setStyleSheet("border-radius: 22px; background-color: #334155;")
        
        self.chat_header_label = QLabel(f"Chat with {self.current_friend}")
        self.chat_header_label.setObjectName("header")
        self.chat_header_label.setStyleSheet("padding: 0; margin: 0; font-size: 20px;")
        
        self.status_label = QLabel("Offline")
        self.status_label.setObjectName("status")
        self.status_label.setStyleSheet("padding: 0; margin: 0; color: #10b981; font-weight: bold;")
        
        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()
        v_layout.addWidget(self.chat_header_label)
        v_layout.addWidget(self.status_label)
        
        h_layout.addWidget(self.header_avatar)
        h_layout.addLayout(v_layout)
        h_layout.addStretch()
        
        header_layout.addLayout(h_layout)
        
        # Messages Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFrameStyle(QFrame.NoFrame)
        
        self.typing_label = QLabel("")
        self.typing_label.setStyleSheet("color: #94a3b8; font-style: italic; padding-left: 10px;")

        # Input Area
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_layout = QHBoxLayout(input_frame)
        
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self.send_message)
        self.msg_input.textChanged.connect(self.send_typing_event)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self.send_message)
        self.apply_glow(self.send_btn, "#6366f1", 15)
        
        self.img_btn = QPushButton("📷")
        self.img_btn.setObjectName("icon_button")
        self.img_btn.setFixedWidth(50)
        self.img_btn.clicked.connect(self.send_image)
        
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setObjectName("icon_button")
        self.voice_btn.setFixedWidth(50)
        self.voice_btn.clicked.connect(self.record_voice)
        
        self.camera_btn = QPushButton("📸")
        self.camera_btn.setObjectName("icon_button")
        self.camera_btn.setFixedWidth(50)
        self.camera_btn.clicked.connect(self.capture_photo)
        
        input_layout.addWidget(self.img_btn)
        input_layout.addWidget(self.camera_btn)
        input_layout.addWidget(self.voice_btn)
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(self.stories_frame)
        chat_layout.addWidget(header_frame)
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.typing_label)
        chat_layout.addWidget(input_frame)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(chat_container)
        self.setLayout(main_layout)

    def filter_contacts(self, text):
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            contact_name = item.data(Qt.UserRole)
            if contact_name:
                item.setHidden(text.lower() not in contact_name.lower())

    def change_chat(self, item):
        # Fade transition animation
        self.chat_anim = QPropertyAnimation(self.chat_opacity_effect, b"opacity")
        self.chat_anim.setDuration(400)
        self.chat_anim.setStartValue(0.0)
        self.chat_anim.setEndValue(1.0)
        self.chat_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.chat_anim.start()

        contact_name = item.data(Qt.UserRole)
        if not contact_name:
            contact_name = item.text() # Fallback for groups
            
        if self.unread_counts.get(contact_name, 0) > 0:
            self.unread_counts[contact_name] = 0
            self.create_contact_item(contact_name) # Updates the dot without moving
            
        self.current_friend = contact_name
        self.chat_header_label.setText(f"Chat with {self.current_friend}")
        
        url = self.get_avatar_url(self.current_friend)
        if url:
            try:
                data = requests.get(url, timeout=1).content
                pix = QPixmap()
                pix.loadFromData(data)
                self.header_avatar.setPixmap(pix.scaled(45, 45, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            except:
                self.header_avatar.clear()
        else:
            self.header_avatar.clear()

        self.chat_display.clear()
        self.update_status()
        self.load_chat_history()
        
        sio.emit('join_room', {
            "username": self.username,
            "friend": self.current_friend
        })

    def send_message(self):
        text = self.msg_input.text().strip()
        if text:
            data = {
                "user": self.username,
                "friend": self.current_friend,
                "message": text
            }
            sio.emit('private_message', data)
            self.msg_input.clear()

    def format_message(self, sender, text, timestamp=None):
        import datetime
        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%H:%M")
            
        path = self.get_avatar_local_path(sender)
        img_tag = f"<img src='{path}' width='25' height='25'>" if path else "👤"
        time_tag = f"<span style='color: #64748b; font-size: 11px; margin-left: 10px;'>{timestamp}</span>"
        
        if sender == self.username:
            return f"<div style='text-align: right; color: #818cf8; font-size: 15px;'>{text} {time_tag} <b>:You</b> {img_tag}</div>"
        else:
            return f"<div style='text-align: left; color: #e2e8f0; font-size: 15px;'>{img_tag} <b>{sender}:</b> {text} {time_tag}</div>"

    def handle_receive_message(self, data):
        sender = data['user']
        msg = data['message']
        timestamp = data.get('timestamp')
        
        other_person = sender if sender != self.username else data.get('friend')
        
        if other_person and other_person != self.current_friend and sender != self.username:
            self.unread_counts[other_person] = self.unread_counts.get(other_person, 0) + 1
            self.create_contact_item(other_person, insert_at_row=0)
            return
            
        if other_person:
            self.unread_counts[other_person] = 0
            self.create_contact_item(other_person, insert_at_row=0)
            
        formatted_msg = self.format_message(sender, msg, timestamp)
        self.chat_display.append(formatted_msg)
        self.typing_label.setText("")

    def send_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            try:
                files = {'file': open(path, 'rb')}
                r = requests.post("http://127.0.0.1:5555/upload", files=files)
                filename = r.json().get('filename')
                if filename:
                    data = {
                        "user": self.username,
                        "friend": self.current_friend,
                        "message": f"🖼 Sent an image: http://127.0.0.1:5555/uploads/{filename}"
                    }
                    sio.emit('private_message', data)
            except Exception as e:
                print(f"Upload error: {e}")

    def send_typing_event(self):
        sio.emit('typing', {"user": self.username, "friend": self.current_friend})

    def handle_receive_typing(self, data):
        if data['user'] == self.current_friend:
            self.typing_label.setText(f"{self.current_friend} is typing...")

    def update_status(self):
        try:
            r = requests.get(f"http://127.0.0.1:5555/last_seen/{self.current_friend}")
            self.status_label.setText(r.json().get('status', 'Offline'))
        except:
            self.status_label.setText("Offline")

    def handle_update_online_status(self, users):
        if self.current_friend in users:
            self.status_label.setText("Online")
        else:
            self.update_status()

    def create_group(self):
        group_name, ok = QInputDialog.getText(self, "Create Group", "Enter Group Name:")
        if ok and group_name:
            item = QListWidgetItem(f"Group: {group_name}")
            item.setData(Qt.UserRole, f"Group: {group_name}")
            self.chat_list.addItem(item)
            QMessageBox.information(self, "Success", f"Group '{group_name}' created!")
            
    def create_contact_item(self, contact_name, insert_at_row=None):
        current_row = None
        for i in range(self.chat_list.count()):
            if self.chat_list.item(i).data(Qt.UserRole) == contact_name:
                current_row = i
                self.chat_list.takeItem(i)
                break
                
        if insert_at_row is None:
            insert_at_row = current_row if current_row is not None else self.chat_list.count()
            
        item = QListWidgetItem()
        item.setData(Qt.UserRole, contact_name)
        
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        # Avatar
        url = self.get_avatar_url(contact_name)
        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(35, 35)
        icon = self.get_avatar_icon(url)
        avatar_lbl.setPixmap(icon.pixmap(35, 35))
        avatar_lbl.setScaledContents(True)
        
        # Name
        name_lbl = QLabel(contact_name)
        name_lbl.setStyleSheet("color: #e2e8f0; font-size: 15px; font-weight: bold; background: transparent;")
        
        # Three dots menu
        btn = QPushButton("⋮")
        btn.setFixedSize(25, 25)
        btn.setStyleSheet("background: transparent; color: #94a3b8; font-weight: bold; border: none; font-size: 20px;")
        
        # Unread dot
        unread_lbl = QLabel("")
        unread_lbl.setFixedSize(20, 20)
        unread_lbl.setAlignment(Qt.AlignCenter)
        unread_lbl.setStyleSheet("background-color: #4f46e5; color: white; border-radius: 10px; font-size: 11px; font-weight: bold;")
        count = self.unread_counts.get(contact_name, 0)
        if count > 0:
            unread_lbl.setText(str(count))
        else:
            unread_lbl.hide()
            
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda checked, name=contact_name, itm=item: self.edit_contact(name, itm))
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda checked, name=contact_name, itm=item: self.delete_contact(name, itm))
        block_action = QAction("Block", self)
        block_action.triggered.connect(lambda checked, name=contact_name: self.block_contact(name))
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(block_action)
        btn.setMenu(menu)
        
        layout.addWidget(avatar_lbl)
        layout.addWidget(name_lbl)
        layout.addStretch()
        layout.addWidget(unread_lbl)
        layout.addWidget(btn)
        
        widget.setLayout(layout)
        widget.setStyleSheet("background: transparent;")
        item.setSizeHint(QSize(250, 65))
        
        self.chat_list.insertItem(insert_at_row, item)
        self.chat_list.setItemWidget(item, widget)

    def add_contact(self):
        contact_name, ok = QInputDialog.getText(self, "Add Contact", "Enter Contact Username:")
        if ok and contact_name:
            requests.post("http://127.0.0.1:5555/contacts", json={
                "username": self.username,
                "contact": contact_name
            })
            self.create_contact_item(contact_name)
            QMessageBox.information(self, "Success", f"Contact '{contact_name}' added to your list!")

    def edit_contact(self, old_name, item):
        new_name, ok = QInputDialog.getText(self, "Edit Contact", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            requests.put("http://127.0.0.1:5555/contacts", json={
                "username": self.username,
                "old_contact": old_name,
                "new_contact": new_name
            })
            row = self.chat_list.row(item)
            self.chat_list.takeItem(row)
            self.create_contact_item(new_name)
            
    def delete_contact(self, contact_name, item):
        reply = QMessageBox.question(self, 'Delete Contact', f"Are you sure you want to delete {contact_name}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            requests.delete("http://127.0.0.1:5555/contacts", json={
                "username": self.username,
                "contact": contact_name
            })
            row = self.chat_list.row(item)
            self.chat_list.takeItem(row)
            
    def block_contact(self, contact_name):
        reply = QMessageBox.question(self, 'Block Contact', f"Are you sure you want to block {contact_name}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            requests.post("http://127.0.0.1:5555/block", json={
                "username": self.username,
                "contact": contact_name
            })
            QMessageBox.information(self, "Blocked", f"User '{contact_name}' has been blocked.")

    def view_blocked_contacts(self):
        try:
            r = requests.get(f"http://127.0.0.1:5555/blocked/{self.username}")
            blocked = r.json().get('blocked', [])
            if not blocked:
                QMessageBox.information(self, "Blocked Contacts", "You have no blocked contacts.")
                return
            
            contact, ok = QInputDialog.getItem(self, "Blocked Contacts", "Select a contact to unblock:", blocked, 0, False)
            if ok and contact:
                requests.post("http://127.0.0.1:5555/unblock", json={"username": self.username, "contact": contact})
                QMessageBox.information(self, "Success", f"User '{contact}' has been unblocked.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load blocked contacts: {e}")

    def share_profile(self):
        invite_text = f"Hey! Let's chat on NexusChat. Add me using my username: {self.username}\nJoin here: https://nexus-chat1.vercel.app"
        clipboard = QApplication.clipboard()
        clipboard.setText(invite_text)
        QMessageBox.information(self, "Share Profile", f"Profile invite copied to clipboard!\n\n{invite_text}\n\nShare this with your friends to connect!")

    def change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Profile Photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            try:
                files = {'file': open(path, 'rb')}
                r = requests.post("http://127.0.0.1:5555/upload", files=files)
                filename = r.json().get('filename')
                if filename:
                    url = f"http://127.0.0.1:5555/uploads/{filename}"
                    requests.post("http://127.0.0.1:5555/update_avatar", json={
                        "username": self.username,
                        "avatar_url": url
                    })
                    self.avatars[self.username] = url
                    self.avatar_paths.pop(self.username, None) # Clear local cache
                    QMessageBox.information(self, "Success", "Profile photo updated!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to upload: {e}")

    def switch_account(self):
        reply = QMessageBox.question(self, 'Switch Account', 'Are you sure you want to log out?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            import subprocess
            subprocess.Popen([sys.executable, "client/login.py"])
            self.close()

    def capture_photo(self):
        try:
            import cv2
            import tempfile
            import os
            
            cap = cv2.VideoCapture(0)
            # Warm up the camera to avoid dark images
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, "live_capture.jpg")
                cv2.imwrite(temp_path, frame)
                
                files = {'file': open(temp_path, 'rb')}
                r = requests.post("http://127.0.0.1:5555/upload", files=files)
                filename = r.json().get('filename')
                if filename:
                    data = {
                        "user": self.username,
                        "friend": self.current_friend,
                        "message": f"🖼 Live Photo: http://127.0.0.1:5555/uploads/{filename}"
                    }
                    sio.emit('private_message', data)
                    QMessageBox.information(self, "Success", "Live photo captured and sent!")
            else:
                QMessageBox.warning(self, "Camera Error", "Could not capture image from webcam.")
        except ImportError:
            QMessageBox.warning(self, "Missing Module", "OpenCV is required. Run 'pip install opencv-python'")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def record_voice(self):
        QMessageBox.information(self, "Voice Note", "Voice recording feature coming soon! (Requires PyAudio/SoundDevice)")

    def refresh_stories(self):
        # Clear layout
        for i in reversed(range(self.stories_layout.count())): 
            self.stories_layout.itemAt(i).widget().setParent(None)
            
        # Add "Your Story" button
        add_story_btn = QPushButton("+")
        add_story_btn.setFixedSize(60, 60)
        add_story_btn.setStyleSheet("border-radius: 30px; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #6366f1); font-size: 20px; font-weight: bold; border: none;")
        add_story_btn.clicked.connect(self.upload_story)
        self.apply_glow(add_story_btn, "#6366f1", 15)
        self.stories_layout.addWidget(add_story_btn)

        try:
            r = requests.get("http://127.0.0.1:5555/stories")

            stories = r.json().get('stories', [])
            for s in stories:
                lbl = QLabel(s['username'][0].upper())
                lbl.setFixedSize(60, 60)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("border-radius: 30px; border: 2px solid #6366f1; background-color: #1e293b; font-weight: bold; color: white;")
                lbl.setToolTip(f"{s['username']} at {s['time']}")
                self.apply_glow(lbl, "#6366f1", 10)
                self.stories_layout.addWidget(lbl)

        except:
            pass

    def upload_story(self):
        path, _ = QFileDialog.getOpenFileName(self, "Upload Story", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            try:
                files = {'file': open(path, 'rb')}
                r = requests.post("http://127.0.0.1:5555/upload", files=files)
                filename = r.json().get('filename')
                if filename:
                    requests.post("http://127.0.0.1:5555/stories", json={
                        "username": self.username,
                        "image_url": f"http://127.0.0.1:5555/uploads/{filename}"
                    })

                    self.refresh_stories()
                    QMessageBox.information(self, "Success", "Story uploaded!")
            except Exception as e:
                print(f"Story upload error: {e}")

    def load_chat_history(self):
        try:
            r = requests.get("http://127.0.0.1:5555/private_messages", params={

                "user1": self.username,
                "user2": self.current_friend
            })
            messages = r.json().get('messages', [])
            for msg in messages:
                sender = msg['user']
                text = msg['message']
                timestamp = msg.get('timestamp')
                formatted_msg = self.format_message(sender, text, timestamp)
                self.chat_display.append(formatted_msg)
        except Exception as e:
            print(f"History error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatWindow("User")
    window.show()
    sys.exit(app.exec_())
