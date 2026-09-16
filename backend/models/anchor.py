# -*- coding: utf-8 -*-
"""
锚点实体
受 GPL v3.0 保护

锚点是"物理孔洞"的数字生命体。
可以是膨胀螺栓孔、法兰螺栓孔、焊接孔等。

A-2 新增：万物皆数字生命体
- 锚点有独立六层
- 有独立生命周期（未打孔/已打孔/已装螺栓）
- 有独立 CBM 规则
- 有独立 L4 履历

★ 本类不继承 BaseEntity，完全自包含，避免依赖复杂。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard
from config import config


class AnchorEntity:
    """锚点实体（物理孔洞）"""

    # 类变量：锚点计数器
    _anchor_counter = 0

    def __init__(self, anchor_type: str = 'M12_膨胀螺栓孔',
                 owner_id: Optional[str] = None,
                 position: Optional[Dict] = None,
                 space: Optional[Dict] = None):
        """
        参数：
            anchor_type: 锚点类型（从 anchors.json 里查）
            owner_id: 所属实体ID（如 SUP-001）
            position: 绝对坐标
            space: 空间定位
        """
        # 从标准库读参数
        spec = read_standard('anchors', anchor_type)
        position = position or {'x': 0, 'y': 0, 'z': 0}

        # 提取参数
        hole_d = spec.get('孔径', 12)
        depth = spec.get('深度', 80)
        tool = spec.get('打孔工具', '电锤')
        drill_time = spec.get('打孔时间', 5)
        tolerance = spec.get('允许偏差', 5)
        purpose = spec.get('用途', '穿M12膨胀螺栓')
        standard = spec.get('标准', 'GB/T 5782')

        # 生成唯一 ID
        AnchorEntity._anchor_counter += 1
        self.id = f'ANCHOR-{AnchorEntity._anchor_counter:03d}'

        # 手动构造六层
        self.layer = {
            'r_layer': {
                '类别': '锚点',
                '规格': anchor_type,
                '子类型': spec.get('锚点类型', '膨胀螺栓孔'),
            },
            'l1_identity': {
                '唯一ID': self.id,
                '存在锚点': '不可替换',
                '模板ID': f'TPL-{anchor_type}',
            },
            'l2_static_attributes': {
                '锚点类型': spec.get('锚点类型', '膨胀螺栓孔'),
                '孔径': f'{hole_d}mm',
                '深度': f'{depth}mm',
                '用途': purpose,
                '打孔工具': tool,
                '打孔时间': f'{drill_time}min',
                '允许偏差': f'±{tolerance}mm',
                '属于': owner_id,
                '受力点': [
                    {
                        'id': 'fp_center',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '类型': '孔中心',
                        '方向': 'Z-',
                        '传力对象': '螺栓',
                        '承重上限': '200kg',
                    }
                ],
                '接触面': [
                    {
                        'id': 'cf_hole_wall',
                        '类型': '孔壁',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'Z+',
                        '接触对象类型': ['膨胀螺栓'],
                        '允许偏差': '0mm',
                        '必须包含': [],
                        '违反后果': '螺栓松动',
                        '装配顺序': 1,
                    }
                ],
                '包围盒': {'x': hole_d, 'y': hole_d, 'z': depth},
            },
            'l3_dynamic_state': {
                '绝对坐标': position,
                '状态': '未打孔',
                '打孔时间': None,
                '打孔人': None,
                '安装的螺栓ID': None,
                '受力点实时坐标': [],
            },
            'l4_event_chain': [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event': '创建',
                    'detail': f'锚点创建，属于 {owner_id}',
                }
            ],
            'cbm_abilities': {
                '物理规则': {
                    '包围盒': {'x': hole_d, 'y': hole_d, 'z': depth},
                    '最小间距': 30,
                    '允许接触': ['膨胀螺栓'],
                    '禁止穿透': True,
                    '接触方式': '孔壁接触',
                },
                '受力规则': {
                    '自重': '0kg',
                    '受力点': {'x': 0, 'y': 0, 'z': 0},
                    '传力路径': ['螺栓预紧力 → 孔壁 → 楼板'],
                    '承重上限': '200kg',
                },
                '装配规则': {
                    '连接对象': ['膨胀螺栓'],
                    '拧紧力矩': '20N·m',
                    '装配顺序': ['打孔', '装膨胀螺栓'],
                    '密封等级': '无',
                },
                '规范约束': {
                    '安装规范': standard,
                    '孔径要求': f'{hole_d}mm',
                    '深度要求': f'{depth}mm',
                    '打孔工具': tool,
                    '允许偏差': f'±{tolerance}mm',
                    '前置条件': '支架已定位',
                },
            },
        }

        self.entity_type = '锚点'
        self.anchor_type = anchor_type
        self.owner_id = owner_id
        self.space = space or config.SPACE_UNITS

    # ==================== 通用方法（模仿 BaseEntity 接口）====================

    def get_position(self) -> Dict[str, float]:
        return self.layer['l3_dynamic_state'].get('绝对坐标', {'x': 0, 'y': 0, 'z': 0})

    def get_attr(self, key: str, default: Any = None) -> Any:
        return self.layer['l2_static_attributes'].get(key, default)

    def get_status(self, key: str, default: Any = None) -> Any:
        return self.layer['l3_dynamic_state'].get(key, default)

    def get_bounding_box(self) -> Dict[str, float]:
        return self.layer['l2_static_attributes'].get('包围盒', {'x': 0, 'y': 0, 'z': 0})

    def get_force_points(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        return self.layer['l2_static_attributes'].get('接触面', [])

    def add_event(self, event: str, detail: str = '') -> Dict[str, Any]:
        self.layer['l4_event_chain'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event': event,
            'detail': detail,
        })
        return {'success': True}

    def update_status(self, key: str, value: Any) -> Dict[str, Any]:
        self.layer['l3_dynamic_state'][key] = value
        return {'success': True}

    def move_to(self, x: float, y: float, z: float) -> Dict[str, Any]:
        self.layer['l3_dynamic_state']['绝对坐标'] = {'x': x, 'y': y, 'z': z}
        return {'success': True}

    def check_collision(self, other) -> Dict[str, Any]:
        b1 = self.get_bounding_box()
        b2 = other.get_bounding_box() if hasattr(other, 'get_bounding_box') else {'x': 0, 'y': 0, 'z': 0}
        p1 = self.get_position()
        p2 = other.get_position() if hasattr(other, 'get_position') else {'x': 0, 'y': 0, 'z': 0}
        dx = abs(p1['x'] - p2['x'])
        dy = abs(p1['y'] - p2['y'])
        dz = abs(p1['z'] - p2['z'])
        overlap = (
            dx < (b1['x'] + b2['x']) / 2 and
            dy < (b1['y'] + b2['y']) / 2 and
            dz < (b1['z'] + b2['z']) / 2
        )
        return {'collision': overlap, 'distance': {'dx': dx, 'dy': dy, 'dz': dz}}

    # ==================== 锚点专属操作 ====================

    def drill(self, operator: str = '') -> Dict[str, Any]:
        """打孔"""
        if self.layer['l3_dynamic_state']['状态'] != '未打孔':
            return {'success': False, 'message': '已打孔或状态不对'}

        self.layer['l3_dynamic_state']['状态'] = '已打孔'
        self.layer['l3_dynamic_state']['打孔时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.layer['l3_dynamic_state']['打孔人'] = operator
        self.add_event('打孔完成', f'操作人：{operator}')

        return {'success': True, 'anchor_id': self.id}

    def install_bolt(self, bolt_id: str) -> Dict[str, Any]:
        """装膨胀螺栓"""
        if self.layer['l3_dynamic_state']['状态'] != '已打孔':
            return {'success': False, 'message': '必须先打孔'}

        self.layer['l3_dynamic_state']['状态'] = '已装螺栓'
        self.layer['l3_dynamic_state']['安装的螺栓ID'] = bolt_id
        self.add_event('装膨胀螺栓', f'螺栓ID：{bolt_id}')

        return {'success': True, 'anchor_id': self.id, 'bolt_id': bolt_id}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '锚点',
            'anchor_type': self.anchor_type,
            'owner_id': self.owner_id,
            'layer': self.layer,
        }