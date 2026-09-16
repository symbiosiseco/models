# -*- coding: utf-8 -*-
"""
厂家实体
受 GPL v3.0 保护

定义产品生产厂家。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import manufacturer_cbm
from config import config


class ManufacturerEntity(BaseEntity):
    """厂家实体"""

    # 已知厂家（用于校验）
    KNOWN_MANUFACTURERS = [
        '苏州纽威', '上海冠龙', '广东永泉',
        '天津塘沽', '成都成高', '浙江盾安',
    ]

    def __init__(self, manufacturer_name: str = '',
                 contact: str = '', phone: str = '',
                 address: str = '',
                 products: Optional[List[str]] = None,
                 space: Optional[Dict] = None):
        products = products or []

        # L2层
        l2 = {
            '厂家名称': manufacturer_name,
            '联系人': contact,
            '电话': phone,
            '地址': address,
            '产品列表': products,
        }

        # L3层
        l3 = {
            '状态': '正常',
        }

        # CBM层
        cbm = manufacturer_cbm(manufacturer_name)

        super().__init__(
            entity_type='厂家',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.manufacturer_name = manufacturer_name
        self.contact = contact
        self.phone = phone
        self.address = address
        self.products = list(products)
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['厂家'] = manufacturer_name

    def get_products(self) -> List[str]:
        """获取该厂家的所有产品"""
        return self.layer['l2_static_attributes'].get('产品列表', [])

    def add_product(self, product_id: str) -> Dict[str, Any]:
        """添加产品"""
        if product_id not in self.products:
            self.products.append(product_id)
            self.layer['l2_static_attributes']['产品列表'].append(product_id)
            self.add_event('新增产品', product_id)
        return {'success': True, 'product_id': product_id, 'total': len(self.products)}

    def get_contact(self) -> Dict[str, Any]:
        """获取联系方式"""
        return {
            'manufacturer': self.manufacturer_name,
            'contact': self.contact,
            'phone': self.phone,
            'address': self.address,
        }

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '厂家',
            'manufacturer_name': self.manufacturer_name,
            'contact': self.contact,
            'phone': self.phone,
            'address': self.address,
            'products': self.products,
            'layer': self.layer,
        }