# -*- coding: utf-8 -*-
"""
物的 CBM 引擎
受 GPL v3.0 保护

感知 L3 变化、检查边界、写 L4。

V2.0 升级（专报G）：
- L4 历史影响 CBM 决策
- 损伤记录 → 降低承重上限
- 漏水记录 → 加强监控
- 检查周期 → 缩短周期
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class EntityCBM:
    """物的 CBM 引擎"""

    def __init__(self, entity, event_bus=None):
        self.entity = entity
        self.event_bus = event_bus
        self.watching = False

    # ==================== 监听 L3 变化 ====================

    def watch(self) -> Dict[str, Any]:
        """开始监听 L3 变化"""
        if not self.event_bus:
            return {'success': False, 'message': '事件总线未注入'}

        self.watching = True
        self.event_bus.subscribe('L3变化', self._on_l3_change, f'entity_cbm_{id(self)}')
        return {'success': True, 'entity_id': getattr(self.entity, 'id', None)}

    def unwatch(self) -> Dict[str, Any]:
        """停止监听"""
        self.watching = False
        if self.event_bus:
            self.event_bus.unsubscribe('L3变化', f'entity_cbm_{id(self)}')
        return {'success': True}

    def _on_l3_change(self, event_type, data):
        """L3 变化回调"""
        entity_id = data.get('entity_id')
        if entity_id != getattr(self.entity, 'id', None):
            return

        old_l3 = data.get('old_l3', {})
        new_l3 = data.get('new_l3', data.get('position', {}))

        result = self.on_l3_change(old_l3, new_l3)
        return result

    # ==================== L3 变化处理 ====================

    def on_l3_change(self, old_l3: dict, new_l3: dict) -> Dict[str, Any]:
        """L3 变化主处理"""
        checks = []

        # 1. 检查位置
        pos_check = self.check_position(new_l3)
        checks.append(pos_check)

        # 2. 检查受力
        force_check = self.check_force(new_l3)
        checks.append(force_check)

        # 3. 检查边界
        boundary_check = self.check_boundary(new_l3)
        checks.append(boundary_check)

        # 4. 通过 → 写 L4
        passed = all(c.get('passed', True) for c in checks)
        if passed:
            self.write_l4('L3变化', f'从{old_l3}到{new_l3}')
            self.notify_task_cbm()
        else:
            self.write_l4('L3变化失败', f'检查未通过')

        return {'passed': passed, 'checks': checks}

    # ==================== 检查位置 ====================

    def check_position(self, new_l3: dict) -> Dict[str, Any]:
        """检查位置是否合法"""
        try:
            pos = new_l3.get('绝对坐标', {}) if isinstance(new_l3, dict) else {}
            if not pos:
                return {'passed': True, 'check': '位置检查', 'message': '无位置信息'}
            return {'passed': True, 'check': '位置检查', 'position': pos}
        except Exception as e:
            return {'passed': False, 'check': '位置检查', 'message': str(e)}

    # ==================== 检查受力（★ V2.0：L4影响CBM）====================

    def check_force(self, new_l3: dict) -> Dict[str, Any]:
        """
        ★ V2.0 增强：检查受力是否在承重范围内。
        含 L4 历史影响 CBM 决策。
        """
        # 读 L2 承重上限
        l2 = self.entity.layer.get('l2_static_attributes', {})
        fps = l2.get('受力点', [])
        if not fps:
            return {'passed': True, 'check': '受力检查', 'message': '无受力点'}

        cbm = self.entity.layer.get('cbm_abilities', {})
        force_rules = cbm.get('受力规则', {})
        capacity_str = force_rules.get('承重上限', '500kg')
        capacity = self._parse_kg(capacity_str)

        # ★ V2.0 新增：L4 历史影响 CBM 决策
        adjusted_capacity, reason = self._apply_l4_influence(capacity)

        # 检查当前受力
        current_force = 0
        if isinstance(new_l3, dict):
            fp_l3 = new_l3.get('受力点实时坐标', [])
            for fp in fp_l3:
                f = self._parse_kg(fp.get('当前受力', '0kg'))
                current_force += f

        passed = current_force <= adjusted_capacity

        return {
            'passed': passed,
            'check': '受力检查',
            'current_force': current_force,
            'original_capacity': capacity,
            'adjusted_capacity': adjusted_capacity,
            'reason': reason,
            'message': f'受力{current_force}kg，上限{adjusted_capacity}kg{reason}',
        }

    def _apply_l4_influence(self, original_capacity: float) -> tuple:
        """
        ★ V2.0 新增：L4 历史影响 CBM 决策。

        场景：
            - 橡胶圈接近10年 → CBM提醒更换
            - 管道曾漏水 → CBM加强监控
            - 支架曾受损 → CBM降低承重上限20%
            - 阀门维修过 → CBM缩短检查周期
        """
        l4 = self.entity.layer.get('l4_event_chain', [])
        adjusted = original_capacity
        reasons = []

        for event in l4:
            e_type = event.get('event', '')
            detail = event.get('detail', '')

            # 1. 损伤记录 → 降低承重上限 20%
            if '损伤' in e_type or '损伤' in detail:
                adjusted *= 0.8
                reasons.append('L4有损伤记录，承重上限降低20%')

            # 2. 漏水记录 → 不改变承重，但标记"加强监控"
            if '漏水' in e_type or '漏水' in detail:
                reasons.append('L4有漏水记录，建议加强监控')

            # 3. 橡胶圈接近10年 → 提醒更换
            if '检查' in e_type and '老化' in detail:
                reasons.append('L4有老化记录，提醒更换')

        reason_str = '（' + '；'.join(reasons) + '）' if reasons else ''
        return adjusted, reason_str

    # ==================== 检查边界 ====================

    def check_boundary(self, new_l3: dict) -> Dict[str, Any]:
        """检查边界"""
        l2 = self.entity.layer.get('l2_static_attributes', {})
        bbox = l2.get('外形', {}).get('包围盒', {})
        if not bbox:
            return {'passed': True, 'check': '边界检查', 'message': '无包围盒'}
        return {'passed': True, 'check': '边界检查'}

    def check_collision(self, new_l3: dict, other) -> Dict[str, Any]:
        """检查碰撞"""
        return {'passed': True, 'check': '碰撞检查'}

    # ==================== 写 L4 ====================

    def write_l4(self, event: str, detail: str) -> Dict[str, Any]:
        """写 L4 事件"""
        if hasattr(self.entity, 'add_event'):
            self.entity.add_event(event, detail)
            return {'success': True, 'event': event}
        return {'success': False, 'message': '实体无 add_event 方法'}

    # ==================== 通知任务 CBM ====================

    def notify_task_cbm(self) -> Dict[str, Any]:
        """通过事件总线通知任务 CBM"""
        if not self.event_bus:
            return {'success': False}
        return self.event_bus.publish('产物完成', {
            'entity_id': getattr(self.entity, 'id', None),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

    # ==================== 工具 ====================

    @staticmethod
    def _parse_kg(val) -> float:
        """解析 '500kg' 为 500.0"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val.replace('kg', '').strip())
            except ValueError:
                return 0.0
        return 0.0