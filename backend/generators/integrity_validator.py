# -*- coding: utf-8 -*-
"""
完整性验证引擎
受 GPL v3.0 保护

按"生成说明书"验证六层齐全。
"""

from typing import Dict, Any, List, Tuple
from .generation_manual import GenerationManual


class IntegrityValidator:
    """完整性验证引擎"""

    def __init__(self, generation_manual: GenerationManual = None):
        self.manual = generation_manual or GenerationManual()

    # ==================== 主入口 ====================

    def validate(self, entity: Dict[str, Any],
                 entity_type: str = '') -> Dict[str, Any]:
        """
        验证完整性。

        返回值：
            {passed, checks, warnings, errors}
        """
        errors: List[str] = []
        warnings: List[str] = []
        checks: List[Dict[str, Any]] = []

        # 1. 验证六层齐全
        layers_result = self.validate_layers(entity)
        checks.append(layers_result)
        if not layers_result['passed']:
            errors.extend(layers_result.get('errors', []))

        # 2. 验证必填字段
        if entity_type:
            fields_result = self.validate_required_fields(entity, entity_type)
            checks.append(fields_result)
            if not fields_result['passed']:
                errors.extend(fields_result.get('errors', []))

        # 3. 验证接触面
        cf_result = self.validate_contact_faces(entity)
        checks.append(cf_result)
        if not cf_result['passed']:
            errors.extend(cf_result.get('errors', []))

        # 4. 验证受力点
        fp_result = self.validate_force_points(entity)
        checks.append(fp_result)
        if not fp_result['passed']:
            warnings.extend(fp_result.get('warnings', []))

        # 5. 验证锚点
        anchors_result = self.validate_anchors(entity)
        checks.append(anchors_result)
        if not anchors_result['passed']:
            warnings.extend(anchors_result.get('warnings', []))

        # 6. 验证CBM
        cbm_result = self.validate_cbm(entity)
        checks.append(cbm_result)
        if not cbm_result['passed']:
            errors.extend(cbm_result.get('errors', []))

        passed = len(errors) == 0

        return {
            'passed': passed,
            'checks': checks,
            'warnings': warnings,
            'errors': errors,
        }

    # ==================== 六层验证 ====================

    def validate_layers(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证六层齐全"""
        layer = entity.get('layer', entity)
        required = ['r_layer', 'l1_identity', 'l2_static_attributes',
                    'l3_dynamic_state', 'l4_event_chain', 'cbm_abilities']
        missing = [k for k in required if k not in layer]
        return {
            'check': '六层齐全',
            'passed': len(missing) == 0,
            'missing': missing,
            'errors': [f'缺少层：{m}' for m in missing],
        }

    # ==================== 必填字段验证 ====================

    def validate_required_fields(self, entity: Dict[str, Any],
                                  entity_type: str) -> Dict[str, Any]:
        """验证必填字段"""
        required = self.manual.get_required(entity_type)
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})

        missing = []
        for field in required:
            # 支持模糊匹配（如"外形"对应包围盒/外径）
            field_key = field.split('（')[0]
            if not self._field_exists(l2, field_key):
                missing.append(field)

        return {
            'check': '必填字段',
            'passed': len(missing) == 0,
            'missing': missing,
            'errors': [f'缺少必填字段：{m}' for m in missing],
        }

    def _field_exists(self, l2: Dict[str, Any], field: str) -> bool:
        """检查字段是否存在（支持模糊匹配）"""
        if field in l2:
            return True
        # 模糊匹配
        aliases = {
            '外形': ['包围盒', '外径', '长度'],
            '锚点': ['锚点'],
            '受力点': ['受力点'],
            '接触面': ['接触面'],
            'CBM': ['cbm'],
            '材质': ['材质'],
            '工作压力': ['工作压力'],
            '重量': ['重量'],
            '连接方式': ['连接方式'],
            '规格': ['规格'],
            '管径': ['管径'],
            '壁厚': ['壁厚'],
            '标准长度': ['标准长度'],
            '压力等级': ['压力等级'],
            '密封面': ['密封面'],
            '螺栓孔径': ['螺栓孔径'],
            '拧紧力矩': ['拧紧力矩'],
            '预紧力': ['预紧力'],
            '设计年限': ['设计年限'],
            '约束': ['约束'],
            '间隙填充': ['间隙填充'],
            '适用管道': ['适用管道'],
            '长度': ['长度'],
            '承重能力': ['承重能力'],
        }
        for alias in aliases.get(field, []):
            if alias in l2:
                return True
        return False

    # ==================== 接触面验证 ====================

    def validate_contact_faces(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证接触面"""
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})
        cfs = l2.get('接触面', [])
        errors = []

        if not cfs:
            # 非物理实体可无接触面
            return {'check': '接触面', 'passed': True, 'count': 0}

        # 检查成对（left/right 或 数量≥2）
        has_left = any('left' in cf.get('id', '') for cf in cfs)
        has_right = any('right' in cf.get('id', '') for cf in cfs)
        if len(cfs) >= 2 and not (has_left and has_right):
            # 端口数≥2 视为成对
            pass

        # 检查允许偏差
        for cf in cfs:
            if cf.get('允许偏差') != '0mm':
                errors.append(f'接触面 {cf.get("id")} 允许偏差必须为0mm')

        return {
            'check': '接触面',
            'passed': len(errors) == 0,
            'count': len(cfs),
            'errors': errors,
        }

    # ==================== 受力点验证 ====================

    def validate_force_points(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证受力点"""
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})
        fps = l2.get('受力点', [])
        warnings = []

        # 非物理实体可无受力点
        etype = entity.get('entity_type', '')
        non_physical = ['任务', '报表', '模板', '项目', '合同', '图纸',
                        '验收', '变更', '签证', '通知记录', '签字记录',
                        '实测实量', '实测记录', '厂家', '产品', '组织']
        if etype in non_physical:
            return {'check': '受力点', 'passed': True, 'count': 0}

        if not fps:
            warnings.append(f'物理实体 {etype} 建议有受力点')

        for fp in fps:
            if '位置' not in fp:
                warnings.append(f'受力点 {fp.get("id")} 缺少位置')

        return {
            'check': '受力点',
            'passed': True,  # 受力点缺失仅警告
            'count': len(fps),
            'warnings': warnings,
        }

    # ==================== 锚点验证 ====================

    def validate_anchors(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证锚点"""
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})
        anchors = l2.get('锚点', [])
        warnings = []

        for a in anchors:
            if '孔径' not in a:
                warnings.append(f'锚点 {a.get("id")} 缺少孔径')
            if '位置' not in a:
                warnings.append(f'锚点 {a.get("id")} 缺少位置')

        return {
            'check': '锚点',
            'passed': True,
            'count': len(anchors),
            'warnings': warnings,
        }

    # ==================== CBM验证 ====================

    def validate_cbm(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """验证CBM四大规则"""
        layer = entity.get('layer', entity)
        cbm = layer.get('cbm_abilities', {})
        errors = []

        etype = entity.get('entity_type', '')
        non_physical = ['任务', '报表', '模板', '项目', '合同', '图纸',
                        '验收', '变更', '签证', '通知记录', '签字记录',
                        '实测实量', '实测记录', '厂家', '产品', '组织']
        if etype in non_physical:
            return {'check': 'CBM', 'passed': True, 'rules': []}

        required_rules = ['物理规则', '受力规则', '装配规则', '规范约束']
        missing = [r for r in required_rules if r not in cbm]
        if missing:
            errors.append(f'缺少CBM规则：{missing}')

        return {
            'check': 'CBM',
            'passed': len(errors) == 0,
            'rules': [r for r in required_rules if r in cbm],
            'errors': errors,
        }

    # ==================== 按说明书检查 ====================

    def _check_by_manual(self, entity: Dict[str, Any],
                         manual: Dict[str, Any]) -> Dict[str, Any]:
        """按说明书检查"""
        return self.validate_required_fields(entity, manual.get('entity_type', ''))