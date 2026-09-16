# -*- coding: utf-8 -*-
"""
从标准库生成任务的函数
受 GPL v3.0 保护

A-4 新增：任务也像动作一样，从标准库生成。

★ 本模块不修改现有 task.py，而是提供一个"从标准库创建 TaskEntity"的函数。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard
from config import config


class TaskFromStd:
    """从标准库生成的任务实体（不依赖现有 TaskEntity）"""

    _task_counter = 0

    def __init__(self, task_type: str = '安装支架',
                 predecessor: Optional[str] = None,
                 space: Optional[Dict] = None):
        """
        参数：
            task_type: 任务类型（从 tasks.json 里查）
            predecessor: 前置任务ID（可选，覆盖标准库）
            space: 空间定位
        """
        spec = read_standard('tasks', task_type)
        if not spec:
            raise ValueError(f'tasks.json 里没有任务类型：{task_type}')

        # 提取参数
        task_name = spec.get('任务名', task_type)
        actions = spec.get('包含动作', [])
        duration = spec.get('标准时长', 30)
        worker = spec.get('需要工种', '管道工')
        equipment = spec.get('需要设备', '')
        inputs = spec.get('输入物料', [])
        outputs = spec.get('输出产物', [])
        pre_task = predecessor if predecessor is not None else spec.get('前置任务')
        next_tasks = spec.get('后续任务', [])
        standard = spec.get('标准', 'GB 50242')

        # 生成唯一 ID
        TaskFromStd._task_counter += 1
        self.id = f'TASK-{TaskFromStd._task_counter:03d}'

        # 手动构造六层
        self.layer = {
            'r_layer': {
                '类别': '任务',
                '规格': task_type,
                '子类型': task_name,
            },
            'l1_identity': {
                '唯一ID': self.id,
                '存在锚点': '不可替换',
                '模板ID': f'TPL-TASK-{task_type}',
            },
            'l2_static_attributes': {
                '任务类型': task_type,
                '任务名': task_name,
                '包含动作': actions,
                '标准时长': f'{duration}min',
                '需要工种': worker,
                '需要设备': equipment,
                '输入物料': inputs,
                '输出产物': outputs,
                '前置任务': pre_task,
                '后续任务': next_tasks,
                '受力点': [
                    {
                        'id': 'fp_workload',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '类型': '任务载荷',
                        '方向': 'Z-',
                        '传力对象': '执行人',
                        '承重上限': f'{duration}min',
                    }
                ],
                '接触面': [
                    {
                        'id': 'cf_input',
                        '类型': '输入接口',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X-',
                        '接触对象类型': inputs + (['前置任务'] if pre_task else []),
                        '允许偏差': '0',
                        '必须包含': [],
                        '违反后果': '任务无法开始',
                        '装配顺序': 1,
                    },
                    {
                        'id': 'cf_output',
                        '类型': '输出接口',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X+',
                        '接触对象类型': outputs + (['后续任务'] if next_tasks else []),
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
                '完成动作数': 0,
                '总动作数': len(actions),
                '产出实体ID': None,
            },
            'l4_event_chain': [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event': '创建',
                    'detail': f'任务创建：{task_name}',
                }
            ],
            'cbm_abilities': {
                '物理规则': {
                    '包围盒': {'x': 0, 'y': 0, 'z': 0},
                    '最小间距': 0,
                    '允许接触': ['人员', '设备', '物料', '产物', '动作'],
                    '禁止穿透': False,
                    '接触方式': '逻辑关联',
                },
                '受力规则': {
                    '标准时长': f'{duration}min',
                    '需要工种': worker,
                    '需要设备': equipment,
                    '输入物料': inputs,
                    '输出产物': outputs,
                },
                '装配规则': {
                    '前置任务': pre_task,
                    '后续任务': next_tasks,
                    '触发规则': '所有动作完成后自动触发后续任务',
                    '完成条件': '所有动作都完成',
                },
                '规范约束': {
                    '安装规范': standard,
                    '状态': ['待执行', '执行中', '已完成', '已失败'],
                    '检查周期': '每任务1次',
                },
            },
        }

        self.entity_type = '任务'
        self.task_type = task_type
        self.task_name = task_name
        self.actions = list(actions)
        self.predecessor = pre_task
        self.successor = list(next_tasks) if next_tasks else []
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

    # ==================== 任务专属操作 ====================

    def start(self, operator: str = '') -> Dict[str, Any]:
        """开始任务"""
        if self.layer['l3_dynamic_state']['状态'] != '待执行':
            return {'success': False, 'message': '状态不对，不是待执行'}

        self.layer['l3_dynamic_state']['状态'] = '执行中'
        self.layer['l3_dynamic_state']['开始时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.layer['l3_dynamic_state']['执行人'] = operator
        self.add_event('开始执行', f'执行人：{operator}')

        return {'success': True, 'task_id': self.id}

    def complete_action(self, action_type: str) -> Dict[str, Any]:
        """完成一个动作"""
        if action_type not in self.actions:
            return {'success': False, 'message': f'动作 {action_type} 不属于本任务'}

        self.layer['l3_dynamic_state']['完成动作数'] += 1
        self.add_event('动作完成', f'动作：{action_type}')

        # 检查是否全部完成
        done = self.layer['l3_dynamic_state']['完成动作数']
        total = self.layer['l3_dynamic_state']['总动作数']
        if done >= total:
            self.layer['l3_dynamic_state']['状态'] = '已完成'
            self.layer['l3_dynamic_state']['结束时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.add_event('任务完成', f'{done}/{total} 动作完成')

        return {'success': True, 'done': done, 'total': total}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '任务',
            'task_type': self.task_type,
            'predecessor': self.predecessor,
            'successor': self.successor,
            'layer': self.layer,
        }