# -*- coding: utf-8 -*-
"""
实测实量引擎
受 GPL v3.0 保护

现场测量→数据录入→支架调节。
写L4影响CBM决策。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class MeasurementEngine:
    """实测实量引擎"""

    # 偏差阈值（mm）
    THRESHOLD = 5.0

    # 测量类型→设计值默认
    DESIGN_DEFAULTS = {
        '楼板高度': 3000,
        '支架高度': 2500,
        '管道坡度': 0.5,
        '垂直度': 90,
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.records: List[Dict[str, Any]] = []
        self.counter = 0

    # ==================== 记录测量 ====================

    def record_measurement(self, target_id: str, measure_type: str,
                            value: float) -> Dict[str, Any]:
        """
        记录测量数据。

        流程：
            1. 计算偏差
            2. 检查阈值
            3. 写L4
            4. 通过事件总线发布
        """
        design_value = self.DESIGN_DEFAULTS.get(measure_type, 0)
        deviation = self.calculate_deviation(design_value, value)
        qualified = self.check_threshold(deviation)

        self.counter += 1
        record_id = f'MEAS-{self.counter:04d}'

        record = {
            'record_id': record_id,
            'target_id': target_id,
            'measure_type': measure_type,
            'design_value': design_value,
            'actual_value': value,
            'deviation': deviation,
            'qualified': qualified,
            'measured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.records.append(record)

        # 写L4
        self._update_l4(target_id, '实测记录', f'{measure_type} 偏差{deviation:+}mm')

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('实测记录', {
                'record_id': record_id,
                'target_id': target_id,
                'measure_type': measure_type,
                'deviation': deviation,
                'qualified': qualified,
            })

        return {
            'success': True,
            'record_id': record_id,
            'deviation': deviation,
            'qualified': qualified,
        }

    # ==================== 偏差计算 ====================

    def calculate_deviation(self, design_value: float, actual_value: float) -> float:
        """计算偏差"""
        return round(actual_value - design_value, 2)

    def check_threshold(self, deviation: float) -> bool:
        """检查是否超阈值"""
        return abs(deviation) <= self.THRESHOLD

    # ==================== 支架调节 ====================

    def adjust_support(self, support_id: str, adjust_value: float) -> Dict[str, Any]:
        """
        调节支架。

        流程：
            1. 读取支架当前高度
            2. 计算新高度
            3. 更新支架 L3
            4. 写L4
        """
        # 简化：直接返回调节结果
        new_height = 2500 + adjust_value

        # 写L4
        self._update_l4(support_id, '支架调节', f'{adjust_value:+}mm，新高度{new_height}mm')

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('支架调节', {
                'support_id': support_id,
                'adjust_value': adjust_value,
                'new_height': new_height,
            })

        return {
            'success': True,
            'support_id': support_id,
            'new_height': new_height,
        }

    # ==================== 查询 ====================

    def get_records(self, target_id: str) -> List[Dict[str, Any]]:
        """获取测量记录"""
        return [r for r in self.records if r['target_id'] == target_id]

    def get_deviations(self, target_id: str) -> List[Dict[str, Any]]:
        """获取所有偏差"""
        return [
            {'record_id': r['record_id'], 'deviation': r['deviation']}
            for r in self.records if r['target_id'] == target_id
        ]

    def get_summary(self, entities: List) -> Dict[str, Any]:
        """获取实测实量摘要"""
        total = len(self.records)
        qualified = len([r for r in self.records if r['qualified']])
        unqualified = total - qualified

        by_type: Dict[str, Dict[str, int]] = {}
        for r in self.records:
            mtype = r['measure_type']
            if mtype not in by_type:
                by_type[mtype] = {'total': 0, 'qualified': 0}
            by_type[mtype]['total'] += 1
            if r['qualified']:
                by_type[mtype]['qualified'] += 1

        return {
            'total': total,
            'qualified': qualified,
            'unqualified': unqualified,
            'by_type': by_type,
        }

    # ==================== 内部方法 ====================

    def _update_l4(self, target_id: str, event: str, detail: str):
        """写L4（简化）"""
        # 真实场景会写入目标实体的L4
        pass

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}