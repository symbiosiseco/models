# -*- coding: utf-8 -*-
"""
参数传播引擎
受 GPL v3.0 保护

V2.0（阶段2-2）：
- 定义实体之间的依赖关系
- 参数变更时找到所有受影响实例
- 广播事件，标记状态

本模块不直接重建实体（那是阶段2-3的事）。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from data.standard_reader import read_standard


# ==================== 实体依赖关系表 ====================
# key: 实体类型
# value: {category: JSON类别, fields: [关注的字段], upstream: [上游实体], downstream: [下游实体]}

ENTITY_RELATIONS: Dict[str, Dict[str, Any]] = {
    '阀门': {
        'category': 'valves',
        'fields': ['外径', '长度', '重量'],
        'upstream': [],
        'downstream': ['法兰'],
    },
    '法兰': {
        'category': 'flanges',
        'fields': ['外径', '厚度', '螺栓孔径', '螺栓孔数'],
        'upstream': ['阀门', '管道'],
        'downstream': ['垫片', '螺栓'],
    },
    '垫片': {
        'category': 'gaskets',
        'fields': ['垫片外径', '垫片内径', '厚度'],
        'upstream': ['法兰'],
        'downstream': [],
    },
    '螺栓': {
        'category': 'bolts',
        'fields': ['直径', '标准长度', '拧紧力矩'],
        'upstream': ['法兰'],
        'downstream': [],
    },
    '管道': {
        'category': 'pipes',
        'fields': ['外径', '壁厚', '标准长度'],
        'upstream': [],
        'downstream': ['卡箍', '支架'],
    },
    '卡箍': {
        'category': 'clamps',
        'fields': ['卡箍外径', '卡箍宽度'],
        'upstream': ['管道'],
        'downstream': [],
    },
    '支架': {
        'category': 'angles',
        'fields': ['规格', '理论重量'],
        'upstream': ['管道'],
        'downstream': [],
    },
    '风管': {
        'category': 'ducts',
        'fields': ['宽度', '高度'],
        'upstream': [],
        'downstream': [],
    },
    '桥架': {
        'category': 'trays',
        'fields': ['宽度', '高度'],
        'upstream': [],
        'downstream': [],
    },
}


class PropagationEngine:
    """参数传播引擎"""

    def __init__(self, event_bus=None, entity_map=None):
        self.event_bus = event_bus
        self.entity_map = entity_map or {}
        self.relations = ENTITY_RELATIONS
        self.change_history: List[Dict[str, Any]] = []

    # ==================== 设置依赖 ====================

    def set_entity_map(self, entity_map: Dict[str, Any]) -> None:
        """注入实体表（启动后调用）"""
        self.entity_map = entity_map

    def set_event_bus(self, event_bus) -> None:
        """注入事件总线"""
        self.event_bus = event_bus

    # ==================== 参数变更主入口 ====================

    def on_param_change(self, category: str, spec: str,
                         old_value: Any = None, new_value: Any = None) -> Dict[str, Any]:
        """
        参数变更回调（注册到 standard_reader）。

        参数：
            category: JSON 类别（如 'flanges'）
            spec: 规格（如 'DN100'），'*' 表示整个文件变了
            old_value: 旧值（stage2-2 暂不传）
            new_value: 新值（stage2-2 暂不传）

        返回：
            {success, changes: [...]}
        """
        if not category:
            return {'success': False, 'message': '缺少 category'}

        # 找到所有受影响的实体类型
        affected_types = self._find_affected_types(category)
        if not affected_types:
            return {'success': True, 'changes': [], 'message': '无关联实体类型'}

        # 收集受影响实例
        changes = []
        for entity_type in affected_types:
            instances = self._find_instances(entity_type, spec if spec != '*' else None)
            for entity in instances:
                change = self._analyze_entity(entity, category)
                if change:
                    changes.append(change)
                    # 标记状态
                    self._mark_entity(entity, category, change)
                    # 广播事件
                    self._broadcast_change(entity, category, change)

        # 记录历史
        record = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'category': category,
            'spec': spec,
            'affected_count': len(changes),
        }
        self.change_history.append(record)

        return {
            'success': True,
            'category': category,
            'spec': spec,
            'affected_count': len(changes),
            'changes': changes,
        }

    # ==================== 查找关联 ====================

    def _find_affected_types(self, category: str) -> List[str]:
        """找到所有受此 category 影响的实体类型"""
        result = []
        for entity_type, rel in self.relations.items():
            if rel.get('category') == category:
                result.append(entity_type)
        return result

    def _find_instances(self, entity_type: str,
                         spec: Optional[str] = None) -> List[Any]:
        """找到所有该类型的实例，可选按 spec 过滤"""
        result = []
        for e in self.entity_map.values():
            if getattr(e, 'entity_type', '') != entity_type:
                continue
            if spec:
                r_layer = e.layer.get('r_layer', {}) if hasattr(e, 'layer') else {}
                e_spec = r_layer.get('规格', '')
                if e_spec != spec:
                    continue
            result.append(e)
        return result

    def _analyze_entity(self, entity: Any, category: str) -> Optional[Dict[str, Any]]:
        """分析实体是否需要更新"""
        if not hasattr(entity, 'layer'):
            return None

        rel = self.relations.get(getattr(entity, 'entity_type', ''), {})
        if rel.get('category') != category:
            return None

        l2 = entity.layer.get('l2_static_attributes', {})
        l3 = entity.layer.get('l3_dynamic_state', {})
        status = l3.get('状态', '未安装')

        # 判断是否需要更新
        # 简化：只要 category 匹配且实体存在，就标记（阶段2-3 再细化）
        return {
            'entity_id': getattr(entity, 'id', None),
            'entity_type': getattr(entity, 'entity_type', ''),
            'status': status,
            'needs_rebuild': status not in ('已安装', '已验收'),
            'is_installed': status in ('已安装', '已验收'),
        }

    # ==================== 标记与广播 ====================

    def _mark_entity(self, entity: Any, category: str, change: Dict[str, Any]) -> None:
        """标记实体状态"""
        if not hasattr(entity, 'layer'):
            return

        l3 = entity.layer.get('l3_dynamic_state', {})
        if change['needs_rebuild']:
            # 未安装 → 标记"待更新"
            l3['参数更新标记'] = {
                'category': category,
                'marked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reason': '参数变更',
            }
        else:
            # 已安装 → 标记"待确认"
            l3['变更待确认'] = {
                'category': category,
                'marked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reason': '已安装实体参数变更，需人工确认',
            }

    def _broadcast_change(self, entity: Any, category: str, change: Dict[str, Any]) -> None:
        """通过事件总线广播"""
        if not self.event_bus:
            return
        try:
            self.event_bus.publish('参数变更', {
                'entity_id': change['entity_id'],
                'entity_type': change['entity_type'],
                'category': category,
                'needs_rebuild': change['needs_rebuild'],
                'is_installed': change['is_installed'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
        except Exception as e:
            print(f"⚠️ 广播参数变更事件失败：{e}")

    # ==================== 查询 ====================

    def get_change_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取变更历史"""
        return self.change_history[-limit:]

    def get_pending_rebuilds(self) -> List[Dict[str, Any]]:
        """获取所有待重建的实体"""
        result = []
        for e in self.entity_map.values():
            if not hasattr(e, 'layer'):
                continue
            l3 = e.layer.get('l3_dynamic_state', {})
            if '参数更新标记' in l3:
                result.append({
                    'entity_id': getattr(e, 'id', None),
                    'entity_type': getattr(e, 'entity_type', ''),
                    'mark': l3['参数更新标记'],
                })
        return result

    def get_pending_confirmations(self) -> List[Dict[str, Any]]:
        """获取所有待确认的已安装实体"""
        result = []
        for e in self.entity_map.values():
            if not hasattr(e, 'layer'):
                continue
            l3 = e.layer.get('l3_dynamic_state', {})
            if '变更待确认' in l3:
                result.append({
                    'entity_id': getattr(e, 'id', None),
                    'entity_type': getattr(e, 'entity_type', ''),
                    'mark': l3['变更待确认'],
                })
        return result

    def get_relations(self) -> Dict[str, Any]:
        """获取依赖关系表"""
        return self.relations