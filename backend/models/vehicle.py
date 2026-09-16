# -*- coding: utf-8 -*-
"""
车辆实体
受 GPL v3.0 保护

定义运输车辆。
"""

from typing import Dict, Any, Optional
from .entity import BaseEntity
from .physics_rules import vehicle_cbm
from config import config


class VehicleEntity(BaseEntity):
    """车辆实体"""

    # 车型规格
    VEHICLE_SPECS = {
        '货车':  {'capacity': '3吨', 'speed': '80km/h'},
        '叉车':  {'capacity': '1吨', 'speed': '20km/h'},
        '吊车':  {'capacity': '10吨', 'speed': '60km/h'},
    }

    def __init__(self, plate_number: str = '', vehicle_type: str = '货车',
                 capacity: str = '', driver: Optional[str] = None,
                 space: Optional[Dict] = None):
        if vehicle_type not in self.VEHICLE_SPECS:
            vehicle_type = '货车'
        spec = self.VEHICLE_SPECS[vehicle_type]
        capacity = capacity or spec['capacity']

        # L2层
        l2 = {
            '车牌号': plate_number,
            '车型': vehicle_type,
            '载重': capacity,
            '司机': driver,
            '最高速度': spec['speed'],
            '可运输货物': ['管道', '支架', '阀门', '卡箍', '其他物料'],
        }

        # L3层
        l3 = {
            '状态': '空闲',
            '绝对坐标': space or {'x': 0, 'y': 0, 'z': 0},
        }

        # CBM层
        cbm = vehicle_cbm(vehicle_type, capacity)

        super().__init__(
            entity_type='车辆',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.plate_number = plate_number
        self.vehicle_type = vehicle_type
        self.capacity = capacity
        self.driver = driver
        self.space = space or config.SPACE_UNITS

    def check_capacity(self, load_weight: str) -> bool:
        """检查载重是否超限"""
        try:
            load = self._parse_ton(load_weight)
            cap = self._parse_ton(self.capacity)
            return load <= cap
        except (ValueError, TypeError):
            return True

    def update_location(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """更新位置"""
        self.layer['l3_dynamic_state']['绝对坐标'] = {'x': x, 'y': y, 'z': z}
        return {'success': True}

    def get_status(self) -> str:
        """获取状态"""
        return self.layer['l3_dynamic_state'].get('状态', '空闲')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '车辆',
            'plate_number': self.plate_number,
            'vehicle_type': self.vehicle_type,
            'capacity': self.capacity,
            'layer': self.layer,
        }

    @staticmethod
    def _parse_ton(val: str) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('吨', '').strip())
        return 0.0