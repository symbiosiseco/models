# -*- coding: utf-8 -*-
"""
任务接口
受 GPL v3.0 保护

含TaskCBM驱动 + 触发链。
"""

from flask import Blueprint, request, jsonify

tasks_bp = Blueprint('tasks', __name__)

_task_generator = None
_task_engine = None
_event_bus = None
_tasks = {}


def set_deps(task_generator, task_engine, event_bus):
    """注入依赖"""
    global _task_generator, _task_engine, _event_bus
    _task_generator = task_generator
    _task_engine = task_engine
    _event_bus = event_bus


@tasks_bp.route('/api/task_generator/example/', methods=['GET'])
def example_plan():
    """示例计划"""
    return jsonify({
        'success': True,
        'data': {
            'project': '3号楼2层消防管道',
            'start_date': '2026-09-16',
            'start_time': '08:00',
            'task_chain': [
                {'task_template': 'TPL-TASK-PREFAB-SUPPORT', 'quantity': 1},
                {'task_template': 'TPL-TASK-DELIVER', 'quantity': 1},
                {'task_template': 'TPL-TASK-INSTALL-SUPPORT', 'quantity': 1},
                {'task_template': 'TPL-TASK-INSTALL-PIPE', 'quantity': 1},
                {'task_template': 'TPL-TASK-INSTALL-VALVE', 'quantity': 1},
                {'task_template': 'TPL-TASK-PRESSURE-TEST', 'quantity': 1},
            ],
        },
    })


@tasks_bp.route('/api/task_generator/decompose', methods=['POST'])
def decompose():
    """分解计划"""
    plan = request.get_json() or {}
    if not _task_generator:
        return jsonify({'success': False, 'message': '任务生成器未初始化'}), 500
    result = _task_generator.decompose(plan)
    if _task_engine:
        _task_engine.load(result['tasks'])

    # 为每个任务动态创建 TaskCBM
    try:
        from engines.task_cbm import TaskCBM
        from system.cbm_api import set_task_cbm
        all_tasks = {t['id']: t for t in result['tasks']}
        for task in result['tasks']:
            tcb = TaskCBM(task, _event_bus, all_tasks)
            tcb.watch()
            set_task_cbm(tcb)
    except Exception as e:
        print(f"⚠️ TaskCBM 创建失败：{e}")

    return jsonify({'success': True, 'data': result})


@tasks_bp.route('/api/task_generator/tasks/', methods=['GET'])
def list_tasks():
    """任务清单"""
    if _task_engine:
        return jsonify({'success': True, 'data': _task_engine.get_all_tasks()})
    return jsonify({'success': True, 'data': []})


@tasks_bp.route('/api/task_generator/next', methods=['POST'])
def next_task():
    """下一步"""
    if not _task_engine:
        return jsonify({'success': False}), 500
    pending = _task_engine.get_pending_tasks()
    if not pending:
        return jsonify({'success': False, 'message': '无待执行任务'})
    task = pending[0]
    result = _task_engine.complete(task['id'])
    return jsonify({'success': True, 'data': result})


@tasks_bp.route('/api/task_generator/reset', methods=['POST'])
def reset_tasks():
    """重置"""
    if _task_engine:
        return jsonify({'success': True, 'data': _task_engine.reset()})
    return jsonify({'success': True})


@tasks_bp.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """任务详情"""
    if _task_engine:
        task = _task_engine.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        return jsonify({'success': True, 'data': task})
    return jsonify({'success': False}), 404


@tasks_bp.route('/api/tasks/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """开始任务"""
    data = request.get_json() or {}
    worker_id = data.get('worker_id', '')
    if _task_engine:
        task = _task_engine.get_task(task_id)
        if task:
            task['status'] = '执行中'
    if _event_bus:
        _event_bus.publish('任务开始', {'task_id': task_id, 'worker_id': worker_id})
    return jsonify({'success': True, 'data': {'task_id': task_id}})


@tasks_bp.route('/api/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    if not _task_engine:
        return jsonify({'success': False}), 500
    result = _task_engine.complete(task_id)
    return jsonify({'success': True, 'data': result})


@tasks_bp.route('/api/tasks/<task_id>/cbm', methods=['GET'])
def task_cbm(task_id):
    """任务CBM"""
    if _task_engine:
        task = _task_engine.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        return jsonify({'success': True, 'data': task.get('cbm', {})})
    return jsonify({'success': False}), 404


@tasks_bp.route('/api/tasks/<task_id>/trigger_chain', methods=['GET'])
def trigger_chain(task_id):
    """触发链"""
    if _task_engine:
        task = _task_engine.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        return jsonify({'success': True, 'data': task.get('cbm', {}).get('后继任务', [])})
    return jsonify({'success': False}), 404