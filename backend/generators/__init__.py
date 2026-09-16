# -*- coding: utf-8 -*-
"""
generators 包入口
受 GPL v3.0 保护

导出所有生成器组件。
"""

# 1. 生成说明书（无依赖）
from .generation_manual import GENERATION_MANUAL, GenerationManual

# 2. 规则库（无依赖）
from .rules import RULES

# 3. AI连接器（依赖AI API）
from .ai_connector import AIConnector

# 4. AI产品理解引擎（依赖 ai_connector）
from .ai_understanding import AIUnderstanding

# 5. 参数映射引擎（依赖 templates.store）
from .param_mapper import ParamMapper

# 6. 规则注入引擎（依赖 rules + ai_connector）
from .rule_injector import RuleInjector

# 7. 边界计算引擎（依赖 ai_connector + rules）
from .boundary_calculator import BoundaryCalculator

# 8. 模板匹配引擎（依赖 templates.store）
from .template_matcher import TemplateMatcher

# 9. 完整性验证引擎（依赖 generation_manual）
from .integrity_validator import IntegrityValidator

# 10. 数字生命体生成器（核心，依赖前面所有组件）
from .digital_life import DigitalLifeGenerator, GeneratedEntity


__all__ = [
    # 核心
    'DigitalLifeGenerator',
    'GeneratedEntity',
    # AI 相关
    'AIConnector',
    'AIUnderstanding',
    # 映射/注入/计算
    'ParamMapper',
    'RuleInjector',
    'BoundaryCalculator',
    # 匹配/验证
    'TemplateMatcher',
    'IntegrityValidator',
    # 说明书/规则
    'GENERATION_MANUAL',
    'GenerationManual',
    'RULES',
]