"""
Storage service for managing user storage quotas and usage tracking.
Implements Google Photos-style storage management with atomic operations.
"""

from datetime import datetime
from models.user import User
from models.media import Media
from extensions import mongo
import logging

class StorageService:
    """Service for managing user storage quotas and usage"""
    
    @staticmethod
    def check_upload_quota(user_id, file_size_bytes):
        """
        Check if user has enough quota for upload.
        Returns (can_upload: bool, user: User, error_message: str)
        """
        try:
            user = User.find_by_id(user_id)
            if not user:
                return False, None, "User not found"
            
            if not user.check_storage_quota(file_size_bytes):
                used_gb = user.usedBytes / (1024 * 1024 * 1024)
                quota_gb = user.planQuotaBytes / (1024 * 1024 * 1024)
                return False, user, f"Storage quota exceeded. Using {used_gb:.1f} GB of {quota_gb:.1f} GB"
            
            return True, user, None
            
        except Exception as e:
            logging.error(f"Storage quota check error: {str(e)}")
            return False, None, "Storage check failed"
    
    @staticmethod
    def commit_upload(user, media_item, file_size_bytes):
        """
        Atomically commit an upload by updating both media record and user storage.
        This prevents double-counting and ensures consistency.
        """
        try:
            # Set the file size in media record
            media_item.sizeBytes = file_size_bytes
            media_item.status = 'active'
            
            # Save media record
            media_item.save()
            
            # Update user storage usage
            user.update_storage_usage(file_size_bytes)
            
            return True, media_item
            
        except Exception as e:
            logging.error(f"Upload commit error: {str(e)}")
            # If media was saved but storage update failed, we need to clean up
            try:
                if hasattr(media_item, '_id'):
                    media_item.delete()
            except:
                pass
            raise e
    
    @staticmethod
    def move_to_trash(media_id, user_id):
        """
        Move media to trash. In Model 1, storage usage doesn't change.
        """
        try:
            media = Media.find_by_id(media_id, user_id)
            if not media:
                return False, "Media not found"
            
            if media.status == 'trashed':
                return True, "Already in trash"
            
            # Update status to trashed (no storage change in Model 1)
            media.update(status='trashed')
            
            return True, "Moved to trash"
            
        except Exception as e:
            logging.error(f"Move to trash error: {str(e)}")
            return False, "Failed to move to trash"
    
    @staticmethod
    def restore_from_trash(media_id, user_id):
        """
        Restore media from trash. In Model 1, storage usage doesn't change.
        """
        try:
            media = Media.find_by_id(media_id, user_id)
            if not media:
                return False, "Media not found"
            
            if media.status != 'trashed':
                return True, "Not in trash"
            
            # Update status to active (no storage change in Model 1)
            media.update(status='active')
            
            return True, "Restored from trash"
            
        except Exception as e:
            logging.error(f"Restore from trash error: {str(e)}")
            return False, "Failed to restore from trash"
    
    @staticmethod
    def delete_permanently(media_id, user_id):
        """
        Permanently delete media and update storage usage.
        This is the only operation that decreases storage in Model 1.
        """
        try:
            media = Media.find_by_id(media_id, user_id)
            if not media:
                return False, "Media not found"
            
            # Delete with storage update
            media.delete_permanently_with_storage_update()
            
            return True, "Permanently deleted"
            
        except Exception as e:
            logging.error(f"Permanent delete error: {str(e)}")
            return False, "Failed to delete permanently"
    
    @staticmethod
    def get_storage_summary(user_id):
        """Get user's current storage summary"""
        try:
            user = User.find_by_id(user_id)
            if not user:
                return None
            
            return user.get_storage_summary()
            
        except Exception as e:
            logging.error(f"Storage summary error: {str(e)}")
            return None
    
    @staticmethod
    def reconcile_user_storage(user_id):
        """
        Reconcile user's storage usage by recalculating from media records.
        This is the self-healing mechanism.
        """
        try:
            success, actual_bytes = User.recalculate_storage_usage(user_id)
            if success:
                logging.info(f"Storage reconciled for user {user_id}: {actual_bytes} bytes")
                return True, actual_bytes
            else:
                logging.error(f"Storage reconciliation failed for user {user_id}")
                return False, 0
                
        except Exception as e:
            logging.error(f"Storage reconciliation error: {str(e)}")
            return False, 0
    
    @staticmethod
    def format_bytes_for_display(bytes_value):
        """Format bytes for human-readable display"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def get_plan_display_name(quota_bytes):
        """Get display name for storage plan"""
        gb = quota_bytes / (1024 * 1024 * 1024)
        if gb <= 5:
            return "Free Plan"
        elif gb <= 100:
            return "Pro Plan"
        else:
            return "Enterprise Plan"