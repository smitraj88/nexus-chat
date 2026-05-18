from flask import request, jsonify
from database import users_collection
import bcrypt
import datetime
import jwt

SECRET_KEY = "your_super_secret_key" # In production, use environment variables

def register_routes(app):
    # =========================
    # SIGNUP API
    # =========================
    @app.route('/signup', methods=['POST'])
    def signup():
        print("DEBUG: Received Signup Request")
        try:

            data = request.json
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not password or not email:
                return jsonify({"message": "All fields are required"}), 400

            # CHECK IF USER EXISTS
            if users_collection.find_one({"username": username}):
                return jsonify({"message": "Username already exists"}), 400

            # HASH PASSWORD
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # SAVE USER
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.datetime.utcnow()
            }
            users_collection.insert_one(user_data)

            return jsonify({"message": "User created successfully"}), 201
        except Exception as e:
            return jsonify({"message": str(e)}), 500

    # =========================
    # LOGIN API
    # =========================
    @app.route('/login', methods=['POST'])
    def login():
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')

            # FIND USER
            user = users_collection.find_one({"username": username})

            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
                return jsonify({"message": "Invalid username or password"}), 401

            # GENERATE TOKEN (Optional for now, but good practice)
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm="HS256")

            return jsonify({
                "message": "Login successful",
                "username": username,
                "token": token
            }), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500

    # =========================
    # USER PROFILE API
    # =========================
    @app.route('/update_avatar', methods=['POST'])
    def update_avatar():
        data = request.json
        username = data.get('username')
        avatar_url = data.get('avatar_url')
        if not username: return jsonify({"message": "Missing username"}), 400
        
        users_collection.update_one(
            {"username": username},
            {"$set": {"avatar_url": avatar_url}}
        )
        return jsonify({"message": "Avatar updated"}), 200

    @app.route('/user/<username>', methods=['GET'])
    def get_user(username):
        user = users_collection.find_one({"username": username})
        default_avatar = f"https://api.dicebear.com/9.x/adventurer/png?seed={username}"
        if user:
            return jsonify({
                "username": user["username"],
                "avatar_url": user.get("avatar_url") or default_avatar
            }), 200
            
        # Return default for users not in DB (like AI Assistant)
        return jsonify({
            "username": username,
            "avatar_url": default_avatar
        }), 200
