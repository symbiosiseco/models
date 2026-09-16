# -*- coding: utf-8 -*-
"""
流程引擎
受 GPL v3.0 保护

多级审批流转。
通过事件总线通知相关方。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class WorkflowEngine:
    """流程引擎"""

    # 流程模板
    TEMPLATES = {
        '进度款': ['施工员', '项目经理', '公司经理', '甲方工程师', '甲方项目负责人', '甲方成本', '甲方财务'],
        '变更':   ['施工员', '项目经理', '监理', '设计', '甲方工程师', '甲方项目负责人'],
        '验收':   ['施工员', '质检员', '监理', '甲方工程师', '甲方项目负责人'],
        '签证':   ['施工员', '预算员', '项目经理', '监理', '甲方工程师'],
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.instances: Dict[str, Dict[str, Any]] = {}
        self.counter = 0

    # ==================== 加载模板 ====================

    def load_template(self, workflow_template: Dict[str, Any]) -> Dict[str, Any]:
        """加载流程模板"""
        wtype = workflow_template.get('type', '')
        if wtype:
            self.TEMPLATES[wtype] = workflow_template.get('steps', [])
        return {'success': True, 'template_id': wtype}

    # ==================== 启动流程 ====================

    def start(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """启动流程实例"""
        wtype = instance_data.get('workflow_type', '进度款')
        steps = self.TEMPLATES.get(wtype, [])
        if not steps:
            return {'success': False, 'message': f'未知流程类型：{wtype}'}

        self.counter += 1
        instance_id = f'FLOW-{self.counter:03d}'

        instance = {
            'instance_id': instance_id,
            'workflow_type': wtype,
            'current_step': 0,
            'total_steps': len(steps),
            'steps': steps,
            'status': '进行中',
            'signers': {},
            'times': {},
            'comments': {},
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.instances[instance_id] = instance

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('流程启动', {
                'instance_id': instance_id,
                'workflow_type': wtype,
            })
        # 通知当前步骤审批人
        self._notify_current_step(instance_id)

        return {'success': True, 'instance_id': instance_id}

    # ==================== 审批 ====================

    def approve(self, instance_id: str, role: str, comment: str = '') -> Dict[str, Any]:
        """审批通过"""
        instance = self.instances.get(instance_id)
        if not instance:
            return {'success': False, 'message': f'流程不存在：{instance_id}'}

        if instance['status'] == '已完成':
            return {'success': False, 'message': '流程已完成'}

        current_role = instance['steps'][instance['current_step']]
        if role != current_role:
            return {'success': False, 'message': f'角色不匹配：当前步骤需要 {current_role}'}

        # 记录审批
        instance['signers'][instance['current_step']] = role
        instance['times'][instance['current_step']] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        instance['comments'][instance['current_step']] = comment

        # 推进
        next_step = self._advance(instance_id)

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('流程审批', {
                'instance_id': instance_id,
                'role': role,
                'current_step': instance['current_step'],
            })

        return {'success': True, 'instance_id': instance_id, 'next_step': next_step}

    def reject(self, instance_id: str, role: str, reason: str = '') -> Dict[str, Any]:
        """驳回"""
        instance = self.instances.get(instance_id)
        if not instance:
            return {'success': False, 'message': f'流程不存在：{instance_id}'}

        # 记录驳回
        instance['comments'][instance['current_step']] = f'驳回：{reason}'

        # 回退
        previous_step = self._rollback(instance_id)

        if self.event_bus:
            self.event_bus.publish('流程驳回', {
                'instance_id': instance_id,
                'role': role,
                'reason': reason,
            })

        return {'success': True, 'instance_id': instance_id, 'previous_step': previous_step}

    # ==================== 内部流转 ====================

    def _advance(self, instance_id: str) -> int:
        """推进到下一步"""
        instance = self.instances[instance_id]
        instance['current_step'] += 1

        if instance['current_step'] >= instance['total_steps']:
            instance['status'] = '已完成'
            if self.event_bus:
                self.event_bus.publish('流程完成', {
                    'instance_id': instance_id,
                    'workflow_type': instance['workflow_type'],
                })
        else:
            self._notify_current_step(instance_id)

        return instance['current_step']

    def _rollback(self, instance_id: str) -> int:
        """驳回回到上一步"""
        instance = self.instances[instance_id]
        if instance['current_step'] > 0:
            instance['current_step'] -= 1
        self._notify_current_step(instance_id)
        return instance['current_step']

    def _notify_current_step(self, instance_id: str):
        """通知当前步骤审批人"""
        instance = self.instances.get(instance_id)
        if not instance:
            return
        current_step = instance['current_step']
        if current_step < instance['total_steps']:
            role = instance['steps'][current_step]
            if self.event_bus:
                self.event_bus.publish('流程通知', {
                    'instance_id': instance_id,
                    'role': role,
                    'step': current_step + 1,
                })

    # ==================== 查询 ====================

    def get_status(self, instance_id: str) -> Dict[str, Any]:
        """获取流程状态"""
        instance = self.instances.get(instance_id)
        if not instance:
            return {'success': False, 'message': '流程不存在'}
        return {
            'instance_id': instance_id,
            'current_step': instance['current_step'],
            'total_steps': instance['total_steps'],
            'status': instance['status'],
        }

    def get_pending(self, role: str) -> List[Dict[str, Any]]:
        """获取待审批列表"""
        pending = []
        for iid, instance in self.instances.items():
            if instance['status'] != '进行中':
                continue
            current_step = instance['current_step']
            if current_step < instance['total_steps']:
                if instance['steps'][current_step] == role:
                    pending.append({
                        'instance_id': iid,
                        'workflow_type': instance['workflow_type'],
                        'current_step': current_step + 1,
                    })
        return pending

    def get_history(self, instance_id: str) -> List[Dict[str, Any]]:
        """获取流程历史"""
        instance = self.instances.get(instance_id)
        if not instance:
            return []
        history = []
        for step in range(instance['current_step']):
            history.append({
                'step': step + 1,
                'role': instance['steps'][step],
                'signer': instance['signers'].get(step),
                'time': instance['times'].get(step),
                'comment': instance['comments'].get(step),
            })
        return history

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取流程实例"""
        return self.instances.get(instance_id)