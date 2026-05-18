STYLE_SHEET = """
QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar */
QListWidget {
    background-color: #1e293b;
    border: none;
    border-right: 1px solid #334155;
    outline: none;
    padding: 15px;
}

QListWidget::item {
    background-color: transparent;
    border-radius: 12px;
    margin-bottom: 8px;
    color: #94a3b8;
    font-size: 14px;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1d4ed8, stop:1 #3b82f6);
    color: white;
    font-weight: bold;
}

QListWidget::item:hover:!selected {
    background-color: #334155;
    color: white;
}

/* Chat Area */
QTextEdit {
    background-color: #0f172a;
    border: none;
    padding: 20px;
    font-size: 15px;
    selection-background-color: #1d4ed8;
}

/* Input Area */
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 12px 20px;
    font-size: 15px;
    color: white;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #1e293b;
}

/* Primary Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #3b82f6);
    color: white;
    border-radius: 20px;
    padding: 12px 25px;
    font-weight: bold;
    font-size: 14px;
    border: none;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
}

QPushButton:pressed {
    background: #1e3a8a;
}

/* Icon Buttons */
QPushButton#icon_button {
    background: transparent;
    color: #3b82f6;
    font-size: 22px;
    padding: 5px;
    border-radius: 20px;
}

QPushButton#icon_button:hover {
    background-color: #334155;
    color: #60a5fa;
}

QPushButton#icon_button:pressed {
    background-color: #334155;
}

/* Headers */
QLabel#header {
    font-size: 26px;
    font-weight: 800;
    color: white;
    padding: 10px;
    letter-spacing: 1px;
}

QLabel#status {
    font-size: 13px;
    color: #10b981;
    padding-left: 10px;
    font-weight: bold;
}
"""
