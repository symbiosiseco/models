# -*- coding: utf-8 -*-
"""
模板存储器
受 GPL v3.0 保护

管理模板的增删改查和实例化。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .item_templates import ITEM_TEMPLATES
from .worker_templates import WORKER_TEMPLATES
from .equip_templates import EQUIP_TEMPLATES
from .task_templates import TASK_TEMPLATES


class TemplateStore:
    """模板存储器"""

    # 实体类型 → ID前缀映射
    _PREFIX_MAP = {
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
    }

    # 实例ID计数器（类变量）
    _counters: Dict[str, int] = {}

    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_presets()

    def _load_presets(self):
        """从4个模板库加载预设"""
        for tid, tpl in ITEM_TEMPLATES.items():
            self.templates[tid] = tpl
        for tid, tpl in WORKER_TEMPLATES.items():
            self.templates[tid] = tpl
        for tid, tpl in EQUIP_TEMPLATES.items():
            self.templates[tid] = tpl
        for tid, tpl in TASK_TEMPLATES.items():
            self.templates[tid] = tpl

    # ==================== 查询 ====================

    def list_all(self, category: Optional[str] = None,
                 entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取模板列表（可选筛选）"""
        result = []
        for tid, tpl in self.templates.items():
            if category and tpl.get('category') != category:
                continue
            if entity_type and tpl.get('entity_type') != entity_type:
                continue
            result.append({
                'template_id': tid,
                'category': tpl.get('category', ''),
                'entity_type': tpl.get('entity_type', ''),
                'name': tpl.get('name', ''),
                'manufacturer': tpl.get('manufacturer', ''),
                'spec': tpl.get('spec', ''),
            })
        return result

    def get(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板详情"""
        return self.templates.get(template_id)

    def get_by_category(self) -> Dict[str, List[str]]:
        """按类别分组"""
        groups: Dict[str, List[str]] = {}
        for tid, tpl in self.templates.items():
            cat = tpl.get('category', '未分类')
            groups.setdefault(cat, []).append(tid)
        return groups

    # ==================== 创建/删除 ====================

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模板"""
        tid = data.get('template_id')
        if not tid:
            raise ValueError('缺少 template_id')
        if tid in self.templates:
            raise ValueError(f'模板已存在：{tid}')
        self.templates[tid] = data
        return data

    def delete(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    # ==================== 实例化 ====================

    def instantiate(self, template_id: str,
                    position: Optional[Dict] = None,
                    instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从模板生成实例。

        核心流程：
            1. 从模板取信息
            2. 生成实例ID
            3. 组装六层（R/L1/L2/L3/L4/CBM）
            4. L3默认状态="待装配"
        """
        tpl = self.templates.get(template_id)
        if not tpl:
            raise ValueError(f'模板不存在：{template_id}')

        position = position or {'x': 0, 'y': 0, 'z': 0}
        entity_type = tpl.get('entity_type', '')
        instance_id = instance_id or self._gen_instance_id(entity_type)

        # 计算包围盒
        bbox = self._calc_bounding_box(tpl.get('params', {}))

        # R层
        r_layer = {
            '类别': tpl.get('entity_type', ''),
            '规则组': tpl.get('category', '') + '管理规则组',
            '厂家': tpl.get('manufacturer', ''),
            '模板ID': template_id,
            '模板名': tpl.get('name', ''),
            '类型': tpl.get('spec', ''),
        }

        # L1层
        l1_identity = {
            '唯一ID': instance_id,
            '存在锚点': '不可替换',
            '模板ID': template_id,
        }

        # L2层
        l2 = dict(tpl.get('params', {}))
        l2['锚点'] = tpl.get('anchors', [])
        l2['受力点'] = tpl.get('force_points', [])
        l2['接触面'] = tpl.get('contact_faces', [])
        l2['包围盒'] = bbox

        # L3层
        l3 = {
            '绝对坐标': position,
            '状态': '待装配',
            '受力点实时坐标': [],
        }

        # L4层
        l4 = [
            {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event': '实例化',
                'detail': f'从模板 {template_id} 实例化',
            }
        ]

        # CBM层
        cbm = dict(tpl.get('cbm', {}))

        return {
            'id': instance_id,
            'entity_type': entity_type,
            'layer': {
                'r_layer': r_layer,
                'l1_identity': l1_identity,
                'l2_static_attributes': l2,
                'l3_dynamic_state': l3,
                'l4_event_chain': l4,
                'cbm_abilities': cbm,
            },
        }

    def _gen_instance_id(self, entity_type: str) -> str:
        """生成实例ID"""
        prefix = self._PREFIX_MAP.get(entity_type, 'ENT')
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f'{prefix}-{self._counters[prefix]:03d}'

    def _calc_bounding_box(self, params: Dict[str, Any]) -> Dict[str, float]:
        """从params计算包围盒"""
        def parse(val, default=100.0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace('mm', '').strip())
                except ValueError:
                    return default
            return default

        length = parse(params.get('长度', params.get('外径', 100)), 100)
        outer = parse(params.get('外径', params.get('宽度', 100)), 100)
        thickness = parse(params.get('厚度', params.get('高度', outer)), outer)

        return {'x': length, 'y': outer, 'z': thickness}

    @classmethod
    def reset_counters(cls):
        """重置计数器（测试用）"""
        cls._counters = {}