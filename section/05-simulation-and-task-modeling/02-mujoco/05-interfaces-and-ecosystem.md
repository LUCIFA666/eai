# 接口与生态

到这里，我们已经能自己读 MJCF、控制机器人、取观测和渲染了。但在实际训练代码里，常会看到这样一行：`env = gym.make("Humanoid-v5")`。这台机器人是谁写的？reward 又是谁定义的？这一章就拆开“从 MJCF 到 RL env”中间那几层接口，看清每一层谁负责什么。

## 前置概念

读这一节前，建议先理解：

- **MJCF / mjModel / mjData**（详见 [建模](02-modeling.md)）：这一节讨论的接口都是这三个对象的不同包装。
- **step 循环**（详见 [MuJoCo 程序怎么运转](01-overview/02-mental-model.md)）：所有上层接口都把 step 这一步重新包了一遍。

## 环境从哪里来：一条拼装链

`gym.make("Humanoid-v5")` 这一行背后，是这样一条链：

<figure class="doc-figure figure-pipeline" aria-label="从 MJCF 到 RL 的拼装链">
  <p class="doc-figure-title">环境拼装链：MJCF → Task → Env → RL</p>
  <div class="figure-pipeline">
    <div class="figure-node tone-green">
      <strong>MJCF</strong>
      <span>某人写的 XML：humanoid.xml + scene.xml。<br/>MuJoCo 编译 → mjModel + mjData。</span>
    </div>
    <div class="figure-node tone-blue">
      <strong>Task</strong>
      <span>某人写的 Task 类，定义 reward / reset / observation。</span>
    </div>
    <div class="figure-node tone-gold">
      <strong>Env</strong>
      <span>dm_control.Environment 或 gymnasium.Env，<br/>注册到 registry。</span>
    </div>
    <div class="figure-node tone-rose">
      <strong>RL</strong>
      <span>训练框架调 env.step → policy 学习。</span>
    </div>
  </div>
  <div class="figure-note">每一层一般都可以替换，下面逐层讲清"谁负责什么、能不能自己写、什么时候值得自己写"。</div>
</figure>

## 学习路径

| 小节 | 读完能回答 | 重点 |
|---|---|---|
| [Python API 巡览](05-interfaces-and-ecosystem/01-python-api-tour.md) | mujoco 模块都有什么？MjSpec 是什么？ | 包结构、MjSpec、rollout |
| [mujoco_menagerie](05-interfaces-and-ecosystem/02-menagerie.md) | 上哪找现成校准好的模型？ | 模型库巡览、加载对比 |
| [dm_control suite](05-interfaces-and-ecosystem/03-dm-control-suite.md) | cartpole、humanoid 这些经典任务怎么用？ | suite 接口、env.step / env.reset |
| [dm_control composer](05-interfaces-and-ecosystem/04-dm-control-composer.md) | 怎么自己写一个任务？ | Entity / Arena / Task |
| [Gymnasium 风格包装](05-interfaces-and-ecosystem/05-gymnasium-wrappers.md) | 把 MuJoCo 包装成标准 gym env | gymnasium-robotics、自定义 gym.Env |
| [接口选择](05-interfaces-and-ecosystem/06-when-to-use-what.md) | 四种接口怎么选？ | 选型矩阵、三个典型决策场景 |

## 导航

- 上一节：[观测与渲染](04-observation-and-rendering.md)
- 返回上级：[MuJoCo](../02-mujoco.md)
- 下一节：[抓取实战](06-grasping-walkthrough.md)
