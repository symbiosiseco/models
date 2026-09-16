# -*- coding: utf-8 -*-
"""
深化设计场景
受 GPL v3.0 保护

支架深化、管线综合。
调用接触面检查引擎。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DeepenDesignScene:
    """深化设计场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.supports: List[Dict[str, Any]] = []
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        """订阅事件"""
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('L3变化', self._on_event, 'deepen_design')
        self.event_bus.subscribe('装配失败', self._on_event, 'deepen_design')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        """事件回调"""
        pass

    # ==================== 支架深化 ====================

    def deepen_support(self, pipe_id: str, space: Optional[Dict] = None) -> Dict[str, Any]:
        """支架深化"""
        from models import SupportEntity, PipeEntity

        # 读取管道位置
        pipe = self.entities.get(pipe_id)
        if not pipe:
            return {'success': False, 'message': f'管道不存在：{pipe_id}'}

        # 生成支架布置
        length = 10000
        if hasattr(pipe, 'layer'):
            length = pipe.layer.get('l3_dynamic_state', {}).get('长度', 10000)

        # 每3米一个支架
        count = max(1, int(length / 3000) + 1)
        support_ids = []
        for i in range(count):
            x_pos = i * 3000
            support = SupportEntity(index=i, x_pos=x_pos)
            support_id = support.id
            self.supports.append({
                'id': support_id,
                'x_pos': x_pos,
                'support_type': '单支角钢支架',
            })
            support_ids.append(support_id)

        return {
            'success': True,
            'pipe_id': pipe_id,
            'support_ids': support_ids,
            'count': len(support_ids),
        }

    # ==================== 综合排布 ====================

    def comprehensive_layout(self, entities: List) -> Dict[str, Any]:
        """综合排布"""
        # 按优先级排序
        sorted_entities = self.engines.get('priority').sort_by_priority(entities) \
            if self.engines.get('priority') else entities

        layout = []
        for e in sorted_entities:
            eid = getattr(e, 'id', '')
            etype = getattr(e, 'entity_type', '')
            layout.append({'id': eid, 'type': etype})

        return {'success': True, 'layout': layout}

    # ==================== 碰撞检查 ====================

    def check_collision(self, entities: List) -> List[Dict[str, Any]]:
        """碰撞检查"""
        if self.engines.get('collision'):
            return self.engines['collision'].detect_all(entities)
        return []

    # ==================== 接触面检查 ====================

    def check_contact_faces(self, entity) -> Dict[str, Any]:
        """接触面检查"""
        if self.engines.get('contact_check'):
            return self.engines['contact_check'].check_all(entity, list(self.entities.values()))
        return {'passed': True, 'checks': []}

    # ==================== 管道分段检查 ====================

    def check_pipe_segments(self, pipe) -> Dict[str, Any]:
        """管道分段检查"""
        if self.engines.get('contact_check'):
            return self.engines['contact_check'].check_pipe_segments(pipe)

        # 降级：本地计算
        length = 10000
        if hasattr(pipe, 'layer'):
            length = pipe.layer.get('l3_dynamic_state', {}).get('长度', 10000)

        if length <= 6000:
            return {'passed': True, 'segments': [length], 'clamps': 0}

        segments = [6000, length - 6000]
        return {'passed': True, 'segments': segments, 'clamps': 1}

    # ==================== 提交审批 ====================

    def submit_for_approval(self, design_id: str) -> Dict[str, Any]:
        """提交甲方确认"""
        if self.event_bus:
            self.event_bus.publish('设计提交审批', {
                'design_id': design_id,
                'role': '甲方',
            })
        return {'success': True, 'approval_id': f'APP-{design_id}'}

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {
            'role': role,
            'supports': self.supports,
        }