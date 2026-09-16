# -*- coding: utf-8 -*-
"""
签字引擎
受 GPL v3.0 保护

多级审批签字。
与 workflow.py 配合，通过事件总线流转。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class SignatureEngine:
    """签字引擎"""

    # 7步签字流程（进度款）
    FLOW_TEMPLATES = {
        '进度款': ['施工员', '项目经理', '公司经理', '甲方工程师', '甲方项目负责人', '甲方成本', '甲方财务'],
        '变更':   ['施工员', '项目经理', '监理', '设计', '甲方工程师', '甲方项目负责人'],
        '验收':   ['施工员', '质检员', '监理', '甲方工程师', '甲方项目负责人'],
        '签证':   ['施工员', '预算员', '项目经理', '监理', '甲方工程师'],
    }

    def __init__(self, event_bus: Optional[EventBus] = None, workflow_engine=None):
        self.event_bus = event_bus or EventBus()
        self.workflow_engine = workflow_engine
        self.flows: Dict[str, Dict[str, Any]] = {}
        self.counter = 0

    # ==================== 创建签字流程 ====================

    def create_signature_flow(self, type: str, target: str) -> Dict[str, Any]:
        """创建签字流程"""
        steps = self._get_flow_template(type)
        if not steps:
            return {'success': False, 'message': f'未知签字类型：{type}'}

        self.counter += 1
        flow_id = f'SIG-{self.counter:03d}'

        self.flows[flow_id] = {
            'flow_id': flow_id,
            'signature_type': type,
            'target': target,
            'current_step': 0,
            'total_steps': len(steps),
            'steps': steps,
            'status': '进行中',
            'records': [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('签字流程启动', {
                'flow_id': flow_id,
                'signature_type': type,
                'target': target,
            })

        return {'success': True, 'flow_id': flow_id}

    # ==================== 签字 ====================

    def sign(self, flow_id: str, signer: str, role: str, comment: str = '') -> Dict[str, Any]:
        """签字"""
        flow = self.flows.get(flow_id)
        if not flow:
            return {'success': False, 'message': f'流程不存在：{flow_id}'}

        if flow['status'] == '已完成':
            return {'success': False, 'message': '流程已完成'}

        # 检查角色匹配
        if not self._check_role_match(flow_id, role):
            return {'success': False, 'message': f'角色不匹配：当前需要 {flow["steps"][flow["current_step"]]}'}

        # 创建签字记录
        record = self._create_signature_record(flow_id, signer, role, comment)
        flow['records'].append(record)

        # 推进
        flow['current_step'] += 1
        if flow['current_step'] >= flow['total_steps']:
            flow['status'] = '已完成'
            if self.event_bus:
                self.event_bus.publish('签字完成', {
                    'flow_id': flow_id,
                    'signature_type': flow['signature_type'],
                })
        else:
            if self.event_bus:
                self.event_bus.publish('签字', {
                    'flow_id': flow_id,
                    'signer': signer,
                    'role': role,
                    'next_step': flow['current_step'],
                })

        return {
            'success': True,
            'flow_id': flow_id,
            'next_step': flow['current_step'],
        }

    def reject(self, flow_id: str, signer: str, role: str, reason: str = '') -> Dict[str, Any]:
        """拒绝签字"""
        flow = self.flows.get(flow_id)
        if not flow:
            return {'success': False, 'message': f'流程不存在：{flow_id}'}

        if flow['status'] == '已完成':
            return {'success': False, 'message': '流程已完成'}

        # 记录驳回
        record = self._create_signature_record(flow_id, signer, role, f'驳回：{reason}')
        record['status'] = '退回'
        flow['records'].append(record)

        # 回退
        if flow['current_step'] > 0:
            flow['current_step'] -= 1

        if self.event_bus:
            self.event_bus.publish('签字驳回', {
                'flow_id': flow_id,
                'signer': signer,
                'role': role,
                'reason': reason,
            })

        return {
            'success': True,
            'flow_id': flow_id,
            'previous_step': flow['current_step'],
        }

    # ==================== 查询 ====================

    def get_pending(self, role: str) -> List[Dict[str, Any]]:
        """获取待签字列表"""
        pending = []
        for fid, flow in self.flows.items():
            if flow['status'] != '进行中':
                continue
            current_step = flow['current_step']
            if current_step < flow['total_steps']:
                if flow['steps'][current_step] == role:
                    pending.append({
                        'flow_id': fid,
                        'signature_type': flow['signature_type'],
                        'target': flow['target'],
                        'current_step': current_step + 1,
                    })
        return pending

    def get_history(self, flow_id: str) -> List[Dict[str, Any]]:
        """获取签字历史"""
        flow = self.flows.get(flow_id)
        if not flow:
            return []
        return flow['records']

    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """获取签字流程状态"""
        flow = self.flows.get(flow_id)
        if not flow:
            return {'success': False, 'message': '流程不存在'}
        return {
            'flow_id': flow_id,
            'current_step': flow['current_step'],
            'total_steps': flow['total_steps'],
            'status': flow['status'],
        }

    # ==================== 内部方法 ====================

    def _get_flow_template(self, type: str) -> List[str]:
        """获取签字流程模板"""
        return self.FLOW_TEMPLATES.get(type, [])

    def _check_role_match(self, flow_id: str, role: str) -> bool:
        """检查角色匹配"""
        flow = self.flows.get(flow_id)
        if not flow:
            return False
        current_step = flow['current_step']
        if current_step >= flow['total_steps']:
            return False
        return flow['steps'][current_step] == role

    def _create_signature_record(self, flow_id: str, signer: str,
                                  role: str, comment: str) -> Dict[str, Any]:
        """创建签字记录"""
        return {
            'flow_id': flow_id,
            'signer': signer,
            'role': role,
            'comment': comment,
            'sign_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': '已签',
        }

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}