# -*- coding: utf-8 -*-
"""
产品实体
受 GPL v3.0 保护

定义厂家产品。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import product_cbm
from config import config


class ProductEntity(BaseEntity):
    """产品实体"""

    def __init__(self, product_name: str = '',
                 product_code: str = '',
                 manufacturer_id: Optional[str] = None,
                 params: Optional[Dict] = None,
                 anchors: Optional[List[Dict]] = None,
                 force_points: Optional[List[Dict]] = None,
                 contact_faces: Optional[List[Dict]] = None,
                 cbm: Optional[Dict] = None,
                 space: Optional[Dict] = None):
        params = params or {}
        anchors = anchors or []
        force_points = force_points or []
        contact_faces = contact_faces or []

        # L2层
        l2 = {
            '产品名称': product_name,
            '产品编码': product_code,
            '厂家ID': manufacturer_id,
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
        cbm_layer = product_cbm(product_name, product_code)

        super().__init__(
            entity_type='产品',
            l2=l2,
            l3=l3,
            cbm=cbm_layer,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.product_name = product_name
        self.product_code = product_code
        self.manufacturer_id = manufacturer_id
        self.params = dict(params)
        self.anchors = list(anchors)
        self.force_points = list(force_points)
        self.contact_faces = list(contact_faces)
        self.cbm_rules = dict(cbm or {})
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['产品名称'] = product_name
        self.layer['r_layer']['产品编码'] = product_code
        self.layer['r_layer']['厂家ID'] = manufacturer_id

    # ==================== 查询方法 ====================

    def get_params(self) -> Dict[str, Any]:
        """获取产品参数"""
        return self.layer['l2_static_attributes'].get('参数', {})

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
        从产品生成实例。

        注意：本方法仅生成实体字典，不做全局注册。
        """
        position = position or {'x': 0, 'y': 0, 'z': 0}
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        instance = {
            'r_layer': {
                '类别': self.product_name,
                '产品编码': self.product_code,
                '厂家ID': self.manufacturer_id,
                '模板ID': self.id,
            },
            'l1_identity': {
                '唯一ID': f'PROD-INST-{self.id}',
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
                    'time': now,
                    'event': '实例化',
                    'detail': f'从产品 {self.id} 实例化',
                }
            ],
            'cbm_abilities': self.cbm_rules,
        }
        return instance

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '产品',
            'product_name': self.product_name,
            'product_code': self.product_code,
            'manufacturer_id': self.manufacturer_id,
            'layer': self.layer,
        }