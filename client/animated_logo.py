from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

class AnimatedLogoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 150)
        
        # Bubble 1 (Purple)
        self.bubble1 = QLabel("😊", self)
        self.bubble1.setAlignment(Qt.AlignCenter)
        self.bubble1.setStyleSheet("background-color: #a855f7; font-size: 25px; border-radius: 25px; border-bottom-left-radius: 5px;")
        self.bubble1.setFixedSize(50, 50)
        self.bubble1.move(100, 20)
        
        # Bubble 2 (Dark)
        self.bubble2 = QLabel("😉", self)
        self.bubble2.setAlignment(Qt.AlignCenter)
        self.bubble2.setStyleSheet("background-color: #1e293b; font-size: 20px; border-radius: 20px; border-bottom-right-radius: 5px; border: 2px solid #a855f7;")
        self.bubble2.setFixedSize(40, 40)
        self.bubble2.move(155, 30)
        
        # Title "Nexus Chat"
        self.title_nexus = QLabel("Nexus", self)
        self.title_nexus.setStyleSheet("font-size: 35px; font-weight: 900; color: white; background: transparent;")
        self.title_nexus.move(65, 80)
        
        self.title_chat = QLabel("Chat", self)
        self.title_chat.setStyleSheet("font-size: 35px; font-weight: 900; color: #a855f7; background: transparent;")
        self.title_chat.move(175, 80)
        
        # Animation for Bubble 1
        self.anim1 = QPropertyAnimation(self.bubble1, b"pos")
        self.anim1.setDuration(2000)
        self.anim1.setKeyValueAt(0, QPoint(100, 20))
        self.anim1.setKeyValueAt(0.5, QPoint(100, 10))
        self.anim1.setKeyValueAt(1, QPoint(100, 20))
        self.anim1.setLoopCount(-1)
        self.anim1.start()
        
        # Animation for Bubble 2
        self.anim2 = QPropertyAnimation(self.bubble2, b"pos")
        self.anim2.setDuration(2500)
        self.anim2.setKeyValueAt(0, QPoint(155, 30))
        self.anim2.setKeyValueAt(0.5, QPoint(155, 22))
        self.anim2.setKeyValueAt(1, QPoint(155, 30))
        self.anim2.setLoopCount(-1)
        self.anim2.start()
