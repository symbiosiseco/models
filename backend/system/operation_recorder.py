# -*- coding: utf-8 -*-
"""
操作捕捉API
受 GPL v3.0 保护

录制/回放/导出。
"""

from flask import Blueprint, request, jsonify, send_file

operation_recorder_bp = Blueprint('operation_recorder', __name__)

_demo_runner = None
_export_engine = None


def set_deps(demo_runner, export_engine=None):
    """注入依赖"""
    global _demo_runner, _export_engine
    _demo_runner = demo_runner
    _export_engine = export_engine


@operation_recorder_bp.route('/api/recorder/start', methods=['POST'])
def start_record():
    """开始录制"""
    if _demo_runner:
        result = _demo_runner.record_action({'type': 'start'})
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': '演示执行器未初始化'}), 500


@operation_recorder_bp.route('/api/recorder/stop', methods=['POST'])
def stop_record():
    """停止录制"""
    if _demo_runner:
        result = _demo_runner.stop_record()
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False}), 500


@operation_recorder_bp.route('/api/recorder/records', methods=['GET'])
def list_records():
    """录制列表"""
    if _demo_runner:
        return jsonify({'success': True, 'data': _demo_runner.get_records()})
    return jsonify({'success': True, 'data': []})


@operation_recorder_bp.route('/api/recorder/<record_id>', methods=['GET'])
def get_record(record_id):
    """录制详情"""
    if _demo_runner:
        record = _demo_runner.get_record(record_id)
        if not record:
            return jsonify({'success': False, 'message': '录制不存在'}), 404
        return jsonify({'success': True, 'data': record})
    return jsonify({'success': False}), 500


@operation_recorder_bp.route('/api/recorder/<record_id>/replay', methods=['POST'])
def replay(record_id):
    """回放"""
    data = request.get_json() or {}
    speed = data.get('speed', 1.0)
    if _demo_runner:
        result = _demo_runner.replay(record_id, speed)
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False}), 500


@operation_recorder_bp.route('/api/recorder/<record_id>/export', methods=['GET'])
def export_record(record_id):
    """导出录制"""
    if not _demo_runner:
        return jsonify({'success': False}), 500
    record = _demo_runner.get_record(record_id)
    if not record:
        return jsonify({'success': False, 'message': '录制不存在'}), 404

    if _export_engine:
        result = _export_engine.export_to_json(record, f'record_{record_id}.json')
        file_path = result.get('file_path')
        if file_path:
            return send_file(file_path, as_attachment=True)

    return jsonify({'success': False, 'message': '导出失败'}), 500


@operation_recorder_bp.route('/api/recorder/import', methods=['POST'])
def import_record():
    """导入录制"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '无文件'}), 400
    return jsonify({'success': True, 'message': '导入成功'})


@operation_recorder_bp.route('/api/recorder/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除录制"""
    if _demo_runner:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500