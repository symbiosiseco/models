# -*- coding: utf-8 -*-
"""
templates 包入口
受 GPL v3.0 保护

导出模板存储器和4个模板库。
"""

from .item_templates import ITEM_TEMPLATES
from .worker_templates import WORKER_TEMPLATES
from .equip_templates import EQUIP_TEMPLATES
from .task_templates import TASK_TEMPLATES
from .store import TemplateStore


__all__ = [
    'TemplateStore',
    'ITEM_TEMPLATES',
    'WORKER_TEMPLATES',
    'EQUIP_TEMPLATES',
    'TASK_TEMPLATES',
]