# -*- coding: utf-8 -*-
"""
engines 包入口
受 GPL v3.0 保护

导出所有引擎。
"""

# ==================== CBM 引擎（第2批）====================
from .event_bus import EventBus
from .entity_cbm import EntityCBM
from .worker_cbm import WorkerCBM
from .task_cbm import TaskCBM
from .project_cbm import ProjectCBM
from .contact_check import ContactCheckEngine

# ==================== 核心引擎（第6批）====================
from .assembly import AssemblyEngine
from .task_generator import TaskGenerator
from .collision import CollisionEngine
from .cost import CostEngine

# ==================== 业务引擎（第7批）====================
from .task import TaskEngine
from .workflow import WorkflowEngine
from .schedule import ScheduleEngine
from .report import ReportEngine
from .notification import NotificationEngine

# ==================== 支撑引擎（第8批）====================
from .signature import SignatureEngine
from .measurement import MeasurementEngine
from .replacement import ReplacementEngine
from .template import TemplateEngine
from .bom import BOMEngine
from .priority import PriorityEngine

# ==================== 系统引擎（第9批）====================
from .sync import SyncEngine
from .auth import AuthEngine
from .search import SearchEngine
from .export import ExportEngine
from .validation import ValidationEngine
from .log import LogEngine

# ==================== 演示引擎（第17批下）====================
from .demo_runner import DemoRunner


__all__ = [
    # CBM 引擎
    'EventBus',
    'EntityCBM',
    'WorkerCBM',
    'TaskCBM',
    'ProjectCBM',
    'ContactCheckEngine',
    # 核心引擎
    'AssemblyEngine',
    'TaskGenerator',
    'CollisionEngine',
    'CostEngine',
    # 业务引擎
    'TaskEngine',
    'WorkflowEngine',
    'ScheduleEngine',
    'ReportEngine',
    'NotificationEngine',
    # 支撑引擎
    'SignatureEngine',
    'MeasurementEngine',
    'ReplacementEngine',
    'TemplateEngine',
    'BOMEngine',
    'PriorityEngine',
    # 系统引擎
    'SyncEngine',
    'AuthEngine',
    'SearchEngine',
    'ExportEngine',
    'ValidationEngine',
    'LogEngine',
    # 演示引擎
    'DemoRunner',
]