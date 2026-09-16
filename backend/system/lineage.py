# -*- coding: utf-8 -*-
"""
数据血缘API
受 GPL v3.0 保护

追溯来源 + 数据版本。
"""

import sqlite3
from flask import Blueprint, request, jsonify

lineage_bp = Blueprint('lineage', __name__)

_all_entities = {}
_db_path = ''


def set_deps(entities, db_path):
    """注入依赖"""
    global _all_entities, _db_path
    _all_entities = entities
    _db_path = db_path


@lineage_bp.route('/api/lineage/<entity_id>', methods=['GET'])
def get_lineage(entity_id):
    """数据血缘"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    source = {}
    events = []
    if hasattr(entity, 'layer'):
        source = {
            'template': entity.layer.get('r_layer', {}).get('模板ID'),
            'manufacturer': entity.layer.get('r_layer', {}).get('厂家'),
        }
        events = entity.layer.get('l4_event_chain', [])

    return jsonify({
        'success': True,
        'data': {
            'entity_id': entity_id,
            'source': source,
            'events': events,
            'relations': _get_relations(entity_id),
        },
    })


@lineage_bp.route('/api/lineage/<entity_id>/versions', methods=['GET'])
def get_versions(entity_id):
    """版本历史"""
    versions = _query_versions(entity_id)
    return jsonify({'success': True, 'data': versions})


@lineage_bp.route('/api/lineage/<entity_id>/version/<int:version>', methods=['GET'])
def get_version(entity_id, version):
    """特定版本"""
    versions = _query_versions(entity_id)
    for v in versions:
        if v.get('version') == version:
            return jsonify({'success': True, 'data': v})
    return jsonify({'success': False, 'message': '版本不存在'}), 404


@lineage_bp.route('/api/lineage/<entity_id>/diff', methods=['GET'])
def get_diff(entity_id):
    """版本差异"""
    versions = _query_versions(entity_id)
    if len(versions) < 2:
        return jsonify({'success': True, 'data': {'diff': []}})
    v1 = versions[-2]
    v2 = versions[-1]
    return jsonify({
        'success': True,
        'data': {
            'from_version': v1.get('version'),
            'to_version': v2.get('version'),
            'diff': [
                {'field': 'snapshot', 'from': v1.get('snapshot'), 'to': v2.get('snapshot')}
            ],
        },
    })


@lineage_bp.route('/api/lineage/<entity_id>/trace', methods=['GET'])
def trace_lineage(entity_id):
    """追溯来源"""
    entity = _all_entities.get(entity_id)
    if not entity:
        return jsonify({'success': False, 'message': '实体不存在'}), 404

    trace = []
    if hasattr(entity, 'layer'):
        l4 = entity.layer.get('l4_event_chain', [])
        for event in l4:
            trace.append({
                'time': event.get('time'),
                'event': event.get('event'),
                'detail': event.get('detail'),
                'source': event.get('source', 'unknown'),
            })

    return jsonify({'success': True, 'data': trace})


@lineage_bp.route('/api/lineage/stats', methods=['GET'])
def lineage_stats():
    """血缘统计"""
    conn = _get_conn()
    total_entities = 0
    total_versions = 0
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT entity_id) FROM versions')
        total_entities = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COUNT(*) FROM versions')
        total_versions = cursor.fetchone()[0] or 0
        conn.close()
    except Exception:
        pass

    return jsonify({
        'success': True,
        'data': {
            'total_entities': total_entities,
            'total_versions': total_versions,
        },
    })


# ==================== 内部方法 ====================

def _get_conn():
    """获取数据库连接"""
    return sqlite3.connect(_db_path or ':memory:')


def _query_versions(entity_id):
    """查询版本历史"""
    conn = _get_conn()
    versions = []
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, entity_id, version, snapshot, changed_at, changed_by, change_type '
            'FROM versions WHERE entity_id = ? ORDER BY version DESC',
            (entity_id,)
        )
        rows = cursor.fetchall()
        cols = ['id', 'entity_id', 'version', 'snapshot', 'changed_at', 'changed_by', 'change_type']
        versions = [dict(zip(cols, row)) for row in rows]
        conn.close()
    except Exception:
        pass
    return versions


def _get_relations(entity_id):
    """获取关系"""
    conn = _get_conn()
    relations = []
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT from_id, to_id, relation_type FROM relations WHERE from_id = ? OR to_id = ?',
            (entity_id, entity_id)
        )
        rows = cursor.fetchall()
        cols = ['from_id', 'to_id', 'relation_type']
        relations = [dict(zip(cols, row)) for row in rows]
        conn.close()
    except Exception:
        pass
    return relations