# -*- coding: utf-8 -*-
"""
甲方场景
受 GPL v3.0 保护

投资管理。
调用ProjectCBM进行项目协调。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class OwnerScene:
    """甲方场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.contracts: Dict[str, Dict[str, Any]] = {}
        self.payments: Dict[str, Dict[str, Any]] = {}
        self.changes: Dict[str, Dict[str, Any]] = {}
        self._subscribe_events()

    def _subscribe_events(self) -> Dict[str, Any]:
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('任务完成', self._on_event, 'owner')
        self.event_bus.subscribe('流程完成', self._on_event, 'owner')
        self.event_bus.subscribe('签证生成', self._on_event, 'owner')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        pass

    # ==================== 进度查看 ====================

    def view_progress(self, project_id: str) -> Dict[str, Any]:
        """进度查看"""
        project_cbm = self.engines.get('project_cbm')
        progress = {'total': 0, 'completed': 0, 'percentage': 0}
        if project_cbm:
            progress = project_cbm.get_progress()
        return {
            'project_id': project_id,
            'progress': progress,
            'percentage': progress.get('percentage', 0),
        }

    # ==================== 审批付款 ====================

    def approve_payment(self, payment_id: str) -> Dict[str, Any]:
        """审批付款"""
        sig_engine = self.engines.get('signature')
        flow_id = None
        if sig_engine:
            result = sig_engine.create_signature_flow('进度款', payment_id)
            flow_id = result.get('flow_id')

        self.payments[payment_id] = {
            'payment_id': payment_id,
            'status': '已审批',
            'flow_id': flow_id,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        if self.event_bus:
            self.event_bus.publish('付款审批', {'payment_id': payment_id})

        return {'success': True, 'payment_id': payment_id, 'status': '已审批'}

    # ==================== 审批变更 ====================

    def approve_change(self, change_id: str) -> Dict[str, Any]:
        """审批变更"""
        self.changes[change_id] = {
            'change_id': change_id,
            'status': '已确认',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        if self.event_bus:
            self.event_bus.publish('变更审批', {'change_id': change_id})
        return {'success': True, 'change_id': change_id, 'status': '已确认'}

    # ==================== 合同总览 ====================

    def get_contract_summary(self, contract_id: str) -> Dict[str, Any]:
        """合同总览"""
        contract = self.contracts.get(contract_id, {})
        return {
            'contract_id': contract_id,
            'amount': contract.get('amount', 0),
            'paid': contract.get('paid', 0),
            'pending': contract.get('pending', 0),
        }

    # ==================== 项目总览 ====================

    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """项目总览"""
        project_cbm = self.engines.get('project_cbm')
        if project_cbm:
            return project_cbm.get_progress()
        return {'total': 0, 'completed': 0, 'pending': 0}

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {
            'role': role,
            'payments': list(self.payments.values()),
            'changes': list(self.changes.values()),
        }