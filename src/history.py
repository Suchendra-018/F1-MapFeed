from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Analysis, Favorite
from datetime import datetime
import json

history_bp = Blueprint('history', __name__, url_prefix='/api/history')


@history_bp.route('/analyses', methods=['GET'])
@login_required
def get_analyses():
    """Get user's saved analyses"""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(
            Analysis.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            "analyses": [a.to_dict() for a in analyses.items],
            "total": analyses.total,
            "pages": analyses.pages,
            "current_page": page
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route('/analyses', methods=['POST'])
@login_required
def save_analysis():
    """Save an analysis"""
    try:
        data = request.json
        
        required = ['year', 'race', 'session_type', 'analysis_type', 'drivers']
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        analysis = Analysis(
            user_id=current_user.id,
            year=data['year'],
            race=data['race'],
            session_type=data['session_type'],
            analysis_type=data['analysis_type'],
            drivers=','.join(data['drivers']) if isinstance(data['drivers'], list) else data['drivers'],
            results=json.dumps(data.get('results', {})),
            notes=data.get('notes', '')
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            "message": "Analysis saved",
            "analysis": analysis.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@history_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id):
    """Get a specific analysis"""
    try:
        analysis = Analysis.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404
        
        result = analysis.to_dict()
        result['results'] = json.loads(analysis.results) if analysis.results else {}
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route('/analyses/<int:analysis_id>', methods=['PUT'])
@login_required
def update_analysis(analysis_id):
    """Update analysis notes"""
    try:
        analysis = Analysis.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404
        
        data = request.json
        if 'notes' in data:
            analysis.notes = data['notes']
        
        db.session.commit()
        return jsonify({
            "message": "Analysis updated",
            "analysis": analysis.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@history_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis(analysis_id):
    """Delete an analysis"""
    try:
        analysis = Analysis.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404
        
        db.session.delete(analysis)
        db.session.commit()
        
        return jsonify({"message": "Analysis deleted"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ====== FAVORITES ======

@history_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    """Get user's favorites"""
    try:
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        return jsonify([f.to_dict() for f in favorites]), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route('/favorites', methods=['POST'])
@login_required
def add_favorite():
    """Add to favorites"""
    try:
        data = request.json
        
        if not data.get('favorite_type') or not data.get('drivers') or not data.get('label'):
            return jsonify({"error": "Missing required fields"}), 400
        
        favorite = Favorite(
            user_id=current_user.id,
            favorite_type=data['favorite_type'],
            drivers=','.join(data['drivers']) if isinstance(data['drivers'], list) else data['drivers'],
            label=data['label']
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            "message": "Added to favorites",
            "favorite": favorite.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@history_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def remove_favorite(favorite_id):
    """Remove from favorites"""
    try:
        favorite = Favorite.query.filter_by(
            id=favorite_id,
            user_id=current_user.id
        ).first()
        
        if not favorite:
            return jsonify({"error": "Favorite not found"}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({"message": "Removed from favorites"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
