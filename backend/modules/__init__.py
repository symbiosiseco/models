# -*- coding: utf-8 -*-
"""
modules 包入口
受 GPL v3.0 保护

导出13个场景类。
"""

# 设计阶段
from .design import DesignScene
from .deepen_design import DeepenDesignScene
from .bim_team import BIMTeamScene

# 采购阶段
from .supplier import SupplierScene
from .factory import FactoryScene
from .logistics import LogisticsScene

# 施工阶段
from .construction import ConstructionScene
from .subcontractor import SubcontractorScene
from .supervision import SupervisionScene

# 管理阶段
from .owner import OwnerScene
from .regulator import RegulatorScene
from .third_party import ThirdPartyScene

# 运维阶段
from .maintenance import MaintenanceScene


__all__ = [
    # 设计阶段
    'DesignScene',
    'DeepenDesignScene',
    'BIMTeamScene',
    # 采购阶段
    'SupplierScene',
    'FactoryScene',
    'LogisticsScene',
    # 施工阶段
    'ConstructionScene',
    'SubcontractorScene',
    'SupervisionScene',
    # 管理阶段
    'OwnerScene',
    'RegulatorScene',
    'ThirdPartyScene',
    # 运维阶段
    'MaintenanceScene',
]