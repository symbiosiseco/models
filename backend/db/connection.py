# -*- coding: utf-8 -*-
"""
数据库连接管理
受 GPL v3.0 保护

包含：
- 5张表：entities / events / relations / event_bus / versions
- 4个索引：idx_entities_type / idx_events_entity / idx_event_bus_type / idx_versions_entity
- 备份 / 恢复
"""

import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from config import config


# ==================== 连接 ====================

def get_connection() -> sqlite3.Connection:
    """
    获取数据库连接。

    数据库文件不存在时自动创建。
    """
    db_path = config.DB_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """关闭数据库连接"""
    if conn:
        try:
            conn.close()
        except Exception:
            pass


# ==================== 初始化 ====================

def init_db() -> Dict[str, Any]:
    """
    初始化数据库：创建5张表 + 4个索引。

    返回值：
        {success, tables, indexes}
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ---------- 表1：entities（实体表） ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            r_layer TEXT,
            l1_identity TEXT,
            l2_static_attributes TEXT,
            l3_dynamic_state TEXT,
            cbm_abilities TEXT,
            created_at TEXT,
            updated_at TEXT,
            version INTEGER DEFAULT 1
        )
    ''')

    # ---------- 表2：events（事件表） ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            time TEXT NOT NULL,
            event TEXT NOT NULL,
            detail TEXT,
            event_type TEXT,
            source TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
    ''')

    # ---------- 表3：relations（关系表） ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            FOREIGN KEY (from_id) REFERENCES entities(id),
            FOREIGN KEY (to_id) REFERENCES entities(id)
        )
    ''')

    # ---------- 表4：event_bus（事件总线表） ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_bus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_id TEXT,
            data TEXT,
            timestamp TEXT,
            publisher TEXT
        )
    ''')

    # ---------- 表5：versions（数据版本表） ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            snapshot TEXT,
            changed_at TEXT,
            changed_by TEXT,
            change_type TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
    ''')

    # ---------- 4个索引 ----------
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_bus_type ON event_bus(event_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_versions_entity ON versions(entity_id)')

    conn.commit()
    close_connection(conn)

    return {'success': True, 'tables': 5, 'indexes': 4}


# ==================== SQL 执行 ====================

def execute_sql(sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """
    执行SQL，返回查询结果。

    用于 SELECT。
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return result
    finally:
        close_connection(conn)


def execute_many(sql: str, params_list: List[Tuple]) -> int:
    """
    批量执行SQL，返回影响行数。

    用于 INSERT / UPDATE / DELETE。
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, params_list)
        conn.commit()
        return cursor.rowcount
    finally:
        close_connection(conn)


# ==================== 备份 / 恢复 ====================

def backup_db(backup_path: str) -> Dict[str, Any]:
    """
    备份数据库。

    参数：
        backup_path: 备份文件路径
    """
    backup_dir = os.path.dirname(backup_path)
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)

    conn = get_connection()
    backup_conn = sqlite3.connect(backup_path)
    try:
        conn.backup(backup_conn)
        return {'success': True, 'path': backup_path}
    finally:
        backup_conn.close()
        close_connection(conn)


def restore_db(backup_path: str) -> Dict[str, Any]:
    """
    恢复数据库。

    参数：
        backup_path: 备份文件路径
    """
    if not os.path.exists(backup_path):
        return {'success': False, 'message': f'备份文件不存在：{backup_path}'}

    backup_conn = sqlite3.connect(backup_path)
    conn = get_connection()
    try:
        backup_conn.backup(conn)
        return {'success': True, 'path': backup_path}
    finally:
        close_connection(conn)
        backup_conn.close()