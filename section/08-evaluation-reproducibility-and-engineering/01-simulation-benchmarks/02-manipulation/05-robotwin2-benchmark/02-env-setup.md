# 9.1.5.2 环境配置

目标：按照官方项目入口完成 RoboTwin 2.0 的基础环境配置、依赖安装和 assets 下载，为后续数据采集与 policy 评测做准备。

## 环境准备

RoboTwin 2.0 使用 SAPIEN 和 GPU 渲染/仿真相关依赖，建议在 Linux + NVIDIA GPU 环境中安装。官方项目 README 指向安装文档，项目中提供了安装脚本：

```bash
conda create -n RoboTwin python=3.10 -y
conda activate RoboTwin

git clone https://github.com/RoboTwin-Platform/RoboTwin.git
cd RoboTwin

bash script/_install.sh
```


## cuRobo 下载失败处理

如果 `script/_install.sh` 中 cuRobo 下载或安装失败，可能是 cuRobo main 分支更新导致与当前 RoboTwin 环境不一致。本文采用固定版本分支的处理方式，因此与官方文档略有不同：

```bash
cd envs
git clone --branch v0.7.8 --depth 1 https://github.com/NVlabs/curobo.git
cd curobo
pip install -e . --no-build-isolation
```

执行完成后回到 RoboTwin 项目根目录，再继续下载 assets 或运行数据采集命令。

## 下载 assets

官方项目提供资产下载脚本：

```bash
bash script/_download_assets.sh
```

在国内网络环境中，如果需要使用 Hugging Face 镜像，可以在运行下载脚本前设置：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

assets 会影响任务能否启动，也会影响物体模型、碰撞模型、功能点和随机干扰物等内容。安装完成后，至少应确认下面这些目录存在：

```text
assets/objects/
assets/embodiments/
```

## 常见问题

| 问题 | 排查方式 |
|---|---|
| assets 缺失 | 重新执行 `bash script/_download_assets.sh` |
| 渲染失败 | 确认 GPU、驱动、SAPIEN 和 headless 渲染环境 |
| cuRobo 安装失败 | 使用上面的固定 `v0.7.8` 分支重新安装 |
