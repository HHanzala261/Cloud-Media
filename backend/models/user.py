from datetime import datetime
from bson import ObjectId
from extensions import mongo
import re

class User:
    """User model for MediaCloud application"""
    
    def __init__(self, firstName=None, lastName=None, email=None, passwordHash=None, 
                 planQuotaBytes=None, usedBytes=None, _id=None):
        self._id = _id or ObjectId()
        self.firstName = firstName
        self.lastName = lastName
        self.email = email.lower() if email else None  # Always store email in lowercase
        self.passwordHash = passwordHash
        self.createdAt = datetime.utcnow()
        # Storage tracking - default to 5GB free plan
        self.planQuotaBytes = planQuotaBytes if planQuotaBytes is not None else 5 * 1024 * 1024 * 1024  # 5GB
        self.usedBytes = usedBytes if usedBytes is not None else 0
        self.storageUpdatedAt = datetime.utcnow()
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            '_id': self._id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'passwordHash': self.passwordHash,
            'createdAt': self.createdAt,
            'planQuotaBytes': self.planQuotaBytes,
            'usedBytes': self.usedBytes,
            'storageUpdatedAt': self.storageUpdatedAt
        }
    
    def to_public_dict(self):
        """Convert user object to public dictionary (without password hash)"""
        return {
            'id': str(self._id),
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'storage': {
                'usedBytes': self.usedBytes,
                'quotaBytes': self.planQuotaBytes,
                'updatedAt': self.storageUpdatedAt.isoformat() if self.storageUpdatedAt else None
            }
        }
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_user_data(firstName, lastName, email, password):
        """Validate all user registration data"""
        errors = []
        
        if not firstName or not firstName.strip():
            errors.append("First name is required")
        
        if not lastName or not lastName.strip():
            errors.append("Last name is required")
        
        if not User.validate_email(email):
            errors.append("Valid email is required")
        
        is_valid_password, password_message = User.validate_password(password)
        if not is_valid_password:
            errors.append(password_message)
        
        return len(errors) == 0, errors
    
    def save(self):
        """Save user to database"""
        try:
            result = mongo.db.users.insert_one(self.to_dict())
            self._id = result.inserted_id
            return True
        except Exception as e:
            # Handle duplicate email error
            if 'duplicate key error' in str(e).lower():
                raise ValueError("Email address already exists")
            raise e
    
    @staticmethod
    def find_by_email(email):
        """Find user by email address"""
        if not email:
            return None
        
        user_data = mongo.db.users.find_one({'email': email.lower()})
        if not user_data:
            return None
        
        user = User(
            firstName=user_data['firstName'],
            lastName=user_data['lastName'],
            email=user_data['email'],
            passwordHash=user_data['passwordHash'],
            _id=user_data['_id']
        )
        user.createdAt = user_data.get('createdAt', datetime.utcnow())
        # Load storage data with defaults for existing users
        user.planQuotaBytes = user_data.get('planQuotaBytes', 5 * 1024 * 1024 * 1024)  # 5GB default
        user.usedBytes = user_data.get('usedBytes', 0)
        user.storageUpdatedAt = user_data.get('storageUpdatedAt', datetime.utcnow())
        return user
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            user_data = mongo.db.users.find_one({'_id': user_id})
            if not user_data:
                return None
            
            user = User(
                firstName=user_data['firstName'],
                lastName=user_data['lastName'],
                email=user_data['email'],
                passwordHash=user_data['passwordHash'],
                _id=user_data['_id']
            )
            user.createdAt = user_data.get('createdAt', datetime.utcnow())
            # Load storage data with defaults for existing users
            user.planQuotaBytes = user_data.get('planQuotaBytes', 5 * 1024 * 1024 * 1024)  # 5GB default
            user.usedBytes = user_data.get('usedBytes', 0)
            user.storageUpdatedAt = user_data.get('storageUpdatedAt', datetime.utcnow())
            return user
            
        except Exception:
            return None
    
    @staticmethod
    def email_exists(email):
        """Check if email already exists in database"""
        if not email:
            return False
        
        return mongo.db.users.find_one({'email': email.lower()}) is not None
    
    def update_storage_usage(self, bytes_delta):
        """Update user's storage usage atomically"""
        try:
            from extensions import mongo
            
            # Atomic update to prevent race conditions
            result = mongo.db.users.update_one(
                {'_id': self._id},
                {
                    '$inc': {'usedBytes': bytes_delta},
                    '$set': {'storageUpdatedAt': datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                # Update local instance
                self.usedBytes += bytes_delta
                self.storageUpdatedAt = datetime.utcnow()
                return True
            return False
            
        except Exception as e:
            raise e
    
    def check_storage_quota(self, additional_bytes):
        """Check if user has enough storage quota for additional bytes"""
        return (self.usedBytes + additional_bytes) <= self.planQuotaBytes
    
    def get_storage_summary(self):
        """Get storage usage summary"""
        return {
            'usedBytes': self.usedBytes,
            'quotaBytes': self.planQuotaBytes,
            'availableBytes': max(0, self.planQuotaBytes - self.usedBytes),
            'usagePercentage': (self.usedBytes / self.planQuotaBytes * 100) if self.planQuotaBytes > 0 else 0,
            'updatedAt': self.storageUpdatedAt.isoformat() if self.storageUpdatedAt else None
        }
    
    @staticmethod
    def recalculate_storage_usage(user_id):
        """Recalculate user's storage usage from media records (reconciliation)"""
        try:
            from models.media import Media
            from extensions import mongo
            
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            # Calculate actual usage from active and trashed media (Model 1: trash counts)
            pipeline = [
                {
                    '$match': {
                        'ownerId': user_id,
                        'status': {'$in': ['active', 'trashed']}  # Both count toward quota
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'totalBytes': {'$sum': '$sizeBytes'}
                    }
                }
            ]
            
            result = list(mongo.db.media.aggregate(pipeline))
            actual_used_bytes = result[0]['totalBytes'] if result else 0
            
            # Update user's storage usage
            update_result = mongo.db.users.update_one(
                {'_id': user_id},
                {
                    '$set': {
                        'usedBytes': actual_used_bytes,
                        'storageUpdatedAt': datetime.utcnow()
                    }
                }
            )
            
            return update_result.modified_count > 0, actual_used_bytes
            
        except Exception as e:
            raise e