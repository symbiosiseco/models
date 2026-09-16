# -*- coding: utf-8 -*-
"""
任务实体
受 GPL v3.0 保护

定义施工任务。
含任务CBM：前驱/后继/触发规则/产物清单。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .physics_rules import task_cbm
from config import config


class TaskEntity(BaseEntity):
    """任务实体"""

    # 任务类型（含标准时长，单位：分钟）
    TASK_TYPES = {
        '预制': {'standard_duration': 120, 'required_worker': '焊工', 'required_equipment': '电焊机'},
        '配送': {'standard_duration': 30,  'required_worker': '配送员', 'required_equipment': '叉车'},
        '安装支架': {'standard_duration': 240, 'required_worker': '管道工', 'required_equipment': '电锤'},
        '安装管道': {'standard_duration': 480, 'required_worker': '管道工', 'required_equipment': '电锤'},
        '安装阀门': {'standard_duration': 180, 'required_worker': '管道工', 'required_equipment': '扳手'},
        '试压': {'standard_duration': 60,  'required_worker': '质检员', 'required_equipment': '试压泵'},
    }

    # 任务状态
    STATUSES = ['待执行', '执行中', '已完成', '取消']

    def __init__(self, task_name: str = '', task_type: str = '预制',
                 start_time: str = '', end_time: str = '',
                 actor_id: Optional[str] = None,
                 predecessor: Optional[str] = None,
                 successor: Optional[List[str]] = None,
                 materials: Optional[List[str]] = None,
                 products: Optional[List[str]] = None,
                 space: Optional[Dict] = None):
        # 参数校验
        if task_type not in self.TASK_TYPES:
            task_type = '预制'
        spec = self.TASK_TYPES[task_type]

        # L2层
        l2 = {
            '任务名': task_name,
            '任务类型': task_type,
            '标准时长': spec['standard_duration'],
            '需要人员': spec['required_worker'],
            '需要设备': spec['required_equipment'],
            '输入物料': materials or [],
            '输出产物': products or [],
            '开始时间': start_time,
            '结束时间': end_time,
        }

        # L3层
        l3 = {
            '状态': '待执行',
            '开始时间': start_time,
            '结束时间': end_time,
            '实际执行人': actor_id,
        }

        # CBM层（任务CBM）
        cbm = task_cbm(
            task_name=task_name,
            task_type=task_type,
            predecessor=predecessor,
            successor=successor or [],
        )
        # 补充产物清单
        cbm['装配规则']['产物清单'] = products or []
        cbm['装配规则']['完成条件'] = '所有产物都完成'

        super().__init__(
            entity_type='任务',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        # 私有字段
        self.task_name = task_name
        self.task_type = task_type
        self.actor_id = actor_id
        self.predecessor = predecessor
        self.successor = list(successor or [])
        self.materials = list(materials or [])
        self.products = list(products or [])
        self.completed_products: List[str] = []
        self.space = space or config.SPACE_UNITS

        # 更新R层
        self.layer['r_layer']['任务类型'] = task_type

    # ==================== 任务CBM方法 ====================

    def on_product_complete(self, product_id: str) -> Dict[str, Any]:
        """记录产物完成"""
        if product_id not in self.completed_products:
            self.completed_products.append(product_id)

        all_done = self.check_all_products_done()
        if all_done:
            self.mark_complete()

        return {
            'recorded': True,
            'all_done': all_done,
            'completed': len(self.completed_products),
        }

    def check_all_products_done(self) -> bool:
        """检查所有产物是否完成"""
        if not self.products:
            return True  # 无产物定义时视为完成
        return all(pid in self.completed_products for pid in self.products)

    def mark_complete(self) -> Dict[str, Any]:
        """标记任务完成 + 写L4"""
        self.layer['l3_dynamic_state']['状态'] = '已完成'
        self.add_event('任务完成', f'完成产物{len(self.completed_products)}个')
        return {
            'success': True,
            'task_id': self.id,
            'triggered_tasks': self.get_successor(),
        }

    def trigger_successor(self) -> List[str]:
        """触发下游任务"""
        return self.get_successor()

    def get_predecessor(self) -> Optional[str]:
        """获取前置任务"""
        return self.layer['cbm_abilities']['装配规则'].get('前置任务')

    def get_successor(self) -> List[str]:
        """获取后继任务"""
        successors = self.layer['cbm_abilities']['装配规则'].get('后继任务', [])
        if isinstance(successors, str):
            return [successors] if successors else []
        return list(successors or [])

    def get_products(self) -> List[str]:
        """获取产物清单"""
        return self.layer['cbm_abilities']['装配规则'].get('产物清单', [])

    # ==================== 状态管理 ====================

    def start(self, actor_id: Optional[str] = None) -> Dict[str, Any]:
        """开始任务"""
        self.layer['l3_dynamic_state']['状态'] = '执行中'
        if actor_id:
            self.layer['l3_dynamic_state']['实际执行人'] = actor_id
        self.add_event('任务开始', f'执行人：{actor_id or "未指定"}')
        return {'success': True, 'task_id': self.id}

    def get_status(self) -> str:
        """获取任务状态"""
        return self.layer['l3_dynamic_state'].get('状态', '待执行')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '任务',
            'task_name': self.task_name,
            'task_type': self.task_type,
            'status': self.get_status(),
            'predecessor': self.get_predecessor(),
            'successor': self.get_successor(),
            'products': self.get_products(),
            'completed_products': self.completed_products,
            'layer': self.layer,
        }