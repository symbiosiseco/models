# -*- coding: utf-8 -*-
"""
CBM API
受 GPL v3.0 保护

CBM（边界判定）相关接口：
- CBM 检查
- CBM 状态查询
- CBM 统计
- CBM 监听（物 / 人 / 任务 / 项目）
"""

from flask import Blueprint, request, jsonify

cbm_bp = Blueprint('cbm', __name__)


# ============================================================
# 全局依赖
# ============================================================

_entity_cbm = None
_worker_cbm = None
_task_cbm = None
_project_cbm = None
_contact_check = None
_all_entities = {}


def set_deps(entity_cbm, worker_cbm, task_cbm, project_cbm, contact_check, entities):
    """注入依赖（app.py 调用）"""
    global _entity_cbm, _worker_cbm, _task_cbm, _project_cbm, _contact_check, _all_entities
    _entity_cbm = entity_cbm
    _worker_cbm = worker_cbm
    _task_cbm = task_cbm
    _project_cbm = project_cbm
    _contact_check = contact_check
    _all_entities = entities


def set_task_cbm(task_cbm_instance):
    """动态注入 TaskCBM（供 tasks.py 在任务分解后调用）"""
    global _task_cbm
    _task_cbm = task_cbm_instance


# ============================================================
# 工具函数（兼容 BaseEntity 实例 与 dict）
# ============================================================

def _get_layer(entity, layer_name):
    """从实体中取某一层的数据"""
    if entity is None:
        return {}
    if hasattr(entity, 'layer'):
        return entity.layer.get(layer_name, {}) or {}
    if isinstance(entity, dict):
        if 'layer' in entity and isinstance(entity['layer'], dict):
            return entity['layer'].get(layer_name, {}) or {}
        return entity.get(layer_name, {}) or {}
    return {}


def _get_cbm_status(entity):
    """获取实体的 CBM 状态（stable / warning / overload / collision / unbuilt）"""
    l3 = _get_layer(entity, 'l3_dynamic_state')
    return l3.get('cbm_status', 'stable') or 'stable'


def _get_entity_id(entity):
    """获取实体 ID"""
    if entity is None:
        return None
    if hasattr(entity, 'id'):
        return entity.id
    if isinstance(entity, dict):
        return entity.get('id')
    return None


# ============================================================
# CBM 检查
# ============================================================

@cbm_bp.route('/api/cbm/check', methods=['POST'])
def cbm_check():
    """CBM 检查"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id')
    check_type = data.get('check_type', 'all')

    entity = _all_entities.get(entity_id) if entity_id else None
    if entity_id and not entity:
        return jsonify({'success': False, 'message': f'实体不存在：{entity_id}'}), 404

    checks = []

    # 物理规则
    if check_type in ('all', 'physical', 'boundary'):
        cbm = _get_layer(entity, 'cbm_abilities')
        physical_rules = cbm.get('物理规则', {}) if cbm else {}
        checks.append({
            'type': '物理规则',
            'passed': bool(physical_rules),
            'detail': '包围盒 / 最小间距 / 允许接触 / 禁止穿透',
        })

    # 受力规则
    if check_type in ('all', 'force'):
        cbm = _get_layer(entity, 'cbm_abilities')
        force_rules = cbm.get('受力规则', {}) if cbm else {}
        checks.append({
            'type': '受力规则',
            'passed': bool(force_rules),
            'detail': '自重 / 受力点 / 传力路径 / 承重上限',
        })

    # 装配规则
    if check_type in ('all', 'assembly'):
        cbm = _get_layer(entity, 'cbm_abilities')
        assembly_rules = cbm.get('装配规则', {}) if cbm else {}
        checks.append({
            'type': '装配规则',
            'passed': bool(assembly_rules),
            'detail': '连接对象 / 拧紧力矩 / 装配顺序 / 密封等级',
        })

    # 规范约束
    if check_type in ('all', 'spec'):
        cbm = _get_layer(entity, 'cbm_abilities')
        spec_rules = cbm.get('规范约束', {}) if cbm else {}
        checks.append({
            'type': '规范约束',
            'passed': bool(spec_rules),
            'detail': '安装规范 / 维护空间 / 检查周期',
        })

    # 接触面检查
    if check_type in ('all', 'contact'):
        if _contact_check is not None and entity is not None:
            try:
                result = _contact_check.check_all(entity, list(_all_entities.values()))
                checks.append({
                    'type': '接触面检查',
                    'passed': result.get('passed', True),
                    'detail': result,
                })
            except Exception as e:
                checks.append({
                    'type': '接触面检查',
                    'passed': False,
                    'detail': str(e),
                })
        else:
            checks.append({
                'type': '接触面检查',
                'passed': True,
                'detail': '接触面检查引擎未初始化，跳过',
            })

    passed = all(c.get('passed', False) for c in checks) if checks else True

    return jsonify({
        'success': True,
        'data': {
            'entity_id': entity_id,
            'check_type': check_type,
            'passed': passed,
            'checks': checks,
        }
    })


# ============================================================
# CBM 状态
# ============================================================

@cbm_bp.route('/api/cbm/status/<entity_id>', methods=['GET'])
def cbm_status(entity_id):
    """CBM 状态查询"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': f'实体不存在：{entity_id}'}), 404

    cbm = _get_layer(entity, 'cbm_abilities')
    status = _get_cbm_status(entity)
    l3 = _get_layer(entity, 'l3_dynamic_state')
    checks = l3.get('checks', []) if l3 else []

    return jsonify({
        'success': True,
        'data': {
            'entity_id': entity_id,
            'rules': cbm,
            'status': status,
            'checks': checks,
        }
    })


# ============================================================
# 物的 CBM 监听
# ============================================================

@cbm_bp.route('/api/cbm/entity/<entity_id>/watch', methods=['POST'])
def watch_entity(entity_id):
    """开始监听物的 CBM"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': f'实体不存在：{entity_id}'}), 404

    if _entity_cbm is None:
        return jsonify({'success': False, 'message': '物的CBM未初始化'}), 500

    try:
        result = _entity_cbm.watch() if hasattr(_entity_cbm, 'watch') else {'success': True}
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'物的CBM监听失败：{e}'}), 500


@cbm_bp.route('/api/cbm/entity/<entity_id>/unwatch', methods=['POST'])
def unwatch_entity(entity_id):
    """停止监听物的 CBM"""
    if _entity_cbm is None:
        return jsonify({'success': False, 'message': '物的CBM未初始化'}), 500

    try:
        result = _entity_cbm.unwatch() if hasattr(_entity_cbm, 'unwatch') else {'success': True}
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'物的CBM停止监听失败：{e}'}), 500


# ============================================================
# 人的 CBM 监听
# ============================================================

@cbm_bp.route('/api/cbm/worker/<worker_id>/watch', methods=['POST'])
def watch_worker(worker_id):
    """监听人的 CBM"""
    if _worker_cbm is None:
        return jsonify({'success': False, 'message': '人的CBM未初始化'}), 500
    try:
        result = _worker_cbm.watch() if hasattr(_worker_cbm, 'watch') else {'success': True}
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'人的CBM监听失败：{e}'}), 500


# ============================================================
# 任务 CBM 监听
# ============================================================

@cbm_bp.route('/api/cbm/task/<task_id>/watch', methods=['POST'])
def watch_task(task_id):
    """监听任务 CBM"""
    if _task_cbm is None:
        return jsonify({
            'success': False,
            'message': '任务CBM未初始化，请先通过 /api/task_generator/decompose 分解任务'
        }), 500
    try:
        result = _task_cbm.watch() if hasattr(_task_cbm, 'watch') else {'success': True}
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'任务CBM监听失败：{e}'}), 500


# ============================================================
# 项目 CBM 监听
# ============================================================

@cbm_bp.route('/api/cbm/project/<project_id>/watch', methods=['POST'])
def watch_project(project_id):
    """监听项目 CBM"""
    if _project_cbm is None:
        return jsonify({'success': False, 'message': '项目CBM未初始化'}), 500
    try:
        result = _project_cbm.watch() if hasattr(_project_cbm, 'watch') else {'success': True}
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'项目CBM监听失败：{e}'}), 500


# ============================================================
# CBM 统计
# ============================================================

@cbm_bp.route('/api/cbm/stats', methods=['GET'])
def cbm_stats():
    """CBM 统计：稳定 / 预警 / 超载 / 碰撞 / 未施工"""
    stats = {
        'stable': 0,
        'warning': 0,
        'overload': 0,
        'collision': 0,
        'unbuilt': 0,
        'total': 0,
    }

    for entity in _all_entities.values():
        stats['total'] += 1
        status = _get_cbm_status(entity)
        if status in stats:
            stats[status] += 1
        else:
            stats['stable'] += 1

    return jsonify({'success': True, 'data': stats})