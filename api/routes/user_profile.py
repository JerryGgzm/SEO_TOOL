from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from typing import Dict, Any
import jwt
from datetime import datetime, timedelta
import os

# Initialize Flask application (this part is usually in the main application file)
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

# Database session (should use dependency injection in actual applications)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.user_profile import UserProfileService, UserProfileRepository

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/ideation_db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_user_service() -> UserProfileService:
    """Get user service instance"""
    db_session = SessionLocal()
    repository = UserProfileRepository(db_session)
    return UserProfileService(repository)

def generate_jwt_token(user_id: str) -> str:
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def require_auth(f):
    """Authentication decorator"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_jwt_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401
        
        request.current_user_id = payload['user_id']
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# API route definitions

@app.route('/auth/register', methods=['POST'])
def register():
    """User registration"""
    try:
        from modules.user_profile.models import UserRegistrationRequest
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        # Validate input data
        try:
            user_data = UserRegistrationRequest(**data)
        except Exception as e:
            return jsonify({'error': f'Input data validation failed: {str(e)}'}), 400
        
        # Register user
        service = get_user_service()
        success, result = service.register_user(user_data)
        
        if success:
            # Generate JWT token
            token = generate_jwt_token(result)
            return jsonify({
                'message': 'Registration successful',
                'user_id': result,
                'token': token
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        from modules.user_profile.models import UserLoginRequest
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        # Validate input data
        try:
            login_data = UserLoginRequest(**data)
        except Exception as e:
            return jsonify({'error': f'Input data validation failed: {str(e)}'}), 400
        
        # User authentication
        service = get_user_service()
        user_id = service.authenticate_user(login_data)
        
        if user_id:
            # Generate JWT token
            token = generate_jwt_token(user_id)
            return jsonify({
                'message': 'Login successful',
                'user_id': user_id,
                'token': token
            }), 200
        else:
            return jsonify({'error': 'Incorrect email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
    try:
        service = get_user_service()
        user_profile = service.get_user_profile(request.current_user_id)
        
        if user_profile:
            return jsonify(user_profile.dict()), 200
        else:
            return jsonify({'error': 'User does not exist'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to get user information: {str(e)}'}), 500

@app.route('/profile/product', methods=['PUT'])
@require_auth  
def update_product_info():
    """Update product information"""
    try:
        from modules.user_profile.models import ProductInfoData
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        # Validate product information data
        try:
            product_info = ProductInfoData(**data)
        except Exception as e:
            return jsonify({'error': f'Product information validation failed: {str(e)}'}), 400
        
        # Update product information
        service = get_user_service()
        success = service.update_product_info(request.current_user_id, product_info)
        
        if success:
            return jsonify({'message': 'Product information updated successfully'}), 200
        else:
            return jsonify({'error': 'Product information update failed'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to update product information: {str(e)}'}), 500

@app.route('/profile/product', methods=['GET'])
@require_auth
def get_product_info():
    """Get product information"""
    try:
        service = get_user_service()
        product_info = service.get_product_info(request.current_user_id)
        
        if product_info:
            return jsonify(product_info.dict()), 200
        else:
            return jsonify({'error': 'Product information not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to get product information: {str(e)}'}), 500

@app.route('/twitter/auth_url', methods=['GET'])
@require_auth
def get_twitter_auth_url():
    """Get Twitter OAuth authorization URL"""
    try:
        service = get_user_service()
        auth_url, state = service.get_twitter_auth_url(request.current_user_id)
        
        return jsonify({
            'auth_url': auth_url,
            'state': state
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get Twitter authorization URL: {str(e)}'}), 500

@app.route('/twitter/callback', methods=['POST'])
def twitter_callback():
    """Handle Twitter OAuth callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        code = data.get('code')
        state = data.get('state')
        
        if not code or not state:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        service = get_user_service()
        success, message = service.handle_twitter_callback(code, state)
        
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to handle Twitter callback: {str(e)}'}), 500

@app.route('/twitter/status', methods=['GET'])
@require_auth
def get_twitter_status():
    """Get Twitter connection status"""
    try:
        service = get_user_service()
        access_token = service.get_twitter_access_token(request.current_user_id)
        
        return jsonify({
            'connected': access_token is not None,
            'has_valid_token': access_token is not None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get Twitter status: {str(e)}'}), 500