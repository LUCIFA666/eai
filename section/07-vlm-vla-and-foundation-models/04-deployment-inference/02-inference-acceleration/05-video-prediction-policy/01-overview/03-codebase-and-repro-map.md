# 代码与复现地图

目标：把仓库主干脚本、配置文件和推荐复现顺序对应起来，知道“下一步该打开哪个文件、该跑哪个命令”。

## 先从哪些文件读起

第一次读这个仓库，建议按下面顺序打开：

1. `README.md`
2. `make_prediction.py`
3. `step1_train_svd.py`
4. `policy_models/module/diffusion_extract.py`
5. `policy_models/VPP_policy.py`
6. `policy_evaluation/calvin_evaluate.py`
7. `step2_train_action_calvin.py`
8. `step2_train_action_xbot.py`

这个顺序的好处是：

- 先看能跑起来的推理入口
- 再看第一阶段训练
- 再看第二阶段如何消费视频特征
- 最后才进入多分支训练脚本

## 仓库的主干脚本

| 脚本 | 作用 | 什么时候看 |
|---|---|---|
| `make_prediction.py` | 第一阶段视频推理与可视化 | 第一次复现的入口 |
| `step1_prepare_latent.py` | 原始数据转视频、latent 和 annotation | 做自定义数据前必须看 |
| `step1_train_svd.py` | 第一阶段视频模型训练 | 确认视频训练细节时看 |
| `step2_prepare_json.py` | 为第二阶段生成样本索引和归一化统计 | 做真实机器人数据时看 |
| `step2_train_action_calvin.py` | CALVIN 动作训练 | 想复现 benchmark 训练时看 |
| `step2_train_action_xbot.py` | xbot / xhand 动作训练 | 做真实机器人分支时看 |
| `policy_evaluation/calvin_evaluate.py` | CALVIN 闭环评测 | 第二阶段最小复现入口 |
| `step3_deploy_real_xbot.py` | 真实机器人推理模板 | 想接真机时看 |

## 关键配置文件

| 配置 | 作用 |
|---|---|
| `video_conf/val_svd.yaml` | 第一阶段推理配置 |
| `video_conf/train_calvin_svd.yaml` | 第一阶段 CALVIN 视频训练配置 |
| `policy_conf/VPP_Calvinabc_train.yaml` | 第二阶段 CALVIN 动作训练配置 |
| `policy_conf/calvin_evaluate_all.yaml` | CALVIN 评测配置 |
| `policy_conf/VPP_xbot_train.yaml` | xbot / xhand 动作训练配置 |

## 最推荐的新手复现顺序

### 第一步：只跑第一阶段推理

命令入口：

```bash
python make_prediction.py \
  --config video_conf/val_svd.yaml \
  --video_model_path /path/to/svd-robot \
  --clip_model_path /path/to/clip-vit-base-patch32 \
  --val_dataset_dir video_dataset_instance/xhand \
  --val_idx 0+50+100+150
```

目的：

- 验证模型和依赖是否能加载
- 理解输出视频的含义
- 把第一阶段输入输出吃透

### 第二步：只跑第二阶段评测

命令入口：

```bash
python policy_evaluation/calvin_evaluate.py \
  --video_model_path /path/to/svd-robot-calvin \
  --action_model_folder /path/to/dp-calvin \
  --clip_model_path /path/to/clip-vit-base-patch32 \
  --calvin_abc_dir /path/to/calvin_debug_dataset
```

目的：

- 验证第二阶段动作策略、环境和模型联通
- 看清楚评测输出到底是什么意思

### 第三步：再回去碰训练和自定义数据

只有在前两步都通了之后，才值得继续看：

- `step1_prepare_latent.py`
- `step2_prepare_json.py`
- `step1_train_svd.py`
- `step2_train_action_*`

否则你很容易在一堆数据和配置错误里迷路。

## 读这份代码时必须先知道的现实

这是研究代码，不是打磨好的产品库。实际复现时要预期这些问题：

1. README、脚本名和真实文件名并不总一致。
2. 有些配置默认写死了作者机器路径。
3. CALVIN 路线和 xbot 路线是两套分支，不是完全统一的配置系统。
4. 原始评测脚本更偏“跑完整 benchmark”，不够适合最小复现。

## 论文和代码的对应关系

如果你是先读论文再读代码，推荐这样建立映射：

| 论文概念 | 代码位置 |
|---|---|
| 视频预测模型 | `step1_train_svd.py`、`video_models/` |
| predictive representation | `policy_models/module/diffusion_extract.py` |
| Video Former | `policy_models/module/Video_Former.py` |
| 动作扩散策略 | `policy_models/VPP_policy.py` |
| CALVIN 评测 | `policy_evaluation/calvin_evaluate.py` |

## 小结

- 新手最应该先读 `make_prediction.py` 和 `calvin_evaluate.py`。
- 真正稳定的复现顺序是：视频推理 → 闭环评测 → 数据与训练。
- 论文里的“预测式表征”在代码里最核心的落点是 `diffusion_extract.py`。

## 导航

- 上一节：[两阶段心智模型](02-two-stage-mental-model.md)
- 返回上级：[项目总览](../01-overview.md)
- 下一节：[环境准备与第一次视频预测](../02-setup-and-first-prediction.md)
