# -*- coding: utf-8 -*-
"""
工地场景
受 GPL v3.0 保护

施工执行。
调用全部6个CBM引擎，事件驱动核心场景。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ConstructionScene:
    """工地场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.materials_in_stock: List[str] = []
        self.problems: List[Dict[str, Any]] = []
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        """订阅全部CBM事件"""
        if not self.event_bus:
            return {'success': False}
        for et in [
            'L3变化', '任务派发', '产物完成', '任务完成',
            '装配失败', '接触面错误', '换货触发',
        ]:
            self.event_bus.subscribe(et, self._on_event, 'construction')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        """事件回调"""
        pass

    # ==================== 收货入库 ====================

    def receive_material(self, material_id: str,
                          position: Optional[Dict] = None) -> Dict[str, Any]:
        """收货入库"""
        position = position or {'x': 1000, 'y': -800, 'z': 100}
        entity = self.entities.get(material_id)
        if entity and hasattr(entity, 'layer'):
            entity.layer['l3_dynamic_state']['状态'] = '已入库'
            entity.layer['l3_dynamic_state']['绝对坐标'] = position
            if hasattr(entity, 'add_event'):
                entity.add_event('收货入库', f'位置：{position}')

        self.materials_in_stock.append(material_id)
        if self.event_bus:
            self.event_bus.publish('L3变化', {
                'entity_id': material_id,
                'old_status': '待装配',
                'new_status': '已入库',
                'position': position,
            })
        return {'success': True, 'material_id': material_id, 'status': '已入库'}

    # ==================== 开始任务 ====================

    def start_task(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        """开始任务"""
        # 通过 WorkerCBM 检查工人
        worker_cbm = self.engines.get('worker_cbm')
        if worker_cbm:
            check = worker_cbm.on_task_assigned({'id': task_id})
            if not check.get('accepted'):
                return {'success': False, 'message': check.get('message', '工人不可用')}

        # 更新任务状态
        task_engine = self.engines.get('task')
        if task_engine:
            task = task_engine.get_task(task_id)
            if task:
                task['status'] = '执行中'

        if self.event_bus:
            self.event_bus.publish('任务开始', {
                'task_id': task_id,
                'worker_id': worker_id,
            })

        return {'success': True, 'task_id': task_id, 'worker_id': worker_id}

    # ==================== 安装构件 ====================

    def install_entity(self, entity_id: str,
                        position: Optional[Dict] = None) -> Dict[str, Any]:
        """
        安装构件（核心）。

        流程：
            1. 调用装配引擎检查
            2. 调用接触面检查
            3. 更新实体
            4. 通过事件总线发布
        """
        position = position or {'x': 3000, 'y': -100, 'z': 2500}
        entity = self.entities.get(entity_id)
        if not entity:
            return {'success': False, 'message': f'实体不存在：{entity_id}'}

        # 1. 装配检查
        assembly_engine = self.engines.get('assembly')
        if assembly_engine:
            result = assembly_engine.check_assembly(entity, entity)
            if not result.get('success', True):
                # 装配失败处理
                self.handle_assembly_error(entity_id, entity_id, result.get('message', ''))
                return {'success': False, 'message': result.get('message', '装配失败')}

        # 2. 接触面检查
        contact_check = self.engines.get('contact_check')
        if contact_check:
            check_result = contact_check.check_all(entity, list(self.entities.values()))
            if not check_result.get('passed', True):
                self.handle_contact_error(entity_id, check_result.get('errors', []))
                return {'success': False, 'message': '接触面检查失败'}

        # 3. 更新实体
        if hasattr(entity, 'layer'):
            entity.layer['l3_dynamic_state']['状态'] = '已安装'
            entity.layer['l3_dynamic_state']['绝对坐标'] = position
            if hasattr(entity, 'add_event'):
                entity.add_event('安装完成', f'坐标{position}')

        # 4. 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('L3变化', {
                'entity_id': entity_id,
                'old_status': '待装配',
                'new_status': '已安装',
                'position': position,
            })

        return {'success': True, 'entity_id': entity_id, 'assembly_result': 'success'}

    # ==================== 完成任务 ====================

    def complete_task(self, task_id: str,
                       photos: Optional[List] = None) -> Dict[str, Any]:
        """完成任务"""
        photos = photos or []
        task_engine = self.engines.get('task')

        triggered = []
        if task_engine:
            result = task_engine.complete(task_id)
            if result.get('success'):
                triggered = result.get('triggered_tasks', [])

        return {
            'success': True,
            'task_id': task_id,
            'triggered_tasks': triggered,
        }

    # ==================== 现场反馈 ====================

    def report_problem(self, entity_id: str, problem: str) -> Dict[str, Any]:
        """现场反馈"""
        problem_id = f'PROB-{len(self.problems) + 1:03d}'
        self.problems.append({
            'problem_id': problem_id,
            'entity_id': entity_id,
            'problem': problem,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

        if self.event_bus:
            self.event_bus.publish('现场反馈', {
                'problem_id': problem_id,
                'entity_id': entity_id,
                'problem': problem,
                'reporter': '施工员',
            })

        return {'success': True, 'problem_id': problem_id}

    # ==================== 装配失败处理 ====================

    def handle_assembly_error(self, part_id: str, target_id: str,
                               error: str) -> Dict[str, Any]:
        """处理装配失败"""
        replacement = self.engines.get('replacement')
        order_id = None
        if replacement:
            result = replacement.handle_assembly_error(part_id, target_id, error)
            order_id = result.get('order_id')

        if self.event_bus:
            self.event_bus.publish('装配失败', {
                'part_id': part_id,
                'target_id': target_id,
                'error': error,
                'order_id': order_id,
            })

        return {'success': True, 'order_id': order_id}

    # ==================== 接触面错误处理 ====================

    def handle_contact_error(self, entity_id: str,
                              errors: List[str]) -> Dict[str, Any]:
        """处理接触面错误"""
        if self.event_bus:
            self.event_bus.publish('接触面错误', {
                'entity_id': entity_id,
                'errors': errors,
            })
        return {'success': True, 'entity_id': entity_id, 'errors': errors}

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        return {
            'role': role,
            'materials_in_stock': self.materials_in_stock,
            'problems': self.problems,
        }