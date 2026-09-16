# -*- coding: utf-8 -*-
"""
从标准库生成流程的函数
受 GPL v3.0 保护

A-5 新增：流程也像任务一样，从标准库生成。

流程是"多个任务组成的完整工序"。
例如：管道安装流程 = 安装支架任务 + 安装管道任务 + 系统试压任务
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard
from config import config


class ProcessFromStd:
    """从标准库生成的流程实体"""

    _process_counter = 0

    def __init__(self, process_type: str = '管道安装流程',
                 space: Optional[Dict] = None):
        """
        参数：
            process_type: 流程类型（从 processes.json 里查）
            space: 空间定位
        """
        spec = read_standard('processes', process_type)
        if not spec:
            raise ValueError(f'processes.json 里没有流程类型：{process_type}')

        # 提取参数
        process_name = spec.get('流程名', process_type)
        tasks = spec.get('包含任务', [])
        duration = spec.get('标准工期', 150)
        participants = spec.get('参与方', [])
        acceptance = spec.get('验收标准', '')
        standard = spec.get('标准', 'GB 50242')

        # 生成唯一 ID
        ProcessFromStd._process_counter += 1
        self.id = f'PROCESS-{ProcessFromStd._process_counter:03d}'

        # 手动构造六层
        self.layer = {
            'r_layer': {
                '类别': '流程',
                '规格': process_type,
                '子类型': process_name,
            },
            'l1_identity': {
                '唯一ID': self.id,
                '存在锚点': '不可替换',
                '模板ID': f'TPL-PROCESS-{process_type}',
            },
            'l2_static_attributes': {
                '流程类型': process_type,
                '流程名': process_name,
                '包含任务': tasks,
                '标准工期': f'{duration}min',
                '参与方': participants,
                '验收标准': acceptance,
                '受力点': [
                    {
                        'id': 'fp_workload',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '类型': '流程载荷',
                        '方向': 'Z-',
                        '传力对象': '项目',
                        '承重上限': f'{duration}min',
                    }
                ],
                '接触面': [
                    {
                        'id': 'cf_input',
                        '类型': '流程输入',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X-',
                        '接触对象类型': ['项目', '图纸', '物料'],
                        '允许偏差': '0',
                        '必须包含': [],
                        '违反后果': '流程无法启动',
                        '装配顺序': 1,
                    },
                    {
                        'id': 'cf_output',
                        '类型': '流程输出',
                        '位置': {'x': 0, 'y': 0, 'z': 0},
                        '法线方向': 'X+',
                        '接触对象类型': ['交付物', '验收记录'],
                        '允许偏差': '0',
                        '必须包含': [],
                        '违反后果': '无法交付',
                        '装配顺序': 2,
                    },
                ],
                '包围盒': {'x': 0, 'y': 0, 'z': 0},
            },
            'l3_dynamic_state': {
                '状态': '待启动',
                '启动时间': None,
                '结束时间': None,
                '实际工期': None,
                '当前任务索引': 0,
                '完成任务数': 0,
                '总任务数': len(tasks),
                '关联任务ID': [],  # 运行时填充
            },
            'l4_event_chain': [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event': '创建',
                    'detail': f'流程创建：{process_name}',
                }
            ],
            'cbm_abilities': {
                '物理规则': {
                    '包围盒': {'x': 0, 'y': 0, 'z': 0},
                    '最小间距': 0,
                    '允许接触': ['项目', '任务', '人员', '交付物'],
                    '禁止穿透': False,
                    '接触方式': '逻辑关联',
                },
                '受力规则': {
                    '标准工期': f'{duration}min',
                    '包含任务数': len(tasks),
                    '参与方': participants,
                },
                '装配规则': {
                    '触发规则': '所有任务完成后自动完成流程',
                    '顺序约束': True,
                    '完成条件': '所有任务都完成',
                },
                '规范约束': {
                    '安装规范': standard,
                    '验收标准': acceptance,
                    '状态': ['待启动', '进行中', '已完成', '已中止'],
                    '检查周期': '每流程1次',
                },
            },
        }

        self.entity_type = '流程'
        self.process_type = process_type
        self.process_name = process_name
        self.tasks = list(tasks)
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

    # ==================== 流程专属操作 ====================

    def start(self) -> Dict[str, Any]:
        """启动流程"""
        if self.layer['l3_dynamic_state']['状态'] != '待启动':
            return {'success': False, 'message': '状态不对，不是待启动'}

        self.layer['l3_dynamic_state']['状态'] = '进行中'
        self.layer['l3_dynamic_state']['启动时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_event('流程启动', '')

        return {'success': True, 'process_id': self.id}

    def link_tasks(self, task_id_list: List[str]) -> Dict[str, Any]:
        """关联实际的任务ID"""
        self.layer['l3_dynamic_state']['关联任务ID'] = list(task_id_list)
        self.add_event('关联任务', f'关联了 {len(task_id_list)} 个任务')
        return {'success': True, 'linked': len(task_id_list)}

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """完成一个任务"""
        if task_id not in self.layer['l3_dynamic_state']['关联任务ID']:
            return {'success': False, 'message': f'任务 {task_id} 不属于本流程'}

        self.layer['l3_dynamic_state']['完成任务数'] += 1
        self.add_event('任务完成', f'任务：{task_id}')

        done = self.layer['l3_dynamic_state']['完成任务数']
        total = self.layer['l3_dynamic_state']['总任务数']
        if done >= total:
            self.layer['l3_dynamic_state']['状态'] = '已完成'
            self.layer['l3_dynamic_state']['结束时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.add_event('流程完成', f'{done}/{total} 任务完成')

        return {'success': True, 'done': done, 'total': total}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': '流程',
            'process_type': self.process_type,
            'tasks': self.tasks,
            'layer': self.layer,
        }