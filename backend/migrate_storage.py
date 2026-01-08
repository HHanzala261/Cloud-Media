#!/usr/bin/env python3
"""
Migration script to add storage tracking to existing MediaCloud users and media.
Run this once to update existing data with the new storage fields.
"""

import os
import sys
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import mongo
from config import Config
from flask import Flask

def create_app():
    """Create minimal Flask app for database access"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize MongoDB
    mongo.init_app(app)
    
    return app

def migrate_users():
    """Add storage fields to existing users"""
    print("Migrating users...")
    
    # Default to 5GB free plan
    default_quota = 5 * 1024 * 1024 * 1024  # 5GB in bytes
    
    # Update users without storage fields
    result = mongo.db.users.update_many(
        {
            '$or': [
                {'planQuotaBytes': {'$exists': False}},
                {'usedBytes': {'$exists': False}},
                {'storageUpdatedAt': {'$exists': False}}
            ]
        },
        {
            '$set': {
                'planQuotaBytes': default_quota,
                'usedBytes': 0,
                'storageUpdatedAt': datetime.utcnow()
            }
        }
    )
    
    print(f"Updated {result.modified_count} users with storage fields")
    return result.modified_count

def migrate_media():
    """Add storage fields to existing media"""
    print("Migrating media...")
    
    # Update media without storage fields
    result = mongo.db.media.update_many(
        {
            '$or': [
                {'sizeBytes': {'$exists': False}},
                {'status': {'$exists': False}}
            ]
        },
        {
            '$set': {
                'sizeBytes': 0,  # Will need manual update for actual file sizes
                'status': 'active',
                'trashedAt': None
            }
        }
    )
    
    print(f"Updated {result.modified_count} media items with storage fields")
    
    # Handle backward compatibility: set status based on isDeleted
    trash_result = mongo.db.media.update_many(
        {
            'isDeleted': True,
            'status': 'active'
        },
        {
            '$set': {
                'status': 'trashed',
                'trashedAt': datetime.utcnow()
            }
        }
    )
    
    print(f"Updated {trash_result.modified_count} media items from isDeleted=true to status=trashed")
    
    return result.modified_count + trash_result.modified_count

def recalculate_storage_usage():
    """Recalculate storage usage for all users based on media records"""
    print("Recalculating storage usage...")
    
    # Get all users
    users = mongo.db.users.find({}, {'_id': 1})
    updated_count = 0
    
    for user_doc in users:
        user_id = user_doc['_id']
        
        # Calculate actual usage from active and trashed media (Model 1: trash counts)
        pipeline = [
            {
                '$match': {
                    'ownerId': user_id,
                    'status': {'$in': ['active', 'trashed']}
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
        mongo.db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'usedBytes': actual_used_bytes,
                    'storageUpdatedAt': datetime.utcnow()
                }
            }
        )
        
        updated_count += 1
        print(f"User {user_id}: {actual_used_bytes} bytes")
    
    print(f"Recalculated storage for {updated_count} users")
    return updated_count

def main():
    """Run the migration"""
    print("Starting MediaCloud storage migration...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            mongo.db.command('ping')
            print("✓ Database connection successful")
            
            # Run migrations
            user_count = migrate_users()
            media_count = migrate_media()
            storage_count = recalculate_storage_usage()
            
            print("=" * 50)
            print("Migration completed successfully!")
            print(f"✓ Users updated: {user_count}")
            print(f"✓ Media items updated: {media_count}")
            print(f"✓ Storage recalculated: {storage_count}")
            print("\nNOTE: Media file sizes are set to 0 bytes.")
            print("You may want to run a separate script to calculate actual file sizes.")
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()