from datetime import datetime
from bson import ObjectId
from extensions import mongo

class Media:
    """Media model for MediaCloud application"""
    
    def __init__(self, ownerId=None, type=None, title=None, originalFilename=None, 
                 blob=None, sizeBytes=None, status='active', isFavorite=False, isDeleted=False, _id=None):
        self._id = _id or ObjectId()
        self.ownerId = ObjectId(ownerId) if isinstance(ownerId, str) else ownerId
        self.type = type  # 'photo', 'video', or 'audio'
        self.title = title
        self.originalFilename = originalFilename
        self.blob = blob or {}  # {containerName, blobName, url}
        self.sizeBytes = sizeBytes or 0  # File size in bytes for quota tracking
        self.status = status  # 'active', 'trashed', 'deleted_permanent'
        self.isFavorite = isFavorite
        self.isDeleted = isDeleted  # Deprecated: use status instead
        self.createdAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
        self.trashedAt = None  # When item was moved to trash
    
    def to_dict(self):
        """Convert media object to dictionary"""
        return {
            '_id': self._id,
            'ownerId': self.ownerId,
            'type': self.type,
            'title': self.title,
            'originalFilename': self.originalFilename,
            'blob': self.blob,
            'sizeBytes': self.sizeBytes,
            'status': self.status,
            'isFavorite': self.isFavorite,
            'isDeleted': self.isDeleted,  # Keep for backward compatibility
            'createdAt': self.createdAt,
            'updatedAt': self.updatedAt,
            'trashedAt': self.trashedAt
        }
    
    def to_public_dict(self):
        """Convert media object to public dictionary"""
        return {
            'id': str(self._id),
            'type': self.type,
            'title': self.title,
            'blob': self.blob,
            'sizeBytes': self.sizeBytes,
            'status': self.status,
            'isFavorite': self.isFavorite,
            'isDeleted': self.status == 'trashed',  # Map status to isDeleted for backward compatibility
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'trashedAt': self.trashedAt.isoformat() if self.trashedAt else None
        }
    
    @staticmethod
    def validate_media_data(type, title, originalFilename):
        """Validate media data"""
        errors = []
        
        if not type or type not in ['photo', 'video', 'audio']:
            errors.append("Valid media type is required (photo, video, or audio)")
        
        if not title or not title.strip():
            errors.append("Title is required")
        
        if not originalFilename or not originalFilename.strip():
            errors.append("Original filename is required")
        
        return len(errors) == 0, errors
    
    def save(self):
        """Save media to database"""
        try:
            self.updatedAt = datetime.utcnow()
            result = mongo.db.media.insert_one(self.to_dict())
            self._id = result.inserted_id
            return True
        except Exception as e:
            raise e
    
    def update(self, **kwargs):
        """Update media fields"""
        try:
            update_data = {}
            
            # Update allowed fields
            allowed_fields = ['isFavorite', 'isDeleted', 'title', 'status']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(self, field, value)
                    update_data[field] = value
            
            # Handle status transitions
            if 'status' in kwargs:
                new_status = kwargs['status']
                if new_status == 'trashed' and self.status != 'trashed':
                    update_data['trashedAt'] = datetime.utcnow()
                    self.trashedAt = update_data['trashedAt']
                elif new_status == 'active' and self.status == 'trashed':
                    update_data['trashedAt'] = None
                    self.trashedAt = None
            
            # Backward compatibility: sync isDeleted with status
            if 'isDeleted' in kwargs:
                if kwargs['isDeleted'] and self.status != 'trashed':
                    update_data['status'] = 'trashed'
                    update_data['trashedAt'] = datetime.utcnow()
                    self.status = 'trashed'
                    self.trashedAt = update_data['trashedAt']
                elif not kwargs['isDeleted'] and self.status == 'trashed':
                    update_data['status'] = 'active'
                    update_data['trashedAt'] = None
                    self.status = 'active'
                    self.trashedAt = None
            
            if update_data:
                update_data['updatedAt'] = datetime.utcnow()
                self.updatedAt = update_data['updatedAt']
                
                mongo.db.media.update_one(
                    {'_id': self._id},
                    {'$set': update_data}
                )
            
            return True
        except Exception as e:
            raise e
    
    def delete(self):
        """Permanently delete media from database"""
        try:
            mongo.db.media.delete_one({'_id': self._id})
            return True
        except Exception as e:
            raise e
    
    def delete_permanently_with_storage_update(self):
        """Permanently delete media and update user storage usage"""
        try:
            from models.user import User
            
            # Get user to update storage
            user = User.find_by_id(self.ownerId)
            if not user:
                raise ValueError("User not found")
            
            # Only decrease storage if item was counting toward quota
            storage_delta = 0
            if self.status in ['active', 'trashed']:  # Model 1: both count toward quota
                storage_delta = -self.sizeBytes
            
            # Delete media record
            self.delete()
            
            # Update user storage if needed
            if storage_delta != 0:
                user.update_storage_usage(storage_delta)
            
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def find_by_id(media_id, owner_id=None):
        """Find media by ID, optionally filtered by owner"""
        try:
            if isinstance(media_id, str):
                media_id = ObjectId(media_id)
            
            query = {'_id': media_id}
            if owner_id:
                query['ownerId'] = ObjectId(owner_id) if isinstance(owner_id, str) else owner_id
            
            media_data = mongo.db.media.find_one(query)
            if not media_data:
                return None
            
            return Media._from_dict(media_data)
            
        except Exception:
            return None
    
    @staticmethod
    def find_by_owner(owner_id, type=None, favorites=None, trash=None, limit=None, skip=None):
        """Find media by owner with optional filters"""
        try:
            if isinstance(owner_id, str):
                owner_id = ObjectId(owner_id)
            
            query = {'ownerId': owner_id}
            
            # Apply filters
            if type:
                query['type'] = type
            
            if favorites is True:
                query['isFavorite'] = True
            
            if trash is True:
                query['isDeleted'] = True
            elif trash is False or trash is None:
                query['isDeleted'] = {'$ne': True}
            
            # Execute query with sorting
            cursor = mongo.db.media.find(query).sort('createdAt', -1)
            
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            media_list = []
            for media_data in cursor:
                media_list.append(Media._from_dict(media_data))
            
            return media_list
            
        except Exception as e:
            raise e
    
    @staticmethod
    def _from_dict(data):
        """Create Media object from dictionary"""
        media = Media(
            ownerId=data['ownerId'],
            type=data['type'],
            title=data['title'],
            originalFilename=data['originalFilename'],
            blob=data.get('blob', {}),
            sizeBytes=data.get('sizeBytes', 0),
            status=data.get('status', 'active'),
            isFavorite=data.get('isFavorite', False),
            isDeleted=data.get('isDeleted', False),
            _id=data['_id']
        )
        media.createdAt = data.get('createdAt', datetime.utcnow())
        media.updatedAt = data.get('updatedAt', datetime.utcnow())
        media.trashedAt = data.get('trashedAt')
        
        # Handle backward compatibility: if status not set but isDeleted is True
        if not data.get('status') and data.get('isDeleted'):
            media.status = 'trashed'
        
        return media
    
    @staticmethod
    def count_by_owner(owner_id, type=None, favorites=None, trash=None):
        """Count media by owner with optional filters"""
        try:
            if isinstance(owner_id, str):
                owner_id = ObjectId(owner_id)
            
            query = {'ownerId': owner_id}
            
            # Apply filters
            if type:
                query['type'] = type
            
            if favorites is True:
                query['isFavorite'] = True
            
            if trash is True:
                query['isDeleted'] = True
            elif trash is False or trash is None:
                query['isDeleted'] = {'$ne': True}
            
            return mongo.db.media.count_documents(query)
            
        except Exception as e:
            raise e