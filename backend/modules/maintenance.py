# -*- coding: utf-8 -*-
"""
运维场景
受 GPL v3.0 保护

物业管理，含寿命管理、品质追溯。

V2.0 升级（专报G）：
- 到期自动提醒（CBM定时器 + L4历史）
- 品质追溯（L4套娃履历）
- 全生命周期查询
"""

from typing import Dict, Any, List
from datetime import datetime


class MaintenanceScene:
    """运维场景"""

    def __init__(self, engine_pack=None, entity_pack=None, event_bus=None):
        self.engines = engine_pack or {}
        self.entities = entity_pack or {}
        self.event_bus = event_bus
        self._subscribe_events()

    def _subscribe_events(self):
        """订阅感兴趣的事件"""
        if self.event_bus:
            self.event_bus.subscribe('寿命到期', self._on_event, 'maintenance')
            self.event_bus.subscribe('L3变化', self._on_event, 'maintenance')

    def _on_event(self, event_type, data):
        """事件回调"""
        if event_type == '寿命到期':
            pass  # 通知物业
        return {'success': True}

    # ==================== 接收移交 ====================

    def receive_handover(self, project_id: str) -> Dict[str, Any]:
        """
        接收移交。

        流程：
            1. 竣工模型自动移交
            2. 资料自动移交
            3. 物业接收
            4. 写 L4
        """
        handover_id = f'HANDOVER-{datetime.now().strftime("%Y%m%d%H%M%S")}'

        # 写 L4 到所有实体
        for e in self.entities.values():
            if hasattr(e, 'add_event'):
                try:
                    e.add_event('移交完成', f'项目{project_id} → 物业')
                except Exception:
                    pass

        if self.event_bus:
            self.event_bus.publish('移交完成', {
                'handover_id': handover_id,
                'project_id': project_id,
            })

        return {
            'success': True,
            'handover_id': handover_id,
            'message': '移交完成，物业可查询所有构件',
        }

    # ==================== ★ V2.0 新增：到期自动提醒 ====================

    def check_lifecycle_alerts(self) -> Dict[str, Any]:
        """
        ★ V2.0 新增：CBM定时器 + L4历史 = 到期自动提醒。

        检查：
            1. 橡胶圈：8年检查，10年更换
            2. 阀门：每年检查
            3. 支架：每年检查
        """
        alerts = []
        now = datetime.now()

        for e in self.entities.values():
            e_type = getattr(e, 'entity_type', '')
            if e_type not in ('垫片', '橡胶圈', '阀门', '支架', '管道'):
                continue

            # 读 L4 历史
            l4 = e.layer.get('l4_event_chain', []) if hasattr(e, 'layer') else []

            # 找最早的安装/生产时间
            install_time = None
            for ev in l4:
                if '安装' in ev.get('event', '') or '生产' in ev.get('event', ''):
                    try:
                        install_time = datetime.strptime(ev['time'], '%Y-%m-%d %H:%M:%S')
                        break
                    except (ValueError, KeyError):
                        pass

            if not install_time:
                continue

            age_years = (now - install_time).days / 365.0

            # 垫片/橡胶圈：8年检查，10年更换
            if e_type in ('垫片', '橡胶圈'):
                if 8 <= age_years < 10:
                    alerts.append({
                        'entity_id': getattr(e, 'id', ''),
                        'entity_type': e_type,
                        'type': '检查',
                        'age_years': round(age_years, 1),
                        'message': f'{e_type}已使用{age_years:.1f}年，建议8年检查',
                    })
                elif age_years >= 10:
                    alerts.append({
                        'entity_id': getattr(e, 'id', ''),
                        'entity_type': e_type,
                        'type': '更换',
                        'age_years': round(age_years, 1),
                        'message': f'{e_type}已使用{age_years:.1f}年，必须更换',
                    })

            # 阀门/支架：每年检查
            elif e_type in ('阀门', '支架') and age_years >= 1:
                alerts.append({
                    'entity_id': getattr(e, 'id', ''),
                    'entity_type': e_type,
                    'type': '检查',
                    'age_years': round(age_years, 1),
                    'message': f'{e_type}已使用{age_years:.1f}年，建议检查',
                })

        # 发布事件
        if alerts and self.event_bus:
            self.event_bus.publish('寿命到期', {'alerts': alerts})

        return {
            'success': True,
            'count': len(alerts),
            'alerts': alerts,
        }

    # ==================== 安排检查 ====================

    def schedule_inspection(self, entity_id: str, date: str) -> Dict[str, Any]:
        """安排检查"""
        inspection_id = f'INSP-{datetime.now().strftime("%Y%m%d%H%M%S")}'

        e = self.entities.get(entity_id)
        if e and hasattr(e, 'add_event'):
            e.add_event('安排检查', f'计划日期：{date}')

        return {
            'success': True,
            'inspection_id': inspection_id,
            'entity_id': entity_id,
            'date': date,
        }

    # ==================== 记录检查 ====================

    def record_inspection(self, entity_id: str, result: str) -> Dict[str, Any]:
        """记录检查"""
        e = self.entities.get(entity_id)
        if e and hasattr(e, 'add_event'):
            e.add_event('检查完成', result)
            if hasattr(e, 'update_status'):
                e.update_status('状态', '已检查')

        return {
            'success': True,
            'entity_id': entity_id,
            'result': result,
        }

    # ==================== 安排更换 ====================

    def schedule_replacement(self, entity_id: str) -> Dict[str, Any]:
        """安排更换"""
        replacement_id = f'REPL-{datetime.now().strftime("%Y%m%d%H%M%S")}'

        e = self.entities.get(entity_id)
        if e and hasattr(e, 'add_event'):
            e.add_event('安排更换', f'计划更换')

        if self.event_bus:
            self.event_bus.publish('更换计划', {
                'entity_id': entity_id,
                'replacement_id': replacement_id,
            })

        return {
            'success': True,
            'replacement_id': replacement_id,
            'entity_id': entity_id,
        }

    # ==================== ★ V2.0 增强：品质追溯 ====================

    def trace_quality(self, entity_id: str) -> Dict[str, Any]:
        """
        ★ V2.0 增强：品质追溯（L4套娃履历）。

        返回：
            - 自身履历
            - 内部零件履历
        """
        e = self.entities.get(entity_id)
        if not e:
            return {'success': False, 'message': f'实体不存在：{entity_id}'}

        l4 = e.layer.get('l4_event_chain', []) if hasattr(e, 'layer') else []

        # 分离自身履历和内部零件履历
        self_history = []
        internal_parts = {}

        for ev in l4:
            if isinstance(ev, dict):
                if '内部零件' in ev or 'part' in ev:
                    part_name = ev.get('part', ev.get('内部零件', '未知'))
                    if part_name not in internal_parts:
                        internal_parts[part_name] = []
                    internal_parts[part_name].append(ev)
                else:
                    self_history.append(ev)

        return {
            'success': True,
            'entity_id': entity_id,
            'entity_type': getattr(e, 'entity_type', ''),
            'self_history': self_history,
            'internal_parts': internal_parts,
            'lifecycle': self.get_lifecycle(entity_id),
        }

    # ==================== 全生命周期 ====================

    def get_lifecycle(self, entity_id: str) -> Dict[str, Any]:
        """获取全生命周期"""
        e = self.entities.get(entity_id)
        if not e:
            return {'success': False}

        l4 = e.layer.get('l4_event_chain', []) if hasattr(e, 'layer') else []

        # 计算使用年限
        years = 0
        for ev in l4:
            if '生产' in ev.get('event', '') or '安装' in ev.get('event', ''):
                try:
                    t = datetime.strptime(ev['time'], '%Y-%m-%d %H:%M:%S')
                    years = (datetime.now() - t).days / 365.0
                    break
                except (ValueError, KeyError):
                    pass

        return {
            'success': True,
            'entity_id': entity_id,
            'events': l4,
            'years': round(years, 1),
        }

    def get_view(self, role: str) -> Dict[str, Any]:
        """获取视图"""
        return {
            'role': role,
            'lifecycle_count': len(self.entities),
        }