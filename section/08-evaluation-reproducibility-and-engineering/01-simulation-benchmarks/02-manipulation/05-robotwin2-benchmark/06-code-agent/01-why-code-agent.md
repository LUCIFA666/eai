# 9.1.5.6.1 为什么需要 Code Agent

RoboTwin 的任务数据采集依赖专家脚本。每个任务通常都需要在 `envs/<task_name>.py` 中实现 `play_once()`，用来描述机器人如何完成任务，例如抓取、移动、放置、按压、开关、双臂协作或工具使用。

手写 `play_once()` 的难点在于：

```text
1. 需要理解 RoboTwin 的机械臂控制 API。
2. 需要知道每个物体有哪些 contact point、functional point 和 target pose。
3. 需要处理左右臂选择、避障、预抓取距离、放置姿态等细节。
4. 新增任务时，专家代码调试成本较高。
```

Code Agent 的作用是把这部分专家控制逻辑交给 LLM 生成。它不是训练 policy，也不是直接生成底层关节轨迹，而是生成一段调用 RoboTwin 高层控制 API 的 Python 代码。

## 整体流程

Code Agent 的输入主要有三类：

```text
1. 任务描述：机器人需要完成什么任务。
2. Actor 信息：任务中有哪些物体、目标位置或中间位姿。
3. 控制 API：LLM 可以调用哪些 RoboTwin 高层函数。
```

输出是一个新的任务类：

```text
envs_gen/gpt_<task_name>.py
```



## 本章对应项目文件

| 内容 | 文件 |
|---|---|
| LLM API 配置 | `code_gen/gpt_agent.py` |
| Prompt 与机械臂控制 API | `code_gen/prompt.py` |
| 任务描述与 actor 信息 | `code_gen/task_info.py` |
| 单次代码生成入口 | `code_gen/task_generation_simple.py` |
| 带错误反馈的迭代生成入口 | `code_gen/task_generation.py` |
| 多模态观察反馈生成入口 | `code_gen/task_generation_mm.py` |
| 生成代码测试入口 | `code_gen/run_code.py` |
| 测试工具函数 | `code_gen/test_gen_code.py` |
| 手写基础任务环境 | `envs/<task_name>.py` |
| LLM 生成任务代码 | `envs_gen/gpt_<task_name>.py` |
| 多模态观察图片 | `camera_images/` |

其中，最重要的是三类文件：

```text
code_gen/task_info.py
    告诉 LLM 当前任务要做什么、有哪些物体、代码模板是什么。

code_gen/prompt.py
    告诉 LLM 可以使用哪些机械臂 API，例如 grasp_actor、place_actor、move。

code_gen/gpt_agent.py
    配置 DeepSeek 或其他 OpenAI-compatible LLM API。
```
