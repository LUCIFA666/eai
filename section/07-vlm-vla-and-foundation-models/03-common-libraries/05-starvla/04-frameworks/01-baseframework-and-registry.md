# baseframework 与 registry

目标：理解 StarVLA 怎样根据 `framework.name` 构建模型，以及一个 framework 需要对外提供哪些接口。

可以先把 framework 看成模型的统一外壳。它内部可以很复杂，对外主要回答两个问题：训练时怎么计算 loss，推理时怎么输出动作。

## 核心接口

所有 VLA framework 都应该实现：

```python
def forward(self, examples, **kwargs):
    return {"action_loss": action_loss}

def predict_action(self, examples, **kwargs):
    return {"normalized_actions": actions_np}
```

训练器调用 `forward()`：

```python
output = model.forward(batch)
loss = output["action_loss"]
```

推理服务调用 `predict_action()`：

```python
out = framework.predict_action(examples=examples)
normalized = out["normalized_actions"]
```

所以读一个新 framework 时，先找这两个函数，就能知道样本字段怎样进入模型，动作怎样被预测出来。

## framework.name

训练配置里会写：

```yaml
framework:
  name: QwenOFT
```

`_auto_import_framework_modules()` 会导入 `starVLA/model/framework/` 下的模块，让注册装饰器生效。StarVLA 用这个名字从注册表中找到对应类：

```python
def build_framework(cfg):
    framework_id = cfg.framework.name
    _auto_import_framework_modules()
    model_class = FRAMEWORK_REGISTRY[framework_id]
    return model_class(cfg)
```

## registry

一个 framework 类会这样注册：

```python
@FRAMEWORK_REGISTRY.register("QwenGR00T")
class Qwen_GR00T(baseframework):
    ...
```

有些类会注册多个名字，例如 `QwenPI`：

```python
@FRAMEWORK_REGISTRY.register("QwenFM")
@FRAMEWORK_REGISTRY.register("QwenPI")
class Qwen_PI(baseframework):
    ...
```

这表示 YAML 里写 `QwenPI` 或 `QwenFM` 都会构建同一个类。新实验建议使用当前文档中更常见的名字，方便后续复现。

## from_pretrained

部署时常见入口是：

```python
framework = baseframework.from_pretrained(<CKPT_PATH>)
```

它会从 checkpoint 路径找到运行目录，并读取：

```text
<RUN_DIR>/<run_id>/
├── checkpoints/
│   └── steps_*.pt
├── config.yaml
└── dataset_statistics.json
```

然后用 `config.yaml` 重建 framework，再加载权重。一个 framework 的构造函数应该只依赖保存下来的配置，否则训练能跑，部署却无法复现模型结构。

## 搭建自己的 framework 模板

```python
from starVLA.model.framework.base_framework import baseframework
from starVLA.model.tools import FRAMEWORK_REGISTRY


@FRAMEWORK_REGISTRY.register("MyFramework")
class MyFramework(baseframework):
    def __init__(self, config):
        super().__init__()
        self.config = config
        # 在这里构建 VLM、动作头或其它模块

    def forward(self, examples, **kwargs):
        images = [e["image"] for e in examples]
        instructions = [e["lang"] for e in examples]
        actions = [e["action"] for e in examples]
        action_loss = ...
        return {"action_loss": action_loss}

    def predict_action(self, examples, **kwargs):
        images = [e["image"] for e in examples]
        instructions = [e["lang"] for e in examples]
        normalized_actions = ...
        return {"normalized_actions": normalized_actions}
```

写完后，建议用随机图像和随机动作做单文件测试，先确认 shape 对齐，再进入训练脚本。

## 小结

- `framework.name` 决定构建哪个模型类。
- `FRAMEWORK_REGISTRY.register()` 把名字和类绑定起来。
- 训练器需要 `forward()` 返回 `action_loss`。
- 推理服务需要 `predict_action()` 返回 `normalized_actions`。
- 部署加载依赖 `config.yaml`、`dataset_statistics.json` 和 checkpoint 目录结构。

## 动手练习

1. 运行 `rg -n "FRAMEWORK_REGISTRY.register" starVLA/model/framework`，列出所有注册名。
2. 运行 `rg -n 'register\("QwenFM"\)|register\("QwenPI"\)|class Qwen_PI' starVLA/model/framework/VLM4A/QwenPI.py`，确认 `QwenPI` 和 `QwenFM` 是否注册到同一个类。
3. 运行 `rg -n "class baseframework|def forward|def predict_action|normalized_actions" starVLA/model/framework/base_framework.py`，写出一个最小 framework 必须满足的接口。

## 导航

- 上一节：[模型框架](../04-frameworks.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[02 Qwen-OFT](02-qwen-oft.md)
