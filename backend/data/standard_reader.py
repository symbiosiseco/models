# -*- coding: utf-8 -*-
"""
标准参数读取器
受 GPL v3.0 保护

★ V2.0（阶段2-3-fix）：兼容旧版JSON结构

支持两种结构：
    结构A（新版，平铺+中文键）：
        {"DN100": {"外径": 240, "厚度": 24}}
    结构B（旧版，嵌套+英文键）：
        {"flanges": {"DN100": {"outer": 240, "thickness": 24}}}

自动识别，自动转换。代码统一返回中文键。
"""

import json
import os
from typing import Dict, Any, Optional, Callable, List


STANDARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'standards')

_change_hooks: List[Callable] = []
_file_mtimes: Dict[str, float] = {}


# ==================== 英中键名映射 ====================

KEY_MAP = {
    # 通用
    'outer': '外径',
    'thickness': '厚度',
    'length': '长度',
    'weight': '重量',
    # 管道
    'wall': '壁厚',
    # 法兰
    'bolts': '螺栓孔数',
    'bolt_spec': '螺栓规格',
    'hole': '螺栓孔径',
    # 卡箍
    'width': '卡箍宽度',
    # 阀门
    # （长度和重量已在通用里）
    # 垫片
    'outer_d': '垫片外径',
    'inner': '垫片内径',
    # 螺栓
    'diameter': '直径',
    'torque': '拧紧力矩',
    'preload': '预紧力',
    # 支架
    'spec': '规格',
    'material': '材质',
    # 风管/桥架
    'height': '高度',
}


def _convert_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """英文键 → 中文键。中文键保持不变。"""
    if not isinstance(data, dict):
        return {}

    result = {}
    for k, v in data.items():
        if k.startswith('_'):
            continue
        # 键名转换：优先中文键，英文键转中文
        new_key = KEY_MAP.get(k, k)
        if v is not None:
            result[new_key] = v
    return result


# ==================== 核心：加载文件 ====================

def _load_standard_file(category: str) -> Dict[str, Any]:
    """
    加载标准 JSON 文件。
    ★ 自动识别两种结构：
        A. 平铺：{"DN100": {...}}
        B. 嵌套：{"flanges": {"DN100": {...}}}
    """
    if not category or not isinstance(category, str):
        return {}

    file_path = os.path.join(STANDARDS_DIR, f'{category}.json')
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ 读取标准文件失败 {file_path}: {e}")
        return {}

    if not isinstance(data, dict):
        return {}

    # 过滤元数据
    filtered = {k: v for k, v in data.items() if not k.startswith('_')}

    if not filtered:
        return {}

    # ★ 判断结构：
    # 如果只有 1 个 key，且它的 value 是 dict，且 value 里的 key 都像规格（DNxxx, Mxx, Lxx）
    # 那说明是嵌套结构（结构B）
    keys = list(filtered.keys())
    if len(keys) == 1:
        only_value = filtered[keys[0]]
        if isinstance(only_value, dict):
            # 检查 value 里的键是不是规格
            sample_keys = list(only_value.keys())[:3]
            if all(k.startswith(('DN', 'M', 'L', 'Φ', 'φ', 'D')) or '×' in k for k in sample_keys):
                # 是嵌套结构，进入子键
                return {
                    spec: _convert_keys(v) if isinstance(v, dict) else {}
                    for spec, v in only_value.items()
                    if isinstance(v, dict)
                }

    # 平铺结构：直接转换每个 value 的键
    result = {}
    for spec, v in filtered.items():
        if isinstance(v, dict):
            # 如果 value 里还是 dict（比如 valves.json 里的子类型），保留一层
            if all(isinstance(vv, dict) for vv in v.values() if not str(vv).startswith('_')):
                # 双层结构（阀门：类型 → DN → 参数）
                result[spec] = {
                    sub: _convert_keys(subv)
                    for sub, subv in v.items()
                    if isinstance(subv, dict)
                }
            else:
                result[spec] = _convert_keys(v)
    return result


def _check_file_changed(category: str) -> bool:
    """检查文件是否变化"""
    file_path = os.path.join(STANDARDS_DIR, f'{category}.json')
    if not os.path.exists(file_path):
        return False
    try:
        mtime = os.path.getmtime(file_path)
    except OSError:
        return False
    old_mtime = _file_mtimes.get(category)
    if old_mtime is None or old_mtime != mtime:
        _file_mtimes[category] = mtime
        return True
    return False


# ==================== 对外接口 ====================

def read_standard(category: str, spec: str, subtype: Optional[str] = None) -> Dict[str, Any]:
    """
    读取标准参数。永远返回 dict（绝不返回 None）。
    """
    if not category or not spec:
        return {}

    data = _load_standard_file(category)
    if not isinstance(data, dict):
        return {}

    entry = data.get(spec)
    if entry is None or not isinstance(entry, dict):
        return {}

    # 如果有子类型，深入一层
    if subtype:
        sub = entry.get(subtype)
        if isinstance(sub, dict):
            return sub

    return entry


def get_param(category: str, spec: str, key: str, default: Any = None,
              subtype: Optional[str] = None) -> Any:
    """读取单个参数值"""
    spec_data = read_standard(category, spec, subtype)
    if not isinstance(spec_data, dict):
        return default
    value = spec_data.get(key)
    return value if value is not None else default


def clear_cache() -> None:
    """清空缓存"""
    _file_mtimes.clear()


def list_categories() -> list:
    """列出所有可用的标准类别"""
    if not os.path.exists(STANDARDS_DIR):
        return []
    return [
        f.replace('.json', '')
        for f in os.listdir(STANDARDS_DIR)
        if f.endswith('.json')
    ]


def list_specs(category: str) -> list:
    """列出某类别下所有规格"""
    data = _load_standard_file(category)
    return list(data.keys()) if isinstance(data, dict) else []


# ==================== 变更通知 ====================

def register_change_hook(callback: Callable) -> None:
    """注册参数变更钩子"""
    if callable(callback) and callback not in _change_hooks:
        _change_hooks.append(callback)


def unregister_change_hook(callback: Callable) -> None:
    """取消注册"""
    if callback in _change_hooks:
        _change_hooks.remove(callback)


def notify_change(category: str, spec: str, old_value: Any, new_value: Any) -> None:
    """触发所有变更钩子"""
    for hook in _change_hooks:
        try:
            hook(category, spec, old_value, new_value)
        except Exception as e:
            print(f"⚠️ 变更钩子执行失败：{e}")


def check_and_reload() -> Dict[str, Any]:
    """检查所有标准文件是否变化"""
    changed = []
    for category in list_categories():
        if _check_file_changed(category):
            changed.append(category)
            notify_change(category, '*', None, None)
    return {'changed': changed, 'total': len(changed)}


def warm_up() -> Dict[str, Any]:
    """启动时预热"""
    loaded = []
    failed = []
    for category in list_categories():
        data = _load_standard_file(category)
        if data:
            loaded.append(f'{category}({len(data)})')
        else:
            failed.append(category)
    return {'loaded': loaded, 'failed': failed, 'total': len(loaded)}