# -*- coding: utf-8 -*-
"""
碰撞检测引擎
受 GPL v3.0 保护

检查实体间是否碰撞。
含规范间距预警（黄）+ 物理穿透分级（红）。
"""

from typing import Dict, Any, List, Tuple
from config import config


class CollisionEngine:
    """碰撞检测引擎"""

    # 承托关系白名单（不算碰撞）
    SUPPORT_RELATIONS = [
        ('管道', '支架'),
        ('管道', '吊杆'),
        ('风管', '支架'),
        ('桥架', '支架'),
        ('支架', '楼板'),
        ('支架', '膨胀螺栓'),
    ]
    # 物理实体白名单（只有这些实体才参与碰撞检测）
    PHYSICAL_TYPES = [
        '管道', '风管', '桥架',
        '支架', '综合支架',
        '阀门', '卡箍', '套管',
        '弯头', '三通', '变径管', '联轴器',
        '法兰', '垫片', '螺栓', '手轮', '阀杆',
        '墙体', '楼板', '地面', '柱子', '吊顶',
        '吊顶丝杆', '支架吊杆',
    ]

    def __init__(self, config_obj=None):
        self.config = config_obj or config
        self.collisions: List[Dict[str, Any]] = []

    # ==================== 主入口 ====================

    def detect_all(self, entities: List) -> List[Dict[str, Any]]:
        """检测所有实体对（O(n²)）"""
        # 关键：先过滤，只保留物理实体
        physical_entities = [
            e for e in entities
            if getattr(e, 'entity_type', '') in self.PHYSICAL_TYPES
        ]

        collisions = []
        n = len(physical_entities)

        for i in range(n):
            for j in range(i + 1, n):
                e1, e2 = physical_entities[i], physical_entities[j]
                result = self.detect_pair(e1, e2)
                if result['collision']:
                    collisions.append({
                        'entity1': getattr(e1, 'id', None),
                        'entity2': getattr(e2, 'id', None),
                        'type': result['type'],
                        'severity': result['severity'],
                        'detail': result['detail'],
                    })

        self.collisions = collisions
        return collisions

    def detect_pair(self, e1, e2) -> Dict[str, Any]:
        """检测两个实体"""
        # 1. 检查承托关系（不算碰撞）
        if self._is_support_relation(e1, e2):
            return {'collision': False}

        # 2. 检查AABB重叠
        box1 = self._get_bbox(e1)
        box2 = self._get_bbox(e2)
        pos1 = self._get_position(e1)
        pos2 = self._get_position(e2)

        if self._check_aabb_overlap(box1, box2, pos1, pos2):
            return {
                'collision': True,
                'type': '物理穿透',
                'severity': 'red',
                'detail': f'{getattr(e1, "id", "")} 与 {getattr(e2, "id", "")} 包围盒重叠',
            }

        # 3. 检查规范间距
        spacing_result = self._check_pipe_spacing(e1, e2, box1, box2, pos1, pos2)
        if spacing_result['violation']:
            return {
                'collision': True,
                'type': '规范间距',
                'severity': 'yellow',
                'detail': spacing_result['detail'],
            }

        return {'collision': False}

    def detect_spacing(self, entities: List) -> List[Dict[str, Any]]:
        """检测规范间距"""
        violations = []
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = entities[i], entities[j]
                box1 = self._get_bbox(e1)
                box2 = self._get_bbox(e2)
                pos1 = self._get_position(e1)
                pos2 = self._get_position(e2)
                result = self._check_pipe_spacing(e1, e2, box1, box2, pos1, pos2)
                if result['violation']:
                    violations.append({
                        'entity1': getattr(e1, 'id', None),
                        'entity2': getattr(e2, 'id', None),
                        'detail': result['detail'],
                    })
        return violations

    # ==================== AABB重叠 ====================

    def _check_aabb_overlap(self, box1: Dict, box2: Dict,
                             pos1: Dict, pos2: Dict) -> bool:
        """检查AABB包围盒重叠"""
        # 任一包围盒为 0，直接不重叠
        if box1.get('x', 0) <= 0 or box2.get('x', 0) <= 0:
            return False

        dx = abs(pos1['x'] - pos2['x'])
        dy = abs(pos1['y'] - pos2['y'])
        dz = abs(pos1['z'] - pos2['z'])

        return (
            dx < (box1['x'] + box2['x']) / 2 and
            dy < (box1['y'] + box2['y']) / 2 and
            dz < (box1['z'] + box2['z']) / 2
        )

    # ==================== 规范间距 ====================

    def _check_pipe_spacing(self, e1, e2, box1: Dict, box2: Dict,
                             pos1: Dict, pos2: Dict) -> Dict[str, Any]:
        """检查管道间距"""
        t1 = getattr(e1, 'entity_type', '')
        t2 = getattr(e2, 'entity_type', '')

        # 只有管道类才检查
        pipe_types = ['管道', '风管', '桥架', '消防管', '给水管']
        if t1 not in pipe_types and t2 not in pipe_types:
            return {'violation': False}

        # 获取规范间距
        required = self._get_required_spacing(t1, t2)

        # 计算实际间距
        actual = self._calc_spacing(box1, box2, pos1, pos2)

        if actual < required:
            return {
                'violation': True,
                'detail': f'{getattr(e1, "id", "")} 与 {getattr(e2, "id", "")} 间距{round(actual, 1)}mm < {required}mm',
                'required': required,
                'actual': actual,
            }
        return {'violation': False}

    def _get_required_spacing(self, t1: str, t2: str) -> float:
        """获取规范间距"""
        collision_config = getattr(self.config, 'COLLISION', {})

        pair = tuple(sorted([t1, t2]))
        key_map = {
            ('管道', '管道'): 'pipe_pipe',
            ('管道', '风管'): 'pipe_duct',
            ('管道', '桥架'): 'pipe_tray',
            ('风管', '桥架'): 'pipe_tray',
        }
        key = key_map.get(pair, 'pipe_pipe')
        return collision_config.get(key, 50)

    def _calc_spacing(self, box1: Dict, box2: Dict,
                       pos1: Dict, pos2: Dict) -> float:
        """计算实际间距"""
        # 使用Y、Z轴的最小间距（管道沿X轴延伸）
        dy = abs(pos1['y'] - pos2['y']) - (box1['y'] + box2['y']) / 2
        dz = abs(pos1['z'] - pos2['z']) - (box1['z'] + box2['z']) / 2
        return max(0, min(dy, dz))

    # ==================== 承托关系 ====================

    def _is_support_relation(self, e1, e2) -> bool:
        """判断是否承托关系"""
        t1 = getattr(e1, 'entity_type', '')
        t2 = getattr(e2, 'entity_type', '')
        pair = tuple(sorted([t1, t2]))
        for rel in self.SUPPORT_RELATIONS:
            if tuple(sorted(rel)) == pair:
                return True
        return False

    # ==================== 报告 ====================

    def get_report(self) -> Dict[str, Any]:
        """获取碰撞报告"""
        return {
            'total': len(self.collisions),
            'by_severity': {
                'red': len([c for c in self.collisions if c['severity'] == 'red']),
                'yellow': len([c for c in self.collisions if c['severity'] == 'yellow']),
            },
            'collisions': self.collisions,
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        red = len([c for c in self.collisions if c['severity'] == 'red'])
        yellow = len([c for c in self.collisions if c['severity'] == 'yellow'])
        return {
            'red': red,
            'yellow': yellow,
            'green': 0 if (red + yellow) == 0 else max(0, 100 - red - yellow),
            'total': len(self.collisions),
        }

    # ==================== 工具 ====================

    def _get_bbox(self, entity) -> Dict[str, float]:
        """获取包围盒（找不到时返回 0，表示不参与碰撞）"""
        if hasattr(entity, 'get_bounding_box'):
            bbox = entity.get_bounding_box()
            if bbox and bbox.get('x', 0) > 0:
                return bbox
        if hasattr(entity, 'layer'):
            l2 = entity.layer.get('l2_static_attributes', {})
            bbox = l2.get('包围盒', {})
            if bbox and bbox.get('x', 0) > 0:
                return bbox
        # 找不到包围盒，返回 0，让 AABB 判定自然不重叠
        return {'x': 0, 'y': 0, 'z': 0}

    def _get_position(self, entity) -> Dict[str, float]:
        """获取位置"""
        if hasattr(entity, 'get_position'):
            return entity.get_position()
        if hasattr(entity, 'layer'):
            return entity.layer.get('l3_dynamic_state', {}).get(
                '绝对坐标', {'x': 0, 'y': 0, 'z': 0}
            )
        return {'x': 0, 'y': 0, 'z': 0}