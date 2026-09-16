# -*- coding: utf-8 -*-
"""
实体重建引擎
受 GPL v3.0 保护

V2.0（阶段2-3）：
- 从标准库重新读参数，更新实体的 L2 和 CBM
- L1/L3/L4 完全不动（ID、坐标、状态、履历保留）
- ID 不变
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard


class RebuildEngine:
    """实体重建引擎"""

    def __init__(self, entity_map=None, event_bus=None):
        self.entity_map = entity_map or {}
        self.event_bus = event_bus
        self.rebuild_history: List[Dict[str, Any]] = []

    def set_entity_map(self, entity_map: Dict[str, Any]) -> None:
        self.entity_map = entity_map

    # ==================== 主入口 ====================

    def rebuild_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        重建单个实体的 L2 + CBM。

        参数：
            entity_id: 实体ID

        返回：
            {success, entity_id, updated_fields: [...], message}
        """
        entity = self.entity_map.get(entity_id)
        if not entity:
            return {'success': False, 'message': f'实体不存在：{entity_id}'}

        entity_type = getattr(entity, 'entity_type', '')
        rebuild_fn = REBUILDERS.get(entity_type)
        if not rebuild_fn:
            return {
                'success': False,
                'message': f'未支持的重建类型：{entity_type}',
            }

        try:
            # 只更新 L2 和 CBM
            updated_fields = rebuild_fn(entity)

            # 清掉"待更新"标记
            l3 = entity.layer.get('l3_dynamic_state', {})
            l3.pop('参数更新标记', None)

            # 写 L4
            if hasattr(entity, 'add_event'):
                entity.add_event('参数重建', f'重建字段：{updated_fields}')

            # 广播
            if self.event_bus:
                self.event_bus.publish('实体重建完成', {
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'updated_fields': updated_fields,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            record = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'entity_id': entity_id,
                'entity_type': entity_type,
                'updated_fields': updated_fields,
            }
            self.rebuild_history.append(record)

            return {
                'success': True,
                'entity_id': entity_id,
                'entity_type': entity_type,
                'updated_fields': updated_fields,
            }
        except Exception as e:
            return {
                'success': False,
                'entity_id': entity_id,
                'message': str(e),
            }

    def rebuild_all_pending(self) -> Dict[str, Any]:
        """重建所有待更新的实体"""
        pending = []
        for e in self.entity_map.values():
            if not hasattr(e, 'layer'):
                continue
            l3 = e.layer.get('l3_dynamic_state', {})
            if '参数更新标记' in l3:
                pending.append(getattr(e, 'id', None))

        results = []
        for eid in pending:
            if eid:
                results.append(self.rebuild_entity(eid))

        success_count = sum(1 for r in results if r.get('success'))
        return {
            'success': True,
            'total': len(pending),
            'success_count': success_count,
            'failed_count': len(pending) - success_count,
            'results': results,
        }

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.rebuild_history[-limit:]


# ==================== 各实体重建函数 ====================
# 每个函数：读 L2 关键标识 → 从 JSON 读参数 → 更新 L2 + CBM

def _rebuild_pipe(entity):
    """重建管道"""
    from models.pipe import PipeEntity
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    dn = r_layer.get('规格', 'DN100')
    length = l2.get('包围盒', {}).get('x', 10000)

    spec = read_standard('pipes', dn)
    l2['外径'] = f'{spec.get("外径", 114.3)}mm'
    l2['壁厚'] = f'{spec.get("壁厚", 4.0)}mm'
    l2['单位重量'] = f'{spec.get("单位重量", 10.9)}kg/m'
    l2['标准长度'] = f'{spec.get("标准长度", 6000)}mm'

    # CBM 更新
    from models.physics_rules import pipe_cbm
    entity.layer['cbm_abilities'] = pipe_cbm(
        dn, spec.get('外径', 114.3), length
    )
    return ['外径', '壁厚', '单位重量', '标准长度', 'CBM']


def _rebuild_flange(entity):
    """重建法兰"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    dn = r_layer.get('规格', 'DN100')
    flange_type = r_layer.get('子类型', '沟槽法兰')
    pressure = r_layer.get('压力等级', 'PN16')

    spec = read_standard('flanges', dn)
    l2['外径'] = f'{spec.get("外径", 220)}mm'
    l2['厚度'] = f'{spec.get("厚度", 24)}mm'
    l2['螺栓孔径'] = f'{spec.get("螺栓孔径", 18)}mm'
    l2['螺栓孔数'] = spec.get('螺栓孔数', 8)
    l2['螺栓规格'] = spec.get('螺栓规格', 'M16')
    l2['压力等级'] = pressure

    # CBM
    from models.physics_rules import flange_cbm
    entity.layer['cbm_abilities'] = flange_cbm(
        dn, spec.get('外径', 220), spec.get('厚度', 24)
    )
    # 更新 bolt_hole_diameter 属性
    if hasattr(entity, 'bolt_hole_diameter'):
        entity.bolt_hole_diameter = spec.get('螺栓孔径', 18)
    return ['外径', '厚度', '螺栓孔径', '螺栓孔数', 'CBM']


def _rebuild_bolt(entity):
    """重建螺栓"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    spec_name = r_layer.get('规格', 'M16')

    spec = read_standard('bolts', spec_name)
    l2['直径'] = f'{spec.get("直径", 16)}mm'
    l2['拧紧力矩'] = f'{spec.get("拧紧力矩", 40)}N·m'
    # 预紧力从 kN → N
    preload_kn = spec.get('预紧力', 25)
    l2['预紧力'] = f'{int(preload_kn * 1000)}N'

    # CBM
    from models.physics_rules import bolt_cbm
    entity.layer['cbm_abilities'] = bolt_cbm(spec_name, spec.get('标准长度', 80))
    # 更新直径属性
    if hasattr(entity, 'diameter'):
        entity.diameter = spec.get('直径', 16)
    return ['直径', '拧紧力矩', '预紧力', 'CBM']


def _rebuild_valve(entity):
    """重建阀门"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    dn = r_layer.get('规格', 'DN100')
    valve_type = r_layer.get('子类型', '闸阀')

    spec = read_standard('valves', dn, valve_type)
    l2['外径'] = f'{spec.get("外径", 220)}mm'
    l2['长度'] = f'{spec.get("长度", 280)}mm'
    l2['重量'] = f'{spec.get("重量", 15)}kg'

    # CBM
    from models.physics_rules import valve_cbm
    entity.layer['cbm_abilities'] = valve_cbm(
        dn, spec.get('外径', 220), spec.get('长度', 280)
    )
    return ['外径', '长度', '重量', 'CBM']


def _rebuild_clamp(entity):
    """重建卡箍"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    dn = r_layer.get('规格', 'DN100')

    spec = read_standard('clamps', dn)
    l2['外径'] = f'{spec.get("卡箍外径", 140)}mm'
    l2['宽度'] = f'{spec.get("卡箍宽度", 60)}mm'
    l2['重量'] = f'{spec.get("重量", 1.2)}kg'
    l2['螺栓规格'] = spec.get('螺栓规格', 'M10×65')
    l2['螺栓数量'] = spec.get('螺栓数', 2)

    from models.physics_rules import clamp_cbm
    entity.layer['cbm_abilities'] = clamp_cbm(
        dn, spec.get('卡箍外径', 140), spec.get('卡箍宽度', 60)
    )
    return ['外径', '宽度', '重量', 'CBM']


def _rebuild_gasket(entity):
    """重建垫片"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    dn = r_layer.get('规格', 'DN100')

    spec = read_standard('gaskets', dn)
    l2['外径'] = f'{spec.get("垫片外径", 162)}mm'
    l2['内径'] = f'{spec.get("垫片内径", 115)}mm'
    l2['厚度'] = f'{spec.get("厚度", 3)}mm'

    from models.physics_rules import gasket_cbm
    entity.layer['cbm_abilities'] = gasket_cbm(
        dn, spec.get('垫片外径', 162), spec.get('厚度', 3)
    )
    return ['外径', '内径', '厚度', 'CBM']


def _rebuild_support(entity):
    """重建支架"""
    l2 = entity.layer['l2_static_attributes']
    angle = read_standard('angles', 'L50×50×6')
    l2['规格'] = angle.get('规格', 'L50×50×6')
    l2['材质'] = angle.get('材质', 'Q235B')
    # 总重量 = 角钢理论重量 × 3米
    weight = angle.get('理论重量', 1.72) * 3
    l2['总重量'] = f'{round(weight, 2)}kg'
    return ['规格', '材质', '总重量']


def _rebuild_duct(entity):
    """重建风管"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    spec_key = r_layer.get('规格', '800×400')
    length = l2.get('包围盒', {}).get('x', 10000)

    spec = read_standard('ducts', spec_key)
    if not spec:
        # JSON 里没有这个规格，尝试用默认的 800×400
        spec = read_standard('ducts', '800×400')
        spec_key = '800×400'

    width = spec.get('宽度', 800)
    height = spec.get('高度', 400)
    weight_per_m = spec.get('单位重量', 18.5)

    l2['规格'] = spec_key
    l2['宽度'] = f'{width}mm'
    l2['高度'] = f'{height}mm'
    l2['单位重量'] = f'{weight_per_m}kg/m'
    l2['总重量'] = f'{round(weight_per_m * length / 1000, 2)}kg'

    from models.physics_rules import duct_cbm
    entity.layer['cbm_abilities'] = duct_cbm(spec_key)
    return ['宽度', '高度', '单位重量', '总重量', 'CBM']


def _rebuild_tray(entity):
    """重建桥架"""
    l2 = entity.layer['l2_static_attributes']
    r_layer = entity.layer['r_layer']
    spec_key = r_layer.get('规格', '300×200')
    length = l2.get('包围盒', {}).get('x', 10000)

    spec = read_standard('trays', spec_key)
    if not spec:
        spec = read_standard('trays', '300×200')
        spec_key = '300×200'

    width = spec.get('宽度', 300)
    height = spec.get('高度', 200)
    weight_per_m = spec.get('单位重量', 9.5)

    l2['规格'] = spec_key
    l2['宽度'] = f'{width}mm'
    l2['高度'] = f'{height}mm'
    l2['单位重量'] = f'{weight_per_m}kg/m'
    l2['总重量'] = f'{round(weight_per_m * length / 1000, 2)}kg'

    from models.physics_rules import tray_cbm
    entity.layer['cbm_abilities'] = tray_cbm(spec_key)
    return ['宽度', '高度', '单位重量', '总重量', 'CBM']


# 分发字典
REBUILDERS = {
    '管道': _rebuild_pipe,
    '法兰': _rebuild_flange,
    '螺栓': _rebuild_bolt,
    '阀门': _rebuild_valve,
    '卡箍': _rebuild_clamp,
    '垫片': _rebuild_gasket,
    '支架': _rebuild_support,
    '风管': _rebuild_duct,
    '桥架': _rebuild_tray,
}