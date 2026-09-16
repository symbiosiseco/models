# -*- coding: utf-8 -*-
"""
人员实体
受 GPL v3.0 保护

定义工人的完整数字生命体。
含L3多维度状态：心态/体力/活动范围/情绪。
物是"死的"，人是"活的"。
"""

from typing import Dict, Any, List, Optional
from .entity import BaseEntity
from .worker_state import WorkerStateEntity
from .physics_rules import worker_cbm, worker_force_points, worker_contact_faces
from config import config


class WorkerEntity(BaseEntity):
    """人员实体"""

    # 工种规格
    WORKER_SPECS = {
        'pipefitter':  {'工种': '管道工', '时薪': 45, '效率系数': 1.0},
        'welder':      {'工种': '焊工',   '时薪': 60, '效率系数': 0.9},
        'electrician': {'工种': '电工',   '时薪': 50, '效率系数': 1.0},
        'deliverer':   {'工种': '配送员', '时薪': 35, '效率系数': 1.0},
        'fitter':      {'工种': '钳工',   '时薪': 50, '效率系数': 1.0},
        'inspector':   {'工种': '质检员', '时薪': 55, '效率系数': 1.0},
        # 岗位映射
        'con_foreman': {'工种': '管道工', '时薪': 45, '效率系数': 1.0},
        'con_pm':      {'工种': '管道工', '时薪': 45, '效率系数': 1.0},
    }

    def __init__(self, name: str = '', position: str = '',
                 organization: str = '', phone: str = '',
                 skills: Optional[List[str]] = None,
                 certificates: Optional[List[str]] = None,
                 space: Optional[Dict] = None):
        spec = self.WORKER_SPECS.get(position, self.WORKER_SPECS['pipefitter'])

        # L2层
        l2 = {
            '姓名': name,
            '岗位': position,
            '单位': organization,
            '电话': phone,
            '技能': skills or [],
            '证书': certificates or [],
            '工种': spec['工种'],
            '时薪': spec['时薪'],
            '日工时': 8,
            '效率系数': spec['效率系数'],
        }

        # L3层（多维度）
        l3 = {
            '状态': '空闲',
            '当前任务': None,
            '心态': '正常',
            '体力': '100%',
            '活动范围': {
                '类型': '多边形',
                '区域': '3号楼2层B轴',
                '边界': [
                    {'x': 0, 'y': 0},
                    {'x': 10000, 'y': 0},
                    {'x': 10000, 'y': -3000},
                    {'x': 0, 'y': -3000},
                ],
            },
            '工作时段': {'开始': '08:00', '结束': '18:00'},
            '技能状态': '熟练',
            '情绪': '平静',
        }

        # CBM层
        cbm = worker_cbm(spec['工种'], spec['时薪'], spec['效率系数'])

        super().__init__(
            entity_type='人员',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        # 私有字段
        self.name = name
        self.position = position
        self.organization = organization
        self.phone = phone
        self.skills = skills or []
        self.certificates = certificates or []
        self.worker_type = spec['工种']
        self.space = space or config.SPACE_UNITS

        # 创建WorkerStateEntity
        self._worker_state = self._init_worker_state()

        # 更新R层
        self.layer['r_layer']['工种'] = spec['工种']
        self.layer['r_layer']['岗位'] = position
        self.layer['r_layer']['单位'] = organization

    def _init_worker_state(self) -> WorkerStateEntity:
        """创建WorkerStateEntity"""
        return WorkerStateEntity(
            worker_id=self.id,
            status=self.layer['l3_dynamic_state']['状态'],
            current_task=self.layer['l3_dynamic_state'].get('当前任务'),
            mentality=self.layer['l3_dynamic_state']['心态'],
            stamina=self.layer['l3_dynamic_state']['体力'],
            activity_area=self.layer['l3_dynamic_state']['活动范围'],
            work_hours=self.layer['l3_dynamic_state']['工作时段'],
            skill_status=self.layer['l3_dynamic_state']['技能状态'],
            emotion=self.layer['l3_dynamic_state']['情绪'],
        )

    # ==================== L3多维度更新 ====================

    def update_mentality(self, mentality: str) -> Dict[str, Any]:
        """更新心态"""
        self.layer['l3_dynamic_state']['心态'] = mentality
        self._worker_state.update_state('心态', mentality)
        self.add_event('心态变化', mentality)
        return {'success': True, 'mentality': mentality}

    def update_stamina(self, stamina: str) -> Dict[str, Any]:
        """更新体力"""
        self.layer['l3_dynamic_state']['体力'] = stamina
        self._worker_state.update_state('体力', stamina)
        self.add_event('体力变化', stamina)
        return {'success': True, 'stamina': stamina}

    def update_activity_area(self, area: Dict[str, Any]) -> Dict[str, Any]:
        """更新活动范围"""
        self.layer['l3_dynamic_state']['活动范围'] = area
        self._worker_state.update_state('活动范围', area)
        return {'success': True, 'activity_area': area}

    def update_emotion(self, emotion: str) -> Dict[str, Any]:
        """更新情绪"""
        self.layer['l3_dynamic_state']['情绪'] = emotion
        self._worker_state.update_state('情绪', emotion)
        return {'success': True, 'emotion': emotion}

    def update_current_task(self, task_id: Optional[str]) -> Dict[str, Any]:
        """更新当前任务"""
        self.layer['l3_dynamic_state']['当前任务'] = task_id
        self._worker_state.update_state('当前任务', task_id)
        return {'success': True, 'current_task': task_id}

    # ==================== 状态检查 ====================

    def check_stamina(self) -> bool:
        """检查体力是否够（≥60%）"""
        return self._worker_state.check_stamina()

    def check_skill(self, task_type: str) -> bool:
        """检查技能是否匹配任务"""
        return self._worker_state.check_skill(task_type)

    def is_available(self) -> bool:
        """检查是否空闲"""
        return self._worker_state.is_available()

    # ==================== 受力点/接触面 ====================

    def get_force_points(self) -> List[Dict[str, Any]]:
        """获取受力点（能力边界）"""
        return self.layer['l2_static_attributes'].get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        """获取接触面（协作接触）"""
        return self.layer['l2_static_attributes'].get('接触面', [])

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '人员',
            'name': self.name,
            'position': self.position,
            'organization': self.organization,
            'worker_type': self.worker_type,
            'layer': self.layer,
        }