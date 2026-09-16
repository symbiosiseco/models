# -*- coding: utf-8 -*-
"""
db 包入口
受 GPL v3.0 保护

导出数据库连接和 ORM 模型。
"""

from .connection import (
    get_connection,
    init_db,
    close_connection,
    execute_sql,
    execute_many,
    backup_db,
    restore_db,
)

from .models import (
    Entity,
    Event,
    Relation,
    EventBusRecord,
    Version,
)


__all__ = [
    # 连接管理
    'get_connection',
    'init_db',
    'close_connection',
    'execute_sql',
    'execute_many',
    'backup_db',
    'restore_db',
    # ORM 模型
    'Entity',
    'Event',
    'Relation',
    'EventBusRecord',
    'Version',
]