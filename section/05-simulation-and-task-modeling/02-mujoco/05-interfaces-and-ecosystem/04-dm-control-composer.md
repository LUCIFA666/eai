# dm_control composer

suite 里的任务是“现成的”。可一旦想做个新任务，比如“让 Panda 把方块推到目标点”，就得自己定义。dm_control 的 `composer` 子模块正是为此设计的高层 API：把任务拆成 Entity / Arena / Task 三层，用写代码的方式拼出来。

## 本节目标

本节回答两个问题：

1. composer 把任务拆成哪几个抽象，各管什么？
2. 一个最小的 composer 任务大致长什么样，自定义的 reward / 观测 / 终止分别写在哪？

## composer 解决什么问题

用原生 MuJoCo 定义新任务时，需要同时处理几件事：写 MJCF 场景、写控制循环、定义奖励函数、管理 episode（一个回合，从重置到结束）的起止。这些代码往往容易混在一起，任务一复杂就更明显。

composer 的思路是把这些关注点拆成三类对象：

<figure class="doc-figure" aria-label="composer 的三类抽象">
  <p class="doc-figure-title">composer 的三类抽象</p>
  <table>
    <tr><th>抽象</th><th>职责</th><th>例子</th></tr>
    <tr><td><strong>Entity</strong></td><td>一个"东西"，机器人、物体、传感器等。自包含的 MJCF + 初始化逻辑</td><td>Panda 机器人、一个方块、一个目标区域</td></tr>
    <tr><td><strong>Arena</strong></td><td>场景的物理环境，地面、光照、物理参数</td><td>一张桌子、一块平整的地板</td></tr>
    <tr><td><strong>Task</strong></td><td>把 Entity 放进 Arena，定义奖励、观测、终止条件</td><td>"Panda 把方块推到目标点"</td></tr>
  </table>
</figure>

## 一个最小的 composer 任务骨架

下面用 composer 搭一个“让 Panda 把方块推到目标点”的任务。代码不长，却完整覆盖了 Entity / Arena / Task 三层。把 Panda 的 XML 指向 menagerie 里的 `panda.xml`，这段就能实际跑起来。观测的接法放在后面的“自定义 reward / observation / termination”一节讲。

```python
from dm_control import composer, mjcf
import numpy as np

# 1. Entity：每个“东西”是一个自带 MJCF 的实体，并通过 mjcf_model 暴露出来
class Panda(composer.Entity):
    def _build(self, xml_path):
        self._model = mjcf.from_path(xml_path)

    @property
    def mjcf_model(self):
        return self._model

class Block(composer.Entity):
    def _build(self):
        self._model = mjcf.RootElement()
        self._body = self._model.worldbody.add('body', name='block', pos=[0.4, 0, 0.05])
        self._body.add('geom', type='box', size=[0.03, 0.03, 0.03], rgba=[0.2, 0.6, 1, 1])

    @property
    def mjcf_model(self):
        return self._model

    @property
    def body(self):          # 记下方块的 body，reward 里要读它的位置
        return self._body

# 2. Task：把实体放进 Arena，定义 reward / 终止条件
class PushTask(composer.Task):
    def __init__(self, panda, block):
        self._arena = composer.Arena()            # Arena 默认是空的
        self._arena.mjcf_model.worldbody.add('geom', type='plane', size=[1, 1, 0.1])
        self._arena.attach(panda)                 # 机械臂焊在地面上
        self._arena.add_free_entity(block)        # 方块可自由移动
        self._panda, self._block = panda, block
        self._target_pos = np.array([0.5, 0.0, 0.05])

    @property
    def root_entity(self):                        # 根实体是 Arena，不是机器人
        return self._arena

    def get_reward(self, physics):
        # 注意 bind 的是具体的 mjcf 元素（body），不是 Block 这个 Entity 对象
        block_pos = physics.bind(self._block.body).xpos
        return -np.linalg.norm(block_pos - self._target_pos)  # 离目标越近 reward 越高

    def should_terminate_episode(self, physics):
        return physics.data.time > 10             # 10 秒后结束

# 3. 交给 composer.Environment，就得到和 suite 一样的 reset / step 接口
task = PushTask(Panda(xml_path='reference/mujoco_menagerie/franka_emika_panda/panda.xml'),
                Block())
env = composer.Environment(task)
time_step = env.reset()
```

这里在内存里构建 MJCF 用的是 dm_control 的 `mjcf` 模块（`mjcf.RootElement` 新建空模型、`mjcf.from_path` 从文件加载），各实体的 `mjcf_model` 会被框架拼成一棵树，最后由 `composer.Environment` 编译成一个完整的 `mjModel`。

## 自定义 reward / observation / termination

在 Task 类里重写这两个方法：

- `get_reward(physics)`：返回标量奖励。每次 `step` 后调用。
- `should_terminate_episode(physics)`：返回 `True` 时当前 episode 结束。

`physics` 参数包装了底层的 `mjModel` / `mjData`。要读某个实体的位姿或速度，用 `physics.bind(<mjcf 元素>)` 把元素映射到运行时数据再取值（就像上面 reward 里 `physics.bind(self._block.body).xpos` 那样）；传入的得是具体的 mjcf 元素，而不是 Entity 对象本身。

观测则**不是**重写一个 `get_observation`（Task 类并没有这个方法），而是走 composer 的 **observables 系统**：在 Entity / Task 上声明 `observables`，框架自动收集成观测字典。这也是 composer 和原生写法差异最大的一处。

## 何时用 composer，何时直接写 MJCF + Python

| 场景 | 推荐方式 |
|---|---|
| 修改已有任务、简单环境 | 直接写 MJCF + Python 循环 |
| 从零定义复杂任务、多个 Entity 组合 | 用 composer |
| 需要快速原型、迭代 reward 函数 | 用 composer |
| 想把任务分享给别人、标准化接口 | 用 composer |

composer 的上手成本比原生 API 高一些。不过对于复杂的多实体任务，它把结构理清楚的价值往往能盖过这点学习成本。

## 小结

- composer 把任务拆成 Arena（场地）、Entity（东西）、Task（规则）三层。
- 适合从零定义复杂、多实体的机器人任务。
- 通过在 Task 子类里重写 `get_reward`、`should_terminate_episode` 自定义奖励与终止；观测则走 observables 系统声明。
- 简单任务或改现有任务的场景，直接用 MJCF + Python 循环更轻量。

## 参考资料

- [dm_control Composer 教程（tutorial.ipynb，creature 示例）](https://github.com/google-deepmind/dm_control/blob/main/tutorial.ipynb)
- [dm_control manipulation 套件（Reach 等任务，本节骨架参照的写法）](https://github.com/google-deepmind/dm_control/tree/main/dm_control/manipulation)
- [dm_control（GitHub）](https://github.com/google-deepmind/dm_control)
- [Tassa et al., "dm_control: Software and Tasks for Continuous Control", 2020](https://arxiv.org/abs/2006.12983)

## 导航

- 上一节：[dm_control suite](03-dm-control-suite.md)
- 返回上级：[接口与生态](../05-interfaces-and-ecosystem.md)
- 下一节：[Gymnasium 风格包装](05-gymnasium-wrappers.md)
