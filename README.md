# NexusChat

NexusChat is a comprehensive AI-powered hybrid chat application. It provides real-time messaging, powerful media attachment capabilities, and a personalized user experience. Featuring both a Python-based client interface and a web/mobile server backend, NexusChat seamlessly integrates AI services to enhance communication.

## Features

- **Hybrid Architecture**: Python client interface coupled with a robust server.
- **AI Integration**: Built-in AI capabilities for smart interactions.
- **Real-Time Chat**: Fast and reliable message delivery.
- **Profile Management**: Customizable user profiles with avatar selection, custom image uploads, and profile resets.
- **Media Support**: Seamless handling of document and media attachments (mobile & desktop).
- **Secure Authentication**: Robust user login and registration system.

## Tech Stack

- **Backend**: Python (`app.py`), integrating AI (`ai_service.py`), Authentication (`auth.py`), and Database management.
- **Frontend / Client**: Python-based graphical client (`chat_window.py`, `animated_logo.py`, `styles.py`) along with a web interface (HTML/CSS/JS in `server/static` and `server/templates`).

## Project Structure

- `client/`: Contains the Python GUI client source code.
- `server/`: Backend API, web server code, and static assets.
- `database/`: Database configuration and storage.
- `assets/`: Static image and media assets for the client.
- `uploads/`: Directory for user-uploaded files and media.

## Setup Instructions

1. Clone this repository.
2. Ensure you have Python installed.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
5. Install necessary dependencies (ensure `requirements.txt` is present or install libraries used).
6. Create a `.env` file based on `.env.example` with your specific configurations.
7. Start the backend server:
   ```bash
   cd server
   python app.py
   ```
8. In a new terminal window, start the client:
   ```bash
   cd client
   python login.py
   ```

## Development

- Make sure to review the `.env.example` file to configure external services (like AI API keys, database URIs).
- The `uploads/` and `__pycache__/` folders are excluded from version control to maintain repository hygiene.
