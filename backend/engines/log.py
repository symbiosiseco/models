# -*- coding: utf-8 -*-
"""
日志引擎
受 GPL v3.0 保护

记录所有操作。
含CBM事件日志。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .event_bus import EventBus


class LogEngine:
    """日志引擎"""

    # 日志级别
    LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

    # 日志上限
    HISTORY_LIMIT = 10000

    # 敏感字段（脱敏）
    SENSITIVE_KEYS = ['password', 'token', 'api_key', 'secret']

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self.logs: List[Dict[str, Any]] = []
        self.counter = 0

    # ==================== 订阅事件 ====================

    def subscribe_events(self) -> Dict[str, Any]:
        """订阅事件总线"""
        if not self.event_bus:
            return {'success': False}
        for event_type in [
            'L3变化', '任务派发', '任务完成', '任务开始',
            '产物完成', '装配失败', '接触面错误', '换货触发',
            '验收通过', '验收不通过', '变更触发', '变更审批',
            '签证生成', '签字', '签字完成', '流程启动', '流程完成',
            '通知', '碰撞解决', '寿命到期', '监管警告', '现场反馈',
        ]:
            self.event_bus.subscribe(event_type, self._on_event, 'log_engine')
        return {'success': True}

    def _on_event(self, event_type: str, data: Dict[str, Any]):
        """事件回调"""
        self.log_cbm_event(event_type, data.get('entity_id', ''), data)

    # ==================== 记录日志 ====================

    def log(self, level: str, message: str,
             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """记录日志"""
        if level not in self.LEVELS:
            level = 'INFO'
        if not message:
            return {'success': False, 'message': '日志消息不能为空'}

        self.counter += 1
        log_id = f'LOG-{self.counter:06d}'

        # 脱敏
        safe_context = self._desensitize(context or {})

        log_record = {
            'log_id': log_id,
            'level': level,
            'message': message,
            'context': safe_context,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.logs.append(log_record)

        # 限制上限
        if len(self.logs) > self.HISTORY_LIMIT:
            self.logs = self.logs[-self.HISTORY_LIMIT:]

        return {'success': True, 'log_id': log_id}

    def log_cbm_event(self, event_type: str, entity_id: str,
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """记录CBM事件"""
        return self.log('INFO', f'CBM事件：{event_type}', {
            'event_type': event_type,
            'entity_id': entity_id,
            'data': self._desensitize(data),
        })

    def log_assembly(self, part_id: str, target_id: str,
                      result: Dict[str, Any]) -> Dict[str, Any]:
        """记录装配日志"""
        return self.log('INFO', f'装配：{part_id}→{target_id}', {
            'part_id': part_id,
            'target_id': target_id,
            'success': result.get('success', False),
            'message': result.get('message', ''),
        })

    def log_task(self, task_id: str, action: str,
                  actor: str = '') -> Dict[str, Any]:
        """记录任务日志"""
        return self.log('INFO', f'任务{action}：{task_id}', {
            'task_id': task_id,
            'action': action,
            'actor': actor,
        })

    def log_contact_check(self, entity_id: str,
                           result: Dict[str, Any]) -> Dict[str, Any]:
        """记录接触面检查日志"""
        return self.log('INFO', f'接触面检查：{entity_id}', {
            'entity_id': entity_id,
            'passed': result.get('passed', False),
        })

    # ==================== 查询 ====================

    def get_logs(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查询日志"""
        if not filter_dict:
            return list(self.logs)

        result = []
        for log in self.logs:
            match = True
            for k, v in filter_dict.items():
                if k == 'level' and log.get('level') != v:
                    match = False
                    break
                if k == 'entity_id':
                    ctx = log.get('context', {})
                    if ctx.get('entity_id') != v:
                        match = False
                        break
            if match:
                result.append(log)
        return result

    def get_logs_by_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """按实体查询"""
        return self.get_logs({'entity_id': entity_id})

    def get_logs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """按级别查询"""
        return self.get_logs({'level': level})

    def get_logs_by_time_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """按时间范围查询"""
        result = []
        for log in self.logs:
            ts = log.get('timestamp', '')
            if start <= ts <= end:
                result.append(log)
        return result

    # ==================== 导出 ====================

    def export_logs(self, filename: str) -> Dict[str, Any]:
        """导出日志"""
        import json
        import os
        file_path = os.path.join('/tmp', filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {'success': False, 'message': str(e)}
        return {'success': True, 'file_path': file_path}

    # ==================== 清理 ====================

    def clear_old_logs(self, days: int = 30) -> Dict[str, Any]:
        """清理旧日志"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

        original = len(self.logs)
        self.logs = [l for l in self.logs if l.get('timestamp', '') >= cutoff_str]
        return {
            'success': True,
            'cleared': original - len(self.logs),
            'remaining': len(self.logs),
        }

    # ==================== 统计 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计"""
        by_level: Dict[str, int] = {}
        for log in self.logs:
            level = log.get('level', 'INFO')
            by_level[level] = by_level.get(level, 0) + 1

        return {
            'total': len(self.logs),
            'by_level': by_level,
        }

    # ==================== 工具 ====================

    def _desensitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏"""
        if not isinstance(data, dict):
            return data
        result = {}
        for k, v in data.items():
            if k.lower() in self.SENSITIVE_KEYS:
                result[k] = '***'
            elif isinstance(v, dict):
                result[k] = self._desensitize(v)
            else:
                result[k] = v
        return result

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}