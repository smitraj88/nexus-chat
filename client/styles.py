STYLE_SHEET = """
QWidget {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar */
QListWidget {
    background-color: #12182b;
    border: none;
    border-right: 1px solid #1e293b;
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #6366f1);
    color: white;
    font-weight: bold;
}

QListWidget::item:hover:!selected {
    background-color: #1e293b;
    color: white;
}

/* Chat Area */
QTextEdit {
    background-color: #0b0f19;
    border: none;
    padding: 20px;
    font-size: 15px;
    selection-background-color: #4f46e5;
}

/* Input Area */
QLineEdit {
    background-color: #12182b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 12px 20px;
    font-size: 15px;
    color: white;
}

QLineEdit:focus {
    border: 1px solid #6366f1;
    background-color: #1a233a;
}

/* Primary Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #6366f1);
    color: white;
    border-radius: 20px;
    padding: 12px 25px;
    font-weight: bold;
    font-size: 14px;
    border: none;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #818cf8);
}

QPushButton:pressed {
    background: #4338ca;
}

/* Icon Buttons */
QPushButton#icon_button {
    background: transparent;
    color: #6366f1;
    font-size: 22px;
    padding: 5px;
    border-radius: 20px;
}

QPushButton#icon_button:hover {
    background-color: #1e293b;
    color: #818cf8;
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
