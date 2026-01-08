from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
import logging

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()

def init_extensions(app):
    """Initialize Flask extensions with the app"""
    try:
        # Initialize MongoDB
        mongo.init_app(app)
        
        # Initialize JWT Manager
        jwt.init_app(app)
        
        # Test MongoDB connection
        with app.app_context():
            mongo.db.command('ping')
            app.logger.info("MongoDB connection successful")
            
        return True
        
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {str(e)}")
        return False

def setup_database_indexes(app):
    """Set up database indexes for optimal performance"""
    try:
        with app.app_context():
            db = mongo.db
            
            # Users collection indexes
            db.users.create_index("email", unique=True)
            app.logger.info("Created unique index on users.email")
            
            # Media collection indexes
            db.media.create_index([("ownerId", 1), ("createdAt", -1)])
            db.media.create_index([("ownerId", 1), ("type", 1), ("createdAt", -1)])
            db.media.create_index([("ownerId", 1), ("isFavorite", 1)])
            db.media.create_index([("ownerId", 1), ("isDeleted", 1)])
            app.logger.info("Created indexes on media collection")
            
        return True
        
    except Exception as e:
        app.logger.error(f"Failed to create database indexes: {str(e)}")
        return False