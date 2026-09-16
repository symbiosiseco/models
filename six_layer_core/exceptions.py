# -*- coding: utf-8 -*-
"""
六层架构自定义异常
受 GPL v3.0 保护
"""


class SixLayerError(Exception):
    """六层架构基础异常"""
    pass


class ValidationError(SixLayerError):
    """数据校验失败异常"""
    pass


class MissingFieldError(ValidationError):
    """缺少必填字段"""
    pass


class InvalidFormatError(ValidationError):
    """字段格式错误"""
    pass