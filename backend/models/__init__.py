# -*- coding: utf-8 -*-
"""
models 包入口
受 GPL v3.0 保护

统一导出所有实体类。
"""

# 实体基类（报告1）
from .entity import BaseEntity
from .physics_rules import (
    valve_cbm, flange_cbm, gasket_cbm, bolt_cbm, support_cbm, pipe_cbm, clamp_cbm, sleeve_cbm,
    valve_force_points, flange_force_points, bolt_force_points, support_force_points,
    pipe_force_points, clamp_force_points, gasket_force_points,
    valve_contact_faces, flange_contact_faces, gasket_contact_faces, bolt_contact_faces,
    support_contact_faces, pipe_contact_faces, clamp_contact_faces,
)

# 核心实体（报告2 K组）
from .force_point import ForcePointEntity
from .contact_face import ContactFaceEntity
from .worker_state import WorkerStateEntity

# A组：管道系统
from .pipe import PipeEntity
from .support import SupportEntity
from .composite_support import CompositeSupportEntity
from .valve import ValveEntity
from .clamp import ClampEntity
from .sleeve import SleeveEntity
from .elbow import ElbowEntity
from .tee import TeeEntity
from .reducer import ReducerEntity
from .coupling import CouplingEntity
from .flange import FlangeEntity
from .gasket import GasketEntity
from .bolt import BoltEntity
from .wheel import WheelEntity
from .stem import StemEntity

# B组：结构
from .wall import WallEntity
from .slab import SlabEntity
from .floor import FloorEntity
from .column import ColumnEntity
from .ceiling import CeilingEntity
from .ceiling_hanger import CeilingHangerEntity
from .hanger import HangerEntity

# C组：其他专业
from .duct import DuctEntity
from .tray import TrayEntity

# D组：人员/组织
from .worker import WorkerEntity
from .worker_skill import WorkerSkillEntity
from .vehicle import VehicleEntity
from .organization import OrganizationEntity

# E组：项目/合同
from .project import ProjectEntity
from .contract import ContractEntity
from .drawing import DrawingEntity

# F组：任务/工序
from .task import TaskEntity
from .process import ProcessEntity
from .order import OrderEntity

# G组：验收/变更
from .acceptance import AcceptanceEntity
from .change import ChangeEntity
from .visa import VisaEntity

# H组：模板/报表
from .template import TemplateEntity
from .report import ReportEntity

# I组：实测/记录
from .measurement import MeasurementEntity
from .measurement_record import MeasurementRecordEntity
from .signature_record import SignatureRecordEntity
from .notification_record import NotificationRecordEntity

# J组：厂家/产品
from .manufacturer import ManufacturerEntity
from .product import ProductEntity


__all__ = [
    # 基类
    'BaseEntity',
    'ForcePointEntity', 'ContactFaceEntity', 'WorkerStateEntity',
    # A组
    'PipeEntity', 'SupportEntity', 'CompositeSupportEntity',
    'ValveEntity', 'ClampEntity', 'SleeveEntity',
    'ElbowEntity', 'TeeEntity', 'ReducerEntity', 'CouplingEntity',
    'FlangeEntity', 'GasketEntity', 'BoltEntity', 'WheelEntity', 'StemEntity',
    # B组
    'WallEntity', 'SlabEntity', 'FloorEntity', 'ColumnEntity',
    'CeilingEntity', 'CeilingHangerEntity', 'HangerEntity',
    # C组
    'DuctEntity', 'TrayEntity',
    # D组
    'WorkerEntity', 'WorkerSkillEntity', 'VehicleEntity', 'OrganizationEntity',
    # E组
    'ProjectEntity', 'ContractEntity', 'DrawingEntity',
    # F组
    'TaskEntity', 'ProcessEntity', 'OrderEntity',
    # G组
    'AcceptanceEntity', 'ChangeEntity', 'VisaEntity',
    # H组
    'TemplateEntity', 'ReportEntity',
    # I组
    'MeasurementEntity', 'MeasurementRecordEntity',
    'SignatureRecordEntity', 'NotificationRecordEntity',
    # J组
    'ManufacturerEntity', 'ProductEntity',
    # 物理规则函数
    'valve_cbm', 'flange_cbm', 'gasket_cbm', 'bolt_cbm', 'support_cbm',
    'pipe_cbm', 'clamp_cbm', 'sleeve_cbm',
    'valve_force_points', 'flange_force_points', 'bolt_force_points',
    'support_force_points', 'pipe_force_points', 'clamp_force_points', 'gasket_force_points',
    'valve_contact_faces', 'flange_contact_faces', 'gasket_contact_faces',
    'bolt_contact_faces', 'support_contact_faces', 'pipe_contact_faces', 'clamp_contact_faces',
]