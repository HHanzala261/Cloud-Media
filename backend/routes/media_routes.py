from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.media import Media
from models.user import User
from services.blob_service import get_blob_service
from services.storage_service import StorageService
from utils.security import get_file_type, validate_file_type
import logging
from werkzeug.utils import secure_filename

media_bp = Blueprint('media', __name__)

@media_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    """Upload media file with storage quota checking"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get title from form data
        title = request.form.get('title', '').strip()
        if not title:
            title = file.filename  # Use filename as default title
        
        # Validate file type
        is_valid, file_type_or_error = validate_file_type(file.filename)
        if not is_valid:
            return jsonify({'error': file_type_or_error}), 400
        
        file_type = file_type_or_error
        
        # Read file content
        file_content = file.read()
        if len(file_content) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Check file size (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        if len(file_content) > max_size:
            return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413
        
        file_size_bytes = len(file_content)
        
        # Check storage quota BEFORE uploading
        can_upload, user, quota_error = StorageService.check_upload_quota(user_id, file_size_bytes)
        if not can_upload:
            return jsonify({'error': quota_error or 'Storage quota exceeded'}), 413
        
        # Upload to blob storage
        blob_service = get_blob_service()
        if not blob_service.is_available():
            # For MVP, we'll create a mock blob info if Azure isn't configured
            import uuid
            container_name = blob_service.get_user_container_name(user_id)
            blob_name = blob_service.generate_blob_name(file.filename)
            blob_info = {
                'containerName': container_name,
                'blobName': blob_name,
                'url': f"https://mock-storage.example.com/{container_name}/{blob_name}"
            }
            logging.warning("Azure Blob Storage not configured - using mock blob info")
        else:
            # Upload to actual Azure Blob Storage
            success, blob_info = blob_service.upload_file(
                user_id=user_id,
                file_data=file_content,
                original_filename=file.filename,
                content_type=file.content_type
            )
            
            if not success:
                return jsonify({'error': 'Failed to upload file to storage'}), 500
        
        # Create media metadata (without saving yet)
        media = Media(
            ownerId=user_id,
            type=file_type,
            title=title,
            originalFilename=secure_filename(file.filename),
            blob=blob_info,
            sizeBytes=file_size_bytes,
            status='active'
        )
        
        # Atomically commit upload (save media + update storage)
        try:
            success, committed_media = StorageService.commit_upload(user, media, file_size_bytes)
            if not success:
                return jsonify({'error': 'Failed to commit upload'}), 500
        except Exception as e:
            logging.error(f"Upload commit failed: {str(e)}")
            return jsonify({'error': 'Upload failed - please try again'}), 500
        
        # Get updated storage summary
        storage_summary = StorageService.get_storage_summary(user_id)
        
        # Return success response with storage info
        response_data = committed_media.to_public_dict()
        response_data['storage'] = storage_summary
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('', methods=['GET'])
@jwt_required()
def get_media():
    """Get media list with optional filters"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        media_type = request.args.get('type')  # photo, video, audio
        favorites = request.args.get('favorites')  # true/false
        trash = request.args.get('trash')  # true/false
        limit = request.args.get('limit', type=int)
        skip = request.args.get('skip', type=int)
        
        # Convert string parameters to boolean
        favorites_bool = None
        if favorites is not None:
            favorites_bool = favorites.lower() == 'true'
        
        trash_bool = None
        if trash is not None:
            trash_bool = trash.lower() == 'true'
        
        # Validate media type
        if media_type and media_type not in ['photo', 'video', 'audio']:
            return jsonify({'error': 'Invalid media type. Must be photo, video, or audio'}), 400
        
        # Get media from database
        media_list = Media.find_by_owner(
            owner_id=user_id,
            type=media_type,
            favorites=favorites_bool,
            trash=trash_bool,
            limit=limit,
            skip=skip
        )
        
        # Convert to public format
        media_items = [media.to_public_dict() for media in media_list]
        
        return jsonify({'items': media_items}), 200
        
    except Exception as e:
        logging.error(f"Get media error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/storage', methods=['GET'])
@jwt_required()
def get_storage_summary():
    """Get user's storage usage summary"""
    try:
        user_id = get_jwt_identity()
        
        storage_summary = StorageService.get_storage_summary(user_id)
        if not storage_summary:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(storage_summary), 200
        
    except Exception as e:
        logging.error(f"Storage summary error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/<media_id>/favorite', methods=['PATCH'])
@jwt_required()
def toggle_favorite(media_id):
    """Toggle favorite status of media item"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data or 'isFavorite' not in data:
            return jsonify({'error': 'isFavorite field is required'}), 400
        
        is_favorite = data['isFavorite']
        if not isinstance(is_favorite, bool):
            return jsonify({'error': 'isFavorite must be a boolean'}), 400
        
        # Find media item
        media = Media.find_by_id(media_id, user_id)
        if not media:
            return jsonify({'error': 'Media not found'}), 404
        
        # Update favorite status
        media.update(isFavorite=is_favorite)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logging.error(f"Toggle favorite error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/<media_id>/trash', methods=['PATCH'])
@jwt_required()
def toggle_trash(media_id):
    """Move media item to/from trash"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data or 'isDeleted' not in data:
            return jsonify({'error': 'isDeleted field is required'}), 400
        
        is_deleted = data['isDeleted']
        if not isinstance(is_deleted, bool):
            return jsonify({'error': 'isDeleted must be a boolean'}), 400
        
        # Use storage service for trash operations
        if is_deleted:
            success, message = StorageService.move_to_trash(media_id, user_id)
        else:
            success, message = StorageService.restore_from_trash(media_id, user_id)
        
        if not success:
            return jsonify({'error': message}), 404 if 'not found' in message.lower() else 500
        
        # Get updated storage summary
        storage_summary = StorageService.get_storage_summary(user_id)
        
        return jsonify({
            'success': True, 
            'message': message,
            'storage': storage_summary
        }), 200
        
    except Exception as e:
        logging.error(f"Toggle trash error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/<media_id>', methods=['DELETE'])
@jwt_required()
def delete_media(media_id):
    """Permanently delete media item"""
    try:
        # Get current user
        user_id = get_jwt_identity()
        
        # Use storage service for permanent deletion
        success, message = StorageService.delete_permanently(media_id, user_id)
        
        if not success:
            return jsonify({'error': message}), 404 if 'not found' in message.lower() else 500
        
        # Get updated storage summary
        storage_summary = StorageService.get_storage_summary(user_id)
        
        return jsonify({
            'success': True,
            'message': message,
            'storage': storage_summary
        }), 200
        
    except Exception as e:
        logging.error(f"Delete media error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@media_bp.errorhandler(413)
def handle_file_too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413

@media_bp.errorhandler(422)
def handle_unprocessable_entity(e):
    """Handle JWT validation errors"""
    return jsonify({'error': 'Invalid token'}), 401