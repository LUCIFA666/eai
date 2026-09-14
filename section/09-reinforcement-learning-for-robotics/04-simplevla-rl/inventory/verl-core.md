# SimpleVLA-RL 文件索引：verl-core

覆盖 `verl-core` 分组，共 `2` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/__init__.py` | 27 | veRL 核心协议和包入口；公共入口/工具 | - | - | logging, os, protocol, utils |
| `verl/protocol.py` | 502 | veRL 核心协议和包入口 | DataProtoItem, DataProto, DataProtoFuture | union_tensor_dict, union_numpy_dict, list_of_dict_to_dict_of_list, collate_fn | copy, dataclasses, numpy, ray, tensordict, torch, typing, verl |
