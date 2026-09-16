# -*- coding: utf-8 -*-
"""
施工计划分解引擎
受 GPL v3.0 保护

输入施工计划→输出任务清单。
含任务CBM生成。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class TaskGenerator:
    """施工计划分解引擎"""

    def __init__(self, template_store):
        self.template_store = template_store
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.counter = 0

    # ==================== 主入口 ====================

    def decompose(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        分解施工计划。

        输入示例：
            {
                "project": "3号楼2层消防管道",
                "start_date": "2026-09-16",
                "start_time": "08:00",
                "task_chain": [
                    {"task_template": "TPL-TASK-PREFAB-SUPPORT", "quantity": 1},
                    ...
                ]
            }
        """
        project = plan.get('project', '')
        start_date = plan.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        start_time = plan.get('start_time', '08:00')
        task_chain = plan.get('task_chain', [])

        current_time = self._parse_datetime(start_date, start_time)
        tasks = []
        prev_task_id = None

        for item in task_chain:
            tpl_id = item.get('task_template', '')
            quantity = item.get('quantity', 1)

            for _ in range(quantity):
                task = self._create_task(tpl_id, prev_task_id, current_time, len(tasks) + 1)
                if task is None:
                    continue
                tasks.append(task)
                # 更新前置任务的successor
                if prev_task_id and prev_task_id in self.tasks:
                    self.tasks[prev_task_id]['successor'].append(task['id'])
                prev_task_id = task['id']
                # 时间累加
                current_time = self._add_minutes(current_time, task['duration'])

        # 计算结束时间
        end_time = tasks[-1]['end_time'] if tasks else start_time
        return {
            'project': project,
            'total_tasks': len(tasks),
            'start_time': f'{start_date} {start_time}',
            'end_time': end_time,
            'tasks': tasks,
        }

    # ==================== 创建任务 ====================

    def _create_task(self, tpl_id: str, prev_task_id: Optional[str],
                     current_time: datetime, seq: int) -> Optional[Dict[str, Any]]:
        """创建单个任务"""
        tpl = self.template_store.get(tpl_id)
        if not tpl:
            return None

        # 生成任务ID
        task_id = f'TASK-{seq:03d}'

        # 时长
        duration = tpl.get('params', {}).get('标准时长', 120)
        start_time = current_time
        end_time = self._add_minutes(current_time, duration)

        # 执行人
        worker_tpl = tpl.get('params', {}).get('需要人员', '')
        actor = self._match_worker(worker_tpl)

        # 设备
        equip_tpl = tpl.get('params', {}).get('需要设备', '')
        equip = self._match_equipment(equip_tpl)

        # 任务CBM
        cbm = self._create_task_cbm(tpl, task_id, prev_task_id)

        task = {
            'id': task_id,
            'name': tpl.get('name', ''),
            'type': tpl.get('params', {}).get('任务类型', ''),
            'start_time': self._format_datetime(start_time),
            'end_time': self._format_datetime(end_time),
            'duration': duration,
            'actor': actor,
            'equip': equip,
            'predecessor': prev_task_id,
            'successor': [],
            'status': '待执行',
            'l4_events': [],
            'cbm': cbm,
        }
        self.tasks[task_id] = task
        return task

    def _create_task_cbm(self, tpl: Dict[str, Any], task_id: str,
                          prev_task_id: Optional[str]) -> Dict[str, Any]:
        """创建任务CBM"""
        return {
            '前置任务': prev_task_id,
            '后继任务': [],  # 由后续任务填充
            '触发规则': '完成后自动触发后继',
            '产物清单': tpl.get('params', {}).get('输出产物', []),
            '完成条件': '所有产物都完成',
        }

    # ==================== 匹配工人/设备 ====================

    def _match_worker(self, worker_type: str) -> str:
        """匹配工人"""
        if not worker_type:
            return '未指定'
        worker_map = {
            '焊工': '焊工张三',
            '管道工': '管道工王五',
            '电工': '电工李四',
            '配送员': '配送员赵六',
            '钳工': '钳工孙七',
            '质检员': '质检员周八',
        }
        return worker_map.get(worker_type, f'{worker_type}（待派）')

    def _match_equipment(self, equip_type: str) -> str:
        """匹配设备"""
        if not equip_type:
            return '未指定'
        return equip_type

    # ==================== 查找后继 ====================

    def _find_successor(self, task_id: str, all_tasks: List[Dict]) -> List[str]:
        """查找后继任务"""
        successors = []
        for t in all_tasks:
            if t.get('predecessor') == task_id:
                successors.append(t['id'])
        return successors

    # ==================== 时间工具 ====================

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """解析日期时间"""
        try:
            return datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        except ValueError:
            return datetime.now()

    def _add_minutes(self, dt: datetime, minutes: int) -> datetime:
        """加分钟"""
        return dt + timedelta(minutes=minutes)

    def _format_datetime(self, dt: datetime) -> str:
        """格式化时间"""
        return dt.strftime('%Y-%m-%d %H:%M')

    # ==================== 查询/重置 ====================

    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取任务清单"""
        return list(self.tasks.values())

    def reset(self) -> Dict[str, Any]:
        """重置"""
        self.tasks = {}
        self.counter = 0
        return {'success': True}