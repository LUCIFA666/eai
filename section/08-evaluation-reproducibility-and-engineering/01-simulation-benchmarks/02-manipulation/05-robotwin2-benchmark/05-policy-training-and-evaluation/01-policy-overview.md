# 9.1.5.5.1 官方 Policy 总览

RoboTwin 2.0 官方 Usage 手册提供了多个 policy 的使用说明。当前项目 `/path/RoboTwin/policy/` 中也能看到这些入口：

| 类型 | Policy | 当前项目中的常见入口 |
|---|---|---|
| 可参考官方手册 | DP3、RDT、Pi0.5、OpenVLA-oft、TinyVLA、DexVLA、LLaVA-VLA、GO1、SmolVLA | 各自目录下的 `eval.sh`、`deploy_policy.py` 或训练脚本 |
| 自定义接入 | Your_Policy | `deploy_policy.py`、`deploy_policy.yml`、`eval.sh` |

本手册后续展开三个最常用、且已经整理成可执行命令的 policy：

| 章节 | 内容 |
|---|---|
| [ACT：训练与评测](02-act.md) | ACT 的数据处理、训练和评测 |
| [DP：训练与评测](03-dp.md) | DP 的 Zarr 数据处理、训练和评测 |
| [Pi0：训练与评测](04-pi0.md) | Pi0 的 OpenPI 数据转换、finetune 和评测 |

其他 policy 建议直接参考官方 Usage 手册：

- [RoboTwin Usage Guide](https://robotwin-platform.github.io/doc/usage/)
- [Deploy Your Policy](https://robotwin-platform.github.io/doc/usage/deploy-your-policy.html)
