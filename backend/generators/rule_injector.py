# -*- coding: utf-8 -*-
"""
规则注入引擎
受 GPL v3.0 保护

自动注入物理/受力/装配/规范规则。
"""

from typing import Dict, Any
from .rules import RULES
from .ai_connector import AIConnector


class RuleInjector:
    """规则注入引擎"""

    def __init__(self, rules: Dict[str, Any] = None):
        self.rules = rules or RULES
        self.ai = AIConnector()

    # ==================== 注入方法 ====================

    def inject_physical_rules(self, product: Dict[str, Any],
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """注入物理规则"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        rule = self.rules.get(ptype, self.rules.get('_default', {}))
        physical = dict(rule.get('cbm', {}).get('物理规则', {}))
        # 从params补充包围盒
        if '包围盒' not in physical:
            physical['包围盒'] = self._calc_bbox(params)
        return physical

    def inject_force_rules(self, product: Dict[str, Any],
                           params: Dict[str, Any]) -> Dict[str, Any]:
        """注入受力规则"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        rule = self.rules.get(ptype, self.rules.get('_default', {}))
        return dict(rule.get('cbm', {}).get('受力规则', {}))

    def inject_assembly_rules(self, product: Dict[str, Any],
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """注入装配规则"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        rule = self.rules.get(ptype, self.rules.get('_default', {}))
        return dict(rule.get('cbm', {}).get('装配规则', {}))

    def inject_spec_rules(self, product: Dict[str, Any],
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """注入规范约束"""
        ptype = self.ai._guess_type(product.get('产品名称', ''))
        rule = self.rules.get(ptype, self.rules.get('_default', {}))
        return dict(rule.get('cbm', {}).get('规范约束', {}))

    def inject_all(self, product: Dict[str, Any],
                   params: Dict[str, Any]) -> Dict[str, Any]:
        """注入所有规则"""
        return {
            '物理规则': self.inject_physical_rules(product, params),
            '受力规则': self.inject_force_rules(product, params),
            '装配规则': self.inject_assembly_rules(product, params),
            '规范约束': self.inject_spec_rules(product, params),
        }

    # ==================== 从标准推导 ====================

    def _derive_from_standard(self, product: Dict[str, Any],
                              standard: str) -> Dict[str, Any]:
        """从标准推导规则"""
        # 简化：直接返回默认规则
        return self.inject_all(product, {})

    # ==================== 工具 ====================

    def _calc_bbox(self, params: Dict[str, Any]) -> Dict[str, float]:
        """计算包围盒"""
        def parse(val, default=100.0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace('mm', '').strip())
                except ValueError:
                    return default
            return default

        length = parse(params.get('长度', params.get('外径', 100)), 100)
        outer = parse(params.get('外径', params.get('宽度', 100)), 100)
        thickness = parse(params.get('厚度', params.get('高度', outer)), outer)
        return {'x': length, 'y': outer, 'z': thickness}