# -*- coding: utf-8 -*-
"""
用户管理接口
受 GPL v3.0 保护
"""

from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__)

# 内存存储（简化）
_all_users = {}


@users_bp.route('/api/users/', methods=['GET'])
def list_users():
    """用户列表"""
    users = list(_all_users.values())
    return jsonify({'success': True, 'data': users})


@users_bp.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """用户详情"""
    user = _all_users.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    return jsonify({'success': True, 'data': user})


@users_bp.route('/api/users/', methods=['POST'])
def create_user():
    """创建用户"""
    data = request.get_json() or {}
    uid = data.get('user_id', '')
    if not uid:
        return jsonify({'success': False, 'message': '缺少 user_id'}), 400
    if uid in _all_users:
        return jsonify({'success': False, 'message': '用户已存在'}), 400
    # 简化：不存明文密码
    user = {k: v for k, v in data.items() if k != 'password'}
    user['password'] = '***'
    _all_users[uid] = user
    return jsonify({'success': True, 'data': user})


@users_bp.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户"""
    user = _all_users.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    data = request.get_json() or {}
    for k, v in data.items():
        if k == 'password':
            continue
        user[k] = v
    return jsonify({'success': True, 'data': user})


@users_bp.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    if user_id in _all_users:
        del _all_users[user_id]
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '用户不存在'}), 404


@users_bp.route('/api/users/<user_id>/state', methods=['GET'])
def get_user_state(user_id):
    """获取用户状态"""
    user = _all_users.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    state = user.get('state', {'status': '空闲', '体力': '100%', '心态': '正常', '情绪': '平静'})
    return jsonify({'success': True, 'data': state})


@users_bp.route('/api/users/<user_id>/state', methods=['PUT'])
def update_user_state(user_id):
    """更新用户状态"""
    user = _all_users.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    data = request.get_json() or {}
    user.setdefault('state', {}).update(data)
    return jsonify({'success': True, 'data': user['state']})