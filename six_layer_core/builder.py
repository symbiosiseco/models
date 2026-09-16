# -*- coding: utf-8 -*-
"""
六层架构纯壳构建器
受 GPL v3.0 保护

本构建器仅提供"六层框架"的链式构建能力。
所有层的数据完全由用户自由传入，不预设任何具体格式。
"""

from typing import Dict, Any, List


class SixLayerBuilder:
    """六层架构纯壳构建器"""

    def __init__(self):
        self.entity: Dict[str, Any] = {}

    def set_r_layer(self, data: Dict[str, Any]) -> 'SixLayerBuilder':
        """设置R层（类别定义层）"""
        self.entity['r_layer'] = data
        return self

    def set_l1_identity(self, data: Dict[str, Any]) -> 'SixLayerBuilder':
        """设置L1层（身份标识层）"""
        self.entity['l1_identity'] = data
        return self

    def set_l2_static_attributes(self, data: Dict[str, Any]) -> 'SixLayerBuilder':
        """设置L2层（静态属性层：外形+锚点+受力点+接触面）"""
        self.entity['l2_static_attributes'] = data
        return self

    def set_l3_dynamic_state(self, data: Dict[str, Any]) -> 'SixLayerBuilder':
        """设置L3层（动态状态层）"""
        self.entity['l3_dynamic_state'] = data
        return self

    def set_l4_event_chain(self, data: List[Dict[str, Any]]) -> 'SixLayerBuilder':
        """设置L4层（事件链层）"""
        self.entity['l4_event_chain'] = data
        return self

    def set_cbm_abilities(self, data: Dict[str, Any]) -> 'SixLayerBuilder':
        """设置CBM层（行为与认知模块）"""
        self.entity['cbm_abilities'] = data
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建六层实体。
        若缺 r_layer 或 l1_identity，自动补全为空字典（最小合法实体）。
        """
        if 'r_layer' not in self.entity:
            self.entity['r_layer'] = {}
        if 'l1_identity' not in self.entity:
            self.entity['l1_identity'] = {}
        return self.entity