# -*- coding: utf-8 -*-
"""
动作实体
受 GPL v3.0 保护

动作是"施工动作"的数字生命体。
例如：打孔、装膨胀螺栓、上支架、锁紧、放管道、装卡箍……

A-3 新增：动作也是数字生命体
- 从 actions.json 标准库读取
- 有完整六层
- 有生命周期（待执行/执行中/已完成/已失败）
- 有前置条件检查
- 有独立 L4 履历
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard
from config import config


class ActionEntity:
    """动作实体（施工动作）"""

    _action_counter = 0

    def __init__(self, action_type: str = '打孔',
                 task_id: Optional[str] = None,
                 target_id: Optional[str] = None,
                 sequence: int = 1,
                 space: Optional[Dict] = None):
        """
        参数：
            action_type: 动作类型（从 actions.json 里查）
            task_id: 所属任务ID
            target_id: 目标实体ID（比如锚点ID）
            sequence: 序号（同任务内的第几步）
            space: 空间定位
        """
        spec = read_standard('actions', action_type)

        # 提取参数
        duration = spec.get('标准时长', 5)
        worker = spec.get('需要工种', '管道工')
        tool = spec.get('需要工具', '电锤')
        inputs = spec.get('输入', [])
        outputs = spec.get('输出', [])
        pre_conditions = spec.get('前置条件', [])
        post_conditions = spec.get('后置条件', [])
        quality = spec.get('质量标准', '')
        standard = spec.get('标准', 'GB 50242')

        # 生成唯一 ID
        ActionEntity._action_counter += 1
        self.id = f'ACTION-{ActionEntity._action_counter:03d}'

        # 手动构造六层
        self.layer = {
            'r_layer': {
                '类别': '动作',
                '规格': action_type,
                '子类型': spec.get('动作类型', action_type),
            },
            'l1_identity': {
                '唯一ID': self.id,
                '存在锚点': '不可替换',
                '模板ID': f'TPL-ACTION-{action_type}',
            },
            'l2_static_attributes': {
                '动作类型': action_type,
                '标准时长': f'{duration}min',
                '需要工种': worker,
                '需要工具': tool,
                '输入': inputs,
                '输出': outputs,
                '前置条件': pre_conditions,
                '后置条件': post_conditions,
                '质量标准': quality,
                '所属任务': task_id,
                '目标实体': target_id,
                '序号': sequence,
                # 动作的"受力点"是"工作量"（抽象）
                '受力点': [
                    {
                        'id': 'fp_workload',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '类型': '工作载荷',
                        '方向': 'Z-',
                        '传力对象': '执行人',
                        '承重上限': f'{duration}min',
                    }
                ],
                # 动作的"接触面"是"输入接口"和"输出接口"
                '接触面': [
                    {
                        'id': 'cf_input',
                        '类型': '输入接口',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X-',
                        '接触对象类型': inputs,
                        '允许偏差': '0',
                        '必须包含': [],
                        '违反后果': '动作无法开始',
                        '装配顺序': 1,
                    },
                    {
                        'id': 'cf_output',
                        '类型': '输出接口',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X+',
                        '接触对象类型': outputs,
                        '允许偏差': '0',
                        '必须包含': [],
                        '违反后果': '下游无法触发',
                        '装配顺序': 2,
                    },
                ],
                '包围盒': {'x': 0, 'y': 0, 'z': 0},
            },
            'l3_dynamic_state': {
                '状态': '待执行',
                '开始时间': None,
                '结束时间': None,
                '实际时长': None,
                '执行人': None,
                '产出实体ID': None,
            },
            'l4_event_chain': [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event': '创建',
                    'detail': f'动作创建，属于任务 {task_id}',
                }
            ],
            'cbm_abilities': {
                '物理规则': {
                    '包围盒': {'x': 0, 'y': 0, 'z': 0},
                    '最小间距': 0,
                    '允许接触': ['任务', '物料', '工具', '人员'],
                    '禁止穿透': False,
                    '接触方式': '逻辑关联',
                },
                '受力规则': {
                    '标准时长': f'{duration}min',
                    '需要工种': worker,
                    '需要工具': tool,
                },
                '装配规则': {
                    '可执行操作': ['开始', '暂停', '完成', '失败'],
                    '前置检查': True,
                    '后置检查': True,
                },
                '规范约束': {
                    '安装规范': standard,
                    '质量标准': quality,
                    '前置条件': pre_conditions,
                    '后置条件': post_conditions,
                    '检查周期': '每次执行1次',
                },
            },
        }

        self.entity_type = '动作'
        self.action_type = action_type
        self.task_id = task_id
        self.target_id = target_id
        self.sequence = sequence
        self.space = space or config.SPACE_UNITS

    # ==================== 通用方法 ====================

    def get_position(self) -> Dict[str, float]:
        return {'x': 0, 'y': 0, 'z': 0}

    def get_attr(self, key: str, default: Any = None) -> Any:
        return self.layer['l2_static_attributes'].get(key, default)

    def get_status(self, key: str, default: Any = None) -> Any:
        return self.layer['l3_dynamic_state'].get(key, default)

    def get_bounding_box(self) -> Dict[str, float]:
        return {'x': 0, 'y': 0, 'z': 0}

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
        return {'success': True}

    def check_collision(self, other) -> Dict[str, Any]:
        return {'collision': False, 'distance': {'dx': 0, 'dy': 0, 'dz': 0}}

    # ==================== 动作专属操作 ====================

    def start(self, operator: str = '') -> Dict[str, Any]:
        """开始执行"""
        if self.layer['l3_dynamic_state']['状态'] != '待执行':
            return {'success': False, 'message': '状态不对，不是待执行'}

        self.layer['l3_dynamic_state']['状态'] = '执行中'
        self.layer['l3_dynamic_state']['开始时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.layer['l3_dynamic_state']['执行人'] = operator
        self.add_event('开始执行', f'执行人：{operator}')

        return {'success': True, 'action_id': self.id}

    def complete(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """完成执行"""
        if self.layer['l3_dynamic_state']['状态'] != '执行中':
            return {'success': False, 'message': '状态不对，不是执行中'}

        self.layer['l3_dynamic_state']['状态'] = '已完成'
        self.layer['l3_dynamic_state']['结束时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.layer['l3_dynamic_state']['产出实体ID'] = product_id
        self.add_event('执行完成', f'产出：{product_id}')

        return {'success': True, 'action_id': self.id, 'product_id': product_id}

    def fail(self, reason: str = '') -> Dict[str, Any]:
        """执行失败"""
        self.layer['l3_dynamic_state']['状态'] = '已失败'
        self.layer['l3_dynamic_state']['结束时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_event('执行失败', reason)

        return {'success': True, 'action_id': self.id}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '动作',
            'action_type': self.action_type,
            'task_id': self.task_id,
            'target_id': self.target_id,
            'sequence': self.sequence,
            'layer': self.layer,
        }