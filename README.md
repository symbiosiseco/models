[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# 六层架构纯壳框架

**一套定义了六层数据结构的"纯壳骨架"，不包含任何具体业务实现。**

## ⚠️ 法律声明

本仓库所有代码均采用 **GNU General Public License v3.0** 协议开源。

- 任何**分发**本代码衍生作品的行为，均须将**整个衍生项目**的完整源代码以 GPL v3.0 协议公开。
- **商业闭源分发**本代码严格禁止，如需商业授权，请联系作者。
- 内部使用、私有修改（不分发）不触发源代码公开义务。
- GPL v3 不涉及网络服务（SaaS）场景；如需覆盖SaaS，请使用 AGPL v3。

## 这是什么？

这是一个**纯壳框架**——它只定义了六层架构的数据结构框架，不包含任何具体的业务逻辑或功能实现。

就像一辆汽车的车架——你可以往上面安装任何类型的发动机、变速箱和车身，但它本身不是一辆完整的车。

## 六层架构

| 层级 | 名称 | 用途 |
|------|------|------|
| R层 | 类别定义层 | 定义实体是什么 |
| L1层 | 身份标识层 | 定义实体是哪个 |
| L2层 | 静态属性层 | 定义实体有什么（外形+锚点+受力点+接触面）|
| L3层 | 动态状态层 | 定义实体现在怎么样 |
| L4层 | 事件链层 | 定义实体经历过什么 |
| CBM层 | 行为与认知模块 | 定义实体如何感知、决策与行动（数字大脑）|

## 快速开始

```python
from six_layer_core import SixLayerBuilder, SixLayerValidator

# 构建一个六层实体
entity = (
    SixLayerBuilder()
    .set_r_layer({"category": "my-type"})
    .set_l1_identity({"id": "my-id"})
    .set_l2_static_attributes({"color": "blue"})
    .set_l3_dynamic_state({"status": "active"})
    .set_l4_event_chain([{"event": "created"}])
    .set_cbm_abilities({"actions": ["start", "stop"]})
    .build()
)

# 校验框架结构
validator = SixLayerValidator()
is_valid, msgs = validator.validate_entity(entity)