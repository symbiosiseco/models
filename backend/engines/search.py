# -*- coding: utf-8 -*-
"""
搜索引擎
受 GPL v3.0 保护

实体快速检索。
支持受力点/接触面搜索。
"""

from typing import Dict, Any, List, Optional
from .event_bus import EventBus


class SearchEngine:
    """搜索引擎"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.index: Dict[str, Any] = {
            'by_id': {},
            'by_type': {},
            'by_system': {},
            'by_status': {},
            'by_force_point': {},
            'by_contact_face': {},
        }
        self.entities: List = []

    # ==================== 建立索引 ====================

    def index_entities(self, entities: List) -> Dict[str, Any]:
        """建立索引"""
        self.entities = list(entities)
        self.index = {
            'by_id': {},
            'by_type': {},
            'by_system': {},
            'by_status': {},
            'by_force_point': {},
            'by_contact_face': {},
        }
        for e in entities:
            self._index_entity(e)
        return {'success': True, 'indexed_count': len(entities)}

    def _index_entity(self, entity):
        """索引单个实体"""
        eid = getattr(entity, 'id', '')
        etype = getattr(entity, 'entity_type', '')
        if not eid:
            return

        # by_id
        self.index['by_id'][eid] = entity

        # by_type
        self.index['by_type'].setdefault(etype, []).append(eid)

        # by_system
        if hasattr(entity, 'layer'):
            system = entity.layer.get('l2_static_attributes', {}).get('系统', '')
            if system:
                self.index['by_system'].setdefault(system, []).append(eid)

            # by_status
            status = entity.layer.get('l3_dynamic_state', {}).get('状态', '')
            if status:
                self.index['by_status'].setdefault(status, []).append(eid)

            # by_force_point
            fps = entity.layer.get('l2_static_attributes', {}).get('受力点', [])
            for fp in fps:
                cap = fp.get('承重上限', '')
                if cap:
                    self.index['by_force_point'].setdefault(str(cap), []).append(eid)

            # by_contact_face
            cfs = entity.layer.get('l2_static_attributes', {}).get('接触面', [])
            for cf in cfs:
                cft = cf.get('类型', '')
                if cft:
                    self.index['by_contact_face'].setdefault(cft, []).append(eid)

    def update_index(self, entity) -> Dict[str, Any]:
        """更新索引"""
        self._index_entity(entity)
        if entity not in self.entities:
            self.entities.append(entity)
        return {'success': True}

    def remove_from_index(self, entity_id: str) -> Dict[str, Any]:
        """从索引移除"""
        if entity_id in self.index['by_id']:
            del self.index['by_id'][entity_id]
        for key in ['by_type', 'by_system', 'by_status', 'by_force_point', 'by_contact_face']:
            for k in list(self.index[key].keys()):
                if entity_id in self.index[key][k]:
                    self.index[key][k].remove(entity_id)
        return {'success': True}

    # ==================== 搜索方法 ====================

    def search(self, keyword: str) -> List:
        """关键词搜索"""
        if not keyword:
            return []
        keyword_lower = keyword.lower()
        results = []
        for e in self.entities:
            if self._match_keyword(e, keyword_lower):
                results.append(e)
        return results

    def _match_keyword(self, entity, keyword: str) -> bool:
        """匹配关键词"""
        eid = getattr(entity, 'id', '').lower()
        etype = getattr(entity, 'entity_type', '').lower()
        if keyword in eid or keyword in etype:
            return True
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            for v in l2.values():
                if keyword in str(v).lower():
                    return True
        return False

    def search_by_type(self, entity_type: str) -> List:
        """按类型搜索"""
        ids = self.index['by_type'].get(entity_type, [])
        return [self.index['by_id'][i] for i in ids if i in self.index['by_id']]

    def search_by_position(self, x: float, y: float, z: float,
                            radius: float = 1000) -> List:
        """按位置搜索"""
        results = []
        for e in self.entities:
            pos = self._get_position(e)
            distance = ((pos['x'] - x) ** 2 + (pos['y'] - y) ** 2 + (pos['z'] - z) ** 2) ** 0.5
            if distance <= radius:
                results.append(e)
        return results

    def search_by_force_point(self, capacity_min: float = 0,
                               capacity_max: float = 99999) -> List:
        """按受力点承重范围搜索"""
        results = []
        for e in self.entities:
            if not hasattr(e, 'layer'):
                continue
            fps = e.layer.get('l2_static_attributes', {}).get('受力点', [])
            for fp in fps:
                cap_str = str(fp.get('承重上限', '0'))
                cap = self._parse_capacity(cap_str)
                if capacity_min <= cap <= capacity_max:
                    results.append(e)
                    break
        return results

    def search_by_contact_face(self, cf_type: str) -> List:
        """按接触面类型搜索"""
        ids = self.index['by_contact_face'].get(cf_type, [])
        return [self.index['by_id'][i] for i in ids if i in self.index['by_id']]

    def search_by_status(self, status: str) -> List:
        """按状态搜索"""
        ids = self.index['by_status'].get(status, [])
        return [self.index['by_id'][i] for i in ids if i in self.index['by_id']]

    def search_by_system(self, system: str) -> List:
        """按系统搜索"""
        ids = self.index['by_system'].get(system, [])
        return [self.index['by_id'][i] for i in ids if i in self.index['by_id']]

    # ==================== 统计 ====================

    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计"""
        return {
            'total': len(self.entities),
            'by_type': {k: len(v) for k, v in self.index['by_type'].items()},
            'by_system': {k: len(v) for k, v in self.index['by_system'].items()},
            'by_status': {k: len(v) for k, v in self.index['by_status'].items()},
        }

    # ==================== 工具 ====================

    def _get_position(self, entity) -> Dict[str, float]:
        if hasattr(entity, 'get_position'):
            return entity.get_position()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l3_dynamic_state', {}).get(
                '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
            )
        return {'x': 0, 'y': 0, 'z': 0}

    def _parse_capacity(self, val: str) -> float:
        try:
            return float(str(val).replace('kg', '').replace('N·m', '').strip())
        except (ValueError, TypeError):
            return 0.0