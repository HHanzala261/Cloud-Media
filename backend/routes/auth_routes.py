from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models.user import User
from utils.security import hash_password, verify_password, generate_jwt_token
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input data
        is_valid, errors = User.validate_user_data(first_name, last_name, email, password)
        if not is_valid:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Check if email already exists
        if User.email_exists(email):
            return jsonify({'error': 'Email address already exists'}), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            firstName=first_name,
            lastName=last_name,
            email=email,
            passwordHash=password_hash
        )
        
        # Save user to database
        user.save()
        
        # Generate JWT token
        access_token = generate_jwt_token(user._id)
        
        # Return success response
        return jsonify({
            'accessToken': access_token,
            'user': user.to_public_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with email and password"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.find_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not verify_password(password, user.passwordHash):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        access_token = generate_jwt_token(user._id)
        
        # Return success response
        return jsonify({
            'accessToken': access_token,
            'user': user.to_public_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Find user by ID
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Return user information
        return jsonify({
            'user': user.to_public_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Get current user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# JWT error handlers
@auth_bp.errorhandler(422)
def handle_unprocessable_entity(e):
    """Handle JWT validation errors"""
    return jsonify({'error': 'Invalid token'}), 401

@auth_bp.errorhandler(401)
def handle_unauthorized(e):
    """Handle unauthorized access"""
    return jsonify({'error': 'Authentication required'}), 401