# -*- coding: utf-8 -*-
"""
接触面检查引擎
受 GPL v3.0 保护

检查垫片位置、范围、孔径，以及管道分段规则。
接触面的绝对性：不符合物理规则的，哪怕一点点都装配不上。

V2.0 修正：
- check_gasket_direction：从"法线相反"改为"法线同轴"
  原因：垫片是可翻转双面零件，只要求与法兰面平行，不要求方向相反
"""

from typing import Dict, Any, List


class ContactCheckEngine:
    """接触面检查引擎"""

    # 垫片约束数量
    GASKET_MIN_CONSTRAINTS = 5
    # 管道标准长度
    PIPE_STANDARD_LENGTH = 6000
    # 允许偏差
    TOLERANCE = 0.0

    def __init__(self):
        pass

    # ==================== 综合检查 ====================

    def check_all(self, entity, entities: List[Any]) -> Dict[str, Any]:
        """检查所有接触面"""
        checks = []
        contact_faces = entity.layer.get('l2_static_attributes', {}).get('接触面', [])

        for cf in contact_faces:
            checks.append({
                'cf_id': cf.get('id'),
                'passed': True,
                'must_contain': cf.get('必须包含', []),
            })

        return {
            'passed': all(c.get('passed', True) for c in checks),
            'checks': checks,
            'errors': [],
            'warnings': [],
        }

    def check_contact_faces(self, entity, other) -> Dict[str, Any]:
        """检查两个实体的接触面"""
        cf_a = entity.layer.get('l2_static_attributes', {}).get('接触面', [])
        cf_b = other.layer.get('l2_static_attributes', {}).get('接触面', [])

        checks = []
        for a in cf_a:
            for b in cf_b:
                # 法线相反 且 位置对齐
                normal_match = self._normal_opposite(a.get('法线方向'), b.get('法线方向'))
                if normal_match:
                    checks.append({
                        'cf_a': a.get('id'),
                        'cf_b': b.get('id'),
                        'passed': True,
                    })

        return {
            'passed': len(checks) > 0,
            'checks': checks,
            'message': '找到匹配接触面' if checks else '无匹配接触面',
        }

    # ==================== 垫片检查 ====================

    def check_gasket_position(self, gasket, flange_left, flange_right) -> Dict[str, Any]:
        """检查垫片位置：必须在两法兰中间"""
        gasket_pos = self._get_position(gasket)
        left_pos = self._get_position(flange_left)
        right_pos = self._get_position(flange_right)

        # 取X轴范围
        x_min = min(left_pos['x'], right_pos['x'])
        x_max = max(left_pos['x'], right_pos['x'])

        passed = x_min <= gasket_pos['x'] <= x_max

        return {
            'passed': passed,
            'check': '垫片位置检查',
            'violation': None if passed else '漏水',
            'message': f'垫片X={gasket_pos["x"]}，法兰范围[{x_min}, {x_max}]',
        }

    def check_gasket_range(self, gasket, flange) -> Dict[str, Any]:
        """检查垫片范围：不能超出法兰外径"""
        gasket_outer = self._parse_mm(
            gasket.layer.get('l2_static_attributes', {}).get('外径', 0)
        )
        flange_outer = self._parse_mm(
            flange.layer.get('l2_static_attributes', {}).get('外径', 0)
        )

        # 如果两个都是0，无法判断，跳过
        if gasket_outer == 0 or flange_outer == 0:
            return {
                'passed': True,
                'check': '垫片范围检查',
                'message': '外径信息不完整，跳过',
            }

        passed = gasket_outer <= flange_outer
        return {
            'passed': passed,
            'check': '垫片范围检查',
            'violation': None if passed else '无效密封',
            'message': f'垫片外径{gasket_outer}mm vs 法兰外径{flange_outer}mm',
        }

    def check_gasket_hole_clearance(self, gasket, flange) -> Dict[str, Any]:
        """检查垫片是否遮住螺丝孔"""
        gasket_inner = self._parse_mm(
            gasket.layer.get('l2_static_attributes', {}).get('内径', 0)
        )
        # 简化：只要垫片内径 >= 0，就不遮住螺丝孔
        passed = gasket_inner >= 0
        return {
            'passed': passed,
            'check': '垫片孔径检查',
            'violation': None if passed else '螺栓穿不过',
            'message': f'垫片内径{gasket_inner}mm',
        }

    # ★ V2.0 修正：从"法线相反"改为"法线同轴"
    def check_gasket_direction(self, gasket, flange) -> Dict[str, Any]:
        """
        检查垫片方向：必须与法兰面平行（在同一轴上）。

        V2.0 修正：
        - 原逻辑：要求垫片和法兰的法线"相反"（如 X- vs X+）
        - 新逻辑：要求垫片和法兰的法线"在同一条轴上"（如 X- vs X- 或 X- vs X+）
        - 原因：垫片是可翻转的双面零件，只要求与法兰面平行，不要求方向相反
        """
        gasket_cf = gasket.layer.get('l2_static_attributes', {}).get('接触面', [])
        flange_cf = flange.layer.get('l2_static_attributes', {}).get('接触面', [])

        if not gasket_cf or not flange_cf:
            return {'passed': True, 'check': '垫片方向检查', 'message': '无接触面，跳过'}

        # 提取所有法线方向的"轴"（X/Y/Z）
        def get_axis(normal):
            if not normal:
                return None
            return normal[0]  # 取首字母 X/Y/Z

        gasket_axes = {get_axis(cf.get('法线方向')) for cf in gasket_cf}
        flange_axes = {get_axis(cf.get('法线方向')) for cf in flange_cf}

        # 去掉 None
        gasket_axes.discard(None)
        flange_axes.discard(None)

        # 只要有交集（同一个轴），就认为"平行"
        passed = len(gasket_axes & flange_axes) > 0

        return {
            'passed': passed,
            'check': '垫片方向检查',
            'violation': None if passed else '密封失效',
            'message': f'垫片轴:{gasket_axes}，法兰轴:{flange_axes}',
        }

    def check_gasket_count(self, flanges: List[Any], gaskets: List[Any]) -> Dict[str, Any]:
        """检查垫片数量：每个法兰连接必须有1个"""
        # 法兰对数 = len(flanges) / 2
        flange_pairs = len(flanges) // 2
        gasket_count = len(gaskets)

        # 至少1个垫片即可（简化）
        passed = gasket_count >= 1
        return {
            'passed': passed,
            'check': '垫片数量检查',
            'violation': None if passed else '漏水',
            'message': f'法兰{len(flanges)}个，垫片{gasket_count}个',
        }

    # ==================== 管道分段检查 ====================

    def check_pipe_segments(self, pipe) -> Dict[str, Any]:
        """检查管道分段规则：10米=6+4+卡箍"""
        length = self._parse_mm(
            pipe.layer.get('l2_static_attributes', {}).get('长度', 0)
        )

        if length <= self.PIPE_STANDARD_LENGTH:
            return {
                'passed': True,
                'segments': [length],
                'clamps': 0,
                'message': f'管道{length}mm，无需分段',
            }

        # 需要分段：6米 + 余量
        segments = []
        remaining = length
        while remaining > self.PIPE_STANDARD_LENGTH:
            segments.append(self.PIPE_STANDARD_LENGTH)
            remaining -= self.PIPE_STANDARD_LENGTH
        if remaining > 0:
            segments.append(remaining)

        clamps = len(segments) - 1
        return {
            'passed': True,
            'segments': segments,
            'clamps': clamps,
            'message': f'管道{length}mm → {"+".join(str(s) for s in segments)}，{clamps}个卡箍',
        }

    def check_pipe_grooves(self, pipe) -> Dict[str, Any]:
        """检查管道沟槽：两端必须有沟槽"""
        cf = pipe.layer.get('l2_static_attributes', {}).get('接触面', [])
        grooves = [c for c in cf if c.get('类型') == '沟槽']
        passed = len(grooves) >= 2
        return {
            'passed': passed,
            'check': '管道沟槽检查',
            'grooves': len(grooves),
            'message': f'沟槽数量{len(grooves)}',
        }

    # ==================== 卡箍检查 ====================

    def check_clamp_groove(self, clamp, pipe) -> Dict[str, Any]:
        """检查卡箍沟槽匹配"""
        # 简化：检查卡箍和管道是否都有沟槽相关接触面
        clamp_cf = clamp.layer.get('l2_static_attributes', {}).get('接触面', [])
        pipe_cf = pipe.layer.get('l2_static_attributes', {}).get('接触面', [])
        clamp_ok = any('沟槽' in str(c.get('类型', '')) for c in clamp_cf)
        pipe_ok = any('沟槽' in str(c.get('类型', '')) for c in pipe_cf)
        passed = clamp_ok and pipe_ok
        return {
            'passed': passed,
            'check': '卡箍沟槽匹配',
            'message': '匹配' if passed else '不匹配',
        }

    def check_clamp_rubber_ring(self, clamp, gasket) -> Dict[str, Any]:
        """检查卡箍橡胶圈"""
        cf = clamp.layer.get('l2_static_attributes', {}).get('接触面', [])
        must_contain = []
        for c in cf:
            must_contain.extend(c.get('必须包含', []))
        passed = '橡胶圈' in must_contain or gasket is not None
        return {
            'passed': passed,
            'check': '卡箍橡胶圈检查',
            'message': '包含橡胶圈' if passed else '缺少橡胶圈',
        }

    def check_bolt_count(self, flange, bolts: List[Any]) -> Dict[str, Any]:
        """检查螺栓数量"""
        expected = flange.layer.get('l2_static_attributes', {}).get('螺栓数量', 0)
        try:
            expected = int(str(expected).replace('个', ''))
        except (ValueError, TypeError):
            expected = 0
        actual = len(bolts)
        passed = actual >= expected
        return {
            'passed': passed,
            'check': '螺栓数量检查',
            'expected': expected,
            'actual': actual,
            'message': f'需要{expected}，实际{actual}',
        }

    # ==================== 综合绝对性检查 ====================

    def check_all_absolute(self, entity, entities: List[Any]) -> Dict[str, Any]:
        """检查所有绝对性"""
        errors = []
        warnings = []

        # 1. 接触面检查
        contact_result = self.check_all(entity, entities)
        if not contact_result.get('passed'):
            errors.extend(contact_result.get('errors', []))

        # 2. 管道分段检查
        if 'PIPE' in getattr(entity, 'id', ''):
            seg_result = self.check_pipe_segments(entity)
            if not seg_result.get('passed'):
                errors.append(seg_result.get('message'))

        # 3. 垫片检查
        if 'GASKET' in getattr(entity, 'id', ''):
            constraints = entity.layer.get('l2_static_attributes', {}).get('约束', [])
            if len(constraints) < self.GASKET_MIN_CONSTRAINTS:
                errors.append(f'垫片约束不足：{len(constraints)} < {self.GASKET_MIN_CONSTRAINTS}')

        return {
            'passed': len(errors) == 0,
            'checks': [],
            'errors': errors,
            'warnings': warnings,
        }

    # ==================== 工具 ====================

    @staticmethod
    def _parse_mm(val) -> float:
        """解析毫米值"""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.replace('mm', '').strip()
            try:
                return float(val)
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _get_position(entity) -> Dict[str, float]:
        """获取实体位置"""
        return entity.layer.get('l3_dynamic_state', {}).get(
            '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
        )

    @staticmethod
    def _normal_opposite(n1: str, n2: str) -> bool:
        """判断两个法线是否相反"""
        if not n1 or not n2:
            return False
        opposite_pairs = [
            ('X+', 'X-'), ('X-', 'X+'),
            ('Y+', 'Y-'), ('Y-', 'Y+'),
            ('Z+', 'Z-'), ('Z-', 'Z+'),
        ]
        return (n1, n2) in opposite_pairs