# REST Server

目标：读懂 `vla-scripts/deploy.py` 怎样加载 OpenVLA，并把 `predict_action` 暴露成 `/act` 接口。

OpenVLA 的 REST 部署脚本只实现 server 端。server 启动后常驻一个模型实例，客户端每次把图像和语言指令发到 `/act`，server 调用 `predict_action()` 后返回一条 action。

## 启动命令

最小启动命令如下：

```bash
python vla-scripts/deploy.py \
  --openvla_path openvla/openvla-7b \
  --port 8000
```

`openvla_path` 可以是 Hugging Face model id，也可以是本地 fine-tuned checkpoint 目录。使用本地 checkpoint 时，目录中应包含 `dataset_statistics.json`，这样 server 才能在反归一化时找到对应的动作统计量。

常见参数只有两个：

| 参数 | 作用 |
| --- | --- |
| `--openvla_path` | HF model id 或本地 checkpoint 目录。 |
| `--port` | FastAPI server 监听端口，默认 `8000`。 |

## Server 加载了什么

`OpenVLAServer` 初始化时会先创建 processor 和模型：

```python
self.processor = AutoProcessor.from_pretrained(self.openvla_path, trust_remote_code=True)
self.vla = AutoModelForVision2Seq.from_pretrained(
    self.openvla_path,
    attn_implementation=attn_implementation,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
).to(self.device)
```

这段代码说明 REST server 走的是 Hugging Face AutoClass 路径，和前面最小 `predict_action` 页面中的加载方式一致。区别在于模型加载一次后常驻进程，后续请求复用同一个 `self.vla`。

本地 checkpoint 还会额外读取统计量：

```python
if os.path.isdir(self.openvla_path):
    with open(Path(self.openvla_path) / "dataset_statistics.json", "r") as f:
        self.vla.norm_stats = json.load(f)
```

这里对应前面数据章节讲过的 `dataset_statistics.json`。如果 checkpoint 目录缺少这个文件，或者请求里的 `unnorm_key` 对不上统计量 key，server 可以启动，但 `/act` 请求会在动作反归一化阶段失败。

## `/act` 做了什么

server 的核心接口是 `predict_action()`：

```python
image, instruction = payload["image"], payload["instruction"]
unnorm_key = payload.get("unnorm_key", None)

prompt = get_openvla_prompt(instruction, self.openvla_path)
inputs = self.processor(prompt, Image.fromarray(image).convert("RGB")).to(
    self.device, dtype=torch.bfloat16
)
action = self.vla.predict_action(**inputs, unnorm_key=unnorm_key, do_sample=False)
```

这段代码把 REST payload 转回 OpenVLA 熟悉的输入：图像、指令、prompt、processor inputs 和 `unnorm_key`。因此 server 返回 action 并不代表机器人已经完成任务；它只说明一次单步模型调用完成了。

最后，`run()` 把这个函数挂到 FastAPI：

```python
self.app = FastAPI()
self.app.post("/act")(self.predict_action)
uvicorn.run(self.app, host=host, port=port)
```

启动日志中看到 `Uvicorn running on http://0.0.0.0:8000` 这类信息时，说明 HTTP 服务已经监听端口。下一步还要从客户端发送真实 payload，检查 action 返回和 server 日志。

## 本页小结

- `deploy.py` 的 server 端使用 `AutoProcessor` 和 `AutoModelForVision2Seq` 加载 OpenVLA。
- 本地 checkpoint 目录需要能读到 `dataset_statistics.json`，否则部署阶段无法正确使用本地数据统计量。
- `/act` 的核心仍然是 `predict_action()`；server 连通属于单步接口检查。

## 导航

- 上一节：[部署](../07-deployment.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[请求与 Action 格式](02-request-and-action-format.md)
