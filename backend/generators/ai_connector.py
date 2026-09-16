# -*- coding: utf-8 -*-
"""
AI连接器
受 GPL v3.0 保护

负责调用AI（联网）查询产品标准。
支持：OpenAI / DeepSeek / 本地模型；不可用时降级到本地RULES。
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class AIConnector:
    """AI连接器"""

    # 默认配置
    DEFAULT_MODEL = 'gpt-3.5-turbo'
    TIMEOUT = 10  # 联网超时（秒）
    MAX_RETRY = 3

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get('AI_API_KEY', '')
        self.model = model or self.DEFAULT_MODEL
        self.available = bool(self.api_key)
        self.cache: Dict[str, Any] = {}

    # ==================== 产品理解 ====================

    def understand_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI理解产品本质。

        返回值：
            {产品类型, 关键参数, 适用标准, 全寿命周期, 关系}
        """
        cache_key = f"understand_{product.get('产品名称', '')}_{product.get('规格', '')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.available:
            return self._fallback_understand(product)

        prompt = self._build_prompt('understand', product)
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            self.cache[cache_key] = result
            return result
        except Exception as e:
            print(f"⚠️ AI不可用，降级：{e}")
            return self._fallback_understand(product)

    # ==================== 标准查询 ====================

    def search_standard(self, product_type: str, spec: str) -> Dict[str, Any]:
        """联网查国标"""
        cache_key = f"standard_{product_type}_{spec}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.available:
            return self._fallback_standard(product_type, spec)

        prompt = f"请查询 {product_type} {spec} 相关的国家标准，返回JSON格式。"
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            self.cache[cache_key] = result
            return result
        except Exception as e:
            print(f"⚠️ AI联网失败，降级：{e}")
            return self._fallback_standard(product_type, spec)

    # ==================== 厂家手册查询 ====================

    def search_manufacturer(self, manufacturer: str, model: str) -> Dict[str, Any]:
        """查厂家手册"""
        cache_key = f"mfr_{manufacturer}_{model}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.available:
            return {'manufacturer': manufacturer, 'model': model, 'found': False}

        prompt = f"请查询 {manufacturer} {model} 的产品参数，返回JSON格式。"
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            self.cache[cache_key] = result
            return result
        except Exception:
            return {'manufacturer': manufacturer, 'model': model, 'found': False}

    # ==================== 同类产品查询 ====================

    def search_similar(self, product_type: str, spec: str) -> Dict[str, Any]:
        """查同类产品"""
        cache_key = f"similar_{product_type}_{spec}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.available:
            return {'product_type': product_type, 'spec': spec, 'similar': []}

        prompt = f"请查询与 {product_type} {spec} 同类的产品，返回JSON格式。"
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            self.cache[cache_key] = result
            return result
        except Exception:
            return {'product_type': product_type, 'spec': spec, 'similar': []}

    # ==================== 参数补全 ====================

    def complete_params(self, params: Dict[str, Any],
                        context: Optional[Dict] = None) -> Dict[str, Any]:
        """参数补全"""
        if not self.available:
            return self._fallback_complete(params)

        context = context or {}
        prompt = f"请补全以下产品缺失参数：{json.dumps(params, ensure_ascii=False)}，上下文：{json.dumps(context, ensure_ascii=False)}。返回JSON格式。"
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            return result
        except Exception:
            return self._fallback_complete(params)

    # ==================== 规则推导 ====================

    def derive_rules(self, product: Dict[str, Any],
                     params: Dict[str, Any]) -> Dict[str, Any]:
        """规则推导"""
        if not self.available:
            return self._fallback_derive(product)

        prompt = f"请根据产品和参数推导CBM规则（物理/受力/装配/规范）。产品：{json.dumps(product, ensure_ascii=False)}。返回JSON格式。"
        try:
            response = self._call_ai(prompt)
            result = self._parse_ai_response(response)
            return result
        except Exception:
            return self._fallback_derive(product)

    # ==================== 调用AI ====================

    def _call_ai(self, prompt: str) -> str:
        """
        调用AI API。

        说明：真实项目使用 openai 库或 requests 库；
             当前为演示版，直接返回mock响应，实际接入见TODO。
        """
        if not self.available:
            raise RuntimeError('AI API key未配置')

        # TODO: 实际调用 openai/DeepSeek API
        # import openai
        # openai.api_key = self.api_key
        # response = openai.ChatCompletion.create(model=self.model, messages=[...])
        # return response.choices[0].message.content

        # 演示版：返回结构化的mock响应
        return json.dumps({
            'success': True,
            'source': 'ai_mock',
            'message': f'AI理解：{prompt[:50]}...',
        }, ensure_ascii=False)

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'success': False, 'raw': response}

    def _build_prompt(self, task: str, product: Dict[str, Any]) -> str:
        """构造prompt"""
        if task == 'understand':
            return f"请理解产品并返回JSON：{json.dumps(product, ensure_ascii=False)}"
        return json.dumps(product, ensure_ascii=False)

    # ==================== 降级方案 ====================

    def _fallback_understand(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """降级：本地理解"""
        pname = product.get('产品名称', '')
        ptype = self._guess_type(pname)
        return {
            'success': True,
            'source': 'local_rules',
            '产品类型': ptype,
            '关键参数': ['外径', '长度', '重量'],
            '适用标准': self._guess_standard(ptype),
            '全寿命周期': ['设计', '生产', '施工', '运维', '更换'],
            '关系': {'上游': [], '下游': []},
        }

    def _fallback_standard(self, product_type: str, spec: str) -> Dict[str, Any]:
        """降级：本地国标"""
        standards = {
            '阀门': 'GB/T 12224',
            '法兰': 'GB/T 9119',
            '螺栓': 'GB/T 5782',
            '卡箍': 'CJ/T 156',
            '管道': 'GB 50242',
            '支架': 'GB 50242',
        }
        return {
            'success': True,
            'source': 'local_rules',
            'product_type': product_type,
            'spec': spec,
            'standard': standards.get(product_type, 'GB 50242'),
        }

    def _fallback_complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """降级：不补全"""
        return {'success': True, 'source': 'local_rules', 'params': params}

    def _fallback_derive(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """降级：从RULES取"""
        from .rules import RULES
        ptype = self._guess_type(product.get('产品名称', ''))
        return RULES.get(ptype, RULES.get('_default', {})).get('cbm', {})

    @staticmethod
    def _guess_type(name: str) -> str:
        """从名称猜测类型"""
        mapping = {
            '阀': '阀门', '法兰': '法兰', '螺栓': '膨胀螺栓',
            '卡箍': '卡箍', '支架': '承重支架', '管': '镀锌钢管',
            '垫片': '橡胶圈', '橡胶圈': '橡胶圈',
        }
        for k, v in mapping.items():
            if k in name:
                return v
        return '_default'

    @staticmethod
    def _guess_standard(product_type: str) -> str:
        """猜测标准"""
        standards = {
            '阀门': 'GB/T 12224', '法兰': 'GB/T 9119',
            '膨胀螺栓': 'GB/T 5782', '卡箍': 'CJ/T 156',
            '承重支架': 'GB 50242', '镀锌钢管': 'GB 50242',
            '橡胶圈': 'GB/T 9126',
        }
        return standards.get(product_type, 'GB 50242')