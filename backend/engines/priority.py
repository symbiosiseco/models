# -*- coding: utf-8 -*-
"""
优先级引擎
受 GPL v3.0 保护

管道优先级排序。
优先级从 config.PIPE_PRIORITY 读取。
"""

from typing import Dict, Any, List
from config import config


class PriorityEngine:
    """优先级引擎"""

    # 默认优先级（从config读取）
    DEFAULT_PRIORITY = {
        '重力排水管': 1,
        '风管': 2,
        '桥架': 3,
        '消防管': 4,
        '给水管': 5,
    }

    # 优先级名称
    PRIORITY_NAMES = {
        1: '重力排水管',
        2: '风管',
        3: '桥架',
        4: '消防管',
        5: '给水管',
    }

    def __init__(self, config_obj=None):
        self.config = config_obj or config

    # ==================== 优先级查询 ====================

    def get_priority(self, entity) -> int:
        """获取实体优先级"""
        # 优先从 CBM.优先级 读取
        if hasattr(entity, 'layer'):
            cbm = entity.layer.get('cbm_abilities', {})
            if '规范约束' in cbm and '优先级' in cbm['规范约束']:
                return int(cbm['规范约束']['优先级'])

            # 从 L2.系统 读取
            l2 = entity.layer.get('l2_static_attributes', {})
            system = l2.get('系统', '')
            priority = self.get_pipe_priority(system)
            if priority:
                return priority

        # 从实体类型读取
        etype = getattr(entity, 'entity_type', '')
        return self.get_pipe_priority(etype)

    def get_pipe_priority(self, pipe_type: str) -> int:
        """获取管道类型优先级"""
        priority_map = getattr(self.config, 'PIPE_PRIORITY', self.DEFAULT_PRIORITY)
        for key, p in priority_map.items():
            if key in pipe_type:
                return p
        return 5

    def get_all_priorities(self) -> Dict[str, int]:
        """获取所有优先级"""
        return dict(getattr(self.config, 'PIPE_PRIORITY', self.DEFAULT_PRIORITY))

    # ==================== 排序 ====================

    def sort_by_priority(self, entities: List) -> List:
        """按优先级排序"""
        return sorted(entities, key=lambda e: (self.get_priority(e), getattr(e, 'id', '')))

    # ==================== 冲突解决 ====================

    def resolve_conflict(self, e1, e2) -> Dict[str, Any]:
        """冲突解决"""
        p1 = self.get_priority(e1)
        p2 = self.get_priority(e2)

        # 数字小的胜出
        if p1 <= p2:
            winner, loser = e1, e2
            wp, lp = p1, p2
        else:
            winner, loser = e2, e1
            wp, lp = p2, p1

        return {
            'winner': getattr(winner, 'id', None),
            'winner_priority': wp,
            'loser': getattr(loser, 'id', None),
            'loser_priority': lp,
            'reason': f'优先级 {wp} 优于 {lp}',
        }

    # ==================== 优先级名称 ====================

    def get_priority_name(self, priority: int) -> str:
        """获取优先级名称"""
        return self.PRIORITY_NAMES.get(priority, '未知')

    # ==================== 综合支架校验 ====================

    def can_join_composite_support(self, entity) -> Dict[str, Any]:
        """检查实体能否放入综合支架"""
        priority = self.get_priority(entity)
        etype = getattr(entity, 'entity_type', '')
        system = entity.layer.get('l2_static_attributes', {}).get('系统', '') if hasattr(entity, 'layer') else ''

        if '重力排水' in etype or '重力排水' in system:
            return {
                'allowed': False,
                'reason': '重力排水管不能放入综合支架（坡度要求）',
            }
        return {'allowed': True}