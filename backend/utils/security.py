import bcrypt
from flask_jwt_extended import create_access_token
import secrets

def hash_password(password):
    """Hash a password using bcrypt"""
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    if not password or not password_hash:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def generate_jwt_token(user_id):
    """Generate JWT access token for user"""
    if not user_id:
        raise ValueError("User ID is required")
    
    # Create token with user ID as identity
    access_token = create_access_token(identity=str(user_id))
    return access_token

def generate_secure_filename(original_filename):
    """Generate a secure filename with UUID"""
    import uuid
    import os
    
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate UUID-based filename
    secure_name = f"{uuid.uuid4()}{ext}"
    return secure_name

def validate_file_type(filename):
    """Validate if file type is allowed for media upload"""
    if not filename:
        return False, "No filename provided"
    
    # Get file extension
    _, ext = filename.rsplit('.', 1) if '.' in filename else ('', '')
    ext = ext.lower()
    
    # Define allowed extensions
    allowed_extensions = {
        'photo': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'],
        'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma']
    }
    
    # Check if extension is allowed
    for media_type, extensions in allowed_extensions.items():
        if ext in extensions:
            return True, media_type
    
    return False, f"File type '{ext}' is not supported"

def get_file_type(filename):
    """Get media type based on file extension"""
    is_valid, result = validate_file_type(filename)
    if is_valid:
        return result
    return None