# -*- coding: utf-8 -*-
"""
文件上传下载接口
受 GPL v3.0 保护
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

files_bp = Blueprint('files', __name__)

# 上传目录
UPLOAD_DIR = '/tmp/uploads'
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except OSError:
    pass

# 文件类型白名单
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'xls', 'json', 'csv', 'txt'}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

# 内存文件索引
_files_db = {}


def _allowed(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXT


@files_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    """上传"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '无文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '文件名为空'}), 400
    if not _allowed(file.filename):
        return jsonify({'success': False, 'message': '文件类型不允许'}), 400

    file_id = f'FILE-{uuid.uuid4().hex[:8]}'
    safe_name = f'{file_id}_{os.path.basename(file.filename)}'
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    file.save(file_path)
    size = os.path.getsize(file_path)
    if size > MAX_SIZE:
        os.remove(file_path)
        return jsonify({'success': False, 'message': '文件太大'}), 400

    _files_db[file_id] = {
        'id': file_id,
        'filename': file.filename,
        'path': file_path,
        'size': size,
        'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    return jsonify({'success': True, 'data': {'file_id': file_id}})


@files_bp.route('/api/files/<file_id>', methods=['GET'])
def download_file(file_id):
    """下载"""
    info = _files_db.get(file_id)
    if not info:
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    return send_file(info['path'], as_attachment=True, download_name=info['filename'])


@files_bp.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除"""
    info = _files_db.get(file_id)
    if not info:
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    try:
        if os.path.exists(info['path']):
            os.remove(info['path'])
    except OSError:
        pass
    del _files_db[file_id]
    return jsonify({'success': True})


@files_bp.route('/api/files/', methods=['GET'])
def list_files():
    """文件列表"""
    return jsonify({'success': True, 'data': list(_files_db.values())})


@files_bp.route('/api/files/<file_id>/info', methods=['GET'])
def file_info(file_id):
    """文件信息"""
    info = _files_db.get(file_id)
    if not info:
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    return jsonify({'success': True, 'data': info})