# 8.5.2.2 环境安装与 Policy 选择

## 学习目标

- 完成 LeRobot 源码的 clone 与基础环境安装。
- 理解不同 policy 的依赖差异，学会按需安装扩展。
- 根据学习目标选择合适的 policy 模型。

## 环境配置

首先从 GitHub clone LeRobot 源码并切换到指定版本：

```bash
git clone https://github.com/huggingface/lerobot.git
cd lerobot
git checkout v0.5.2
```

然后创建 conda 环境（`xxx` 替换为你自定义的环境名）：

```bash
conda create -y -n xxx python=3.12
conda activate xxx
```

进入 LeRobot 目录，安装基础依赖：

```bash
cd lerobot
pip install -e .
```

安装完成后，验证是否成功：

```bash
python -c "import lerobot; print('lerobot import ok')"
```

后续根据想训练的模型，安装对应的扩展依赖（如 `pip install -e ".[xvla,training]"`）。具体的安装命令在各模型章节中会详细介绍。

## 如何选择 Policy

在 LeRobot 中，policy 指的是机器人策略模型——根据当前观测信息（图像、状态、语言指令）预测机器人动作的模型。不同 policy 的输入形式、训练成本和适用场景差异较大，复现前建议先明确自己的目标。

- **快速熟悉 LeRobot 训练流程** → 选 **ACT**。训练流程最直接，适合理解数据加载、policy 初始化、loss 计算和 checkpoint 保存等基础环节。
- **复现经典模仿学习 baseline** → 选 **Diffusion Policy**。使用生成式方式预测动作序列，适合理解连续控制中的多模态动作建模。
- **进入 VLA / 多模态模型** → 选 **SmolVLA**。结合图像、状态和语言指令，适合理解从传统 policy 到 VLA 的过渡。
- **尝试前沿大模型** → 选 **X-VLA、π0 或 π0.5**。依赖更多、显存需求更高、数据格式要求更严，建议跑通 ACT 或 Diffusion Policy 后再尝试。

总结如下：

| 学习目标 | 推荐 policy | 说明 |
|---|---|---|
| 跑通 LeRobot 基础训练流程 | ACT | 最适合入门，便于理解整体 pipeline |
| 复现经典模仿学习方法 | Diffusion Policy | 适合和 ACT 对比，理解生成式动作预测 |
| 学习 VLA 模型训练 | SmolVLA | 适合从普通 policy 过渡到多模态 policy |
| 复现进阶 VLA 模型 | X-VLA、π0 / π0.5 | 依赖和训练成本更高，适合作为进阶内容 |

## 导航

- 返回父页：[LeRobot](../08-lerobot.md)
- 上一节：[LeRobot 整体介绍](01-overview.md)
- 下一节：[数据格式及转换](03-data-format.md)
