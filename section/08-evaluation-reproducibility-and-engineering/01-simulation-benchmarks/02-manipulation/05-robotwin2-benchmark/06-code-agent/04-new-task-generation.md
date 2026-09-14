# 9.1.5.6.4 生成自己的任务

要让 code agent 为新任务生成专家代码，需要准备三部分：

```text
1. 基础任务环境：envs/<task_name>.py
2. 任务描述：code_gen/task_info.py
3. 任务配置：task_config/<task_name>.yml
```

其中，`setup_demo()`、`load_actors()` 和 `check_success()` 需要人工实现；`play_once()` 是 code agent 要生成的部分。

## 第一步：写基础任务环境

新增文件：

```text
envs/<task_name>.py
```

例如：

```text
envs/my_task.py
```

基础结构示例：

```python
from ._base_task import Base_Task
from .utils import *
import sapien

class my_task(Base_Task):

    def setup_demo(self, **kwags):
        super()._init_task_env_(**kwags)

    def load_actors(self):
        # 在这里加载任务需要的物体
        pass

    def play_once(self):
        # 这里由 code agent 生成
        pass

    def check_success(self):
        # 在这里判断任务是否成功
        pass
```

注意：类名必须和文件名一致。例如文件是 `my_task.py`，类名就应为 `my_task`。

`load_actors()` 通常负责：

```text
1. 加载物体模型。
2. 设置物体初始位姿。
3. 设置目标位姿或中间位姿。
4. 记录禁止放置区域或碰撞区域。
```

`check_success()` 负责判断任务是否完成。

## 第二步：添加任务描述

修改文件：

```text
code_gen/task_info.py
```

在文件中新增一个大写变量。假设任务名是 `my_task`，则变量名应为：

```python
MY_TASK = {...}
```

模板如下：

```python
MY_TASK = {
    "task_name": "my_task",
    "task_description": "Describe what the robot should do.",
    "current_code": """
class gpt_my_task(my_task):
    def play_once(self):
        pass
""",
    "actor_list": {
        "self.object": {
            "name": "object",
            "description": "The object to manipulate.",
            "modelname": "001_bottle"
        }
    }
}
```

字段含义：

| 字段 | 含义 |
|---|---|
| `task_name` | 任务文件名和类名 |
| `task_description` | 用自然语言描述机器人要完成什么 |
| `current_code` | 提供给 LLM 的代码模板 |
| `actor_list` | 任务中涉及的物体、目标 pose 或中间 pose |
| `modelname` | 对应 `assets/objects/<modelname>/` 下的物体资源 |

如果 actor 有 `points_info.json`，`code_gen/test_gen_code.py` 会自动把 functional points 和 contact points 补充进 prompt，帮助 LLM 选择抓取点和功能点。

## 第三步：准备任务配置

可直接复制一份 clean/randomized 配置，再在上面进行修改：

```bash
cp task_config/demo_clean.yml task_config/my_task.yml
```

然后在`task_config/my_task.yml`文件开头添加task_name：

```text
task_name: my_task
```

## 第四步：运行 code agent

先运行单次生成：

```bash
python code_gen/task_generation_simple.py my_task
```

单独测试：

```bash
python code_gen/run_code.py my_task
```

如果成功率不够，再运行：

```bash
python code_gen/task_generation.py my_task
```

如果需要视觉观察反馈，再运行：

```bash
python code_gen/task_generation_mm.py my_task
```

完成以上步骤后，就可以把 code agent 从 `beat_block_hammer` 迁移到自己构建的任务中。
