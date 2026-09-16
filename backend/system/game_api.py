# -*- coding: utf-8 -*-
"""
游戏式安装 API
受 GPL v3.0 保护

第2批：POST /api/game/install
        参数 {entity_id, position}
        更新实体 L3.绝对坐标 + 写 L4
"""

from flask import Blueprint, request, jsonify
from datetime import datetime

game_bp = Blueprint('game', __name__, url_prefix='/api/game')

_entity_map = {}
_event_bus = None


def set_deps(entity_map, event_bus):
    global _entity_map, _event_bus
    _entity_map = entity_map
    _event_bus = event_bus


@game_bp.route('/install', methods=['POST'])
def install():
    """
    安装实体到指定位置。

    请求体：
        {
            "entity_id": "SUP-001",
            "position": {"x": 3000, "y": -100, "z": 2500}
        }
    """
    data = request.get_json() or {}
    entity_id = data.get('entity_id')
    position = data.get('position')

    if not entity_id or not position:
        return jsonify({'success': False, 'message': '缺少 entity_id 或 position'}), 400

    entity = _entity_map.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': f'实体不存在：{entity_id}'}), 404

    try:
        # 更新 L3.绝对坐标
        l3 = entity.layer.get('l3_dynamic_state', {})
        l3['绝对坐标'] = position
        l3['状态'] = '已安装'
        l3['安装时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 写 L4
        if hasattr(entity, 'add_event'):
            entity.add_event('安装完成', f'位置({position.get("x")}, {position.get("y")}, {position.get("z")})')

        # 广播事件
        if _event_bus:
            _event_bus.publish('L3变化', {
                'entity_id': entity_id,
                'old_status': '待装配',
                'new_status': '已安装',
                'position': position,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })

        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'position': position,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500