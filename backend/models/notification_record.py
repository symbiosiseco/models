# -*- coding: utf-8 -*-
"""
通知记录实体
受 GPL v3.0 保护

定义系统通知。含事件驱动。
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .entity import BaseEntity
from .physics_rules import notification_record_cbm
from config import config


class NotificationRecordEntity(BaseEntity):
    """通知记录实体"""

    # 通知类型
    NOTIFY_TYPES = ['任务派发', '变更通知', '验收通知', '进度款通知']

    # 状态
    STATUSES = ['未读', '已读']

    def __init__(self, notify_type: str = '任务派发',
                 recipient: str = '', content: str = '',
                 send_time: str = '', read: bool = False,
                 source_event: str = '',
                 space: Optional[Dict] = None):
        if notify_type not in self.NOTIFY_TYPES:
            notify_type = '任务派发'
        send_time = send_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # L2层
        l2 = {
            '通知类型': notify_type,
            '接收人': recipient,
            '内容': content,
            '发送时间': send_time,
            '源事件': source_event,
        }

        # L3层
        l3 = {
            '状态': '已读' if read else '未读',
        }

        # CBM层
        cbm = notification_record_cbm(notify_type)

        super().__init__(
            entity_type='通知记录',
            l2=l2,
            l3=l3,
            cbm=cbm,
            position=space or {'x': 0, 'y': 0, 'z': 0},
        )

        self.notify_type = notify_type
        self.recipient = recipient
        self.content = content
        self.send_time = send_time
        self.read = read
        self.source_event = source_event
        self.space = space or config.SPACE_UNITS

    def mark_read(self) -> Dict[str, Any]:
        """标记已读"""
        self.layer['l3_dynamic_state']['状态'] = '已读'
        self.read = True
        self.add_event('已读', '')
        return {'success': True, 'notify_id': self.id, 'status': '已读'}

    def get_status(self) -> str:
        """获取通知状态"""
        return self.layer['l3_dynamic_state'].get('状态', '未读')

    def get_recipient(self) -> str:
        """获取接收人"""
        return self.layer['l2_static_attributes'].get('接收人', '')

    def get_source_event(self) -> str:
        """获取源事件"""
        return self.layer['l2_static_attributes'].get('源事件', '')

    def to_dict(self) -> Dict[str, Any]:
        """转字典"""
        return {
            'id': self.id,
            'entity_type': '通知记录',
            'notify_type': self.notify_type,
            'recipient': self.recipient,
            'content': self.content,
            'source_event': self.source_event,
            'status': self.get_status(),
            'layer': self.layer,
        }