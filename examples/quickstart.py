# -*- coding: utf-8 -*-
"""
六层架构纯壳示例 - 展示框架的开放性与自由度
本示例演示如何创建一个自定义实体，各层可自由填入任何内容。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from six_layer_core import SixLayerBuilder, SixLayerValidator, SixLayerParser

print("🚀 步骤1：构建一个自定义实体（纯壳风格）...")

# 六层框架构建：每层都是完全自由的内容
entity = (
    SixLayerBuilder()
    .set_r_layer({
        "category_code": "MY-OWN-CATEGORY-001",
        "custom_field": "anything_here",
        "version": "v1.0"
    })
    .set_l1_identity({
        "instance_id": "my-own-id-001",
        "any_metadata": {"note": "完全由业务层定义"}
    })
    .set_l2_static_attributes({
        "自定义属性1": "任意值",
        "自定义属性2": 12345
    })
    .set_l3_dynamic_state({
        "状态字段1": "active",
        "状态字段2": 98.5
    })
    .set_l4_event_chain([
        {"事件类型": "创建", "时间": "2026-09-01"},
        {"事件类型": "更新", "时间": "2026-09-02"}
    ])
    .set_cbm_abilities({
        "支持的动作": ["action_a", "action_b"],
        "端点": "https://example.com/api"
    })
    .build()
)

print("✅ 构建完成！")
print(f"   - R层内容: {entity['r_layer']}")
print(f"   - L1层内容: {entity['l1_identity']}")

# 步骤2：校验框架结构
print("\n🔍 步骤2：校验数据是否符合六层框架结构...")
validator = SixLayerValidator()
is_valid, msgs = validator.validate_entity(entity)

if is_valid:
    print("✅ 校验通过！数据符合六层框架结构")
else:
    print("❌ 校验失败：")
    for msg in msgs:
        print(f"   {msg}")

# 步骤3：提取层级数据
print("\n📊 步骤3：提取层级摘要...")
summary = SixLayerParser.get_summary(entity)
print(f"   - 已定义的层级: {[k for k, v in summary.items() if v]}")

# 步骤4：按路径取值
print("\n🔍 步骤4：按路径取值...")
category_code = SixLayerParser.get_by_path(entity, "r_layer.category_code")
print(f"   - r_layer.category_code = {category_code}")

print("\n✅ 纯壳示例运行完成！")