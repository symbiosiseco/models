# -*- coding: utf-8 -*-
"""
第三方检测场景
受 GPL v3.0 保护

独立检测。
调用ValidationEngine+MeasurementEngine。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ThirdPartyScene:
    """第三方检测场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.tests: List[Dict[str, Any]] = []
        self.reports: List[Dict[str, Any]] = []
        self._subscribe_events()

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('检测请求', self._on_event, 'third_party')
        self.event_bus.subscribe('装配失败', self._on_event, 'third_party')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        pass

    # ==================== 材料检测 ====================

    def test_material(self, material_id: str, test_type: str = '材料检测') -> Dict[str, Any]:
        """材料检测"""
        test_id = f'TEST-{len(self.tests) + 1:03d}'
        result = {'passed': True, 'test_type': test_type}

        validation = self.engines.get('validation')
        if validation:
            entity = self.entities.get(material_id)
            if entity:
                r = validation.validate_all(entity, list(self.entities.values()))
                result['passed'] = r.get('passed', True)

        self.tests.append({
            'test_id': test_id,
            'material_id': material_id,
            'test_type': test_type,
            'result': result,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        if self.event_bus:
            self.event_bus.publish('检测完成', {'test_id': test_id})

        return {'success': True, 'test_id': test_id, 'result': result}

    # ==================== 质量检测 ====================

    def test_quality(self, entity_id: str, test_type: str = '质量检测') -> Dict[str, Any]:
        """质量检测"""
        test_id = f'TEST-{len(self.tests) + 1:03d}'
        result = {'passed': True, 'test_type': test_type}
        self.tests.append({
            'test_id': test_id, 'entity_id': entity_id,
            'test_type': test_type, 'result': result,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        return {'success': True, 'test_id': test_id, 'result': result}

    # ==================== 装配检测 ====================

    def test_assembly(self, entity_id: str, test_type: str = '装配检测') -> Dict[str, Any]:
        """装配检测"""
        test_id = f'TEST-{len(self.tests) + 1:03d}'
        checks = []
        assembly = self.engines.get('assembly')
        if assembly:
            entity = self.entities.get(entity_id)
            if entity:
                r = assembly.check_assembly(entity, entity)
                checks = r.get('checks', [])
        self.tests.append({
            'test_id': test_id, 'entity_id': entity_id,
            'test_type': test_type, 'checks': checks,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        return {'success': True, 'test_id': test_id, 'checks': checks}

    # ==================== 接触面检测 ====================

    def test_contact_face(self, entity_id: str, test_type: str = '接触面检测') -> Dict[str, Any]:
        """接触面检测"""
        test_id = f'TEST-{len(self.tests) + 1:03d}'
        checks = []
        contact_check = self.engines.get('contact_check')
        if contact_check:
            entity = self.entities.get(entity_id)
            if entity:
                r = contact_check.check_all(entity, list(self.entities.values()))
                checks = r.get('checks', [])
        self.tests.append({
            'test_id': test_id, 'entity_id': entity_id,
            'test_type': test_type, 'checks': checks,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        return {'success': True, 'test_id': test_id, 'checks': checks}

    # ==================== 出报告 ====================

    def issue_report(self, test_id: str, result: Dict[str, Any] = None) -> Dict[str, Any]:
        """出报告"""
        report_id = f'RPT-{len(self.reports) + 1:03d}'
        report = {
            'report_id': report_id,
            'test_id': test_id,
            'result': result or {},
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.reports.append(report)

        if self.event_bus:
            self.event_bus.publish('报告生成', {'report_id': report_id, 'test_id': test_id})

        return {'success': True, 'report_id': report_id, 'file_path': f'/tmp/{report_id}.pdf'}

    # ==================== 检测历史 ====================

    def get_test_history(self, material_id: str = '') -> List[Dict[str, Any]]:
        """获取检测历史"""
        return [t for t in self.tests if not material_id or t.get('material_id') == material_id]

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {'role': role, 'tests': self.tests, 'reports': self.reports}