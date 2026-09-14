# VLM 封装与动作头

目标：理解 framework 内部如何根据配置选择 VLM wrapper 和 action head。新增 backbone 或动作头时，主要改的就是这一层。

StarVLA 的 framework 通常通过构建函数选择并创建组件，减少对具体类名的硬编码：

```python
self.qwen_vl_interface = get_vlm_model(config=self.config)
self.action_model = get_action_model(config=self.config)
```

这使得同一个高层 framework 可以替换底层 VLM 或动作头。

## VLM 选择与封装

入口在 `starVLA/model/modules/vlm/__init__.py`：

```python
def get_vlm_model(config):
    vlm_name = config.framework.qwenvl.base_vlm

    if "Qwen2.5-VL" in vlm_name or "nora" in vlm_name.lower():
        from .QWen2_5 import _QWen_VL_Interface
        return _QWen_VL_Interface(config)
    elif "Qwen3-VL" in vlm_name:
        from .QWen3 import _QWen3_VL_Interface
        return _QWen3_VL_Interface(config)
    elif "Qwen3.5" in vlm_name:
        from .QWen3_5 import _QWen3_5_VL_Interface
        return _QWen3_5_VL_Interface(config)
    elif "gemma-4" in vlm_name.lower() or "gemma4" in vlm_name.lower():
        from .Gemma4 import _Gemma4_VL_Interface
        return _Gemma4_VL_Interface(config)
    elif "molmo2" in vlm_name.lower():
        from .Molmo2 import _Molmo2_VL_Interface
        return _Molmo2_VL_Interface(config)
    elif "minicpm-v" in vlm_name.lower() or "minicpmv" in vlm_name.lower():
        from .MiniCPM_V import _MiniCPM_VL_Interface
        return _MiniCPM_VL_Interface(config)
    elif "florence" in vlm_name.lower():
        from .Florence2 import _Florence_Interface
        return _Florence_Interface(config)
```

它根据 `base_vlm` 字符串选择 wrapper。这种方式简单直接，但也意味着模型路径命名会影响分发。例如模型路径如果不包含 `Qwen3-VL` 字样，可能不会进入预期分支。

## VLM wrapper 的职责

虽然不同 VLM 文件实现不同，但职责大体一致：

- 加载 Hugging Face 模型和 processor。
- 处理图像和文本输入。
- 提供 `build_qwenvl_inputs()` 或类似方法。
- 兼容 `output_hidden_states=True`。
- 对 FAST 变体提供 action token 范围信息。

framework 调用 wrapper，由 wrapper 封装 Qwen2.5 和 Qwen3 的输入差异。

## 动作头组件

action head 的实现分布在：

```text
starVLA/model/modules/action_model/
├── MLP_ActionHeader.py
├── fast_ActionHeader.py
├── GR00T_ActionHeader.py
├── LayerwiseFM_ActionHeader.py
├── DiTActionHeader.py
├── LayerwiseDiscreteDiffusion_ActionHeader.py
├── VLA_AdapterHeader.py
└── ...
```

不同 framework 会 import 不同的 `get_action_model()`。例如：

```python
# QwenOFT.py
from starVLA.model.modules.action_model.MLP_ActionHeader import get_action_model

# QwenFast.py
from starVLA.model.modules.action_model.fast_ActionHeader import get_action_model

# QwenGR00T.py
from starVLA.model.modules.action_model.GR00T_ActionHeader import get_action_model

# QwenPI.py
from starVLA.model.modules.action_model.LayerwiseFM_ActionHeader import get_action_model

# WM4A（CosmoPredict2GR00T）
from starVLA.model.modules.action_model.GR00T_ActionHeader import get_action_model
```

这说明 action head 的选择由具体 framework 决定使用哪个动作头，构建函数负责按名称实例化对应组件。

## 配置字段如何流动

以 GR00T 为例：

```yaml
framework:
  name: QwenGR00T
  action_model:
    action_model_type: DiT-B
    action_dim: 7
    state_dim: 7
    action_horizon: 8
    repeated_diffusion_steps: 8
    num_inference_timesteps: 4
    diffusion_model_cfg:
      num_layers: 16
      dropout: 0.2
```

这些字段会被 `merge_framework_config()` 合并进 `self.config.framework.action_model`，然后传给 action head 构造函数。也就是说，action head 本身不需要直接读取 YAML 文件，它只读 config 对象。

## 冻结和学习率依赖模块路径

训练器按模块路径设置学习率：

```yaml
trainer:
  learning_rate:
    base: 2.5e-05
    qwen_vl_interface: 1.0e-05
    action_model: 1.0e-04
```

`build_param_lr_groups()` 会尝试：

```python
module = model
for attr in module_name.split("."):
    module = getattr(module, attr)
```

所以 framework 内部最好把主干命名为 `qwen_vl_interface`，动作头命名为 `action_model`。否则 YAML 中的学习率组和冻结路径就找不到模块。

同理，冻结 VLM 时：

```bash
--trainer.freeze_modules "qwen_vl_interface"
```

依赖的也是 framework 的属性名。

## 新增 VLM wrapper 的注意点

新增 VLM 时至少要考虑：

1. `get_vlm_model()` 如何识别它。
2. wrapper 是否提供 framework 需要的输入构建函数。
3. 是否能返回 hidden states。
4. hidden size 在 config 中如何暴露。
5. 图像输入是 PIL、ndarray 还是 processor 自己读取路径。
6. 是否支持 bf16、flash attention 或 sdpa。

官方 FAQ 中提到，StarVLA 暂未抽象通用 vision tower 接口，因为未来 VLM 往往会内置视觉塔。实际工程上，新增 backbone 更接近新增一个 VLM wrapper。

## 小结

- VLM wrapper 由 `get_vlm_model()` 根据 `base_vlm` 字符串选择。
- action head 通常由具体 framework import 对应家族的 `get_action_model()`。
- 模块属性名会影响学习率组和冻结配置。
- 新增 backbone 时要保证输入构建、hidden states、hidden size 和精度设置都能对齐。

## 动手练习

1. 运行 `sed -n '1,80p' starVLA/model/modules/vlm/__init__.py`，查看 `get_vlm_model()` 根据 `base_vlm` 字符串选择 wrapper 的分支。
2. 在准备好模型后构建一个 framework 并打印 `model`，找到 `qwen_vl_interface` 和 `action_model`。没有模型时运行 `rg -n "qwen_vl_interface|action_model" starVLA/model/framework/VLM4A/QwenGR00T.py` 完成证据检查。
3. 运行 `rg -n "class _.*VL_Interface|def prepare_input|def forward" starVLA/model/modules/vlm`，列出一个新 VLM wrapper 至少要提供的方法和属性。

## 导航

- 上一节：[05 Qwen-GR00T](05-qwen-gr00t.md)
- 返回上级：[模型框架](../04-frameworks.md)
- 下一节：[07 WM4A](07-wm4a.md)
