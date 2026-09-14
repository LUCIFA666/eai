# 下载任务、资产与演示数据

目标：掌握 ManiSkill3 中 assets 和 demonstration 的通用下载方法，并以 `PickCube-v1` 为例完成一次演示数据下载。

ManiSkill3 里有两类常见外部数据：

| 类型 | 用途 | 下载工具 |
|---|---|---|
| assets | 机器人、物体、场景等资源 | `download_asset` |
| demonstrations | 专家轨迹、视频、metadata、checkpoint | `download_demo` |



## 准备

先进入 ManiSkill 项目，并设置数据目录：

```bash
source /path/to/env/maniskill3/bin/activate
export MS_ASSET_DIR=/path/to/env/maniskill_data
cd /path/to/ManiSkill
```


后续下载的数据会放在这个目录下。

如果服务器不能直连外网，需要先设置代理。


## 通用下载方法

查看可用资产下载命令：

```bash
python -m mani_skill.utils.download_asset --help
```

列出可下载资产：

```bash
python -m mani_skill.utils.download_asset --list robot
python -m mani_skill.utils.download_asset --list task_assets
python -m mani_skill.utils.download_asset --list objects
python -m mani_skill.utils.download_asset --list scene
```

下载某个资产：

```bash
python -m mani_skill.utils.download_asset <asset_uid> -y
```

查看 demonstration 下载命令：

```bash
python -m mani_skill.utils.download_demo --help
```

下载某个任务的 demonstration：

```bash
python -m mani_skill.utils.download_demo <env_id>
```

例如：

```bash
python -m mani_skill.utils.download_demo PickCube-v1
```


## 示例：下载 PickCube-v1 demonstration

本节以 `PickCube-v1` 为例：

```bash
python -m mani_skill.utils.download_demo PickCube-v1
```

本次下载成功后，数据位于：

```text
/path/to/env/maniskill_data/demos/PickCube-v1
```

## 文件怎么看

常见文件含义：

| 文件 | 含义 |
|---|---|
| `.h5` | 轨迹数据，例如状态、动作、episode 信息 |
| `.json` | metadata，例如任务、控制模式、数据来源 |
| `.mp4` | 示例视频 |
| `.pt` | checkpoint，例如 PPO 模型 |



## 导航

- 上一节：[随机动作 demo](05-random-action-demo.md)
- 返回上级：[ManiSkill3](../08-maniskill3-benchmark.md)
- 下一节：[Replay 与 Convert Trajectory](07-replay-and-convert-trajectory.md)
