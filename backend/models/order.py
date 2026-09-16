# -*- coding: utf-8 -*-
"""
订单实体
受 GPL v3.0 保护

定义采购订单。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import order_cbm
from config import config


class OrderEntity(BaseEntity):
    """订单实体"""

    # 订单类型
    ORDER_TYPES = ['采购', '退货']

    # 订单状态
    STATUSES = ['待确认', '已确认', '已发货', '已到货']

    def __init__(self, order_type: str = '采购',
                 supplier_id: Optional[str] = None,
                 materials: Optional[List] = None,
                 total_amount: float = 0, order_date: str = '',
                 space: Optional[Dict] = None):
        if order_type not in self.ORDER_TYPES:
            order_type = '采购'
        materials = materials or []

        # L2层
        l2 = {
            '订单类型': order_type,
            '供应商': supplier_id,
            '物料清单': materials,
            '总金额': f'¥{total_amount}',
            '下单日期': order_date,
        }

        # L3层
        l3 = {
            '状态': '待确认',
        }

        # CBM层
        cbm = order_cbm(order_type, supplier_id)

        super().__init__(
            entity_type='订单',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.order_type = order_type
        self.supplier_id = supplier_id
        self.materials = list(materials)
        self.total_amount = total_amount
        self.order_date = order_date
        self.space = space or config.SPACE_UNITS

    def confirm(self) -> Dict[str, Any]:
        """确认订单"""
        self.layer['l3_dynamic_state']['状态'] = '已确认'
        self.add_event('确认订单', '')
        return {'success': True, 'order_id': self.id, 'status': '已确认'}

    def ship(self) -> Dict[str, Any]:
        """发货"""
        self.layer['l3_dynamic_state']['状态'] = '已发货'
        self.add_event('发货', '')
        return {'success': True, 'order_id': self.id, 'status': '已发货'}

    def receive(self) -> Dict[str, Any]:
        """收货"""
        self.layer['l3_dynamic_state']['状态'] = '已到货'
        self.add_event('收货', '')
        return {'success': True, 'order_id': self.id, 'status': '已到货'}

    def get_status(self) -> str:
        """获取订单状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待确认')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '订单',
            'order_type': self.order_type,
            'supplier_id': self.supplier_id,
            'materials': self.materials,
            'total_amount': self.total_amount,
            'status': self.get_status(),
            'layer': self.layer,
        }