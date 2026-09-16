# -*- coding: utf-8 -*-
"""
全局配置
受 GPL v3.0 保护

包含：国标尺寸、空间定位、碰撞阈值、管道优先级、CBM配置、事件总线配置
"""

import os


class Config:
    """全局配置类"""

    # ===== Flask 基础 =====
    SECRET_KEY = os.environ.get('SECRET_KEY', 'six-layer-demo-secret-2026')
    JSON_AS_ASCII = False

    # ===== 数据库 =====
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'db', 'six_layer.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== 数据目录 =====
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    TEMPLATES_DIR = os.path.join(DATA_DIR, 'templates')
    STANDARDS_DIR = os.path.join(DATA_DIR, 'standards')
    PRODUCTS_DIR = os.path.join(DATA_DIR, 'products')
    UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')

    # ===== 服务器 =====
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # ===== 空间定位默认值 =====
    SPACE_UNITS = {
        'unit_project': '3号楼',
        'floor': '2层',
        'room': 'B轴',
        'system': '消防给水系统',
    }

    # ===== 国标管道尺寸（GB/T 3091）=====
    PIPE_SPECS = {
        'DN50': {'outer': 60.3, 'wall': 3.8, 'weight': 5.3},
        'DN80': {'outer': 88.9, 'wall': 4.0, 'weight': 8.4},
        'DN100': {'outer': 114.3, 'wall': 4.0, 'weight': 10.9},
        'DN150': {'outer': 168.3, 'wall': 4.5, 'weight': 18.2},
        'DN200': {'outer': 219.1, 'wall': 6.0, 'weight': 31.5},
    }

    # ===== 国标法兰尺寸（GB/T 9119 PN16）=====
    FLANGE_SPECS = {
        'DN50': {'outer': 165, 'thickness': 20, 'bolts': 4, 'bolt_spec': 'M16', 'hole': 18},
        'DN80': {'outer': 200, 'thickness': 22, 'bolts': 4, 'bolt_spec': 'M16', 'hole': 18},
        'DN100': {'outer': 220, 'thickness': 24, 'bolts': 8, 'bolt_spec': 'M16', 'hole': 18},
        'DN150': {'outer': 285, 'thickness': 26, 'bolts': 8, 'bolt_spec': 'M20', 'hole': 22},
        'DN200': {'outer': 340, 'thickness': 30, 'bolts': 12, 'bolt_spec': 'M20', 'hole': 22},
    }

    # ===== 国标卡箍尺寸（CJ/T 156）=====
    CLAMP_SPECS = {
        'DN50': {'width': 45, 'outer': 88, 'weight': 0.6, 'bolt': 'M8', 'bolt_count': 2},
        'DN80': {'width': 50, 'outer': 120, 'weight': 0.9, 'bolt': 'M10', 'bolt_count': 2},
        'DN100': {'width': 60, 'outer': 140, 'weight': 1.2, 'bolt': 'M10', 'bolt_count': 2},
        'DN150': {'width': 70, 'outer': 200, 'weight': 2.2, 'bolt': 'M12', 'bolt_count': 2},
        'DN200': {'width': 80, 'outer': 260, 'weight': 3.5, 'bolt': 'M12', 'bolt_count': 2},
    }

    # ===== 国标螺栓（GB/T 5782）=====
    BOLT_SPECS = {
        'M10': {'diameter': 10, 'length': 65, 'torque': 15, 'preload': 10000},
        'M12': {'diameter': 12, 'length': 100, 'torque': 20, 'preload': 15000},
        'M16': {'diameter': 16, 'length': 80, 'torque': 40, 'preload': 25000},
        'M20': {'diameter': 20, 'length': 100, 'torque': 80, 'preload': 40000},
    }

    # ===== 碰撞阈值 =====
    COLLISION = {
        'pipe_pipe': 100,        # 管道与管道（平行）≥100mm
        'pipe_pipe_insulated': 150,  # 保温管道 ≥150mm
        'pipe_wall': 50,         # 管道与墙面 ≥50mm
        'pipe_ceiling': 100,     # 管道与顶板 ≥100mm
        'pipe_beam': 50,         # 管道与梁底 ≥50mm
        'pipe_tray': 100,        # 管道与桥架 ≥100mm
        'pipe_duct': 150,        # 管道与风管 ≥150mm
        'support_support': 100,  # 支架与支架 ≥100mm
        'valve_side': 150,       # 阀门两侧 ≥150mm
    }

    # ===== 管道优先级（数字越小越优先）=====
    PIPE_PRIORITY = {
        '重力排水管': 1,
        '风管': 2,
        '桥架': 3,
        '消防管': 4,
        '给水管': 5,
    }

    # ===== CBM 配置 =====
    CBM_CONFIG = {
        'force_check_interval': 60,       # 受力检查间隔（秒）
        'contact_tolerance': 0,           # 接触面允许偏差（0mm，绝对性）
        'gasket_min_constraints': 5,      # 垫片最小约束数（位置/范围/孔径/方向/数量）
        'pipe_standard_length': 6000,     # 管道标准长度（6米）
        'bolt_fit_tolerance': 0.5,        # 螺栓与孔的公差（0.5mm）
    }

    # ===== 事件总线配置 =====
    EVENT_BUS_CONFIG = {
        'history_limit': 1000,   # 事件历史上限
        'cache_limit': 100,      # 每客户端缓存上限
        'retry_count': 3,        # 重试次数
        'retry_interval': 1,     # 重试间隔（秒）
    }

    # ===== 接触面配置 =====
    CONTACT_TOLERANCE = {
        'flange': 0,     # 法兰面偏差 0mm
        'groove': 0,     # 沟槽偏差 0mm
        'gasket': 0,     # 垫片偏差 0mm
        'support': 0,    # 支架偏差 0mm
    }


config = Config()