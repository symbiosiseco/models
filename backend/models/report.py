# -*- coding: utf-8 -*-
"""
报表实体
受 GPL v3.0 保护

定义工程报表。从L2/L3/L4自动衍生。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import report_cbm
from config import config


class ReportEntity(BaseEntity):
    """报表实体"""

    # 8种报表类型
    REPORT_TYPES = [
        '工程量清单',
        '进度款申请',
        '验收记录',
        '变更台账',
        '材料台账',
        '质量记录',
        '竣工图',
        '签证单',
    ]

    # 导出格式
    EXPORT_FORMATS = ['excel', 'pdf', 'json']

    def __init__(self, report_type: str = '工程量清单',
                 report_name: str = '',
                 content: Optional[Dict] = None,
                 generated_time: str = '',
                 source_data: Optional[Dict] = None,
                 space: Optional[Dict] = None):
        if report_type not in self.REPORT_TYPES:
            report_type = '工程量清单'
        generated_time = generated_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # L2层
        l2 = {
            '报表类型': report_type,
            '报表名': report_name or report_type,
            '内容': content or {},
            '生成时间': generated_time,
            '数据来源': source_data or {},
        }

        # L3层
        l3 = {
            '状态': '已生成',
        }

        # CBM层
        cbm = report_cbm(report_type)

        super().__init__(
            entity_type='报表',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.report_type = report_type
        self.report_name = report_name or report_type
        self.content = dict(content or {})
        self.generated_time = generated_time
        self.source_data = dict(source_data or {})
        self.space = space or config.SPACE_UNITS

    # ==================== 生成/导出 ====================

    def generate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """生成报表"""
        self.layer['l2_static_attributes']['内容'] = content
        self.layer['l2_static_attributes']['生成时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.content = content
        self.add_event('生成报表', f'{self.report_type}')
        return {'success': True, 'report_id': self.id}

    def export(self, format: str = 'excel') -> Dict[str, Any]:
        """导出报表"""
        if format not in self.EXPORT_FORMATS:
            return {'success': False, 'message': f'不支持的导出格式：{format}'}
        return {
            'success': True,
            'report_id': self.id,
            'format': format,
            'file_path': f'/tmp/{self.report_type}.{format}',
        }

    def get_content(self) -> Dict[str, Any]:
        """获取报表内容"""
        return self.layer['l2_static_attributes'].get('内容', {})

    # ==================== 从实体衍生 ====================

    @staticmethod
    def derive_from_entities(entities: List[Any], report_type: str = '工程量清单') -> Dict[str, Any]:
        """
        从实体L2/L3/L4自动衍生报表。

        按 entity_type 分组汇总。
        """
        groups: Dict[str, List[Any]] = {}
        for e in entities:
            e_type = getattr(e, 'entity_type', '未知')
            groups.setdefault(e_type, []).append(e)

        items = []
        total = 0.0
        unit_price_map = {
            '管道': 850, '支架': 120, '阀门': 680,
            '卡箍': 85, '套管': 200, '法兰': 120,
            '螺栓': 5, '垫片': 8,
        }

        for e_type, lst in groups.items():
            unit_price = unit_price_map.get(e_type, 0)
            count = len(lst)
            amount = count * unit_price
            total += amount
            items.append({
                'category': e_type,
                'count': count,
                'unit_price': unit_price,
                'amount': amount,
            })

        return {
            'report_type': report_type,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': items,
            'total': total,
        }

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '报表',
            'report_type': self.report_type,
            'report_name': self.report_name,
            'generated_time': self.generated_time,
            'layer': self.layer,
        }