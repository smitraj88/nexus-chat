
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QStackedWidget,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QFont
from chat_window import ChatWindow
from styles import STYLE_SHEET
from animated_logo import AnimatedLogoWidget


class LoginSignupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexusChat - Login")
        self.setFixedSize(450, 550)
        self.setStyleSheet(STYLE_SHEET)
        self.chat_window = None
        
        self.setWindowOpacity(0.0) # For fade-in animation
        self.setup_ui()
        
        # Fade-in animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()

    def apply_glow(self, widget, color="#6366f1", blur_radius=25):
        glow = QGraphicsDropShadowEffect(widget)
        glow.setBlurRadius(blur_radius)
        glow.setColor(QColor(color))
        glow.setOffset(0, 0)
        widget.setGraphicsEffect(glow)

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(20)
        
        self.stack = QStackedWidget()
        
        # Login Page
        self.login_page = self.create_login_page()
        # Signup Page
        self.signup_page = self.create_signup_page()
        
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.signup_page)
        
        self.main_layout.addWidget(self.stack)
        self.setLayout(self.main_layout)

    def create_login_page(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        # Animated Logo
        logo = AnimatedLogoWidget()
        layout.addWidget(logo, alignment=Qt.AlignCenter)
        
        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username")
        
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Password")
        self.login_pass.setEchoMode(QLineEdit.Password)
        
        btn_login = QPushButton("LOGIN")
        btn_login.clicked.connect(self.handle_login)
        self.apply_glow(btn_login, "#6366f1", 20)
        
        btn_switch = QPushButton("Don't have an account? Sign Up")
        btn_switch.setObjectName("icon_button")
        btn_switch.setStyleSheet("color: #3b82f6; font-size: 12px;")
        btn_switch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        layout.addWidget(self.login_user)
        layout.addWidget(self.login_pass)
        layout.addWidget(btn_login)
        layout.addWidget(btn_switch)
        
        return page

    def create_signup_page(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        # Animated Logo
        logo = AnimatedLogoWidget()
        layout.addWidget(logo, alignment=Qt.AlignCenter)
        
        self.signup_user = QLineEdit()
        self.signup_user.setPlaceholderText("Username")
        
        self.signup_email = QLineEdit()
        self.signup_email.setPlaceholderText("Email Address")
        
        self.signup_pass = QLineEdit()
        self.signup_pass.setPlaceholderText("Password")
        self.signup_pass.setEchoMode(QLineEdit.Password)
        
        btn_signup = QPushButton("SIGN UP")
        btn_signup.clicked.connect(self.handle_signup)
        self.apply_glow(btn_signup, "#6366f1", 20)
        
        btn_switch = QPushButton("Already have an account? Log In")
        btn_switch.setObjectName("icon_button")
        btn_switch.setStyleSheet("color: #3b82f6; font-size: 12px;")
        btn_switch.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        layout.addWidget(self.signup_user)
        layout.addWidget(self.signup_email)
        layout.addWidget(self.signup_pass)
        layout.addWidget(btn_signup)
        layout.addWidget(btn_switch)
        
        return page

    def handle_login(self):
        print("DEBUG: Login button clicked")
        username = self.login_user.text()
        password = self.login_pass.text()
        
        try:
            r = requests.post("http://127.0.0.1:5555/login", json={

                "username": username,
                "password": password
            }, timeout=5)
            print(f"DEBUG: Server responded with {r.status_code}")

            if r.status_code == 200:
                self.chat_window = ChatWindow(username)
                self.chat_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "Login Failed", r.json().get('message', 'Error'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not connect to server: {e}")

    def handle_signup(self):
        print("DEBUG: Signup button clicked")
        username = self.signup_user.text()
        email = self.signup_email.text()
        password = self.signup_pass.text()
        
        if not username or not email or not password:
            QMessageBox.warning(self, "Missing Fields", "Please fill all fields")
            return
            
        try:
            r = requests.post("http://127.0.0.1:5555/signup", json={

                "username": username,
                "email": email,
                "password": password
            }, timeout=5)
            print(f"DEBUG: Server responded with {r.status_code}")

            if r.status_code == 201:
                QMessageBox.information(self, "Success", "Account created! Please log in.")
                self.stack.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Signup Failed", r.json().get('message', 'Error'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not connect to server: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginSignupWindow()
    window.show()
    sys.exit(app.exec_())
