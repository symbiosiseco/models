# -*- coding: utf-8 -*-
"""
监理场景
受 GPL v3.0 保护

质量监理。
调用EntityCBM+TaskCBM。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SupervisionScene:
    """监理场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.pending_inspections: List[str] = []
        self.acceptance_records: List[Dict[str, Any]] = []
        self._subscribe_events()

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('L3变化', self._on_event, 'supervision')
        self.event_bus.subscribe('任务完成', self._on_event, 'supervision')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        if event_type == 'L3变化' and data.get('new_status') == '已安装':
            eid = data.get('entity_id')
            if eid and eid not in self.pending_inspections:
                self.pending_inspections.append(eid)

    # ==================== 检查 ====================

    def inspect(self, entity_id: str) -> Dict[str, Any]:
        """检查"""
        entity = self.entities.get(entity_id)
        if not entity:
            return {'success': False, 'message': '实体不存在'}

        cbm = {}
        force_points = []
        contact_faces = []
        if hasattr(entity, 'layer'):
            cbm = entity.layer.get('cbm_abilities', {})
            force_points = entity.layer.get('l2_static_attributes', {}).get('受力点', [])
            contact_faces = entity.layer.get('l2_static_attributes', {}).get('接触面', [])

        return {
            'success': True,
            'entity_id': entity_id,
            'checks': {
                'force_points': force_points,
                'contact_faces': contact_faces,
                'cbm': cbm,
            },
        }

    # ==================== 验收 ====================

    def accept(self, entity_id: str, result: str = '合格') -> Dict[str, Any]:
        """验收"""
        entity = self.entities.get(entity_id)
        if entity and hasattr(entity, 'layer'):
            entity.layer['l3_dynamic_state']['状态'] = '已验收'
            if hasattr(entity, 'add_event'):
                entity.add_event('验收通过', '')

        acceptance_id = f'ACC-{len(self.acceptance_records) + 1:03d}'
        self.acceptance_records.append({
            'acceptance_id': acceptance_id,
            'entity_id': entity_id,
            'result': result,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        # 触发签字流程
        self.sign_acceptance(acceptance_id)

        if self.event_bus:
            self.event_bus.publish('验收通过', {'entity_id': entity_id})

        return {'success': True, 'entity_id': entity_id, 'status': '已验收'}

    # ==================== 整改 ====================

    def reject(self, entity_id: str, reason: str = '') -> Dict[str, Any]:
        """整改"""
        entity = self.entities.get(entity_id)
        if entity and hasattr(entity, 'layer'):
            entity.layer['l3_dynamic_state']['状态'] = '整改中'
            if hasattr(entity, 'add_event'):
                entity.add_event('验收不通过', f'原因：{reason}')

        if self.event_bus:
            self.event_bus.publish('验收不通过', {'entity_id': entity_id, 'reason': reason})

        return {'success': True, 'entity_id': entity_id, 'status': '整改中'}

    # ==================== 待验收列表 ====================

    def get_pending_inspections(self) -> List[str]:
        """待验收列表"""
        return list(self.pending_inspections)

    # ==================== 签字验收 ====================

    def sign_acceptance(self, acceptance_id: str) -> Dict[str, Any]:
        """签字验收"""
        sig_engine = self.engines.get('signature')
        if sig_engine:
            result = sig_engine.create_signature_flow('验收', acceptance_id)
            return {'success': True, 'acceptance_id': acceptance_id, 'flow_id': result.get('flow_id')}
        return {'success': True, 'acceptance_id': acceptance_id}

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {
            'role': role,
            'pending': self.pending_inspections,
            'records': self.acceptance_records,
        }