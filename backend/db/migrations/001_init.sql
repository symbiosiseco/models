-- ============================================================
-- 001_init.sql
-- 受 GPL v3.0 保护
-- 数据库初始化：5张表 + 4个索引
-- ============================================================

-- ---------- 表1：entities（实体表） ----------
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
);

-- ---------- 表2：events（事件表） ----------
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    time TEXT NOT NULL,
    event TEXT NOT NULL,
    detail TEXT,
    event_type TEXT,
    source TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- ---------- 表3：relations（关系表） ----------
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    FOREIGN KEY (from_id) REFERENCES entities(id),
    FOREIGN KEY (to_id) REFERENCES entities(id)
);

-- ---------- 表4：event_bus（事件总线表） ----------
CREATE TABLE IF NOT EXISTS event_bus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_id TEXT,
    data TEXT,
    timestamp TEXT,
    publisher TEXT
);

-- ---------- 表5：versions（数据版本表） ----------
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    snapshot TEXT,
    changed_at TEXT,
    changed_by TEXT,
    change_type TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- ---------- 索引1：实体类型 ----------
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);

-- ---------- 索引2：事件所属实体 ----------
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id);

-- ---------- 索引3：事件总线事件类型 ----------
CREATE INDEX IF NOT EXISTS idx_event_bus_type ON event_bus(event_type);

-- ---------- 索引4：版本所属实体 ----------
CREATE INDEX IF NOT EXISTS idx_versions_entity ON versions(entity_id);