# server 启动流程

目标：从 `python deployment/model_server/server_policy.py --ckpt_path ...` 开始，理解服务端如何加载模型、构造 metadata 并监听 websocket。

启动命令。前置条件是 `<RUN_DIR>/<run_id>` 中保留了 `config.yaml`、`dataset_statistics.json` 和 `checkpoints/`：

```bash
cd <STARVLA_ROOT>

python deployment/model_server/server_policy.py \
  --ckpt_path <RUN_DIR>/<run_id>/checkpoints/steps_30000_pytorch_model.pt \
  --port 10093 \
  --use_bf16
```

## server_policy.py

入口为：

```python
wrapper = PolicyServerWrapper(
    ckpt_path=args.ckpt_path,
    device="cuda",
    use_bf16=args.use_bf16,
)

server = WebsocketPolicyServer(
    policy=wrapper,
    host="0.0.0.0",
    port=args.port,
    idle_timeout=args.idle_timeout,
    metadata=wrapper.metadata,
)
server.serve_forever()
```

它只负责三件事：

1. 用 checkpoint 创建 `PolicyServerWrapper`。
2. 把 wrapper 交给 `WebsocketPolicyServer`。
3. 在指定端口监听请求。

真正的模型加载和动作反归一化在 wrapper 里。

## PolicyServerWrapper 初始化

核心代码：

```python
framework = baseframework.from_pretrained(self._ckpt_path)
if use_bf16:
    framework = framework.to(torch.bfloat16)
framework = framework.to(device).eval()
self._framework = framework
```

然后读取配置：

```python
model_cfg, _ = read_mode_config(self._ckpt_path)
action_model_cfg = model_cfg["framework"]["action_model"]
```

确定 action chunk 长度：

```python
if "action_horizon" in action_model_cfg:
    self._action_chunk_size = int(action_model_cfg["action_horizon"])
elif "future_action_window_size" in action_model_cfg:
    self._action_chunk_size = int(action_model_cfg["future_action_window_size"]) + 1
```

这保证旧配置和新配置都能得到统一的 `action_chunk_size`。

## metadata

server 启动后会把 metadata 发给 client：

```python
{
    "env": "starvla_policy_server",
    "ckpt_path": self._ckpt_path,
    "action_chunk_size": self._action_chunk_size,
    "available_unnorm_keys": self._available_unnorm_keys,
    "default_unnorm_key": self._default_unnorm_key,
}
```

client 会用 `action_chunk_size` 决定多久请求一次新动作 chunk。

如果有默认反归一化 key，还会加上：

```python
"action_keys": proc.action_keys
"state_keys": proc.state_keys
```

这对调试动作维度很有用。

## 端口和地址

server 监听：

```python
host="0.0.0.0"
port=args.port
```

`0.0.0.0` 表示监听所有网卡，只表示服务监听所有网卡，client 连接时要使用实际地址。client 本机连接时应使用：

```text
127.0.0.1
```

跨机器连接时使用 server 机器的实际 IP。

## 常见启动错误

| 错误 | 原因 | 处理 |
|---|---|---|
| checkpoint 不存在 | `--ckpt_path` 路径错 | 用 `ls` 确认文件 |
| 缺少 `config.yaml` | 只拷贝了权重文件 | 保留 run 目录结构 |
| 缺少 `dataset_statistics.json` | dataloader 未保存或文件丢失 | 重新训练/复制 statistics |
| state dict key mismatch | framework 配置和权重不匹配 | 检查 `framework.name` 和模型版本 |
| CUDA OOM | 模型过大或 bf16 未启用 | 加 `--use_bf16`、换小模型、指定 GPU |
| 端口占用 | port 已被其他进程使用 | 换端口或结束旧进程 |

## 小结

- `server_policy.py` 只是启动器，模型逻辑在 `PolicyServerWrapper`。
- wrapper 用 `baseframework.from_pretrained()` 从 checkpoint 重建模型。
- server metadata 会告诉 client action chunk 长度和反归一化 key。
- `0.0.0.0` 是监听地址，client 不应把它当远程连接地址。

## 动手练习

1. 运行 `rg -n "parser.add_argument|idle_timeout|metadata" deployment/model_server/server_policy.py`，确认 server 入口支持 `--ckpt_path`、`--port`、`--use_bf16` 和 `--idle_timeout`。
2. 用一个完整 run 目录里的 checkpoint 启动 server。成功日志应包含 `server running ... metadata=`，metadata 中应能看到 `action_chunk_size`。
3. 故意传一个不存在的 checkpoint，观察错误发生在模型加载阶段。这个练习不要求 server 启动成功，目标是确认路径错误能被快速暴露。

## 导航

- 上一节：[部署与推理服务](../06-deployment.md)
- 返回上级：[部署与推理服务](../06-deployment.md)
- 下一节：[02 websocket 协议](02-websocket-protocol.md)
