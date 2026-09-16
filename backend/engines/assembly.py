# -*- coding: utf-8 -*-
"""
装配约束引擎
受 GPL v3.0 保护

检查零件能否装配到目标。
含接触面检查 + 垫片检查。

核心原则：
- 孔径匹配：螺栓直径 + 公差（0.5mm） ≤ 目标孔径
- M16 + 0.5 = 16.5 ≤ 18 ✅
- M20 + 0.5 = 20.5 > 18 ❌
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class AssemblyEngine:
    """装配约束引擎"""

    # 螺栓与孔的公差
    FIT_TOLERANCE = 0.5

    # 目标可接收装配的状态
    ACCEPTABLE_STATUSES = ['待装配', '已安装', '待接收']

    def __init__(self, contact_check_engine=None):
        self.contact_check_engine = contact_check_engine
        self.check_history: List[Dict[str, Any]] = []

    # ==================== 主入口 ====================

    def check_assembly(self, part, target) -> Dict[str, Any]:
        """
        检查装配条件。

        检查：
            1. 孔径匹配
            2. 目标状态
            3. 类型兼容
            4. 接触面检查
            5. 垫片检查
        """
        if part is None or target is None:
            return {'success': False, 'checks': [], 'message': '零件或目标为空'}

        checks = []

        # 1. 孔径匹配
        hole_check = self._check_hole_fit(part, target)
        checks.append(hole_check)
        if not hole_check['passed']:
            return {'success': False, 'checks': checks, 'message': hole_check['message']}

        # 2. 目标状态
        status_check = self._check_target_status(target)
        checks.append(status_check)
        if not status_check['passed']:
            return {'success': False, 'checks': checks, 'message': status_check['message']}

        # 3. 类型兼容
        type_check = self._check_type_compatibility(part, target)
        checks.append(type_check)
        if not type_check['passed']:
            return {'success': False, 'checks': checks, 'message': type_check['message']}

        # 4. 接触面检查
        if self.contact_check_engine:
            contact_check = self._check_contact_faces(part, target)
            checks.append(contact_check)
            if not contact_check['passed']:
                return {'success': False, 'checks': checks, 'message': contact_check['message']}

        # 5. 垫片检查（如果是法兰装配）
        gasket_check = self._check_gasket(part, target, [])
        checks.append(gasket_check)
        if not gasket_check['passed']:
            return {'success': False, 'checks': checks, 'message': gasket_check['message']}

        return {'success': True, 'checks': checks, 'message': '所有检查通过'}

    def assemble(self, part, target, entities: Optional[List] = None) -> Dict[str, Any]:
        """
        执行装配。

        通过 → part.move_to(target位置) + 状态="已装配" + 写L4
        失败 → part留在原地 + 写L4（失败原因）
        """
        result = self.check_assembly(part, target)

        if result['success']:
            # 更新零件位置
            self._update_position(part, target)
            # 写L4
            self._write_l4(part, target, result)
            return {
                'success': True,
                'checks': result['checks'],
                'message': '装配成功',
                'part_id': getattr(part, 'id', None),
                'target_id': getattr(target, 'id', None),
            }
        else:
            # 写L4（失败）
            self._write_l4(part, target, result)
            return {
                'success': False,
                'checks': result['checks'],
                'message': result['message'],
                'part_id': getattr(part, 'id', None),
                'target_id': getattr(target, 'id', None),
            }

    # ==================== 孔径匹配 ====================

    def _check_hole_fit(self, part, target) -> Dict[str, Any]:
        """检查孔径匹配"""
        # 获取零件直径
        part_d = self._get_diameter(part)
        if part_d is None:
            return {'passed': True, 'check': '孔径匹配', 'message': '零件无直径信息，跳过'}

        # 获取目标最大孔径
        hole_d = self._get_max_hole(target)
        if hole_d is None:
            return {'passed': True, 'check': '孔径匹配', 'message': '目标无孔径信息，跳过'}

        passed = (part_d + self.FIT_TOLERANCE) <= hole_d
        return {
            'passed': passed,
            'check': '孔径匹配',
            'part_diameter': part_d,
            'hole_diameter': hole_d,
            'tolerance': self.FIT_TOLERANCE,
            'message': (
                f'{part_d}+{self.FIT_TOLERANCE}<= {hole_d}，可以穿过'
                if passed else
                f'{part_d}+{self.FIT_TOLERANCE}>{hole_d}，无法穿过'
            ),
        }

    def _get_diameter(self, entity) -> Optional[float]:
        """获取实体直径（螺栓直径）"""
        if hasattr(entity, 'diameter'):
            return float(entity.diameter)
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            for key in ['直径', '外径', '管径']:
                if key in l2:
                    return self._parse_mm(l2[key])
        return None

    def _get_max_hole(self, entity) -> Optional[float]:
        """获取目标最大孔径"""
        if hasattr(entity, 'bolt_hole_diameter'):
            return float(entity.bolt_hole_diameter)
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            if '螺栓孔径' in l2:
                return self._parse_mm(l2['螺栓孔径'])
            # 从锚点获取
            anchors = l2.get('锚点', [])
            if anchors:
                holes = [a.get('孔径', 0) for a in anchors if a.get('孔径')]
                if holes:
                    return float(max(holes))
            cbm = entity.layer.get('cbm_abilities', {})
            if '装配规则' in cbm and '孔径' in cbm['装配规则']:
                return float(cbm['装配规则']['孔径'])
        return None

    # ==================== 目标状态 ====================

    def _check_target_status(self, target) -> Dict[str, Any]:
        """检查目标状态"""
        if hasattr(target, 'get_status'):
            status = target.get_status('状态', '待装配')
        elif hasattr(target, 'layer'):
            status = target.layer.get('l3_dynamic_state', {}).get('状态', '待装配')
        else:
            status = '待装配'

        passed = status in self.ACCEPTABLE_STATUSES
        return {
            'passed': passed,
            'check': '目标状态',
            'status': status,
            'message': f'目标状态：{status}' if passed else f'目标状态不可接收：{status}',
        }

    # ==================== 类型兼容 ====================

    def _check_type_compatibility(self, part, target) -> Dict[str, Any]:
        """检查类型兼容"""
        p_type = getattr(part, 'entity_type', '')
        t_type = getattr(target, 'entity_type', '')

        # 兼容矩阵
        compatible = {
            '膨胀螺栓': ['法兰', '支架', '楼板', '地面'],
            '螺栓': ['法兰', '支架'],
            '法兰': ['阀门', '管道', '法兰'],
            '垫片': ['法兰'],
            '卡箍': ['管道'],
            '阀门': ['法兰', '管道'],
        }

        allowed = compatible.get(p_type, [])
        passed = t_type in allowed or not allowed

        return {
            'passed': passed,
            'check': '类型兼容',
            'part_type': p_type,
            'target_type': t_type,
            'message': f'{p_type}→{t_type}兼容' if passed else f'{p_type}无法装到{t_type}',
        }

    def _is_compatible(self, part_type: str, target_type: str) -> bool:
        """判断类型兼容"""
        compatible = {
            '膨胀螺栓': ['法兰', '支架'],
            '螺栓': ['法兰', '支架'],
            '法兰': ['阀门', '管道'],
            '垫片': ['法兰'],
            '卡箍': ['管道'],
        }
        return target_type in compatible.get(part_type, [])

    # ==================== 接触面检查 ====================

    def _check_contact_faces(self, part, target) -> Dict[str, Any]:
        """检查接触面"""
        if not self.contact_check_engine:
            return {'passed': True, 'check': '接触面检查'}
        try:
            result = self.contact_check_engine.check_contact_faces(part, target)
            return {
                'passed': result.get('passed', True),
                'check': '接触面检查',
                'message': result.get('message', ''),
            }
        except Exception as e:
            return {'passed': True, 'check': '接触面检查', 'message': f'接触面检查异常：{e}'}

    # ==================== 垫片检查 ====================

    def _check_gasket(self, part, target, entities: List) -> Dict[str, Any]:
        """检查垫片"""
        p_type = getattr(part, 'entity_type', '')
        t_type = getattr(target, 'entity_type', '')

        # 只有法兰连接才需要垫片
        if '法兰' not in (p_type, t_type):
            return {'passed': True, 'check': '垫片检查', 'message': '非法兰连接，跳过'}

        # 检查接触面是否要求垫片
        if hasattr(target, 'get_contact_faces'):
            for cf in target.get_contact_faces():
                if '垫片' in cf.get('必须包含', []):
                    # 场景里有垫片则视为通过
                    has_gasket = any(
                        getattr(e, 'entity_type', '') == '垫片'
                        for e in entities
                    )
                    return {
                        'passed': has_gasket,
                        'check': '垫片检查',
                        'message': '有垫片' if has_gasket else '缺少垫片',
                    }
        return {'passed': True, 'check': '垫片检查', 'message': '无需垫片'}

    # ==================== 更新位置 ====================

    def _update_position(self, part, target) -> Dict[str, Any]:
        """更新零件位置"""
        target_pos = target.get_position() if hasattr(target, 'get_position') else {'x': 0, 'y': 0, 'z': 0}
        if hasattr(part, 'move_to'):
            part.move_to(target_pos['x'], target_pos['y'], target_pos['z'])
        elif hasattr(part, 'layer'):
            part.layer['l3_dynamic_state']['绝对坐标'] = target_pos
        if hasattr(part, 'update_status'):
            part.update_status('状态', '已装配')
        return {'success': True}

    # ==================== 写L4 ====================

    def _write_l4(self, part, target, result: Dict[str, Any]) -> Dict[str, Any]:
        """写L4事件"""
        if hasattr(part, 'add_event'):
            part.add_event(
                '装配' + ('成功' if result['success'] else '失败'),
                f'目标：{getattr(target, "id", "未知")}，{result.get("message", "")}'
            )
        self.check_history.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'part_id': getattr(part, 'id', None),
            'target_id': getattr(target, 'id', None),
            'success': result['success'],
        })
        return {'success': True}

    # ==================== 工具 ====================

    @staticmethod
    def _parse_mm(val) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace('mm', '').strip())
        return 0.0