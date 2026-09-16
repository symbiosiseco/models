# -*- coding: utf-8 -*-
"""
模板引擎
受 GPL v3.0 保护

模板验证和转换。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class TemplateEngine:
    """模板引擎"""

    # 物理实体类型
    PHYSICAL_TYPES = ['阀门', '法兰', '螺栓', '卡箍', '支架', '管道', '套管',
                      '垫片', '手轮', '阀杆', '弯头', '三通', '变径管', '联轴器']

    def __init__(self, template_store=None):
        self.template_store = template_store
        self.event_bus = None

    # ==================== 验证模板 ====================

    def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板完整性"""
        errors: List[str] = []
        warnings: List[str] = []
        checks: List[Dict[str, Any]] = []

        # 1. 检查必填字段
        fields_check = self._check_required_fields(template)
        checks.append(fields_check)
        errors.extend(fields_check.get('errors', []))

        # 2. 检查受力点
        fp_check = self._check_force_points(template)
        checks.append(fp_check)
        warnings.extend(fp_check.get('warnings', []))

        # 3. 检查接触面
        cf_check = self._check_contact_faces(template)
        checks.append(cf_check)
        warnings.extend(cf_check.get('warnings', []))

        # 4. 检查CBM
        cbm_check = self._check_cbm(template)
        checks.append(cbm_check)
        errors.extend(cbm_check.get('errors', []))

        # 5. 检查硬性要求
        req_check = self._check_hard_requirements(template)
        checks.append(req_check)
        warnings.extend(req_check.get('warnings', []))

        return {
            'success': len(errors) == 0,
            'checks': checks,
            'errors': errors,
            'warnings': warnings,
        }

    def _check_required_fields(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """检查必填字段"""
        required = ['template_id', 'entity_type', 'params']
        missing = [k for k in required if k not in template]
        return {
            'check': '必填字段',
            'passed': len(missing) == 0,
            'missing': missing,
            'errors': [f'缺少：{m}' for m in missing],
        }

    def _check_force_points(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """检查受力点"""
        etype = template.get('entity_type', '')
        fps = template.get('force_points', [])
        warnings = []
        if etype in self.PHYSICAL_TYPES and not fps:
            warnings.append(f'物理实体 {etype} 建议有受力点')
        return {
            'check': '受力点',
            'passed': True,
            'count': len(fps),
            'warnings': warnings,
        }

    def _check_contact_faces(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """检查接触面"""
        etype = template.get('entity_type', '')
        cfs = template.get('contact_faces', [])
        warnings = []
        if etype in self.PHYSICAL_TYPES and not cfs:
            warnings.append(f'物理实体 {etype} 建议有接触面')
        return {
            'check': '接触面',
            'passed': True,
            'count': len(cfs),
            'warnings': warnings,
        }

    def _check_cbm(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """检查CBM"""
        etype = template.get('entity_type', '')
        cbm = template.get('cbm', {})
        errors = []
        if etype in self.PHYSICAL_TYPES:
            required_rules = ['物理规则', '受力规则', '装配规则', '规范约束']
            missing = [r for r in required_rules if r not in cbm]
            if missing:
                errors.append(f'缺少CBM规则：{missing}')
        return {
            'check': 'CBM',
            'passed': len(errors) == 0,
            'errors': errors,
        }

    def _check_hard_requirements(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """检查硬性要求"""
        req = template.get('硬性要求', {})
        warnings = []
        if not req:
            warnings.append('建议添加"硬性要求"字段')
        return {
            'check': '硬性要求',
            'passed': True,
            'warnings': warnings,
        }

    # ==================== 模板转实体 ====================

    def convert_to_entity(self, template: Dict[str, Any],
                           position: Optional[Dict] = None) -> Dict[str, Any]:
        """模板转实体"""
        position = position or {'x': 0, 'y': 0, 'z': 0}
        entity_type = template.get('entity_type', '')

        # 生成 L1层 ID
        prefix = self._prefix(entity_type)
        entity_id = f'{prefix}-{self._next_count(prefix):03d}'

        # 组装六层
        r_layer = {
            '类别': entity_type,
            '厂家': template.get('manufacturer', ''),
            '模板ID': template.get('template_id', ''),
            '模板名': template.get('name', ''),
        }

        l1 = {
            '唯一ID': entity_id,
            '存在锚点': '不可替换',
            '模板ID': template.get('template_id', ''),
        }

        l2 = dict(template.get('params', {}))
        l2['锚点'] = template.get('anchors', [])
        l2['受力点'] = template.get('force_points', [])
        l2['接触面'] = template.get('contact_faces', [])

        l3 = {
            '绝对坐标': position,
            '状态': '待装配',
            '受力点实时坐标': [],
        }

        l4 = [
            {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event': '实例化',
                'detail': f'从模板 {template.get("template_id")} 实例化',
            }
        ]

        return {
            'id': entity_id,
            'entity_type': entity_type,
            'layer': {
                'r_layer': r_layer,
                'l1_identity': l1,
                'l2_static_attributes': l2,
                'l3_dynamic_state': l3,
                'l4_event_chain': l4,
                'cbm_abilities': template.get('cbm', {}),
            },
        }

    # ==================== 实体转模板 ====================

    def extract_template(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """实体转模板"""
        layer = entity.get('layer', entity)
        r = layer.get('r_layer', {})
        l2 = layer.get('l2_static_attributes', {})
        cbm = layer.get('cbm_abilities', {})

        return {
            'template_id': f'TPL-{r.get("类别", "UNKNOWN")}',
            'entity_type': r.get('类别', ''),
            'name': r.get('模板名', ''),
            'manufacturer': r.get('厂家', ''),
            'params': {k: v for k, v in l2.items()
                       if k not in ('锚点', '受力点', '接触面', '包围盒')},
            'anchors': l2.get('锚点', []),
            'force_points': l2.get('受力点', []),
            'contact_faces': l2.get('接触面', []),
            'cbm': cbm,
        }

    # ==================== 合并模板 ====================

    def merge_templates(self, t1: Dict[str, Any], t2: Dict[str, Any]) -> Dict[str, Any]:
        """合并两个模板（t2优先）"""
        merged = dict(t1)
        for k, v in t2.items():
            merged[k] = v
        return merged

    # ==================== 内部方法 ====================

    def _prefix(self, entity_type: str) -> str:
        """实体类型→前缀"""
        mapping = {
            '阀门': 'VALVE', '法兰': 'FLANGE', '螺栓': 'BOLT', '卡箍': 'CLAMP',
            '支架': 'SUP', '管道': 'PIPE', '套管': 'SLEEVE', '垫片': 'GASKET',
        }
        return mapping.get(entity_type, 'ENT')

    _counters: Dict[str, int] = {}

    def _next_count(self, prefix: str) -> int:
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return self._counters[prefix]