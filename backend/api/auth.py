# -*- coding: utf-8 -*-
"""
认证接口
受 GPL v3.0 保护

登录/登出/刷新token。
JWT + 角色权限。
"""

from flask import Blueprint, request, jsonify
from engines.auth import AuthEngine
from config import config

auth_bp = Blueprint('auth', __name__)

# 全局认证引擎
auth_engine = AuthEngine(config)

# JWT 简化实现（真实项目使用 PyJWT）
_active_tokens = {}


def _make_token(user_id: str, role: str) -> str:
    """生成token（简化）"""
    import hashlib
    import time
    raw = f'{user_id}:{role}:{time.time()}'
    token = hashlib.md5(raw.encode()).hexdigest()
    _active_tokens[token] = {'user_id': user_id, 'role': role}
    return token


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """登录"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名或密码不能为空'}), 400

    # 简化认证：演示账号
    demo_users = {
        'worker': {'role': '施工员', 'name': '张三'},
        'owner': {'role': '甲方', 'name': '李总'},
        'supervisor': {'role': '监理', 'name': '王监理'},
        'cost': {'role': '造价员', 'name': '赵造价'},
        'admin': {'role': '管理员', 'name': '管理员'},
    }
    user = demo_users.get(username)
    if not user or password != '123456':
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    token = _make_token(username, user['role'])
    return jsonify({
        'success': True,
        'token': token,
        'user': {'user_id': username, 'role': user['role'], 'name': user['name']},
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """登出"""
    data = request.get_json() or {}
    token = data.get('token', '')
    if token in _active_tokens:
        del _active_tokens[token]
    return jsonify({'success': True})


@auth_bp.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """刷新token"""
    data = request.get_json() or {}
    token = data.get('token', '')
    info = _active_tokens.get(token)
    if not info:
        return jsonify({'success': False, 'message': 'Token无效'}), 401
    new_token = _make_token(info['user_id'], info['role'])
    return jsonify({'success': True, 'token': new_token})


@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    """当前用户"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    info = _active_tokens.get(token)
    if not info:
        return jsonify({'success': False, 'message': '未登录'}), 401
    return jsonify({'success': True, 'user': info})


@auth_bp.route('/api/auth/roles', methods=['GET'])
def list_roles():
    """角色列表"""
    roles = list(AuthEngine.PERMISSION_MATRIX.keys())
    return jsonify({'success': True, 'roles': roles})


@auth_bp.route('/api/auth/permissions/<role>', methods=['GET'])
def get_permissions(role):
    """角色权限"""
    perms = auth_engine.get_role_permissions(role)
    return jsonify({'success': True, 'permissions': perms})