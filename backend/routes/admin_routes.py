"""
Admin routes for MediaCloud application.
Includes storage reconciliation and maintenance endpoints.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from services.storage_service import StorageService
import logging

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/storage/reconcile/<user_id>', methods=['POST'])
@jwt_required()
def reconcile_user_storage(user_id):
    """
    Reconcile storage usage for a specific user.
    This recalculates usedBytes from actual media records.
    """
    try:
        # For MVP, any authenticated user can reconcile (in production, add admin check)
        current_user_id = get_jwt_identity()
        
        # Perform reconciliation
        success, actual_bytes = StorageService.reconcile_user_storage(user_id)
        
        if not success:
            return jsonify({'error': 'Reconciliation failed'}), 500
        
        # Get updated storage summary
        storage_summary = StorageService.get_storage_summary(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Storage reconciled: {actual_bytes} bytes',
            'actualBytes': actual_bytes,
            'storage': storage_summary
        }), 200
        
    except Exception as e:
        logging.error(f"Storage reconciliation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/storage/reconcile-all', methods=['POST'])
@jwt_required()
def reconcile_all_storage():
    """
    Reconcile storage usage for all users.
    This is a maintenance operation that should be run periodically.
    """
    try:
        # For MVP, any authenticated user can reconcile (in production, add admin check)
        current_user_id = get_jwt_identity()
        
        from extensions import mongo
        
        # Get all users
        users = mongo.db.users.find({}, {'_id': 1})
        
        results = []
        for user_doc in users:
            user_id = str(user_doc['_id'])
            try:
                success, actual_bytes = StorageService.reconcile_user_storage(user_id)
                results.append({
                    'userId': user_id,
                    'success': success,
                    'actualBytes': actual_bytes
                })
            except Exception as e:
                results.append({
                    'userId': user_id,
                    'success': False,
                    'error': str(e)
                })
        
        successful_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'message': f'Reconciled {successful_count} of {len(results)} users',
            'results': results
        }), 200
        
    except Exception as e:
        logging.error(f"Bulk storage reconciliation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/storage/stats', methods=['GET'])
@jwt_required()
def get_storage_stats():
    """Get overall storage statistics"""
    try:
        from extensions import mongo
        
        # Aggregate storage statistics
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'totalUsers': {'$sum': 1},
                    'totalUsedBytes': {'$sum': '$usedBytes'},
                    'totalQuotaBytes': {'$sum': '$planQuotaBytes'},
                    'avgUsedBytes': {'$avg': '$usedBytes'}
                }
            }
        ]
        
        result = list(mongo.db.users.aggregate(pipeline))
        stats = result[0] if result else {
            'totalUsers': 0,
            'totalUsedBytes': 0,
            'totalQuotaBytes': 0,
            'avgUsedBytes': 0
        }
        
        # Format for display
        stats['totalUsedDisplay'] = StorageService.format_bytes_for_display(stats['totalUsedBytes'])
        stats['totalQuotaDisplay'] = StorageService.format_bytes_for_display(stats['totalQuotaBytes'])
        stats['avgUsedDisplay'] = StorageService.format_bytes_for_display(stats['avgUsedBytes'])
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging.error(f"Storage stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500