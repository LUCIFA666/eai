# 9.1.5.6 Code Agent：自动生成专家任务代码

目标：复现 RoboTwin 2.0 的 code agent 流程，理解如何从自然语言任务描述生成专家 `play_once()`，并在仿真中测试生成代码的成功率。本章以 `beat_block_hammer` 为最小复现示例。

Code Agent 的作用是把专家任务代码的编写过程自动化。它读取任务描述、物体信息和 RoboTwin 高层机械臂控制 API，然后调用 LLM 生成 `play_once()`，最后把生成代码放到 `envs_gen/gpt_<task_name>.py` 并进行仿真测试。

整体流程如下：

```text
任务描述 + 物体信息 + 控制 API
        ↓
LLM 生成 play_once()
        ↓
保存到 envs_gen/gpt_<task_name>.py
        ↓
在 SAPIEN 仿真中测试 success rate
        ↓
失败时可继续调试修正
```

本章分为四个小节：

| 小节 | 内容 |
|---|---|
| [为什么需要 Code Agent](06-code-agent/01-why-code-agent.md) | 说明 code agent 要解决的问题，以及对应的项目文件 |
| [配置 DeepSeek 与最小复现](06-code-agent/02-deepseek-and-minimal-repro.md) | 配置 DeepSeek API，并跑通 `beat_block_hammer` |
| [调试方法](06-code-agent/03-debugging.md) | 处理 API、配置、生成代码和仿真失败等常见问题 |
| [生成自己的任务](06-code-agent/04-new-task-generation.md) | 新增任务环境、任务描述，并让 code agent 生成专家代码 |


