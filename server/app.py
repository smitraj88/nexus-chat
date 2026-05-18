import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flask import Flask, request, send_from_directory, jsonify, render_template

from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timedelta

from auth import register_routes
from database import messages_collection, contacts_collection, users_collection, stories_collection
from ai_service import get_ai_response

app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'), static_folder=os.path.join(base_dir, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key')

if os.environ.get('VERCEL') == '1':
    app.config['UPLOAD_FOLDER'] = '/tmp'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Register Auth Routes
register_routes(app)

socketio = SocketIO(app, cors_allowed_origins="*")


# State management (In-memory for simplicity in this demo)
online_users = {}
last_seen = {}

@app.route('/')
def home():
    return render_template("index.html")

# =========================
# SOCKET EVENTS
# =========================

@socketio.on('user_connected')
def user_connected(data):
    username = data.get('username')
    if username:
        online_users[username] = request.sid
        print(f"DEBUG: {username} connected")
        emit('online_users', list(online_users.keys()), broadcast=True)

@socketio.on('disconnect')
def user_disconnected():
    disconnected_user = None
    for username, sid in online_users.items():
        if sid == request.sid:
            disconnected_user = username
            break
    
    if disconnected_user:
        del online_users[disconnected_user]
        last_seen[disconnected_user] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"DEBUG: {disconnected_user} disconnected")
        emit('online_users', list(online_users.keys()), broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    username = data.get('username')
    friend = data.get('friend')
    if username and friend:
        room = "_".join(sorted([username, friend]))
        join_room(room)
        print(f"DEBUG: {username} joined room {room}")

@socketio.on('private_message')
def handle_private_message(data):
    username = data.get('user')
    friend = data.get('friend')
    message = data.get('message')
    
    if not username or not friend: return

    room = "_".join(sorted([username, friend]))
    
    # Store in DB
    messages_collection.insert_one({
        "user": username,
        "friend": friend,
        "message": message,
        "room": room,
        "timestamp": datetime.utcnow()
    })

    # Broadcast to room
    emit('private_message', data, room=room)

    # AI Assistant Integration
    if friend == "AI Assistant":
        ai_reply = get_ai_response(message)
        ai_data = {
            "user": "AI Assistant",
            "friend": username,
            "message": ai_reply
        }
        # Store AI reply
        messages_collection.insert_one({
            "user": "AI Assistant",
            "friend": username,
            "message": ai_reply,
            "room": room,
            "timestamp": datetime.utcnow()
        })
        emit('private_message', ai_data, room=room)

@socketio.on('typing')
def handle_typing(data):
    room = "_".join(sorted([data['user'], data['friend']]))
    emit('typing', data, room=room)

@socketio.on('delete_message')
def handle_delete_message(data):
    # data: user, friend, message, timestamp, for_everyone
    room = "_".join(sorted([data['user'], data['friend']]))
    
    if data.get('for_everyone'):
        # Delete completely from database
        messages_collection.delete_many({
            "user": data['user'],
            "message": data['message']
        })
        emit('message_deleted', data, room=room)
    else:
        # Delete only for me (we can just emit a local event back or handle purely locally, but for demo we just send a signal to refresh)
        pass

@socketio.on('edit_message')
def handle_edit_message(data):
    # data: user, friend, old_message, new_message
    room = "_".join(sorted([data['user'], data['friend']]))
    messages_collection.update_many(
        {"user": data['user'], "message": data['old_message']},
        {"$set": {"message": data['new_message']}}
    )
    emit('message_edited', data, room=room)

# =========================
# API ROUTES
# =========================

@app.route('/stories', methods=['POST'])
def upload_story():
    data = request.json
    username = data.get('username')
    image_url = data.get('image_url')
    
    if not username or not image_url:
        return jsonify({"message": "Missing data"}), 400
        
    stories_collection.insert_one({
        "username": username,
        "image_url": image_url,
        "timestamp": datetime.utcnow()
    })
    return jsonify({"message": "Story uploaded"}), 201

@app.route('/stories', methods=['GET'])
def get_stories():
    # Show stories from last 24 hours
    limit = datetime.utcnow() - timedelta(hours=24)
    cursor = stories_collection.find({"timestamp": {"$gt": limit}}).sort("timestamp", -1)
    stories = []
    for s in cursor:
        stories.append({
            "username": s['username'],
            "image_url": s['image_url'],
            "time": s['timestamp'].strftime("%H:%M")
        })
    return jsonify({"stories": stories})

@app.route('/last_seen/<username>')
def get_last_seen(username):
    if username in online_users:
        return jsonify({"status": "Online"})
    return jsonify({"status": f"Last seen: {last_seen.get(username, 'Long ago')}"})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Empty filename"}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    return jsonify({"message": "File uploaded", "filename": file.filename})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/private_messages', methods=['GET'])
def get_private_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    if not user1 or not user2:
        return jsonify({"messages": []})
    
    room = "_".join(sorted([user1, user2]))
    messages = []
    cursor = messages_collection.find({"room": room}).sort("timestamp", 1)
    for msg in cursor:
        messages.append({
            "user": msg['user'],
            "message": msg['message'],
            "timestamp": msg.get('timestamp', datetime.utcnow()).strftime("%H:%M")
        })
    return jsonify({"messages": messages})

@app.route('/contacts/<username>', methods=['GET'])
def get_contacts(username):
    user_data = contacts_collection.find_one({"username": username})
    if user_data and "contacts" in user_data:
        return jsonify({"contacts": user_data["contacts"]})
    
    # Default contacts for new users
    default_contacts = ["AI Assistant", "Rahul", "Priya", "Aman", "Sarah"]
    contacts_collection.insert_one({"username": username, "contacts": default_contacts})
    return jsonify({"contacts": default_contacts})

@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.json
    username = data.get('username')
    contact = data.get('contact')
    contacts_collection.update_one(
        {"username": username},
        {"$addToSet": {"contacts": contact}},
        upsert=True
    )
    return jsonify({"message": "Contact added"}), 201

@app.route('/contacts', methods=['PUT'])
def edit_contact():
    data = request.json
    username = data.get('username')
    old_contact = data.get('old_contact')
    new_contact = data.get('new_contact')
    
    contacts_collection.update_one(
        {"username": username},
        {"$pull": {"contacts": old_contact}}
    )
    contacts_collection.update_one(
        {"username": username},
        {"$addToSet": {"contacts": new_contact}}
    )
    return jsonify({"message": "Contact updated"}), 200

@app.route('/contacts', methods=['DELETE'])
def delete_contact():
    data = request.json
    username = data.get('username')
    contact = data.get('contact')
    contacts_collection.update_one(
        {"username": username},
        {"$pull": {"contacts": contact}}
    )
    return jsonify({"message": "Contact deleted"}), 200

@app.route('/block', methods=['POST'])
def block_user():
    data = request.json
    username = data.get('username')
    contact = data.get('contact')
    users_collection.update_one({"username": username}, {"$addToSet": {"blocked": contact}})
    return jsonify({"message": "Blocked"}), 200

@app.route('/unblock', methods=['POST'])
def unblock_user():
    data = request.json
    username = data.get('username')
    contact = data.get('contact')
    users_collection.update_one({"username": username}, {"$pull": {"blocked": contact}})
    return jsonify({"message": "Unblocked"}), 200

@app.route('/blocked/<username>', methods=['GET'])
def get_blocked(username):
    user = users_collection.find_one({"username": username})
    blocked = user.get("blocked", []) if user else []
    return jsonify({"blocked": blocked})

@app.route('/avatar/<username>', methods=['GET'])
def get_avatar(username):
    user = users_collection.find_one({"username": username})
    if user and "avatar" in user:
        return jsonify({"avatar": user["avatar"]})
    return jsonify({"avatar": f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}"})

@app.route('/avatar', methods=['POST'])
def set_avatar():
    data = request.json
    username = data.get('username')
    avatar = data.get('avatar')
    users_collection.update_one({"username": username}, {"$set": {"avatar": avatar}}, upsert=True)
    return jsonify({"message": "Avatar updated"}), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5555, debug=True, allow_unsafe_werkzeug=True)


