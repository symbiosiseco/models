# -*- coding: utf-8 -*-
"""
六层架构纯壳解析器
受 GPL v3.0 保护
"""

from typing import Dict, Any, List


class SixLayerParser:
    """六层架构纯壳解析器（全部静态方法）"""

    @staticmethod
    def get_r_layer(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取R层（类别定义层）"""
        return entity.get('r_layer', {}) if entity else {}

    @staticmethod
    def get_l1_identity(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取L1层（身份标识层）"""
        return entity.get('l1_identity', {}) if entity else {}

    @staticmethod
    def get_l2_static_attributes(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取L2层（静态属性层）"""
        return entity.get('l2_static_attributes', {}) if entity else {}

    @staticmethod
    def get_l3_dynamic_state(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取L3层（动态状态层）"""
        return entity.get('l3_dynamic_state', {}) if entity else {}

    @staticmethod
    def get_l4_event_chain(entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取L4层（事件链层）"""
        return entity.get('l4_event_chain', []) if entity else []

    @staticmethod
    def get_cbm_abilities(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取CBM层（行为与认知模块）"""
        return entity.get('cbm_abilities', {}) if entity else {}

    @staticmethod
    def get_by_path(entity: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        按点路径取值，如 "r_layer.category_code"

        不支持 list 索引（如 "l4_event_chain.0"）
        """
        if not entity:
            return default
        try:
            parts = path.split('.')
            current = entity
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        except (AttributeError, TypeError, KeyError):
            return default

    @staticmethod
    def has_layer(entity: Dict[str, Any], layer_name: str) -> bool:
        """判断层是否存在（值不为 None 即算存在，空 {} 也算）"""
        if not entity:
            return False
        return layer_name in entity and entity[layer_name] is not None

    @staticmethod
    def get_all_layers(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取所有非空层（排除 None、{}、[]）"""
        layers = {}
        for name in ['r_layer', 'l1_identity', 'l2_static_attributes',
                     'l3_dynamic_state', 'l4_event_chain', 'cbm_abilities']:
            value = entity.get(name)
            if value is not None and value != {} and value != []:
                layers[name] = value
        return layers

    @staticmethod
    def get_summary(entity: Dict[str, Any]) -> Dict[str, Any]:
        """获取六层摘要（has_* 布尔字典）"""
        return {
            'has_r_layer': SixLayerParser.has_layer(entity, 'r_layer'),
            'has_l1_identity': SixLayerParser.has_layer(entity, 'l1_identity'),
            'has_l2_static_attributes': SixLayerParser.has_layer(entity, 'l2_static_attributes'),
            'has_l3_dynamic_state': SixLayerParser.has_layer(entity, 'l3_dynamic_state'),
            'has_l4_event_chain': SixLayerParser.has_layer(entity, 'l4_event_chain'),
            'has_cbm_abilities': SixLayerParser.has_layer(entity, 'cbm_abilities'),
        }