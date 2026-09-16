# -*- coding: utf-8 -*-
"""
校验引擎
受 GPL v3.0 保护

业务数据校验。
含受力点/接触面/CBM校验。
"""

from typing import Dict, Any, List, Optional


class ValidationEngine:
    """校验引擎"""

    # 物理实体类型
    PHYSICAL_TYPES = ['阀门', '法兰', '螺栓', '卡箍', '支架', '管道', '套管',
                      '垫片', '手轮', '阀杆', '弯头', '三通', '变径管', '联轴器',
                      '风管', '桥架', '墙体', '楼板', '地面', '柱子', '吊顶',
                      '吊顶丝杆', '支架吊杆']

    # 非物理实体类型
    NON_PHYSICAL_TYPES = ['任务', '报表', '模板', '项目', '合同', '图纸',
                          '验收', '变更', '签证', '通知记录', '签字记录',
                          '实测实量', '实测记录', '厂家', '产品', '组织', '人员']

    # 偏差阈值（mm）
    THRESHOLD = 5.0

    def __init__(self, config_obj=None):
        self.config = config_obj
        self.contact_check_engine = None

    # ==================== 主入口 ====================

    def validate_all(self, entity, entities: List = None) -> Dict[str, Any]:
        """校验所有项"""
        entities = entities or []
        checks = []
        errors = []
        warnings = []

        # 1. 实体校验
        result = self.validate_entity(entity)
        checks.append(result)
        errors.extend(result.get('errors', []))
        warnings.extend(result.get('warnings', []))

        # 2. 受力点校验
        fp_result = self.validate_force_points(entity)
        checks.append(fp_result)
        errors.extend(fp_result.get('errors', []))
        warnings.extend(fp_result.get('warnings', []))

        # 3. 接触面校验
        cf_result = self.validate_contact_faces(entity)
        checks.append(cf_result)
        errors.extend(cf_result.get('errors', []))
        warnings.extend(cf_result.get('warnings', []))

        # 4. CBM校验
        cbm_result = self.validate_cbm(entity)
        checks.append(cbm_result)
        errors.extend(cbm_result.get('errors', []))
        warnings.extend(cbm_result.get('warnings', []))

        # 5. 管道分段校验
        if getattr(entity, 'entity_type', '') == '管道':
            seg_result = self.validate_pipe_segments(entity)
            checks.append(seg_result)
            errors.extend(seg_result.get('errors', []))

        # 6. 垫片约束校验
        if getattr(entity, 'entity_type', '') == '垫片':
            gasket_result = self.validate_gasket(entity)
            checks.append(gasket_result)
            errors.extend(gasket_result.get('errors', []))

        return {
            'passed': len(errors) == 0,
            'checks': checks,
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== 实体校验 ====================

    def validate_entity(self, entity) -> Dict[str, Any]:
        """校验实体六层完整性"""
        errors = []
        warnings = []

        # 调用六层校验
        try:
            from six_layer_core import SixLayerValidator
            validator = SixLayerValidator()
            layer = getattr(entity, 'layer', entity)
            if isinstance(layer, dict):
                is_valid, msgs = validator.validate_entity(layer)
                if not is_valid:
                    errors.extend(msgs)
        except Exception as e:
            warnings.append(f'六层校验异常：{e}')

        return {
            'check': '实体完整性',
            'passed': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== 碰撞校验 ====================

    def validate_collision(self, entity, entities: List) -> Dict[str, Any]:
        """校验碰撞"""
        collisions = []
        for other in entities:
            if other is entity:
                continue
            try:
                if hasattr(entity, 'check_collision'):
                    result = entity.check_collision(other)
                    if result.get('collision'):
                        collisions.append(getattr(other, 'id', ''))
            except Exception:
                continue
        return {
            'check': '碰撞校验',
            'passed': len(collisions) == 0,
            'collisions': collisions,
        }

    # ==================== 装配校验 ====================

    def validate_assembly(self, part, target) -> Dict[str, Any]:
        """校验装配"""
        if part is None or target is None:
            return {'check': '装配校验', 'passed': False, 'message': '零件或目标为空'}

        # 孔径匹配
        part_d = self._get_diameter(part)
        hole_d = self._get_max_hole(target)

        if part_d is None or hole_d is None:
            return {'check': '装配校验', 'passed': True}

        passed = (part_d + 0.5) <= hole_d
        return {
            'check': '装配校验',
            'passed': passed,
            'message': f'{part_d}+0.5 {("<=" if passed else ">")} {hole_d}',
        }

    # ==================== 位置校验 ====================

    def validate_position(self, entity) -> Dict[str, Any]:
        """校验位置"""
        pos = self._get_position(entity)
        x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)

        passed = (
            -100000 <= x <= 100000 and
            -100000 <= y <= 100000 and
            -1000 <= z <= 10000
        )
        return {
            'check': '位置校验',
            'passed': passed,
            'position': pos,
            'message': f'位置：({x}, {y}, {z})',
        }

    # ==================== 受力点校验 ====================

    def validate_force_points(self, entity) -> Dict[str, Any]:
        """校验受力点"""
        etype = getattr(entity, 'entity_type', '')
        errors = []
        warnings = []

        if etype in self.NON_PHYSICAL_TYPES:
            return {'check': '受力点', 'passed': True}

        fps = self._get_force_points(entity)
        if not fps:
            warnings.append(f'物理实体 {etype} 缺少受力点')

        for fp in fps:
            if '位置' not in fp:
                errors.append(f'受力点 {fp.get("id", "?")} 缺少位置')
            if '承重上限' not in fp:
                warnings.append(f'受力点 {fp.get("id", "?")} 缺少承重上限')

        return {
            'check': '受力点',
            'passed': len(errors) == 0,
            'count': len(fps),
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== 接触面校验 ====================

    def validate_contact_faces(self, entity) -> Dict[str, Any]:
        """校验接触面"""
        etype = getattr(entity, 'entity_type', '')
        errors = []
        warnings = []

        if etype in self.NON_PHYSICAL_TYPES:
            return {'check': '接触面', 'passed': True}

        cfs = self._get_contact_faces(entity)
        if not cfs:
            warnings.append(f'物理实体 {etype} 缺少接触面')

        for cf in cfs:
            if cf.get('允许偏差') != '0mm':
                errors.append(f'接触面 {cf.get("id", "?")} 允许偏差必须为0mm')

        return {
            'check': '接触面',
            'passed': len(errors) == 0,
            'count': len(cfs),
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== CBM校验 ====================

    def validate_cbm(self, entity) -> Dict[str, Any]:
        """校验CBM"""
        etype = getattr(entity, 'entity_type', '')
        errors = []

        if etype in self.NON_PHYSICAL_TYPES:
            return {'check': 'CBM', 'passed': True}

        cbm = self._get_cbm(entity)
        required_rules = ['物理规则', '受力规则', '装配规则', '规范约束']
        missing = [r for r in required_rules if r not in cbm]
        if missing:
            errors.append(f'缺少CBM规则：{missing}')

        return {
            'check': 'CBM',
            'passed': len(errors) == 0,
            'errors': errors,
        }

    # ==================== 管道分段校验 ====================

    def validate_pipe_segments(self, entity) -> Dict[str, Any]:
        """校验管道分段"""
        errors = []

        length_mm = 0
        if hasattr(entity, 'layer'):
            length_mm = entity.layer.get('l3_dynamic_state', {}).get('长度', 0)

        if length_mm <= 6000:
            return {'check': '管道分段', 'passed': True, 'segments': [length_mm]}

        # 10米管道 = 6+4
        segments = []
        remaining = length_mm
        while remaining > 6000:
            segments.append(6000)
            remaining -= 6000
        if remaining > 0:
            segments.append(remaining)

        # 检查 L2 是否有分段规则
        has_segments = False
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            if '分段规则' in l2:
                has_segments = True

        if not has_segments:
            errors.append('超过6米的管道必须分段（10米=6+4+卡箍）')

        return {
            'check': '管道分段',
            'passed': len(errors) == 0,
            'segments': segments,
            'errors': errors,
        }

    # ==================== 垫片约束校验 ====================

    def validate_gasket(self, entity) -> Dict[str, Any]:
        """校验垫片约束"""
        errors = []
        constraints = []
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            constraints = l2.get('约束', [])

        if len(constraints) < 5:
            errors.append(f'垫片必须有5个约束（位置/范围/孔径/方向/数量），当前{len(constraints)}个')

        return {
            'check': '垫片约束',
            'passed': len(errors) == 0,
            'count': len(constraints),
            'errors': errors,
        }

    # ==================== 工具方法 ====================

    def _get_force_points(self, entity) -> List[Dict[str, Any]]:
        if hasattr(entity, 'get_force_points'):
            return entity.get_force_points()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l2_static_attributes', {}).get('受力点', [])
        return []

    def _get_contact_faces(self, entity) -> List[Dict[str, Any]]:
        if hasattr(entity, 'get_contact_faces'):
            return entity.get_contact_faces()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l2_static_attributes', {}).get('接触面', [])
        return []

    def _get_cbm(self, entity) -> Dict[str, Any]:
        if hasattr(entity, 'layer'):
            return entity.layer.get('cbm_abilities', {})
        return {}

    def _get_position(self, entity) -> Dict[str, float]:
        if hasattr(entity, 'get_position'):
            return entity.get_position()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l3_dynamic_state', {}).get(
                '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
            )
        return {'x': 0, 'y': 0, 'z': 0}

    def _get_diameter(self, entity) -> Optional[float]:
        if hasattr(entity, 'diameter'):
            return float(entity.diameter)
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            for key in ['直径', '外径']:
                if key in l2:
                    try:
                        return float(str(l2[key]).replace('mm', '').strip())
                    except ValueError:
                        pass
        return None

    def _get_max_hole(self, entity) -> Optional[float]:
        if hasattr(entity, 'bolt_hole_diameter'):
            return float(entity.bolt_hole_diameter)
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            if '螺栓孔径' in l2:
                try:
                    return float(str(l2['螺栓孔径']).replace('mm', '').strip())
                except ValueError:
                    pass
        return None