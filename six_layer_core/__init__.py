# -*- coding: utf-8 -*-
"""
six_layer_core —— 六层架构纯壳框架
受 GPL v3.0 保护

本包只定义六层数据结构框架（R/L1/L2/L3/L4/CBM），
不包含任何具体业务逻辑。
"""

from .engine import SixLayerEngine
from .validator import SixLayerValidator
from .builder import SixLayerBuilder
from .parser import SixLayerParser
from .exceptions import (
    SixLayerError,
    ValidationError,
    MissingFieldError,
    InvalidFormatError,
)

__all__ = [
    'SixLayerEngine',
    'SixLayerValidator',
    'SixLayerBuilder',
    'SixLayerParser',
    'SixLayerError',
    'ValidationError',
    'MissingFieldError',
    'InvalidFormatError',
]

__version__ = '1.0.0'