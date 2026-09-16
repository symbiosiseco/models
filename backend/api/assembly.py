# -*- coding: utf-8 -*-
"""
装配 API
受 GPL v3.0 保护

提供装配检查接口，调用 AssemblyEngine。
"""

from flask import Blueprint, request, jsonify

# 蓝图
assembly_bp = Blueprint('assembly', __name__, url_prefix='/api')

# 依赖（延迟注入）
_assembly_engine = None
_entity_map = {}


def set_deps(assembly_engine, entity_map):
    """注入依赖"""
    global _assembly_engine, _entity_map
    _assembly_engine = assembly_engine
    _entity_map = entity_map


@assembly_bp.route('/assemble', methods=['POST'])
def assemble():
    """
    执行装配。

    请求体：
        {
            "part_id": "BOLT-027",
            "target_id": "FLANGE-005"
        }

    返回：
        {success, checks, message, part_id, target_id}
    """
    if not _assembly_engine:
        return jsonify({'success': False, 'message': '装配引擎未初始化'}), 500

    data = request.get_json() or {}
    part_id = data.get('part_id')
    target_id = data.get('target_id')

    if not part_id or not target_id:
        return jsonify({'success': False, 'message': '缺少 part_id 或 target_id'}), 400

    part = _entity_map.get(part_id)
    target = _entity_map.get(target_id)

    if not part:
        return jsonify({'success': False, 'message': f'零件不存在：{part_id}'}), 404
    if not target:
        return jsonify({'success': False, 'message': f'目标不存在：{target_id}'}), 404

    # 调用装配引擎
    entities = list(_entity_map.values())
    result = _assembly_engine.assemble(part, target, entities)

    return jsonify(result)


@assembly_bp.route('/assemble/check', methods=['POST'])
def check_assembly():
    """只检查装配条件，不执行装配"""
    if not _assembly_engine:
        return jsonify({'success': False, 'message': '装配引擎未初始化'}), 500

    data = request.get_json() or {}
    part_id = data.get('part_id')
    target_id = data.get('target_id')

    if not part_id or not target_id:
        return jsonify({'success': False, 'message': '缺少 part_id 或 target_id'}), 400

    part = _entity_map.get(part_id)
    target = _entity_map.get(target_id)

    if not part or not target:
        return jsonify({'success': False, 'message': '零件或目标不存在'}), 404

    entities = list(_entity_map.values())
    result = _assembly_engine.check_assembly(part, target, entities)

    return jsonify(result)