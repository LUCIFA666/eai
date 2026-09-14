# RLINF 文件索引：root-other

覆盖 `root-other` 分组，共 `4` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `docs/source-en/conf.py` | 196 | 项目根入口或其他支持文件 | - | render_svg_logo, make_role, setup_html_context, setup | docutils, os, pathlib, re, sys |
| `docs/source-zh/conf.py` | 196 | 项目根入口或其他支持文件 | - | render_svg_logo, make_role, setup_html_context, setup | docutils, os, pathlib, re, sys |
| `rlinf/__init__.py` | 17 | 项目根入口或其他支持文件；公共入口/工具 | - | - | utils |
| `rlinf/config.py` | 1555 | 项目根入口或其他支持文件；配置/参数定义 | SupportedModel | torch_dtype_from_precision, gelu_impl, openai_gelu, squared_relu, erf_gelu, activation_to_func, validate_rollout_cfg, validate_model_cfg_by_hf_config, validate_fsdp_cfg, validate_megatron_cfg | dataclasses, importlib, logging, omegaconf, os, rlinf, torch, typing |
