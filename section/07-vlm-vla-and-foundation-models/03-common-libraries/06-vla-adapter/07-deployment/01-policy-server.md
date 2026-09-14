# Policy Server

目标：理解 VLA-Adapter 如何把 checkpoint 加载成 FastAPI policy server，并区分 ALOHA 部署主线和通用 `vla-scripts/deploy.py` 入口。

VLA-Adapter 里有两个容易混淆的部署入口：

```text
experiments/robot/server_deploy/deploy.py
vla-scripts/deploy.py
```

本节主线使用 `experiments/robot/server_deploy/deploy.py`。ALOHA fake client 和真实 client 都通过 `MsgPackHttpClientPolicy` 请求这个 server，因此它和后续页面的 payload、返回值、action queue 是同一条链路。

`vla-scripts/deploy.py` 也会创建 `OpenVLAServer` 并暴露 `/act`，但它使用 JSON / `json_numpy` 风格的请求包装，更适合作为源码对照。做 ALOHA fake-client sanity check 时，优先使用 `experiments/robot/server_deploy/deploy.py`。

> `experiments/robot/server_deploy/deploy.py` 运行时，`sys.argv` 里既没有 `aloha` 也没有 `libero`，`prismatic/vla/constants.py` 的 `detect_robot_platform()` 因此回退到 LIBERO 常量：`ACTION_DIM=7`、`NUM_ACTIONS_CHUNK=8`、`ACTION_PROPRIO_NORMALIZATION_TYPE=BOUNDS_Q99`。ALOHA 需要的是 `ACTION_DIM=14`、`NUM_ACTIONS_CHUNK=25`、`BOUNDS`，而 `initialize_model()` 里 `proprio_dim` 又硬编码为 14。这是 VLA-Adapter 仓库自身的缺陷：action head 会按 7 维初始化，proprio 归一化也走错统计方式。两种绕过方式：改 `prismatic/vla/constants.py` 里的 `ROBOT_PLATFORM`，让它直接取 `ALOHA`；或让实际运行的 Python 文件路径包含 `aloha`（软链接或包装脚本），使 `detect_robot_platform()` 命中 ALOHA 分支。

## 启动链路

ALOHA 目录提供了一个 shell 包装：

```bash
PRETRAINED_CHECKPOINT=/path/to/checkpoint_dir \
PORT=8888 \
DEVICE=0 \
bash experiments/robot/aloha/eval_files/deploy_server.sh
```

这个脚本最终执行：

```bash
python experiments/robot/server_deploy/deploy.py \
  --pretrained_checkpoint /path/to/checkpoint_dir \
  --model_family openvla \
  --port 8888 \
  --device 0
```

`deploy.py` 的启动过程可以拆成四步：

1. `draccus` 解析命令行参数到 `DeployConfig`。
2. `initialize_model(cfg)` 加载 model、processor、action head、proprio projector。
3. `VLAServer` 创建 FastAPI app，并注册 POST `/act`。
4. `uvicorn.run()` 在指定 host 和 port 上监听请求。

核心结构是：

```python
server = VLAServer(cfg)
server.run()
```

`VLAServer.__init__()` 会先调用 `initialize_model(cfg)`：

```python
self.model, self.processor, self.action_head, self.proprio_projector = initialize_model(cfg)
self.app.post("/act", response_class=MsgPackResponse)(self.get_server_action)
```

组件加载逻辑在 `initialize_model()` 内部完成：

```python
model = get_model(cfg)
proprio_projector = get_proprio_projector(cfg, model.llm_dim, proprio_dim=14)
action_head = get_action_head(cfg, model.llm_dim)
processor = get_processor(cfg)
```

其中 `proprio_dim=14` 对应 ALOHA 双臂 joint state。使用 proprio 训练的 checkpoint，需要让 server 和 client 的 state 维度保持一致。

## DeployConfig 关键字段

| 字段 | 作用 |
| --- | --- |
| `host` / `port` | server 监听地址和端口。server 监听 `0.0.0.0` 时，client 本机连接仍应使用 `127.0.0.1`。 |
| `device` | 模型运行设备，例如 `0` 或 `cuda:0`，取决于脚本参数写法。 |
| `pretrained_checkpoint` | 要部署的 checkpoint 目录，应包含模型、processor、action head、proprio projector、statistics 等组件。 |
| `model_family` | 当前 ALOHA 脚本主线使用 `openvla`。 |
| `use_l1_regression` | 是否加载 continuous action head。ALOHA 部署通常需要打开。 |
| `use_minivlm` | 是否按 MiniVLM 版本加载模型组件，需和 checkpoint 训练配置一致。 |
| `use_proprio` | 是否加载 proprio projector，并要求 payload 提供 `state`。 |
| `num_images_in_input` | 模型预期图像数量，默认 3，对应 ALOHA fake/real client 提供的 front、left wrist、right wrist 三路图像。部署 2 路图像的 LIBERO checkpoint 时需改成 2；取图逻辑按 observation 里键名含 `wrist` 的字段收集，键名不含 `wrist` 会漏收图像。 |
| `center_crop` | 推理图像预处理是否使用 center crop，应与训练时图像增强约定一致。 |
| `num_open_loop_steps` | client 收到 action chunk 后最多执行多少步再重新请求。 |
| `unnorm_key` | action un-normalization 使用的 dataset statistics key。ALOHA client 会在 payload 中传入。 |
| `seed` | 推理侧随机种子，用于固定可复查行为。 |
| `use_pro_version` | 是否按 Pro 版本配置加载，需和训练/评测命令保持一致。 |

这些 flags 会共同决定模型组件和输入输出结构。部署时最重要的原则是让 server flags、checkpoint 训练配置、client observation 结构对齐；配置不一致时，可能直接加载失败，也可能返回动作但尺度或维度错误。

## `/act` 接口

`experiments/robot/server_deploy/deploy.py` 暴露的是 MsgPack HTTP 接口：

```text
POST http://<server-host>:<port>/act
Content-Type: application/msgpack
```

server 会把请求解包成 observation，取出 `instruction` 和 `unnorm_key`，然后调用 `get_action()` 返回动作序列。返回值也是 MessagePack，内容形如：

```python
{"actions": ...}
```

因此 ALOHA 部署排错时，应按 MsgPack HTTP response 读取返回值。当前主线没有 StarVLA 那种建连后第一条 metadata 消息，client 只在每次 `/act` 请求中拿动作。

## 常见启动错误

| 现象 | 优先检查 |
| --- | --- |
| checkpoint 路径不存在 | `PRETRAINED_CHECKPOINT` 是否指向完整目录；部署脚本需要读取多个模型组件，单个权重文件通常不够。 |
| 加载 action head 或 proprio projector 失败 | checkpoint 组件是否齐全，`use_l1_regression`、`use_proprio`、`use_pro_version` 是否与训练配置一致。 |
| `unnorm_key` 相关错误 | client 传入的 `UNNORM_KEY` 是否存在于训练保存的 dataset statistics 中。 |
| CUDA OOM | `DEVICE` 是否选错，模型是否过大，是否有旧 server 占用显存。 |
| 端口占用 | `PORT` 是否已被旧 uvicorn 进程使用。 |
| client 连不上 | server 是否仍在运行，client 是否使用 `127.0.0.1:8888` 或真实机器 IP 这类可访问地址；`0.0.0.0` 只适合 server 监听。 |

## 小结

- ALOHA 部署主线是 `experiments/robot/server_deploy/deploy.py`，协议是 MsgPack HTTP。
- server 启动后加载模型组件，并通过 FastAPI 暴露 `/act`。
- fake client 和 real client 都期待返回顶层 `actions`。
- 启动成功说明模型组件能加载；部署 sanity check 还需要下一步用 fake client 请求动作。

## 动手练习

1. 阅读 `experiments/robot/aloha/eval_files/deploy_server.sh`，写出它传给 `deploy.py` 的四个关键变量。
2. 在 `experiments/robot/server_deploy/deploy.py` 中找到 `MsgPackResponse`，说明这个接口与普通 JSON 的差异。
3. 故意使用一个被占用端口启动 server，观察错误发生在模型加载前还是监听阶段。

## 导航

- 上一节：[部署](../07-deployment.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[Server Request Payload](02-server-request-payload.md)
