# -*- coding: utf-8 -*-
"""
项目实体
受 GPL v3.0 保护

定义工程项目。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import project_cbm
from config import config


class ProjectEntity(BaseEntity):
    """项目实体"""

    # 项目状态
    STATUSES = ['立项', '设计', '施工', '验收', '运维']

    def __init__(self, project_name: str = '', project_code: str = '',
                 location: str = '', total_budget: float = 0,
                 duration_days: int = 0, start_date: str = '',
                 end_date: str = '', space: Optional[Dict] = None):
        # L2层
        l2 = {
            '项目名称': project_name,
            '项目编号': project_code,
            '地点': location,
            '总预算': f'¥{total_budget}',
            '工期': f'{duration_days}天',
            '开工日期': start_date,
            '竣工日期': end_date,
        }

        # L3层
        l3 = {
            '状态': '施工',
            '进度': {
                'total': 0,
                'completed': 0,
                'percentage': 0,
            },
        }

        # CBM层
        cbm = project_cbm(project_code, total_budget)

        super().__init__(
            entity_type='项目',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.project_name = project_name
        self.project_code = project_code
        self.location = location
        self.total_budget = total_budget
        self.duration_days = duration_days
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['项目编号'] = project_code

    def get_progress(self) -> Dict[str, Any]:
        """获取项目进度"""
        return self.layer['l3_dynamic_state'].get('进度', {
            'total': 0, 'completed': 0, 'percentage': 0,
        })

    def get_status(self) -> str:
        """获取项目状态"""
        return self.layer['l3_dynamic_state'].get('状态', '施工')

    def update_status(self, status: str) -> Dict[str, Any]:
        """更新状态"""
        if status not in self.STATUSES:
            return {'success': False, 'message': f'无效状态：{status}'}
        self.layer['l3_dynamic_state']['状态'] = status
        self.add_event('状态变化', status)
        return {'success': True, 'status': status}

    def update_progress(self, total: int, completed: int) -> Dict[str, Any]:
        """更新进度"""
        percentage = round(completed / total * 100, 2) if total > 0 else 0
        self.layer['l3_dynamic_state']['进度'] = {
            'total': total,
            'completed': completed,
            'percentage': percentage,
        }
        return {'success': True, 'progress': self.layer['l3_dynamic_state']['进度']}

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '项目',
            'project_name': self.project_name,
            'project_code': self.project_code,
            'status': self.get_status(),
            'progress': self.get_progress(),
            'layer': self.layer,
        }