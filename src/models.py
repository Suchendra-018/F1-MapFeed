from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Analysis(db.Model):
    """Saved analysis/comparison record"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Session details
    year = db.Column(db.Integer, nullable=False)
    race = db.Column(db.String(120), nullable=False)
    session_type = db.Column(db.String(10), nullable=False)
    
    # Analysis type: 'single' or 'comparison'
    analysis_type = db.Column(db.String(20), nullable=False)
    
    # Driver(s) involved (comma-separated)
    drivers = db.Column(db.String(200), nullable=False)
    
    # Analysis results (JSON stored as text)
    results = db.Column(db.Text, nullable=True)
    
    # User notes
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'race': self.race,
            'session_type': self.session_type,
            'analysis_type': self.analysis_type,
            'drivers': self.drivers.split(','),
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Favorite(db.Model):
    """Saved favorite driver or comparison"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # What's being favorited
    favorite_type = db.Column(db.String(20), nullable=False)  # 'driver' or 'comparison'
    
    # For drivers: just the driver code
    # For comparisons: comma-separated driver codes
    drivers = db.Column(db.String(200), nullable=False)
    
    # Label for this favorite
    label = db.Column(db.String(120), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'favorite_type': self.favorite_type,
            'drivers': self.drivers.split(','),
            'label': self.label,
            'created_at': self.created_at.isoformat()
        }


class AnalysisCache(db.Model):
    """Cache for analysis results to avoid recalculation"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Cache key: hash of query params
    cache_key = db.Column(db.String(200), unique=True, nullable=False, index=True)
    
    # Analysis type
    analysis_type = db.Column(db.String(20), nullable=False)
    
    # Cached data (JSON)
    data = db.Column(db.Text, nullable=False)
    
    # Expiration
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    def is_valid(self):
        """Check if cache is still valid"""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        return {
            'cache_key': self.cache_key,
            'analysis_type': self.analysis_type,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }
