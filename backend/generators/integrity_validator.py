# -*- coding: utf-8 -*-
"""
完整性验证引擎
受 GPL v3.0 保护

按"生成说明书"验证六层齐全。

V2.0 升级（专报C）：
- _check_by_manual 完整实现（逐项检查说明书）
- 新增 _check_validation_rules 执行验证规则
"""

from typing import Dict, Any, List
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

        # ★ V2.0 新增：7. 按说明书检查验证规则
        if entity_type:
            rules_result = self._check_by_manual(entity, entity_type)
            checks.append(rules_result)
            if not rules_result['passed']:
                warnings.extend(rules_result.get('warnings', []))

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
            # ★ V2.0 新增
            '分段规则': ['分段规则'],
            '沟槽': ['沟槽'],
            '封堵要求': ['封堵要求'],
            '墙厚': ['墙厚'],
            # ★ V2.0 新增：设备
            '设备类型': ['设备类型'],
            '型号': ['型号'],
            '功率': ['功率'],
            '可执行任务': ['可执行任务'],
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
            return {'check': '接触面', 'passed': True, 'count': 0}

        # 检查允许偏差
        for cf in cfs:
            if cf.get('允许偏差') and cf.get('允许偏差') != '0mm':
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

        etype = entity.get('entity_type', '')
        non_physical = ['任务', '报表', '模板', '项目', '合同', '图纸',
                        '验收', '变更', '签证', '通知记录', '签字记录',
                        '实测实量', '实测记录', '厂家', '产品', '组织',
                        '设备', '车辆']
        if etype in non_physical:
            return {'check': '受力点', 'passed': True, 'count': 0}

        if not fps:
            warnings.append(f'物理实体 {etype} 建议有受力点')

        for fp in fps:
            if '位置' not in fp:
                warnings.append(f'受力点 {fp.get("id")} 缺少位置')

        return {
            'check': '受力点',
            'passed': True,
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

    # ==================== 按说明书检查（★ V2.0 完整实现）====================

    def _check_by_manual(self, entity: Dict[str, Any],
                         entity_type: str) -> Dict[str, Any]:
        """
        ★ V2.0 完整实现：按说明书逐项检查。

        检查：
            1. 必须包含字段
            2. 验证规则（如"外径必须大于管道外径"）
        """
        manual = self.manual.get(entity_type)
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})

        passed = True
        warnings = []
        errors = []

        # 1. 必须包含字段
        required = manual.get('必须包含', [])
        for field in required:
            field_key = field.split('（')[0]
            if not self._field_exists(l2, field_key):
                errors.append(f'[必须包含] 缺少：{field}')
                passed = False

        # 2. 验证规则
        rules = manual.get('验证规则', [])
        for rule in rules:
            rule_result = self._check_single_rule(entity, rule)
            if not rule_result['passed']:
                warnings.append(f'[验证规则] {rule}：{rule_result["message"]}')

        return {
            'check': f'按说明书检查（{entity_type}）',
            'passed': passed,
            'warnings': warnings,
            'errors': errors,
            'required_count': len(required),
            'rules_count': len(rules),
        }

    def _check_single_rule(self, entity: Dict[str, Any], rule: str) -> Dict[str, Any]:
        """★ V2.0 新增：执行单条验证规则"""
        layer = entity.get('layer', entity)
        l2 = layer.get('l2_static_attributes', {})
        etype = entity.get('entity_type', '')

        # 规则1：外径必须大于管道外径
        if '外径必须大于管道外径' in rule:
            outer = self._parse_mm(l2.get('外径', 0))
            if outer > 0 and outer < 100:
                return {'passed': False, 'message': f'外径{outer}mm 可能小于管道外径'}

        # 规则2：孔径必须大于螺栓直径
        if '孔径必须大于螺栓直径' in rule:
            hole = self._parse_mm(l2.get('螺栓孔径', 0))
            if hole > 0 and hole < 16:
                return {'passed': False, 'message': f'孔径{hole}mm 小于M16螺栓'}

        # 规则3：接触面必须成对出现
        if '接触面必须成对出现' in rule:
            cfs = l2.get('接触面', [])
            if len(cfs) > 0 and len(cfs) % 2 != 0:
                return {'passed': False, 'message': f'接触面数{len(cfs)}不是偶数'}

        # 规则4：10米管道必须分段为6+4
        if '10米管道必须分段为6+4' in rule:
            length = self._parse_mm(l2.get('长度', 0))
            if length == 10000:
                seg = l2.get('分段规则', {})
                if not seg:
                    return {'passed': False, 'message': '缺少分段规则'}

        # 规则5：管道两端必须有沟槽
        if '管道两端必须有沟槽' in rule:
            cfs = l2.get('接触面', [])
            grooves = [c for c in cfs if c.get('类型') == '沟槽']
            if len(grooves) < 2:
                return {'passed': False, 'message': f'沟槽数{len(grooves)}<2'}

        # 规则6：垫片必须5个约束
        if '垫片必须5个约束' in rule:
            constraints = l2.get('约束', [])
            cbm = layer.get('cbm_abilities', {})
            cbm_constraints = cbm.get('规范约束', {}).get('约束', [])
            total = len(constraints) + len(cbm_constraints)
            if total < 5:
                return {'passed': False, 'message': f'约束数{total}<5'}

        # 规则7：套管长度 = 墙厚 + 100mm
        if '套管长度 = 墙厚 + 100mm' in rule:
            wall = self._parse_mm(l2.get('墙厚', 0))
            length = self._parse_mm(l2.get('长度', 0))
            if wall > 0 and length > 0 and length != wall + 100:
                return {'passed': False, 'message': f'长度{length}≠墙厚{wall}+100'}

        # 规则8：间隙必须在20-30mm之间
        if '间隙必须在20-30mm之间' in rule:
            gap = l2.get('间隙', None)
            if gap:
                gap_val = self._parse_mm(gap)
                if gap_val < 20 or gap_val > 30:
                    return {'passed': False, 'message': f'间隙{gap_val}mm不在20-30mm'}

        # 规则9：必须两端封堵
        if '必须两端封堵' in rule:
            sealing = l2.get('封堵要求', '')
            if not sealing:
                return {'passed': False, 'message': '未定义封堵要求'}

        # 规则10：电焊机必须由持证焊工操作
        if '电焊机必须由持证焊工操作' in rule:
            if etype == '设备' and '焊' in str(l2.get('设备类型', '')):
                ops = l2.get('操作人员要求', '')
                if '焊工' not in str(ops):
                    return {'passed': False, 'message': '未指定持证焊工'}

        # 默认：通过
        return {'passed': True, 'message': 'ok'}

    @staticmethod
    def _parse_mm(val) -> float:
        """解析毫米值"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val.replace('mm', '').strip())
            except ValueError:
                return 0.0
        return 0.0