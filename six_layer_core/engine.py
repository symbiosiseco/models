# -*- coding: utf-8 -*-
"""
六层架构纯壳引擎（兼容层）
受 GPL v3.0 保护

本文件作为向后兼容保留，实际校验逻辑已委托给 validator.py。
"""

from .validator import SixLayerValidator


class SixLayerEngine:
    """六层架构纯壳引擎（兼容层）"""

    def __init__(self, schema_path: str = None):
        # schema_path 参数保留用于向后兼容，当前不加载 JSON Schema
        self._validator = SixLayerValidator()
        self.schema = None

    def validate(self, data: dict) -> bool:
        """
        校验六层实体（会打印消息）。

        返回值：
            bool，框架是否合法
        """
        is_valid, messages = self._validator.validate_entity(data)
        for msg in messages:
            print(msg)
        return is_valid


if __name__ == "__main__":
    test_data = {
        "r_layer": {"any_data": "anything_here"},
        "l1_identity": {"any_id": "any_value_here"},
        "l2_static_attributes": {},
        "l3_dynamic_state": {},
        "l4_event_chain": [],
        "cbm_abilities": {}
    }

    engine = SixLayerEngine()
    result = engine.validate(test_data)
    print(f"结果: {'✅ 通过' if result else '❌ 失败'}")