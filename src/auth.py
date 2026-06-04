from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        
        if not email or '@' not in email:
            return jsonify({"error": "Invalid email"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 409
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return jsonify({
            "message": "User created successfully",
            "user": user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid username or password"}), 401
        
        login_user(user)
        return jsonify({
            "message": "Logged in successfully",
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify(current_user.to_dict()), 200


@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_user():
    """Update user profile"""
    try:
        data = request.json
        
        if 'email' in data:
            new_email = data['email'].strip()
            if '@' not in new_email:
                return jsonify({"error": "Invalid email"}), 400
            if User.query.filter_by(email=new_email).filter(User.id != current_user.id).first():
                return jsonify({"error": "Email already in use"}), 409
            current_user.email = new_email
        
        if 'password' in data:
            password = data['password']
            if len(password) < 6:
                return jsonify({"error": "Password must be at least 6 characters"}), 400
            current_user.set_password(password)
        
        db.session.commit()
        return jsonify({
            "message": "User updated successfully",
            "user": current_user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
