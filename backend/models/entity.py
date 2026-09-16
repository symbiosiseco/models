# -*- coding: utf-8 -*-
"""
实体基类
受 GPL v3.0 保护

所有具体实体的父类。继承 SixLayerBuilder 的用法，提供通用能力。
含受力点方法、接触面方法（V2.0新增）。
"""

from typing import Dict, Any, List, Optional
from six_layer_core import SixLayerBuilder
from datetime import datetime


class BaseEntity:
    """实体基类"""

    # 实体类型 → ID前缀映射
    _prefix_map = {
        # A组：管道系统
        '镀锌钢管': 'PIPE', '管道': 'PIPE',
        '支架': 'SUP', '单支角钢支架': 'SUP', '综合支架': 'CSUP',
        '阀门': 'VALVE', '闸阀': 'VALVE', '蝶阀': 'VALVE', '止回阀': 'VALVE',
        '卡箍': 'CLAMP', '沟槽卡箍': 'CLAMP',
        '套管': 'SLEEVE', '穿墙套管': 'SLEEVE',
        '弯头': 'ELBOW', '三通': 'TEE', '变径管': 'REDUCER',
        '联轴器': 'COUPLING',
        '法兰': 'FLANGE', '沟槽法兰': 'FLANGE',
        '垫片': 'GASKET', '橡胶圈': 'GASKET',
        '螺栓': 'BOLT', '膨胀螺栓': 'BOLT',
        '手轮': 'WHEEL', '阀杆': 'STEM',
        # B组：结构
        '墙体': 'WALL', '楼板': 'SLAB', '地面': 'FLOOR',
        '柱子': 'COLUMN', '吊顶': 'CEILING',
        '吊顶丝杆': 'CHANGER', '支架吊杆': 'HANGER',
        # C组：其他专业
        '风管': 'DUCT', '桥架': 'TRAY',
        # D组：人员/组织
        '人员': 'WORKER', '工人': 'WORKER',
        '工人技能': 'SKILL', '车辆': 'VEHICLE', '组织': 'ORG',
        # E组：项目/合同
        '项目': 'PROJ', '合同': 'CONTR', '图纸': 'DRAW',
        # F组：任务/工序
        '任务': 'TASK', '工序': 'PROC', '订单': 'ORDER',
        # G组：验收/变更
        '验收': 'ACC', '变更': 'CHG', '签证': 'VISA',
        # H组：模板/报表
        '模板': 'TPL', '报表': 'RPT',
        # I组：实测/记录
        '实测实量': 'MEAS', '实测记录': 'MEASR',
        '签字记录': 'SIGR', '通知记录': 'NOTIR',
        # J组：厂家/产品
        '厂家': 'MFR', '产品': 'PROD',
        # 核心
        '受力点': 'FP', '接触面': 'CF',
    }

    # 计数器（类变量）
    _counters: Dict[str, int] = {}

    def __init__(self, entity_type: str, rule_group: Optional[str] = None, **kwargs):
        self.entity_type = entity_type
        self.rule_group = rule_group
        self.id = self._generate_id(entity_type)
        self._builder = SixLayerBuilder()
        self.layer: Dict[str, Any] = {}

        # 初始化六层
        self._init_r_layer(**kwargs)
        self._init_l1_layer()
        self._init_l2_layer(**kwargs)
        self._init_l3_layer(**kwargs)
        self._init_l4_layer()
        self._init_cbm_layer(**kwargs)

        # 构建
        self.layer = self._builder.build()

    def _generate_id(self, entity_type: str) -> str:
        """生成唯一ID，如 PIPE-001"""
        prefix = self._prefix_map.get(entity_type, 'ENT')
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}-{self._counters[prefix]:03d}"

    def _init_r_layer(self, **kwargs):
        """初始化R层（类别定义层）"""
        self._builder.set_r_layer({
            '类别': self.entity_type,
            '规则组': self.rule_group or f'{self.entity_type}管理规则组',
            '厂家': kwargs.get('manufacturer', ''),
            '模板ID': kwargs.get('template_id', ''),
            '模板名': kwargs.get('template_name', ''),
        })

    def _init_l1_layer(self):
        """初始化L1层（身份标识层）"""
        self._builder.set_l1_identity({
            '唯一ID': self.id,
            '存在锚点': '不可替换',
            '模板ID': '',
        })

    def _init_l2_layer(self, **kwargs):
        """初始化L2层（静态属性层）"""
        self._builder.set_l2_static_attributes(kwargs.get('l2', {}))

    def _init_l3_layer(self, **kwargs):
        """初始化L3层（动态状态层）"""
        l3 = {
            '状态': kwargs.get('status', '待装配'),
            '绝对坐标': kwargs.get('position', {'x': 0, 'y': 0, 'z': 0}),
            '受力点实时坐标': [],
            'cbm_status': 'stable',
        }
        if kwargs.get('l3'):
            l3.update(kwargs['l3'])
        self._builder.set_l3_dynamic_state(l3)

    def _init_l4_layer(self):
        """初始化L4层（事件链层）"""
        self._builder.set_l4_event_chain([
            {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event': '实体创建',
                'detail': f'由 {self.entity_type} 类创建',
            }
        ])

    def _init_cbm_layer(self, **kwargs):
        """初始化CBM层（行为与认知模块）"""
        self._builder.set_cbm_abilities(kwargs.get('cbm', {}))

    # ========== 通用方法 ==========

    def add_event(self, event: str, detail: str = ''):
        """追加L4事件"""
        self.layer['l4_event_chain'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event': event,
            'detail': detail,
        })

    def update_status(self, key: str, value: Any):
        """更新L3状态"""
        self.layer['l3_dynamic_state'][key] = value

    def get_attr(self, key: str, default: Any = None) -> Any:
        """获取L2属性"""
        return self.layer.get('l2_static_attributes', {}).get(key, default)

    def get_status(self, key: str, default: Any = None) -> Any:
        """获取L3状态"""
        return self.layer.get('l3_dynamic_state', {}).get(key, default)

    def get_bounding_box(self) -> dict:
        """获取包围盒"""
        l2 = self.layer.get('l2_static_attributes', {})
        return l2.get('包围盒', l2.get('外形', {}).get('包围盒', {'x': 0, 'y': 0, 'z': 0}))

    def get_position(self) -> dict:
        """获取绝对坐标"""
        return self.layer.get('l3_dynamic_state', {}).get('绝对坐标', {'x': 0, 'y': 0, 'z': 0})

    def move_to(self, x: float, y: float, z: float):
        """移动到新位置"""
        self.layer['l3_dynamic_state']['绝对坐标'] = {'x': x, 'y': y, 'z': z}

    def check_collision(self, other: 'BaseEntity') -> dict:
        """AABB碰撞检测"""
        b1 = self.get_bounding_box()
        b2 = other.get_bounding_box()
        p1 = self.get_position()
        p2 = other.get_position()

        dx = abs(p1['x'] - p2['x'])
        dy = abs(p1['y'] - p2['y'])
        dz = abs(p1['z'] - p2['z'])

        overlap = (
            dx < (b1['x'] + b2['x']) / 2 and
            dy < (b1['y'] + b2['y']) / 2 and
            dz < (b1['z'] + b2['z']) / 2
        )
        return {
            'collision': overlap,
            'distance': {'dx': dx, 'dy': dy, 'dz': dz},
        }

    # ========== 受力点方法（V2.0新增）==========

    def get_force_points(self) -> List[Dict[str, Any]]:
        """从L2取受力点列表"""
        l2 = self.layer.get('l2_static_attributes', {})
        return l2.get('受力点', [])

    def get_absolute_force_point(self, fp_id: str) -> dict:
        """从L3取受力点实时绝对坐标"""
        l3 = self.layer.get('l3_dynamic_state', {})
        for fp in l3.get('受力点实时坐标', []):
            if fp.get('id') == fp_id:
                return fp
        return {}

    def update_force_point(self, fp_id: str, force_data: dict):
        """更新L3的受力点实时数据"""
        l3 = self.layer['l3_dynamic_state']
        if '受力点实时坐标' not in l3:
            l3['受力点实时坐标'] = []

        for fp in l3['受力点实时坐标']:
            if fp.get('id') == fp_id:
                fp.update(force_data)
                return
        # 不存在则新增
        fp_new = {'id': fp_id}
        fp_new.update(force_data)
        l3['受力点实时坐标'].append(fp_new)

    # ========== 接触面方法（V2.0新增）==========

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        """从L2取接触面列表"""
        l2 = self.layer.get('l2_static_attributes', {})
        return l2.get('接触面', [])

    def get_contact_face(self, cf_id: str) -> dict:
        """获取指定接触面"""
        for cf in self.get_contact_faces():
            if cf.get('id') == cf_id:
                return cf
        return {}

    def to_dict(self) -> dict:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'layer': self.layer,
        }

    @classmethod
    def reset_counters(cls):
        """重置所有计数器（测试用）"""
        cls._counters = {}