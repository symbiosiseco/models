# -*- coding: utf-8 -*-
"""
人的状态扩展
受 GPL v3.0 保护

定义人的L3多维度状态：心态/体力/活动范围/情绪。
物是"死的"，人是"活的"。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity


class WorkerStateEntity(BaseEntity):
    """人的状态扩展实体"""

    # 体力下限
    STAMINA_THRESHOLD = 60

    def __init__(self, worker_id: str = '', status: str = '空闲',
                 current_task: Optional[str] = None, mentality: str = '正常',
                 stamina: str = '100%', activity_area: Optional[Dict] = None,
                 work_hours: Optional[Dict] = None, skill_status: str = '熟练',
                 emotion: str = '平静', space: Optional[Dict] = None):
        # L3层：人的多维度状态
        l3 = {
            '状态': status,
            '当前任务': current_task,
            '心态': mentality,
            '体力': stamina,
            '活动范围': activity_area or {
                '类型': '多边形',
                '区域': '默认全区',
                '边界': [],
            },
            '工作时段': work_hours or {'开始': '08:00', '结束': '18:00'},
            '技能状态': skill_status,
            '情绪': emotion,
        }

        super().__init__(
            entity_type='人员',
            l3=l3,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.worker_id = worker_id
        self.status = status
        self.current_task = current_task
        self.mentality = mentality
        self.stamina = stamina

    def update_state(self, key: str, value: Any) -> Dict[str, Any]:
        """更新任意状态属性"""
        self.layer['l3_dynamic_state'][key] = value
        # 同步私有字段
        if hasattr(self, key):
            setattr(self, key, value)
        return {'success': True, 'key': key, 'value': value}

    def check_stamina(self) -> bool:
        """检查体力是否够（≥60%）"""
        try:
            stamina = float(str(self.layer['l3_dynamic_state'].get('体力', '100%')).replace('%', ''))
            return stamina >= self.STAMINA_THRESHOLD
        except (ValueError, TypeError):
            return True

    def check_skill(self, task_type: str) -> bool:
        """检查技能是否匹配任务"""
        skill_status = self.layer['l3_dynamic_state'].get('技能状态', '熟练')
        # 简化：只要不是"生疏"就通过
        return skill_status != '生疏'

    def is_available(self) -> bool:
        """检查是否空闲"""
        status = self.layer['l3_dynamic_state'].get('状态', '空闲')
        return status in ('空闲', 'idle')

    def get_activity_area(self) -> Dict[str, Any]:
        """获取活动范围"""
        return self.layer['l3_dynamic_state'].get('活动范围', {})

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '人员状态',
            'worker_id': self.worker_id,
            'status': self.status,
            'current_task': self.current_task,
            'mentality': self.mentality,
            'stamina': self.stamina,
            'layer': self.layer,
        }