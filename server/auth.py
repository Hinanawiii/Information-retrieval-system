# server/auth.py

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, request

# JWT配置
JWT_SECRET = 'your-secret-key'  # 在生产环境中应使用更安全的密钥
JWT_EXPIRATION = timedelta(days=1)

# 预设用户数据
USERS = {
    'admin': {
        'password': '12345678',  # 在实际应用中应该使用加密的密码
        'role': 'admin'
    }
}

def generate_token(username):
    """生成JWT token"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def token_required(f):
    """验证token的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': '无效的token格式'}), 401

        if not token:
            return jsonify({'message': '缺少token'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = data['username']
            # 可以在这里添加额外的用户验证逻辑
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def verify_user(username, password):
    """验证用户名和密码"""
    if username not in USERS:
        return False
    return USERS[username]['password'] == password

def get_user_role(username):
    """获取用户角色"""
    return USERS[username]['role'] if username in USERS else None