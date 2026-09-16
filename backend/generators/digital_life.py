# -*- coding: utf-8 -*-
"""
数字生命体生成器 V2.0（AI驱动）
受 GPL v3.0 保护

厂家扔一个参数包进来，AI自动联网查标准、自动理解产品本质、
自动补全所有缺失参数、自动推导物理规则、自动注入六层架构、
自动计算边界、自动验证完整性，最后生成一个完整的、
能立即参与物理世界交互的数字生命体。

一次构建，永久使用，任何实体都能生成。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .ai_connector import AIConnector
from .ai_understanding import AIUnderstanding
from .param_mapper import ParamMapper
from .rule_injector import RuleInjector
from .boundary_calculator import BoundaryCalculator
from .template_matcher import TemplateMatcher
from .integrity_validator import IntegrityValidator
from .generation_manual import GenerationManual
from .rules import RULES


class DigitalLifeGenerator:
    """数字生命体生成器 V2.0（AI驱动）"""

    # 实体类型→ID前缀
    _prefix_map = {
        '阀门': 'VALVE', '法兰': 'FLANGE', '膨胀螺栓': 'BOLT',
        '螺栓': 'BOLT', '卡箍': 'CLAMP', '承重支架': 'SUP',
        '支架': 'SUP', '镀锌钢管': 'PIPE', '管道': 'PIPE',
        '橡胶圈': 'GASKET', '垫片': 'GASKET',
        '套管': 'SLEEVE', '弯头': 'ELBOW', '三通': 'TEE',
        '变径管': 'REDUCER', '联轴器': 'COUPLING',
        '手轮': 'WHEEL', '阀杆': 'STEM',
    }

    _counters: Dict[str, int] = {}

    def __init__(self, ai_connector: Optional[AIConnector] = None):
        # 初始化所有组件
        self.ai = ai_connector or AIConnector()
        self.understanding = AIUnderstanding(self.ai)
        self.mapper = ParamMapper()
        self.injector = RuleInjector()
        self.boundary = BoundaryCalculator()
        self.validator = IntegrityValidator(GenerationManual())
        self.manual = GenerationManual()
        # 延迟初始化 template_matcher（需注入 store）
        self.template_matcher = None

    def set_template_store(self, store):
        """注入模板存储器"""
        self.template_matcher = TemplateMatcher(store)

    # ==================== 主入口 ====================

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        主入口（AI驱动）。

        9步流程：
            1. 参数解析
            2. AI产品理解
            3. 参数补全
            4. 规则推导
            5. 边界计算
            6. 六层注入
            7. 完整性验证
            8. 生成数字生命体
            9. 输出（含生成日志）
        """
        logs = {
            'ai理解': {},
            '联网查询': {},
            '参数补全': {},
            '规则推导': {},
            '完整性验证': {},
        }

        # 1. 参数解析
        product = self._step1_parse(params)

        # 2. AI产品理解
        ai_result = self._step2_ai_understand(product)
        logs['ai理解'] = ai_result

        # 3. 参数补全
        completed = self._step3_complete_params(params, ai_result)
        logs['参数补全'] = completed.get('补全项', {})

        # 4. 规则推导
        rules = self._step4_derive_rules(product, completed)
        logs['规则推导'] = {'规则数': len(rules)}

        # 5. 边界计算
        boundaries = self._step5_calc_boundary(completed)
        logs['联网查询'] = ai_result.get('适用标准', [])

        # 6. 六层注入
        entity = self._step6_inject_layers(product, completed, rules, boundaries)

        # 7. 完整性验证
        validation = self._step7_validate(entity, ai_result.get('产品类型', ''))
        logs['完整性验证'] = {
            'passed': validation.get('passed', False),
            'errors': validation.get('errors', []),
            'warnings': validation.get('warnings', []),
        }

        # 8. 生成数字生命体
        entity['生成日志'] = logs

        # 9. 输出
        return entity

    # ==================== 第1步：参数解析 ====================

    def _step1_parse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参数解析：识别产品类型"""
        product_name = params.get('产品名称', '') or params.get('产品型号', '')
        return {
            '产品名称': product_name,
            '产品型号': params.get('产品型号', ''),
            '厂家': params.get('厂家', ''),
            '规格': params.get('规格', ''),
            '参数': params.get('参数', {}),
            '安装位置': params.get('安装位置', {'x': 0, 'y': 0, 'z': 0}),
        }

    # ==================== 第2步：AI产品理解 ====================

    def _step2_ai_understand(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """AI产品理解"""
        return self.understanding.understand(product)

    # ==================== 第3步：参数补全 ====================

    def _step3_complete_params(self, params: Dict[str, Any],
                                ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """参数补全"""
        original = dict(params.get('参数', {}))
        product_type = ai_result.get('产品类型', '')

        # 从 RULES 取默认参数
        rule = RULES.get(product_type, RULES.get('_default', {}))
        completed = dict(original)
        completed_items = {}

        # 补全常见缺失参数
        default_params = self._get_default_params(product_type)
        for k, v in default_params.items():
            if k not in completed:
                completed[k] = v
                completed_items[k] = v

        return {
            '产品类型': product_type,
            '厂家': params.get('厂家', ''),
            '规格': params.get('规格', ''),
            '参数': completed,
            '安装位置': params.get('安装位置', {'x': 0, 'y': 0, 'z': 0}),
            '补全项': completed_items,
        }

    def _get_default_params(self, product_type: str) -> Dict[str, Any]:
        """获取默认参数"""
        defaults = {
            '阀门': {'外径': 220, '长度': 280, '重量': 15, '材质': '铸钢', '工作压力': '1.6MPa'},
            '法兰': {'外径': 220, '厚度': 24, '螺栓数量': 8, '螺栓孔径': 18, '材质': '铸钢', '压力等级': 'PN16'},
            '膨胀螺栓': {'直径': 12, '长度': 100, '材质': 'Q235B', '拧紧力矩': 20},
            '卡箍': {'外径': 140, '宽度': 60, '重量': 1.2, '材质': '球墨铸铁'},
            '承重支架': {'规格': 'L50×50×6', '材质': 'Q235B', '承重能力': 500},
            '镀锌钢管': {'外径': 114.3, '壁厚': 4.0, '材质': '热浸镀锌钢管', '标准长度': 6000},
            '橡胶圈': {'外径': 220, '内径': 114.3, '厚度': 3, '材质': '三元乙丙(EPDM)', '设计年限': 10},
            '垫片': {'外径': 220, '内径': 114.3, '厚度': 3, '材质': '三元乙丙(EPDM)', '设计年限': 10},
        }
        return defaults.get(product_type, {})

    # ==================== 第4步：规则推导 ====================

    def _step4_derive_rules(self, product: Dict[str, Any],
                             completed: Dict[str, Any]) -> Dict[str, Any]:
        """规则推导"""
        ptype = completed.get('产品类型', '')
        params = completed.get('参数', {})
        return self.injector.inject_all({'产品名称': ptype}, params)

    # ==================== 第5步：边界计算 ====================

    def _step5_calc_boundary(self, completed: Dict[str, Any]) -> Dict[str, Any]:
        """边界计算"""
        product = {'产品名称': completed.get('产品类型', ''), '规格': completed.get('规格', '')}
        params = completed.get('参数', {})
        return self.boundary.calc_all(product, params)

    # ==================== 第6步：六层注入 ====================

    def _step6_inject_layers(self, product: Dict[str, Any],
                              completed: Dict[str, Any],
                              rules: Dict[str, Any],
                              boundaries: Dict[str, Any]) -> Dict[str, Any]:
        """六层注入"""
        ptype = completed.get('产品类型', '未知')
        entity_id = self._gen_id(ptype)
        position = completed.get('安装位置', {'x': 0, 'y': 0, 'z': 0})

        # R层
        r_layer = self.mapper.map_to_r_layer({
            '产品名称': product.get('产品名称', ''),
            '厂家': product.get('厂家', ''),
            'category': '物品',
            '产品型号': product.get('产品型号', ''),
        })

        # L1层
        l1 = self.mapper.map_to_l1_identity({'entity_id': entity_id})

        # L2层
        l2 = self.mapper.map_to_l2_static(
            product,
            completed.get('参数', {}),
            anchors=boundaries.get('锚点', []),
            force_points=boundaries.get('受力点', []),
            contact_faces=boundaries.get('接触面', []),
        )

        # L3层
        l3 = self.mapper.map_to_l3_dynamic(product, position)

        # L4层
        l4 = self.mapper.map_to_l4_events({'厂家': product.get('厂家', '')})

        # CBM层
        cbm = self.mapper.map_to_cbm(product, rules)

        return {
            'id': entity_id,
            'entity_type': ptype,
            'layer': {
                'r_layer': r_layer,
                'l1_identity': l1,
                'l2_static_attributes': l2,
                'l3_dynamic_state': l3,
                'l4_event_chain': l4,
                'cbm_abilities': cbm,
            },
        }

    # ==================== 第7步：完整性验证 ====================

    def _step7_validate(self, entity: Dict[str, Any],
                         entity_type: str) -> Dict[str, Any]:
        """完整性验证"""
        return self.validator.validate(entity, entity_type)

    # ==================== 工具 ====================

    def _gen_id(self, entity_type: str) -> str:
        """生成唯一ID"""
        prefix = self._prefix_map.get(entity_type, 'ENT')
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f'{prefix}-{self._counters[prefix]:03d}'

    # ==================== 批量生成 ====================

    def generate_batch(self, params_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量生成"""
        return [self.generate(p) for p in params_list]

    # ==================== 包装 ====================

    def wrap(self, entity_dict: Dict[str, Any]) -> 'GeneratedEntity':
        """包装为 GeneratedEntity 对象"""
        return GeneratedEntity(entity_dict)

    @classmethod
    def reset_counters(cls):
        """重置计数器"""
        cls._counters = {}


class GeneratedEntity:
    """
    生成的实体包装类。

    让生成的字典兼容 BaseEntity 的接口，支持装配引擎调用。
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.id = data.get('id', '')
        self.entity_type = data.get('entity_type', '')
        self.layer = data.get('layer', {})

    # ==================== 通用方法 ====================

    def get_position(self) -> Dict[str, float]:
        """获取位置"""
        return self.layer.get('l3_dynamic_state', {}).get(
            '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
        )

    def get_attr(self, key: str, default: Any = None) -> Any:
        """获取L2属性"""
        return self.layer.get('l2_static_attributes', {}).get(key, default)

    def get_status(self, key: str, default: Any = None) -> Any:
        """获取L3状态"""
        return self.layer.get('l3_dynamic_state', {}).get(key, default)

    def get_bounding_box(self) -> Dict[str, float]:
        """获取包围盒"""
        l2 = self.layer.get('l2_static_attributes', {})
        return l2.get('包围盒', {'x': 0, 'y': 0, 'z': 0})

    def get_force_points(self) -> List[Dict[str, Any]]:
        """获取受力点"""
        return self.layer.get('l2_static_attributes', {}).get('受力点', [])

    def get_contact_faces(self) -> List[Dict[str, Any]]:
        """获取接触面"""
        return self.layer.get('l2_static_attributes', {}).get('接触面', [])

    # ==================== 状态更新 ====================

    def update_status(self, key: str, value: Any) -> Dict[str, Any]:
        """更新状态"""
        self.layer['l3_dynamic_state'][key] = value
        return {'success': True}

    def move_to(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """移动到新位置"""
        self.layer['l3_dynamic_state']['绝对坐标'] = {'x': x, 'y': y, 'z': z}
        return {'success': True}

    def add_event(self, event: str, detail: str = '') -> Dict[str, Any]:
        """添加L4事件"""
        self.layer['l4_event_chain'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event': event,
            'detail': detail,
        })
        return {'success': True}

    # ==================== 碰撞检测 ====================

    def check_collision(self, other) -> Dict[str, Any]:
        """AABB碰撞检测"""
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

    # ==================== 转字典 ====================

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'layer': self.layer,
            '生成日志': self.data.get('生成日志', {}),
        }