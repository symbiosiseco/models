# -*- coding: utf-8 -*-
"""
设计场景
受 GPL v3.0 保护

设计院的业务入口。
通过事件总线感知现场变化。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DesignScene:
    """设计场景"""

    def __init__(self, engine_pack: Dict[str, Any] = None,
                 entity_pack: Dict[str, Any] = None,
                 event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self.drawings: Dict[str, Any] = {}
        self.site_feedback: List[Dict[str, Any]] = []
        self._subscribe_events()

    # ==================== 事件订阅 ====================

    def _subscribe_events(self) -> Dict[str, Any]:
        """订阅现场反馈事件"""
        if not self.event_bus:
            return {'success': False}
        self.event_bus.subscribe('现场反馈', self._on_event, 'design_scene')
        self.event_bus.subscribe('变更触发', self._on_event, 'design_scene')
        self.event_bus.subscribe('装配失败', self._on_event, 'design_scene')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        """事件回调"""
        if event_type == '现场反馈':
            self.site_feedback.append({
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content': data.get('problem', ''),
                'from': data.get('reporter', '施工方'),
            })

    # ==================== 出图 ====================

    def upload_drawing(self, drawing_data: Dict[str, Any]) -> Dict[str, Any]:
        """出图"""
        from models import DrawingEntity
        drawing = DrawingEntity(
            drawing_name=drawing_data.get('drawing_name', ''),
            discipline=drawing_data.get('discipline', '消防'),
            drawing_type=drawing_data.get('drawing_type', '平面图'),
            version=drawing_data.get('version', 'v1.0'),
            designer=drawing_data.get('designer', ''),
        )
        drawing.issue(datetime.now().strftime('%Y-%m-%d'))
        self.drawings[drawing.id] = drawing

        # 通知施工/监理/甲方
        self._notify_stakeholders('出图', drawing.id)

        return {'success': True, 'drawing_id': drawing.id}

    def review_drawing(self, drawing_id: str, comments: str = '') -> Dict[str, Any]:
        """会审"""
        drawing = self.drawings.get(drawing_id)
        if not drawing:
            return {'success': False, 'message': '图纸不存在'}
        drawing.review(datetime.now().strftime('%Y-%m-%d'), comments)
        return {'success': True, 'drawing_id': drawing_id, 'status': '已会审'}

    def modify_drawing(self, drawing_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """变更设计"""
        drawing = self.drawings.get(drawing_id)
        if not drawing:
            return {'success': False, 'message': '图纸不存在'}

        # 通过事件总线发布"变更触发"
        if self.event_bus:
            self.event_bus.publish('变更触发', {
                'drawing_id': drawing_id,
                'changes': changes,
                'source': 'design',
            })

        # 通知相关方
        self._notify_stakeholders('变更', drawing_id)

        return {'success': True, 'change_id': f'CHG-{drawing_id}', 'drawing_id': drawing_id}

    # ==================== 现场反馈 ====================

    def get_site_feedback(self, drawing_id: str = '') -> List[Dict[str, Any]]:
        """实时看到现场反馈"""
        return list(self.site_feedback)

    def notify_construction(self, drawing_id: str) -> Dict[str, Any]:
        """通知施工方"""
        if self.event_bus:
            self.event_bus.publish('图纸通知', {
                'drawing_id': drawing_id,
                'role': '施工方',
            })
        return {'success': True}

    # ==================== 内部方法 ====================

    def _notify_stakeholders(self, event: str, drawing_id: str):
        """通知相关方"""
        if self.event_bus:
            self.event_bus.publish('设计通知', {
                'event': event,
                'drawing_id': drawing_id,
                'roles': ['施工方', '监理', '甲方'],
            })

    # ==================== 视图 ====================

    def get_view(self, role: str) -> Dict[str, Any]:
        """获取视图"""
        return {
            'role': role,
            'drawings': list(self.drawings.keys()),
            'site_feedback': self.site_feedback,
        }