# -*- coding: utf-8 -*-
"""
六层架构纯壳校验器
受 GPL v3.0 保护

本校验器仅检查"六层框架是否存在"，不检查任何具体字段的内容。
"""

from typing import Tuple, List, Dict, Any


class SixLayerValidator:
    """六层架构纯壳校验器"""

    def validate_entity(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        校验六层框架结构。

        返回值：
            (is_valid, messages)
            - is_valid: bool，框架是否合法
            - messages: List[str]，校验消息
        """
        messages: List[str] = []

        # 1. 检查 R 层（必须存在）
        if not isinstance(data, dict):
            messages.append("❌ 输入数据必须是字典（dict）")
            return False, messages

        if 'r_layer' not in data:
            messages.append("❌ 缺少 R层（r_layer）：每个实体必须定义一个类别层")
            return False, messages
        if not isinstance(data['r_layer'], dict):
            messages.append("❌ R层（r_layer）必须是对象（Object）")
            return False, messages

        # 2. 检查 L1 层（必须存在）
        if 'l1_identity' not in data:
            messages.append("❌ 缺少 L1层（l1_identity）：每个实体必须有一个身份标识层")
            return False, messages
        if not isinstance(data['l1_identity'], dict):
            messages.append("❌ L1层（l1_identity）必须是对象（Object）")
            return False, messages

        # 3-6. 检查其他层（可选，仅提醒类型问题）
        if 'l2_static_attributes' in data and not isinstance(data['l2_static_attributes'], dict):
            messages.append("⚠️ L2层建议为对象（Object），当前不是")

        if 'l3_dynamic_state' in data and not isinstance(data['l3_dynamic_state'], dict):
            messages.append("⚠️ L3层建议为对象（Object），当前不是")

        if 'l4_event_chain' in data and not isinstance(data['l4_event_chain'], list):
            messages.append("⚠️ L4层建议为数组（Array），当前不是")

        if 'cbm_abilities' in data and not isinstance(data['cbm_abilities'], dict):
            messages.append("⚠️ CBM层建议为对象（Object），当前不是")

        if messages:
            messages.insert(0, "✅ 六层框架结构存在，但有以下提醒：")
        else:
            messages.append("✅ 校验通过：数据符合六层框架结构（纯壳校验）")

        return True, messages