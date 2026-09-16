# -*- coding: utf-8 -*-
"""
模板匹配引擎
受 GPL v3.0 保护

从模板库匹配最相似的模板。
"""

from typing import Dict, Any, List, Optional


class TemplateMatcher:
    """模板匹配引擎"""

    # 相似度权重
    WEIGHT_TYPE = 0.5
    WEIGHT_SPEC = 0.3
    WEIGHT_MANUFACTURER = 0.2

    def __init__(self, template_store):
        self.template_store = template_store

    # ==================== 主入口 ====================

    def match(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """匹配模板"""
        candidates = self._get_all_templates()
        if not candidates:
            return None

        best = None
        best_score = 0.0

        for tpl in candidates:
            score = self._calculate_similarity(product, tpl)
            if score > best_score:
                best_score = score
                best = tpl

        # 相似度阈值
        if best_score < 0.5:
            return None
        return best

    def match_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """按类型匹配"""
        return [
            tpl for tpl in self._get_all_templates()
            if tpl.get('entity_type') == entity_type
        ]

    def match_by_spec(self, entity_type: str, spec: str) -> Optional[Dict[str, Any]]:
        """按规格匹配"""
        for tpl in self._get_all_templates():
            if tpl.get('entity_type') == entity_type and tpl.get('spec') == spec:
                return tpl
        return None

    def match_by_manufacturer(self, manufacturer: str) -> List[Dict[str, Any]]:
        """按厂家匹配"""
        return [
            tpl for tpl in self._get_all_templates()
            if tpl.get('manufacturer') == manufacturer
        ]

    # ==================== 相似度计算 ====================

    def _calculate_similarity(self, product: Dict[str, Any],
                              template: Dict[str, Any]) -> float:
        """相似度计算"""
        score = 0.0

        # 类型匹配
        p_type = product.get('产品名称', '') or product.get('产品型号', '')
        t_type = template.get('entity_type', '') or template.get('name', '')
        if p_type and t_type and p_type in t_type or t_type in p_type:
            score += self.WEIGHT_TYPE

        # 规格匹配
        p_spec = product.get('规格', '')
        t_spec = template.get('spec', '')
        if p_spec and t_spec and p_spec == t_spec:
            score += self.WEIGHT_SPEC

        # 厂家匹配
        p_mfr = product.get('厂家', '')
        t_mfr = template.get('manufacturer', '')
        if p_mfr and t_mfr and p_mfr == t_mfr:
            score += self.WEIGHT_MANUFACTURER

        return score

    # ==================== 内部 ====================

    def _get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板"""
        if not self.template_store:
            return []
        return list(self.template_store.templates.values())