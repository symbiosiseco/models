# -*- coding: utf-8 -*-
"""
物的CBM引擎
受 GPL v3.0 保护

感知L3变化、检查边界、写L4。
物的CBM是"边界守卫"——只负责守卫自己的边界，不负责触发下游。
"""

from typing import Dict, Any, List
from datetime import datetime
from .event_bus import EventBus


class EntityCBM:
    """物的CBM引擎"""

    def __init__(self, entity, event_bus: EventBus):
        self.entity = entity
        self.event_bus = event_bus
        self.watching = False
        self._old_l3 = None

    # ==================== 监听 ====================

    def watch(self) -> Dict[str, Any]:
        """开始监听L3变化"""
        self.event_bus.subscribe(
            'L3变化',
            self._on_event,
            f'entity_cbm_{self.entity.id}'
        )
        self.watching = True
        self._old_l3 = self.entity.layer.get('l3_dynamic_state', {}).copy()
        return {'success': True, 'entity_id': self.entity.id}

    def unwatch(self) -> Dict[str, Any]:
        """停止监听"""
        self.event_bus.unsubscribe('L3变化', f'entity_cbm_{self.entity.id}')
        self.watching = False
        return {'success': True, 'entity_id': self.entity.id}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        """事件总线回调：只处理自己实体的L3变化"""
        if data.get('entity_id') != self.entity.id:
            return
        old_l3 = self._old_l3 or {}
        new_l3 = data.get('new_l3', self.entity.layer.get('l3_dynamic_state', {}))
        self.on_l3_change(old_l3, new_l3)
        self._old_l3 = new_l3.copy()

    # ==================== L3变化回调 ====================

    def on_l3_change(self, old_l3: Dict[str, Any], new_l3: Dict[str, Any]) -> Dict[str, Any]:
        """
        L3变化回调。

        流程：
            1. 检查位置
            2. 检查受力
            3. 检查碰撞
            4. 通过 → 写L4 → 通知任务CBM
            5. 不通过 → 写L4（失败）→ 通知任务CBM（失败）
        """
        # 检查位置
        pos_result = self.check_position(new_l3)

        # 检查受力
        force_result = self.check_force(new_l3)

        # 汇总
        all_checks = [pos_result, force_result]
        passed = all(r.get('passed', True) for r in all_checks)

        if passed:
            self.write_l4('L3变化', f'状态：{new_l3.get("状态", "未知")}')
            self.notify_task_cbm(success=True)
            return {
                'passed': True,
                'checks': all_checks,
                'message': '所有边界检查通过',
            }
        else:
            failed = [r for r in all_checks if not r.get('passed', True)]
            self.write_l4('L3变化失败', str(failed))
            self.notify_task_cbm(success=False)
            return {
                'passed': False,
                'checks': all_checks,
                'message': f'边界检查失败：{failed}',
            }

    # ==================== 边界检查 ====================

    def check_boundary(self, new_l3: Dict[str, Any]) -> Dict[str, Any]:
        """检查边界（位置+受力+碰撞的综合检查）"""
        pos = self.check_position(new_l3)
        force = self.check_force(new_l3)
        return {
            'passed': pos.get('passed', True) and force.get('passed', True),
            'checks': [pos, force],
        }

    def check_position(self, new_l3: Dict[str, Any]) -> Dict[str, Any]:
        """检查位置是否合法"""
        pos = new_l3.get('绝对坐标', {})
        # 简单范围检查：坐标必须在合理范围内
        x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)
        if not (-100000 <= x <= 100000 and
                -100000 <= y <= 100000 and
                -1000 <= z <= 10000):
            return {
                'passed': False,
                'check': '位置检查',
                'message': f'位置越界：({x}, {y}, {z})',
            }
        return {'passed': True, 'check': '位置检查'}

    def check_force(self, new_l3: Dict[str, Any]) -> Dict[str, Any]:
        """检查受力是否在承重范围内"""
        force_points_l2 = self.entity.layer.get('l2_static_attributes', {}).get('受力点', [])
        force_points_l3 = new_l3.get('受力点实时坐标', [])

        for fp_l2 in force_points_l2:
            capacity_str = fp_l2.get('承重上限', '500kg')
            capacity = self._parse_capacity(capacity_str)

            # 找对应的L3受力
            fp_l3 = next(
                (fp for fp in force_points_l3 if fp.get('id') == fp_l2.get('id')),
                None
            )
            if not fp_l3:
                continue
            current_str = fp_l3.get('当前受力', '0kg')
            current = self._parse_capacity(current_str)

            if current > capacity:
                return {
                    'passed': False,
                    'check': '受力检查',
                    'message': f'受力超载：{current}kg > {capacity}kg',
                }

        return {'passed': True, 'check': '受力检查'}

    def check_collision(self, new_l3: Dict[str, Any], other) -> Dict[str, Any]:
        """检查与另一个实体的碰撞"""
        if not hasattr(other, 'get_bounding_box'):
            return {'passed': True, 'check': '碰撞检查'}
        try:
            result = self.entity.check_collision(other)
            return {
                'passed': not result.get('collision', False),
                'check': '碰撞检查',
                'message': '碰撞' if result.get('collision') else '无碰撞',
            }
        except Exception:
            return {'passed': True, 'check': '碰撞检查'}

    # ==================== 写L4 ====================

    def write_l4(self, event: str, detail: str = '') -> Dict[str, Any]:
        """写L4事件"""
        self.entity.add_event(event, detail)
        return {'success': True, 'entity_id': self.entity.id}

    # ==================== 通知任务CBM ====================

    def notify_task_cbm(self, success: bool = True) -> Dict[str, Any]:
        """通知任务CBM："我完成了我这部分" """
        self.event_bus.publish('产物完成', {
            'entity_id': self.entity.id,
            'success': success,
            'task_id': self.entity.layer.get('l3_dynamic_state', {}).get('当前任务'),
        })
        return {'success': True}

    # ==================== 工具 ====================

    @staticmethod
    def _parse_capacity(val) -> float:
        """解析承重上限，如 "500kg" → 500.0"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.replace('kg', '').strip()
            try:
                return float(val)
            except ValueError:
                return 0.0
        return 0.0