from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from extensions import mongo, jwt, init_extensions, setup_database_indexes
from routes.auth_routes import auth_bp
from routes.media_routes import media_bp
from routes.admin_routes import admin_bp
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        app.logger.error(f"Configuration error: {str(e)}")
        raise
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize extensions
    if not init_extensions(app):
        raise RuntimeError("Failed to initialize extensions")
    
    # Configure CORS for Angular dev server
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Set up database indexes
    setup_database_indexes(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(media_bp, url_prefix='/api/media')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            # Test database connection
            mongo.db.command('ping')
            return jsonify({
                'ok': True,
                'status': 'healthy',
                'database': 'connected'
            })
        except Exception as e:
            return jsonify({
                'ok': False,
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)