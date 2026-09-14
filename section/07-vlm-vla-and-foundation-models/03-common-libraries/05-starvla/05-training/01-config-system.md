# 配置系统

目标：理解 StarVLA 如何使用 YAML 配置和命令行覆盖项，以及为什么“配置即 API”。

StarVLA 训练脚本的命令行入口比较简单：

```python
parser = argparse.ArgumentParser()
parser.add_argument("--config_yaml", type=str, default="examples/SimplerEnv/train_files/starvla_cotrain_oxe.yaml")
args, clipargs = parser.parse_known_args()

cfg = OmegaConf.load(args.config_yaml)
dotlist = normalize_dotlist_args(clipargs)
cli_cfg = OmegaConf.from_dotlist(dotlist)
cfg = OmegaConf.merge(cfg, cli_cfg)
cfg = apply_config_compat(cfg)
cfg.config_yaml = args.config_yaml
main(cfg)
```

这里只有 `--config_yaml` 是 argparse 明确认识的参数。其他 `--framework.name QwenOFT`、`--trainer.max_train_steps 30000` 都先被收进 `clipargs`，再转成 OmegaConf dotlist。

## dotlist 覆盖

`normalize_dotlist_args()` 支持两种写法：

```bash
--framework.name QwenOFT
--framework.name=QwenOFT
```

它会把参数转成：

```text
framework.name=QwenOFT
```

再由：

```python
OmegaConf.from_dotlist(dotlist)
```

生成覆盖配置。

## 覆盖优先级

优先级是：

```text
framework 默认 dataclass < YAML < CLI 覆盖
```

例如 `QwenGR00TDefaultConfig` 提供默认 `action_horizon: 8`，YAML 可以改成 16，命令行又可以临时覆盖：

```bash
--framework.action_model.action_horizon 12
```

最终 framework 看到的是命令行覆盖后的值。

## apply_config_compat

训练入口会调用：

```python
cfg = apply_config_compat(cfg)
```

这个函数用于兼容旧配置。例如早期 YAML 可能只有：

```yaml
future_action_window_size: 7
```

当前代码更倾向使用：

```yaml
action_horizon: 8
```

兼容函数会把旧字段规约到当前 schema，避免历史配置失效。读代码时要注意：实际进入 framework 的 config 可能已经和原始 YAML 不完全一样。

## AccessTrackedConfig

`main(cfg)` 里第一步：

```python
cfg = wrap_config(cfg)
```

`wrap_config()` 会把 OmegaConf 包成 `AccessTrackedConfig`。它的作用是记录训练过程中实际访问过哪些配置字段。训练开始时会保存：

```python
OmegaConf.save(full_cfg, output_dir / "config.full.yaml", resolve=True)
self.config.save_accessed_config(output_dir / "config.yaml", use_original_values=False)
```

所以输出目录里有两个配置：

| 文件 | 含义 |
|---|---|
| `config.full.yaml` | 完整合并配置 |
| `config.yaml` | 训练过程中访问过的配置快照，部署加载常用 |

如果部署时报配置字段缺失，优先检查 `config.yaml` 是否包含 framework 构造和 dataloader registry 所需字段。

## 常见配置字段

| 字段 | 作用 |
|---|---|
| `framework.name` | 选择 framework 类 |
| `framework.qwenvl.base_vlm` | 基础 VLM 路径或 HF id |
| `framework.qwenvl.attn_implementation` | attention 后端，如 `flash_attention_2`、`sdpa` |
| `framework.action_model.action_dim` | 单步动作维度 |
| `framework.action_model.state_dim` | 状态维度 |
| `framework.action_model.action_horizon` | 动作 chunk 长度 |
| `datasets.vla_data.dataset_py` | VLA dataloader 类型 |
| `datasets.vla_data.data_root_dir` | 数据根目录 |
| `datasets.vla_data.data_mix` | mixture 注册表 key |
| `trainer.learning_rate` | 学习率分组 |
| `trainer.freeze_modules` | 冻结模块路径 |
| `trainer.max_train_steps` | 训练步数上限 |

## 小结

- StarVLA 的 CLI 参数大多通过 OmegaConf dotlist 覆盖。
- `framework.name`、`data_mix`、`action_horizon` 等字段直接决定代码路径。
- `apply_config_compat()` 会把旧字段规约到当前 schema。
- 输出目录中的 `config.full.yaml` 和 `config.yaml` 都有用途，部署通常依赖后者。

## 动手练习

1. 运行 `rg -n "parse_known_args|normalize_dotlist_args|OmegaConf.from_dotlist|merge_with" starVLA/training/train_starvla.py starVLA/training/trainer_utils/trainer_tools.py`，确认 `--framework.name QwenOFT` 会被当作 dotlist 覆盖项。
2. 如果已有训练输出目录，比较 `config.full.yaml` 和 `config.yaml`。成功时两个文件都能打开，`config.full.yaml` 更适合复盘完整配置。
3. 运行 `rg -n "def apply_config_compat|future_action_window_size|action_horizon" starVLA/model/framework/share_tools.py`，查看兼容函数如何处理动作窗口字段。

## 导航

- 上一节：[训练机制](../05-training.md)
- 返回上级：[训练机制](../05-training.md)
- 下一节：[02 训练入口](02-train-entrypoints.md)
