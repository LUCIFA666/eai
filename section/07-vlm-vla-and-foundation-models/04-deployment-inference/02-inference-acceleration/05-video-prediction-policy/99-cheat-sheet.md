# 速查表

目标：给出 VPP 最常用命令、最小复现顺序和最常见故障的一页速查。

## 最小复现顺序

1. `make_prediction.py`
2. `calvin_evaluate.py`
3. 再根据需要调整评测规模或修改配置
4. 再考虑训练或自定义数据

## 最常用命令

### 第一次视频预测

```bash
python make_prediction.py \
  --config video_conf/val_svd.yaml \
  --video_model_path /path/to/models/vpp/svd-robot \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --val_dataset_dir video_dataset_instance/xhand \
  --val_idx 0+50+100+150
```

### 第二阶段最小评测

```bash
python policy_evaluation/calvin_evaluate.py \
  --video_model_path /path/to/models/vpp/svd-robot-calvin \
  --action_model_folder /path/to/models/vpp/dp-calvin \
  --clip_model_path /path/to/models/vpp/clip-vit-base-patch32 \
  --calvin_abc_dir /path/to/calvin_debug_dataset
```

### 一个 50 条 debug 序列的示例评测结果

```text
Average successful sequence length: 4.4
1/5: 96.0%
2/5: 94.0%
3/5: 92.0%
4/5: 80.0%
5/5: 78.0%
```

对应结果文件：

```text
/path/to/models/vpp/dp-calvin/logs/<timestamp>/results.json
```

### 接口说明

原仓库默认命令行参数较少。如果需要缩小评测规模或显式控制日志行为，通常需要自行修改配置文件或脚本，而不是依赖现成的命令行开关。

## 最常见故障

| 现象 | 常见原因 | 处理方向 |
|---|---|---|
| `RuntimeError: Numpy is not available` | `numpy 2.x` 和 `torchvision` ABI 不兼容 | `numpy<2` |
| `pkg_resources` 缺失 | `setuptools` 太新 | 降级 `setuptools` |
| `pyhash` 缺失 | 原包太老 | 用兼容实现 |
| `last.pt` 结果保存崩掉 | 脚本默认 checkpoint 名带 `=` | 兼容 `last.pt` 命名 |
| `wandb.log()` 报错 | 没 `wandb.init()` | 显式初始化或关闭 wandb |
| debug 数据解压失败 | 旧下载 URL 失效 | 改用官方 zip |

## 关键结论

- 第一阶段看视频是否合理，第二阶段看任务是否成功。
- `make_prediction.py` 里的预测视频不是 executed rollout。
- VPP 的加速点在于：用视频模型中间表征代替完整未来视频生成。
- `50` 条 debug 序列的示例结果达到 `avg_seq_len = 4.4`，说明最小复现不仅能够启动，而且可以得到稳定的闭环评测结果。

## 导航

- 返回上级：[Video Prediction Policy](../05-video-prediction-policy.md)
