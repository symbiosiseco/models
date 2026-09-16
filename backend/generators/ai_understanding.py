# -*- coding: utf-8 -*-
"""
AI产品理解引擎
受 GPL v3.0 保护

理解产品本质、识别关键参数。
"""

from typing import Dict, Any, List
from .ai_connector import AIConnector


class AIUnderstanding:
    """AI产品理解引擎"""

    # 产品类型→关键参数映射
    TYPE_PARAMS = {
        '阀门': ['阀门类型', '规格', '外径', '长度', '重量', '材质', '工作压力'],
        '法兰': ['规格', '压力等级', '外径', '厚度', '螺栓数量', '螺栓孔径', '材质'],
        '膨胀螺栓': ['规格', '直径', '长度', '材质', '拧紧力矩'],
        '卡箍': ['规格', '外径', '宽度', '重量', '螺栓规格', '密封圈'],
        '承重支架': ['规格', '材质', '横担长度', '立杆长度', '承重能力'],
        '镀锌钢管': ['管径', '外径', '壁厚', '材质', '标准长度'],
        '橡胶圈': ['规格', '外径', '内径', '厚度', '材质', '设计年限'],
    }

    # 产品类型→标准映射
    TYPE_STANDARDS = {
        '阀门': ['GB/T 12224', 'GB/T 12238'],
        '法兰': ['GB/T 9119'],
        '膨胀螺栓': ['GB/T 5782'],
        '卡箍': ['CJ/T 156'],
        '承重支架': ['GB 50242', 'GB/T 706'],
        '镀锌钢管': ['GB 50242', 'GB/T 3091'],
        '橡胶圈': ['GB/T 9126'],
    }

    def __init__(self, ai_connector: AIConnector):
        self.ai = ai_connector

    # ==================== 主入口 ====================

    def understand(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """理解产品"""
        ptype = self.identify_type(product)
        key_params = self.identify_key_params(product)
        standards = self.identify_standards(product)
        lifecycle = self.identify_lifecycle(product)
        relationships = self.identify_relationships(product)

        return {
            'success': True,
            '产品类型': ptype,
            '关键参数': key_params,
            '适用标准': standards,
            '全寿命周期': lifecycle,
            '关系': relationships,
        }

    # ==================== 识别方法 ====================

    def identify_type(self, product: Dict[str, Any]) -> str:
        """识别产品类型"""
        name = product.get('产品名称', '')
        if not name:
            name = product.get('产品型号', '')
        ptype = self.ai._guess_type(name)
        return ptype if ptype != '_default' else '未知'

    def identify_key_params(self, product: Dict[str, Any]) -> List[str]:
        """识别关键参数"""
        ptype = self.identify_type(product)
        return self.TYPE_PARAMS.get(ptype, ['外径', '长度'])

    def identify_standards(self, product: Dict[str, Any]) -> List[str]:
        """识别适用标准"""
        ptype = self.identify_type(product)
        return self.TYPE_STANDARDS.get(ptype, ['GB 50242'])

    def identify_lifecycle(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """识别全寿命周期"""
        return {
            '设计': {'阶段': '设计阶段', '标准': 'GB 50015'},
            '生产': {'阶段': '工厂生产', '标准': 'GB/T 12224'},
            '施工': {'阶段': '现场安装', '标准': 'GB 50242'},
            '运维': {'阶段': '运维保养', '周期': '每年1次'},
            '更换': {'阶段': '寿命更换', '周期': '10年'},
        }

    def identify_relationships(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """识别与其他实体的关系"""
        ptype = self.identify_type(product)
        relations_map = {
            '阀门': {'上游': ['法兰', '垫片', '螺栓'], '下游': ['管道', '卡箍']},
            '法兰': {'上游': ['螺栓', '垫片'], '下游': ['阀门', '管道']},
            '垫片': {'上游': [], '下游': ['法兰']},
            '卡箍': {'上游': ['橡胶圈'], '下游': ['管道']},
            '承重支架': {'上游': ['管道'], '下游': ['楼板', '膨胀螺栓']},
            '镀锌钢管': {'上游': ['卡箍'], '下游': ['支架']},
        }
        return relations_map.get(ptype, {'上游': [], '下游': []})

    # ==================== 辅助 ====================

    def get_missing_params(self, product: Dict[str, Any]) -> List[str]:
        """获取缺失的参数"""
        key_params = self.identify_key_params(product)
        existing = set(product.get('params', {}).keys())
        return [p for p in key_params if p not in existing]

    def get_recommendations(self, product: Dict[str, Any]) -> List[str]:
        """获取建议"""
        recommendations = []
        missing = self.get_missing_params(product)
        if missing:
            recommendations.append(f'建议补全参数：{missing}')
        if not product.get('厂家'):
            recommendations.append('建议补充厂家信息')
        return recommendations