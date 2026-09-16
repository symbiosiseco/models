# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM 模型
受 GPL v3.0 保护

5张表：
- entities：实体表
- events：事件表
- relations：关系表
- event_bus：事件总线表
- versions：数据版本表
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from sqlalchemy import (
        Column, Text, Integer, ForeignKey, create_engine
    )
    from sqlalchemy.orm import declarative_base, sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    # 降级：提供空基类，避免导入失败
    class _Base:
        pass
    declarative_base = lambda: _Base
    Column = lambda *a, **kw: None
    Text = Integer = ForeignKey = None
    create_engine = sessionmaker = None


from config import config


Base = declarative_base()


# ==================== 表1：entities ====================

class Entity(Base):
    """实体表"""
    __tablename__ = 'entities'

    id = Column(Text, primary_key=True)
    entity_type = Column(Text, nullable=False)
    r_layer = Column(Text)
    l1_identity = Column(Text)
    l2_static_attributes = Column(Text)
    l3_dynamic_state = Column(Text)
    cbm_abilities = Column(Text)
    created_at = Column(Text)
    updated_at = Column(Text)
    version = Column(Integer, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'r_layer': self._load_json(self.r_layer),
            'l1_identity': self._load_json(self.l1_identity),
            'l2_static_attributes': self._load_json(self.l2_static_attributes),
            'l3_dynamic_state': self._load_json(self.l3_dynamic_state),
            'cbm_abilities': self._load_json(self.cbm_abilities),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'version': self.version,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Entity':
        """从字典创建"""
        return Entity(
            id=data.get('id', ''),
            entity_type=data.get('entity_type', ''),
            r_layer=json.dumps(data.get('r_layer', {}), ensure_ascii=False),
            l1_identity=json.dumps(data.get('l1_identity', {}), ensure_ascii=False),
            l2_static_attributes=json.dumps(data.get('l2_static_attributes', {}), ensure_ascii=False),
            l3_dynamic_state=json.dumps(data.get('l3_dynamic_state', {}), ensure_ascii=False),
            cbm_abilities=json.dumps(data.get('cbm_abilities', {}), ensure_ascii=False),
            created_at=data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            updated_at=data.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            version=data.get('version', 1),
        )

    @staticmethod
    def _load_json(val: Optional[str]) -> Any:
        if not val:
            return {}
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}


# ==================== 表2：events ====================

class Event(Base):
    """事件表"""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Text, ForeignKey('entities.id'), nullable=False)
    time = Column(Text, nullable=False)
    event = Column(Text, nullable=False)
    detail = Column(Text)
    event_type = Column(Text)
    source = Column(Text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_id': self.entity_id,
            'time': self.time,
            'event': self.event,
            'detail': self.detail,
            'event_type': self.event_type,
            'source': self.source,
        }


# ==================== 表3：relations ====================

class Relation(Base):
    """关系表"""
    __tablename__ = 'relations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_id = Column(Text, ForeignKey('entities.id'), nullable=False)
    to_id = Column(Text, ForeignKey('entities.id'), nullable=False)
    relation_type = Column(Text, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'from_id': self.from_id,
            'to_id': self.to_id,
            'relation_type': self.relation_type,
        }


# ==================== 表4：event_bus ====================

class EventBusRecord(Base):
    """事件总线表"""
    __tablename__ = 'event_bus'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(Text, nullable=False)
    entity_id = Column(Text)
    data = Column(Text)
    timestamp = Column(Text)
    publisher = Column(Text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_type': self.event_type,
            'entity_id': self.entity_id,
            'data': self._load_json(self.data),
            'timestamp': self.timestamp,
            'publisher': self.publisher,
        }

    @staticmethod
    def _load_json(val: Optional[str]) -> Any:
        if not val:
            return {}
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}


# ==================== 表5：versions ====================

class Version(Base):
    """数据版本表"""
    __tablename__ = 'versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Text, ForeignKey('entities.id'), nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(Text)
    changed_at = Column(Text)
    changed_by = Column(Text)
    change_type = Column(Text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_id': self.entity_id,
            'version': self.version,
            'snapshot': self._load_json(self.snapshot),
            'changed_at': self.changed_at,
            'changed_by': self.changed_by,
            'change_type': self.change_type,
        }

    @staticmethod
    def _load_json(val: Optional[str]) -> Any:
        if not val:
            return {}
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}


# ==================== 引擎 / 会话 ====================

_engine = None
_Session = None


def get_engine():
    """获取SQLAlchemy引擎"""
    global _engine
    if _engine is None and HAS_SQLALCHEMY:
        _engine = create_engine(f'sqlite:///{config.DB_PATH}', echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session():
    """获取SQLAlchemy会话"""
    global _Session
    if _Session is None and HAS_SQLALCHEMY:
        _Session = sessionmaker(bind=get_engine())
    return _Session() if _Session else None