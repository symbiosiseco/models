# -*- coding: utf-8 -*-
"""
监管场景
受 GPL v3.0 保护

政府监管。
只读，调用EventBus+ValidationEngine。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class RegulatorScene:
    """监管场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.warnings: List[Dict[str, Any]] = []
        self._subscribe_events()

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('L3变化', self._on_event, 'regulator')
        self.event_bus.subscribe('验收通过', self._on_event, 'regulator')
        self.event_bus.subscribe('验收不通过', self._on_event, 'regulator')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        pass

    # ==================== 质量检查 ====================

    def check_quality(self, project_id: str) -> Dict[str, Any]:
        """质量检查"""
        validation = self.engines.get('validation')
        entities = list(self.entities.values())
        issues = []
        if validation:
            for e in entities:
                r = validation.validate_all(e, entities)
                if not r.get('passed'):
                    issues.append({'entity_id': getattr(e, 'id', ''), 'errors': r.get('errors', [])})

        total = len(entities)
        passed_count = total - len(issues)
        score = round(passed_count / total * 100, 2) if total > 0 else 100

        return {
            'project_id': project_id,
            'quality_score': score,
            'issues': issues,
        }

    # ==================== 安全检查 ====================

    def check_safety(self, project_id: str) -> Dict[str, Any]:
        """安全检查"""
        hazards = []
        collision = self.engines.get('collision')
        if collision:
            collisions = collision.detect_all(list(self.entities.values()))
            hazards = [c for c in collisions if c.get('severity') == 'red']

        total = len(self.entities)
        score = 100 - len(hazards) * 5

        return {
            'project_id': project_id,
            'safety_score': max(0, score),
            'hazards': hazards,
        }

    # ==================== 合规检查 ====================

    def check_compliance(self, project_id: str) -> Dict[str, Any]:
        """合规检查"""
        violations = []
        # 简化：检查管道分段
        for e in self.entities.values():
            if getattr(e, 'entity_type', '') == '管道':
                if hasattr(e, 'layer'):
                    length = e.layer.get('l3_dynamic_state', {}).get('长度', 0)
                    if length > 6000:
                        segments = e.layer.get('l2_static_attributes', {}).get('分段规则')
                        if not segments:
                            violations.append({
                                'entity_id': getattr(e, 'id', ''),
                                'type': '管道未分段',
                            })

        return {
            'project_id': project_id,
            'compliance': len(violations) == 0,
            'violations': violations,
        }

    # ==================== 下发警告 ====================

    def issue_warning(self, warning: Dict[str, Any]) -> Dict[str, Any]:
        """下发警告"""
        warning_id = f'WARN-{len(self.warnings) + 1:03d}'
        self.warnings.append({
            'warning_id': warning_id,
            'content': warning,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        if self.event_bus:
            self.event_bus.publish('监管警告', {
                'warning_id': warning_id,
                'content': warning,
            })

        return {'success': True, 'warning_id': warning_id}

    # ==================== 警告历史 ====================

    def get_warning_history(self, project_id: str = '') -> List[Dict[str, Any]]:
        """获取警告历史"""
        return list(self.warnings)

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {'role': role, 'warnings': self.warnings}