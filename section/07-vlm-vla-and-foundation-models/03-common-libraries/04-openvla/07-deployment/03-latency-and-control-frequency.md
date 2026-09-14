# 延迟与控制频率

目标：理解怎样记录 OpenVLA REST server 的单步请求延迟，以及这些指标怎样影响控制频率判断。

REST 部署会把一次本地函数调用拆成客户端编码、HTTP 请求、server 推理、HTTP 返回和客户端解码。即使模型不变，这些额外步骤也会进入控制周期。

## 怎么测

可以用固定图像和固定指令做顺序请求 benchmark。第一步先 warmup，一次性初始化开销不计入统计；随后连续发 `N=100` 次请求，记录每次请求耗时。

```python
import statistics
import time

lat = []

_ = requests.post(URL, json=payload).json()

for _ in range(100):
    t0 = time.perf_counter()
    result = requests.post(URL, json=payload).json()
    lat.append((time.perf_counter() - t0) * 1000)

lat.sort()
print("mean", statistics.mean(lat))
print("median", statistics.median(lat))
print("p95", lat[min(len(lat) - 1, int(len(lat) * 0.95))])
print("min/max", lat[0], lat[-1])
```

这类脚本测的是顺序请求延迟，适合估算单客户端单步控制时的吞吐。它不等价于并发压测，也不等价于真实机器人控制频率。

## 指标怎么看

| 指标 | 作用 |
| --- | --- |
| warmup action shape | 先确认 server 返回的是 action，不是 `"error"`。 |
| mean / median | 估算常规单步请求耗时。 |
| p95 | 观察偶发慢请求对控制周期的影响。 |
| min / max | 看最短路径和异常抖动。 |
| sequential throughput | 顺序请求下每秒能完成多少次 `/act`。 |

如果单次请求稳定在 250 ms 左右，顺序闭环的上限大约是 4 Hz。真实机器人还会叠加相机取图、控制命令下发、环境响应和安全检查，这些时间也要计入完整控制周期。

## 本地部署记录怎么看

一次本地部署记录中，server 启动后出现了下面几类信息：

```text
Uvicorn running on http://0.0.0.0:8123
AssertionError: The `unnorm_key` you chose is not in the set of available dataset statistics
POST /act HTTP/1.1" 200 OK
Shutting down
```

这些日志能说明四件事：

| 日志现象 | 判断 |
| --- | --- |
| `Uvicorn running` | server 已经监听端口。 |
| `AssertionError` | 请求进了模型侧，但 `unnorm_key` 没有命中统计量 key。 |
| 多条 `POST /act` | 客户端持续发起请求，server 有响应。 |
| `Shutting down` | server 正常退出。 |

这份日志可以支撑 server 启动、错误请求和后续请求链路的判断。精确延迟、显存和吞吐需要保存 client benchmark stdout 或监控记录；没有原始输出时，不把旧表格数值写成复现结论。

## 和 rollout 的关系

延迟决定的是 policy server 每秒最多能产出多少条 action。rollout 成功率还取决于环境状态、图像质量、动作反归一化、控制器和任务本身。部署页记录延迟，是为了知道这条服务链路是否适合某个控制周期；评测页记录成功率，是为了判断策略在任务环境里能完成多少次。

## 本页小结

- REST benchmark 应先 warmup，再记录多次顺序请求的 mean、median、p95、min/max 和吞吐。
- 只有 server 日志时，可以判断请求链路和错误类型；精确延迟需要 client 侧原始输出。
- 控制频率由模型推理、HTTP 往返、图像获取和动作执行共同决定。

## 导航

- 上一节：[请求与 Action 格式](02-request-and-action-format.md)
- 返回上级：[部署](../07-deployment.md)
- 下一节：[扩展方向](../08-extension.md)
