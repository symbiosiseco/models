# -*- coding: utf-8 -*-
"""
流程接口
受 GPL v3.0 保护

含任务CBM驱动 + 7步签字流程。
"""

from flask import Blueprint, request, jsonify

workflow_bp = Blueprint('workflow', __name__)

_workflow_engine = None
_signature_engine = None
_event_bus = None


def set_deps(workflow_engine, signature_engine, event_bus):
    """注入依赖"""
    global _workflow_engine, _signature_engine, _event_bus
    _workflow_engine = workflow_engine
    _signature_engine = signature_engine
    _event_bus = event_bus


@workflow_bp.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """启动流程"""
    data = request.get_json() or {}
    workflow_type = data.get('workflow_type', '进度款')
    instance_data = data.get('instance_data', {})
    instance_data['workflow_type'] = workflow_type

    if not _workflow_engine:
        return jsonify({'success': False, 'message': '流程引擎未初始化'}), 500

    result = _workflow_engine.start(instance_data)

    if _event_bus:
        _event_bus.publish('流程启动', {
            'instance_id': result.get('instance_id'),
            'workflow_type': workflow_type,
        })

    return jsonify({'success': True, 'data': result})


@workflow_bp.route('/api/workflow/approve', methods=['POST'])
def approve_workflow():
    """审批"""
    data = request.get_json() or {}
    instance_id = data.get('instance_id', '')
    role = data.get('role', '')
    comment = data.get('comment', '')

    if not _workflow_engine:
        return jsonify({'success': False}), 500

    result = _workflow_engine.approve(instance_id, role, comment)
    if not result.get('success'):
        return jsonify(result), 403

    return jsonify({'success': True, 'data': result})


@workflow_bp.route('/api/workflow/reject', methods=['POST'])
def reject_workflow():
    """驳回"""
    data = request.get_json() or {}
    instance_id = data.get('instance_id', '')
    role = data.get('role', '')
    reason = data.get('reason', '')

    if not _workflow_engine:
        return jsonify({'success': False}), 500

    result = _workflow_engine.reject(instance_id, role, reason)
    return jsonify({'success': True, 'data': result})


@workflow_bp.route('/api/workflow/status/<instance_id>', methods=['GET'])
def workflow_status(instance_id):
    """查看状态"""
    if not _workflow_engine:
        return jsonify({'success': False}), 500
    result = _workflow_engine.get_status(instance_id)
    if not result.get('success', True) and 'status' not in result:
        return jsonify(result), 404
    return jsonify({'success': True, 'data': result})


@workflow_bp.route('/api/workflow/templates', methods=['GET'])
def workflow_templates():
    """流程模板列表"""
    if not _workflow_engine:
        return jsonify({'success': True, 'data': {}})
    return jsonify({'success': True, 'data': _workflow_engine.TEMPLATES})


@workflow_bp.route('/api/workflow/<instance_id>/history', methods=['GET'])
def workflow_history(instance_id):
    """流程历史"""
    if not _workflow_engine:
        return jsonify({'success': True, 'data': []})
    return jsonify({'success': True, 'data': _workflow_engine.get_history(instance_id)})


@workflow_bp.route('/api/workflow/<instance_id>/steps', methods=['GET'])
def workflow_steps(instance_id):
    """流程步骤"""
    if not _workflow_engine:
        return jsonify({'success': False}), 500
    instance = _workflow_engine.get_instance(instance_id)
    if not instance:
        return jsonify({'success': False, 'message': '流程不存在'}), 404

    steps = []
    for i, role in enumerate(instance['steps']):
        if i < instance['current_step']:
            status = 'done'
        elif i == instance['current_step']:
            status = 'current'
        else:
            status = 'pending'
        steps.append({
            'step': i + 1,
            'role': role,
            'status': status,
            'signer': instance['signers'].get(i),
            'time': instance['times'].get(i),
        })

    return jsonify({'success': True, 'data': steps})