# -*- coding: utf-8 -*-
"""
导出引擎
受 GPL v3.0 保护

导出报表和数据。
支持：Excel / PDF / JSON。
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_bus import EventBus


class ExportEngine:
    """导出引擎"""

    # 支持的格式
    FORMATS = ['excel', 'pdf', 'json']

    # 8种报表
    REPORT_TYPES = [
        'quantity', 'payment', 'acceptance', 'change',
        'material', 'quality', 'asbuilt', 'visa',
    ]

    # 导出目录
    EXPORT_DIR = '/tmp/exports'

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        # 确保目录存在
        try:
            os.makedirs(self.EXPORT_DIR, exist_ok=True)
        except OSError:
            pass

    # ==================== Excel ====================

    def export_to_excel(self, data: Dict[str, Any],
                         filename: str) -> Dict[str, Any]:
        """导出Excel"""
        if not filename:
            filename = f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        file_path = os.path.join(self.EXPORT_DIR, filename)

        try:
            # 尝试用openpyxl，失败时降级到JSON
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = data.get('report_type', 'Sheet1')
                # 写表头
                ws.append(['字段', '值'])
                # 写数据
                for k, v in data.items():
                    if isinstance(v, (str, int, float)):
                        ws.append([k, str(v)])
                wb.save(file_path)
            except ImportError:
                # 降级：写JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {'success': False, 'message': str(e)}

        # 通过事件总线发布
        if self.event_bus:
            self.event_bus.publish('导出完成', {
                'format': 'excel',
                'filename': filename,
                'file_path': file_path,
            })

        return {
            'success': True,
            'file_path': file_path,
            'file_size': self._get_file_size(file_path),
        }

    # ==================== PDF ====================

    def export_to_pdf(self, data: Dict[str, Any],
                       filename: str) -> Dict[str, Any]:
        """导出PDF"""
        if not filename:
            filename = f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        file_path = os.path.join(self.EXPORT_DIR, filename)

        try:
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(file_path, pagesize=A4)
                c.drawString(100, 800, str(data.get('report_type', 'Report')))
                y = 760
                for k, v in data.items():
                    if isinstance(v, (str, int, float)):
                        c.drawString(100, y, f'{k}: {v}')
                        y -= 20
                        if y < 100:
                            c.showPage()
                            y = 800
                c.save()
            except ImportError:
                # 降级：写JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {'success': False, 'message': str(e)}

        if self.event_bus:
            self.event_bus.publish('导出完成', {
                'format': 'pdf',
                'filename': filename,
                'file_path': file_path,
            })

        return {
            'success': True,
            'file_path': file_path,
            'file_size': self._get_file_size(file_path),
        }

    # ==================== JSON ====================

    def export_to_json(self, data: Dict[str, Any],
                        filename: str) -> Dict[str, Any]:
        """导出JSON"""
        if not filename:
            filename = f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
        if not filename.endswith('.json'):
            filename += '.json'

        file_path = os.path.join(self.EXPORT_DIR, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {'success': False, 'message': str(e)}

        if self.event_bus:
            self.event_bus.publish('导出完成', {
                'format': 'json',
                'filename': filename,
                'file_path': file_path,
            })

        return {
            'success': True,
            'file_path': file_path,
            'file_size': self._get_file_size(file_path),
        }

    # ==================== 导出实体列表 ====================

    def export_entity_list(self, entities: List, format: str = 'excel') -> Dict[str, Any]:
        """导出实体列表"""
        data = {
            'report_type': '实体列表',
            'total': len(entities),
            'entities': [
                {
                    'id': getattr(e, 'id', ''),
                    'entity_type': getattr(e, 'entity_type', ''),
                }
                for e in entities
            ],
        }
        if format == 'excel':
            return self.export_to_excel(data, 'entity_list.xlsx')
        elif format == 'pdf':
            return self.export_to_pdf(data, 'entity_list.pdf')
        else:
            return self.export_to_json(data, 'entity_list.json')

    # ==================== 8种报表导出 ====================

    def export_quantity_report(self, data: Dict[str, Any],
                                format: str = 'excel') -> Dict[str, Any]:
        """导出工程量清单"""
        return self._export_by_format(data, 'quantity_report', format)

    def export_payment_report(self, data: Dict[str, Any],
                               format: str = 'excel') -> Dict[str, Any]:
        """导出进度款"""
        return self._export_by_format(data, 'payment_report', format)

    def export_acceptance_report(self, data: Dict[str, Any],
                                  format: str = 'pdf') -> Dict[str, Any]:
        """导出验收记录"""
        return self._export_by_format(data, 'acceptance_report', format)

    def export_change_report(self, data: Dict[str, Any],
                              format: str = 'excel') -> Dict[str, Any]:
        """导出变更台账"""
        return self._export_by_format(data, 'change_report', format)

    def export_material_report(self, data: Dict[str, Any],
                                format: str = 'excel') -> Dict[str, Any]:
        """导出材料台账"""
        return self._export_by_format(data, 'material_report', format)

    def export_quality_report(self, data: Dict[str, Any],
                               format: str = 'pdf') -> Dict[str, Any]:
        """导出质量记录"""
        return self._export_by_format(data, 'quality_report', format)

    def export_asbuilt_report(self, data: Dict[str, Any],
                               format: str = 'json') -> Dict[str, Any]:
        """导出竣工图"""
        return self._export_by_format(data, 'asbuilt_report', format)

    def export_visa_report(self, data: Dict[str, Any],
                            format: str = 'pdf') -> Dict[str, Any]:
        """导出签证单"""
        return self._export_by_format(data, 'visa_report', format)

    # ==================== 内部方法 ====================

    def _export_by_format(self, data: Dict[str, Any],
                           name: str, format: str) -> Dict[str, Any]:
        """按格式导出"""
        if format == 'excel':
            return self.export_to_excel(data, f'{name}.xlsx')
        elif format == 'pdf':
            return self.export_to_pdf(data, f'{name}.pdf')
        elif format == 'json':
            return self.export_to_json(data, f'{name}.json')
        else:
            return {'success': False, 'message': f'不支持的格式：{format}'}

    def _format_excel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化Excel数据"""
        return data

    def _format_pdf(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化PDF数据"""
        return data

    def _format_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化JSON数据"""
        return data

    def _get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通过事件总线发布"""
        if self.event_bus:
            return self.event_bus.publish(event_type, data)
        return {'success': False}