# -*- coding: utf-8 -*-
"""
图纸实体
受 GPL v3.0 保护

定义设计图纸。
"""

from typing import Dict, Any, Optional, List
from .entity import BaseEntity
from .physics_rules import drawing_cbm
from config import config


class DrawingEntity(BaseEntity):
    """图纸实体"""

    # 专业
    DISCIPLINES = ['消防', '给排水', '通风', '电气']

    # 图纸类型
    DRAWING_TYPES = ['平面图', '系统图', '详图']

    # 状态
    STATUSES = ['设计中', '已出图', '已会审', '已交底']

    def __init__(self, drawing_name: str = '', discipline: str = '消防',
                 drawing_type: str = '平面图', version: str = 'v1.0',
                 designer: str = '', project_id: Optional[str] = None,
                 space: Optional[Dict] = None):
        if discipline not in self.DISCIPLINES:
            discipline = '消防'
        if drawing_type not in self.DRAWING_TYPES:
            drawing_type = '平面图'

        # L2层
        l2 = {
            '图纸名称': drawing_name,
            '专业': discipline,
            '图纸类型': drawing_type,
            '版本': version,
            '设计人': designer,
            '关联项目': project_id,
        }

        # L3层
        l3 = {
            '状态': '设计中',
            '出图日期': None,
            '会审日期': None,
            '会审意见': [],
        }

        # CBM层
        cbm = drawing_cbm(discipline, version)

        super().__init__(
            entity_type='图纸',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.drawing_name = drawing_name
        self.discipline = discipline
        self.drawing_type = drawing_type
        self.version = version
        self.designer = designer
        self.project_id = project_id
        self.space = space or config.SPACE_UNITS

    def issue(self, date: str) -> Dict[str, Any]:
        """出图"""
        self.layer['l3_dynamic_state']['状态'] = '已出图'
        self.layer['l3_dynamic_state']['出图日期'] = date
        self.add_event('出图', date)
        return {'success': True, 'date': date}

    def review(self, date: str, comments: str = '') -> Dict[str, Any]:
        """会审"""
        self.layer['l3_dynamic_state']['状态'] = '已会审'
        self.layer['l3_dynamic_state']['会审日期'] = date
        self.layer['l3_dynamic_state']['会审意见'].append({
            'date': date,
            'comments': comments,
        })
        self.add_event('会审', f'{date}：{comments}')
        return {'success': True, 'date': date}

    def get_status(self) -> str:
        """获取图纸状态"""
        return self.layer['l3_dynamic_state'].get('状态', '设计中')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '图纸',
            'drawing_name': self.drawing_name,
            'discipline': self.discipline,
            'drawing_type': self.drawing_type,
            'version': self.version,
            'status': self.get_status(),
            'layer': self.layer,
        }