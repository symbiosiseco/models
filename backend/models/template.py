# -*- coding: utf-8 -*-
"""
模板实体
受 GPL v3.0 保护

定义六层架构的模板（R层）。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import template_cbm
from config import config


class TemplateEntity(BaseEntity):
    """模板实体"""

    # 模板类型
    TEMPLATE_TYPES = ['物品', '人员', '设备', '任务']

    def __init__(self, template_type: str = '物品',
                 template_name: str = '', category: str = '',
                 params: Optional[Dict] = None,
                 anchors: Optional[List[Dict]] = None,
                 force_points: Optional[List[Dict]] = None,
                 contact_faces: Optional[List[Dict]] = None,
                 cbm: Optional[Dict] = None,
                 space: Optional[Dict] = None):
        if template_type not in self.TEMPLATE_TYPES:
            template_type = '物品'
        params = params or {}
        anchors = anchors or []
        force_points = force_points or []
        contact_faces = contact_faces or []

        # L2层
        l2 = {
            '模板类型': template_type,
            '模板名': template_name,
            '类别': category,
            '参数': params,
            '锚点': anchors,
            '受力点': force_points,
            '接触面': contact_faces,
            'CBM规则': cbm or {},
        }

        # L3层
        l3 = {
            '状态': '可用',
        }

        # CBM层
        cbm_layer = template_cbm(template_type, category)

        super().__init__(
            entity_type='模板',
            l2=l2,
            l3=l3,
            cbm=cbm_layer,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.template_type = template_type
        self.template_name = template_name
        self.category = category
        self.params = dict(params)
        self.anchors = list(anchors)
        self.force_points = list(force_points)
        self.contact_faces = list(contact_faces)
        self.cbm_rules = dict(cbm or {})
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['模板ID'] = self.id
        self.layer['r_layer']['模板名'] = template_name
        self.layer['r_layer']['类别'] = category

    # ==================== 查询方法 ====================

    def get_params(self) -> Dict[str, Any]:
        """获取参数"""
        return self.layer['l2_static_attributes'].get('参数', {})

    def get_anchors(self) -> List[Dict[str, Any]]:
        """获取锚点"""
        return self.layer['l2_static_attributes'].get('锚点', [])

    def get_force_points(self) -> List[Dict[str, Any]]:
        """获取受力点"""
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        """获取接触面"""
        return self.layer['l2_static_attributes'].get('接触面', [])

    def get_cbm(self) -> Dict[str, Any]:
        """获取CBM规则"""
        return self.layer['l2_static_attributes'].get('CBM规则', {})

    # ==================== 实例化 ====================

    def instantiate(self, position: Optional[Dict] = None) -> Dict[str, Any]:
        """
        从模板生成实例（L1层）。

        注意：本方法仅生成实体字典，不做全局注册。
        全局注册由 templates/store.py 负责。
        """
        position = position or {'x': 0, 'y': 0, 'z': 0}

        # 从模板复制六层结构
        instance = {
            'r_layer': {
                '类别': self.category,
                '模板ID': self.id,
                '模板名': self.template_name,
                '厂家': self.layer['r_layer'].get('厂家', ''),
            },
            'l1_identity': {
                '唯一ID': f'{self.category}-INST-001',
                '存在锚点': '不可替换',
                '模板ID': self.id,
            },
            'l2_static_attributes': {
                **self.params,
                '锚点': self.anchors,
                '受力点': self.force_points,
                '接触面': self.contact_faces,
            },
            'l3_dynamic_state': {
                '绝对坐标': position,
                '状态': '待装配',
                '受力点实时坐标': [],
            },
            'l4_event_chain': [
                {
                    'time': self._now(),
                    'event': '实例化',
                    'detail': f'从模板 {self.id} 实例化',
                }
            ],
            'cbm_abilities': self.cbm_rules,
        }
        return instance

    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '模板',
            'template_type': self.template_type,
            'template_name': self.template_name,
            'category': self.category,
            'layer': self.layer,
        }