"""
Property-based tests for file upload storage structure
**Feature: mediacloud-mvp, Property 6: File upload creates proper storage structure**
"""

import pytest
from hypothesis import given, strategies as st, settings
from models.user import User
from models.media import Media
from services.blob_service import BlobStorageService
from utils.security import hash_password, get_file_type
from extensions import mongo
import io
import uuid

# Test data generators
@st.composite
def valid_file_data(draw):
    """Generate valid file upload data"""
    import time
    import random
    
    # Generate file content
    file_size = draw(st.integers(min_value=100, max_value=10000))  # 100 bytes to 10KB for testing
    file_content = draw(st.binary(min_size=file_size, max_size=file_size))
    
    # Generate filename with valid extension
    filename_base = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    extension = draw(st.sampled_from(['jpg', 'png', 'mp4', 'mp3', 'pdf', 'txt']))
    filename = f"{filename_base}.{extension}"
    
    # Generate title
    title = draw(st.text(min_size=1, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyz ').filter(lambda x: x.strip()))
    
    return {
        'content': file_content,
        'filename': filename,
        'title': title,
        'size': file_size
    }

@st.composite
def valid_user_data(draw):
    """Generate valid user data"""
    import time
    import random
    
    first_name = draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz').filter(lambda x: x.strip()))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz').filter(lambda x: x.strip()))
    
    # Generate unique email
    username = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    domain = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))
    timestamp = str(int(time.time() * 1000000))
    random_suffix = str(random.randint(1000, 9999))
    email = f"{username}{timestamp}{random_suffix}@{domain}.com"
    
    return {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': 'password123'
    }

class TestFileUploadStorage:
    """Property-based tests for file upload storage structure"""
    
    def setup_method(self):
        """Set up test database"""
        try:
            mongo.db.users.delete_many({})
            mongo.db.media.delete_many({})
        except Exception:
            pass
    
    @given(user_data=valid_user_data(), file_data=valid_file_data())
    @settings(max_examples=5, deadline=None)
    def test_file_upload_creates_proper_storage_structure(self, user_data, file_data):
        """
        **Feature: mediacloud-mvp, Property 6: File upload creates proper storage structure**
        
        For any uploaded file, the system should store it in Azure Blob Storage with a 
        user-specific container name and UUID-based blob name, while creating corresponding 
        metadata in MongoDB
        """
        # Arrange - Create user
        password_hash = hash_password(user_data['password'])
        user = User(
            firstName=user_data['firstName'],
            lastName=user_data['lastName'],
            email=user_data['email'],
            passwordHash=password_hash
        )
        user.save()
        
        # Arrange - Prepare file data
        file_content = file_data['content']
        filename = file_data['filename']
        title = file_data['title']
        
        # Determine file type
        file_type = get_file_type(filename)
        if not file_type:
            file_type = 'photo'  # Default for testing
        
        # Act - Simulate file upload process
        # 1. Test blob storage naming conventions
        blob_service = BlobStorageService()
        
        # Test container name generation
        container_name = blob_service.get_user_container_name(user._id)
        expected_container_pattern = f"user-{str(user._id).lower()}"
        assert container_name == expected_container_pattern, "Container name should follow user-{userId} pattern"
        
        # Test blob name generation
        blob_name = blob_service.generate_blob_name(filename)
        assert blob_name != filename, "Blob name should be different from original filename"
        assert '.' in blob_name, "Blob name should preserve file extension"
        
        # Verify UUID format in blob name
        blob_name_without_ext = blob_name.rsplit('.', 1)[0]
        try:
            uuid.UUID(blob_name_without_ext)
            uuid_valid = True
        except ValueError:
            uuid_valid = False
        assert uuid_valid, "Blob name should start with valid UUID"
        
        # Test extension preservation
        original_ext = filename.split('.')[-1].lower()
        blob_ext = blob_name.split('.')[-1].lower()
        assert blob_ext == original_ext, "File extension should be preserved in blob name"
        
        # 2. Test media metadata creation
        media = Media(
            ownerId=user._id,
            type=file_type,
            title=title,
            originalFilename=filename,
            blob={
                'containerName': container_name,
                'blobName': blob_name,
                'url': f"https://example.blob.core.windows.net/{container_name}/{blob_name}"
            }
        )
        
        # Save media metadata
        media.save()
        
        # Assert - Verify storage structure
        # 1. Verify media was saved to MongoDB
        saved_media = Media.find_by_id(media._id, user._id)
        assert saved_media is not None, "Media metadata should be saved to MongoDB"
        assert saved_media.ownerId == user._id, "Media should be associated with correct user"
        assert saved_media.type == file_type, "Media type should be correctly determined"
        assert saved_media.title == title, "Media title should be preserved"
        assert saved_media.originalFilename == filename, "Original filename should be preserved"
        
        # 2. Verify blob information structure
        blob_info = saved_media.blob
        assert 'containerName' in blob_info, "Blob info should contain container name"
        assert 'blobName' in blob_info, "Blob info should contain blob name"
        assert 'url' in blob_info, "Blob info should contain URL"
        
        assert blob_info['containerName'] == container_name, "Container name should match expected pattern"
        assert blob_info['blobName'] == blob_name, "Blob name should be UUID-based"
        assert container_name in blob_info['url'], "URL should contain container name"
        assert blob_name in blob_info['url'], "URL should contain blob name"
        
        # 3. Verify user isolation (different users get different containers)
        different_user_id = str(uuid.uuid4())
        different_container = blob_service.get_user_container_name(different_user_id)
        assert different_container != container_name, "Different users should get different containers"
        assert different_container == f"user-{different_user_id.lower()}", "Container naming should be consistent"
    
    def test_blob_service_utilities(self):
        """Test blob service utility functions"""
        blob_service = BlobStorageService()
        
        # Test container name generation
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        container_name = blob_service.get_user_container_name(user_id)
        assert container_name == "user-123e4567-e89b-12d3-a456-426614174000", "Container name should be lowercase"
        
        # Test blob name generation uniqueness
        filename = "test.jpg"
        blob_name1 = blob_service.generate_blob_name(filename)
        blob_name2 = blob_service.generate_blob_name(filename)
        
        assert blob_name1 != blob_name2, "Generated blob names should be unique"
        assert blob_name1.endswith('.jpg'), "Extension should be preserved"
        assert blob_name2.endswith('.jpg'), "Extension should be preserved"
        
        # Test with different extensions
        test_files = ["document.pdf", "image.PNG", "video.MP4", "audio.mp3"]
        for test_file in test_files:
            blob_name = blob_service.generate_blob_name(test_file)
            original_ext = test_file.split('.')[-1].lower()
            blob_ext = blob_name.split('.')[-1].lower()
            assert blob_ext == original_ext, f"Extension should be preserved and lowercase for {test_file}"
    
    def test_file_type_detection(self):
        """Test file type detection utility"""
        # Test photo types
        photo_files = ["image.jpg", "photo.jpeg", "pic.png", "graphic.gif", "bitmap.bmp"]
        for filename in photo_files:
            file_type = get_file_type(filename)
            assert file_type == "photo", f"File {filename} should be detected as photo"
        
        # Test video types
        video_files = ["movie.mp4", "clip.avi", "video.mov", "film.wmv"]
        for filename in video_files:
            file_type = get_file_type(filename)
            assert file_type == "video", f"File {filename} should be detected as video"
        
        # Test audio types
        audio_files = ["song.mp3", "audio.wav", "music.flac", "sound.aac"]
        for filename in audio_files:
            file_type = get_file_type(filename)
            assert file_type == "audio", f"File {filename} should be detected as audio"
        
        # Test unsupported types
        unsupported_files = ["document.txt", "data.csv", "unknown.xyz"]
        for filename in unsupported_files:
            file_type = get_file_type(filename)
            assert file_type is None, f"File {filename} should not be supported"
    
    def test_media_model_validation(self):
        """Test media model validation"""
        # Test valid media data
        is_valid, errors = Media.validate_media_data("photo", "My Photo", "image.jpg")
        assert is_valid, "Valid media data should pass validation"
        assert len(errors) == 0, "Valid data should have no errors"
        
        # Test invalid media data
        is_valid, errors = Media.validate_media_data("invalid", "", "")
        assert not is_valid, "Invalid media data should fail validation"
        assert len(errors) > 0, "Invalid data should have errors"
        
        # Test specific validation cases
        is_valid, errors = Media.validate_media_data("photo", "Valid Title", "image.jpg")
        assert is_valid, "Photo with valid data should pass"
        
        is_valid, errors = Media.validate_media_data("unknown", "Title", "file.jpg")
        assert not is_valid, "Unknown media type should fail validation"