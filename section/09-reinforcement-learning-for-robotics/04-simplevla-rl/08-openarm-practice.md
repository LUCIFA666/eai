# 10.4.7 实战：OpenArm 端到端适配

> 前面讲的都是 LIBERO、RoboTwin 这些现成 benchmark 上的用法。这一节来真的——怎么把 SimpleVLA-RL 适配到一个新的机器人上，以 OpenArm 为例。从动作空间适配，到仿真环境搭建，到数据收集，再到环境注册和训练分析，整个流程走一遍。

---

## 10.4.7.1 动作空间适配

### 问题：动作维度不一样

SimpleVLA-RL 默认支持的是 7-DoF 动作空间（6 维姿态 + 1 维夹爪），这是大部分桌面机械臂的标准配置。

但 OpenArm 不一样——它是 **8-DoF**：7 个关节 + 1 个夹爪。多出来的一个自由度（通常是腕关节的某个旋转轴）让动作空间从 7 维变成了 8 维。

这个差异说大不大，说小也不小——模型的动作头输出维度变了，动作 tokenizer 的配置也得跟着改。

### 方案 A：直接 8-DoF 映射（推荐）

最简单直接的方案：把动作维度从 7 改成 8，其他都不变。

具体要改的地方：

**1. 数据集配置里改 action_dim**

```python
# rob_dataset.py 的 DATASETS 字典里
"openarm_pickplace": {
    "env_name": "openarm",
    "task_name": "pick_place",
    "image_size": 224,
    "camera_names": ["front_camera"],
    "max_episode_length": 200,
    "action_dim": 8,  # 从 7 改成 8
    "num_demos": 50,
}
```

**2. 动作 tokenizer 配置里改维度数**

OpenVLA-OFT 的动作 tokenizer 配置里，每个维度有 256 个 bin。7 维的话，每个分块就是 7 个 token；8 维的话，就是 8 个 token。

配置文件里大概长这样：

```json
{
  "action_chunk_size": 8,
  "action_dim": 8,
  "bins_per_dim": 256,
  "action_min": [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
  "action_max": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
}
```

每个维度的归一化范围也要对应改——如果某个关节的活动范围跟其他不一样，min 和 max 就要单独设。

**3. 模型侧不用大改**

因为动作是 token 化的，模型根本不关心这 8 个 token 分别对应什么维度——它就是按顺序生成 token 而已。所以模型结构不用改，只要 tokenizer 配置对了就行。

这个方案的好处是简单，改的地方少，信息不丢失。推荐优先试这个。

### 方案 B：降维到 7-DoF

如果不想改动作维度，也可以把 8-DoF 降成 7-DoF，让它跟默认配置对齐。

常见的做法是**合并腕关节的两个旋转轴**：比如把腕关节的 roll 和 pitch 合并成一个，或者把某个不重要的自由度直接固定住。

```python
# 伪代码：8DoF → 7DoF 映射
def action_8dof_to_7dof(action_8d):
    # 前 6 维是位置和姿态的主要部分
    pos_euler = action_8d[:6]
    # 第 7、8 维是腕关节的两个旋转，合并成一个
    wrist_combined = (action_8d[6] + action_8d[7]) / 2  # 简单平均，实际可能更复杂
    # 夹爪
    gripper = action_8d[7] if len(action_8d) == 8 else action_8d[6]
    
    return np.concatenate([pos_euler[:5], [wrist_combined], [gripper]])
```

这个方案的好处是完全兼容默认配置，不用改 tokenizer。但缺点是**丢信息**——合并之后，某些精细的腕部动作就做不出来了。

一般来说，如果任务对腕部姿态要求不高（比如简单的抓取放置），降维方案也能用。但如果是精密操作任务，还是建议用方案 A。

### 动作归一化要注意

不管用哪个方案，动作归一化的范围都得仔细设。

每个维度的 min 和 max 应该对应该关节的实际活动范围，不能全都是 [-1, 1] 就完事了。比如夹爪的范围可能是 [0, 1]（0 张开，1 闭合），某个旋转关节可能是 [-π, π]。

归一化错了的话，模型输出的动作就会偏——要么动不起来，要么直接超范围。

---

## 10.4.7.2 仿真环境与数据收集

### Isaac Lab + OpenArm 环境搭建

OpenArm 的仿真环境一般用 Isaac Lab（也就是以前的 Isaac Gym 的继任者），物理仿真更真实，速度也快。

搭建步骤大概是：

**1. 装 Isaac Lab**

```bash
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
./isaaclab.sh --install
```

这一步可能比较折腾，Isaac Sim 的安装比较重。建议用官方推荐的 Docker 镜像，省得配环境。

**2. 装 OpenArm 模型和环境**

OpenArm 的 URDF 模型和 Isaac Lab 环境配置一般在 OpenArm 官方仓库里：

```bash
git clone https://github.com/OpenArm/OpenArm.git
cd OpenArm
pip install -e .
```

装完之后，先跑个简单的测试，确认环境能起来：

```bash
python scripts/test_env.py
```

能看到机械臂在仿真环境里动起来就说明环境没问题。

### RL 专家策略训练

有了仿真环境之后，需要收集演示数据。但手动遥操作收集数据太慢了——更高效的方式是**先用传统 RL 训一个专家策略，然后用这个专家策略来生成演示数据**。

常用的训练库：
- **rsl_rl**：ETH 做的，轻量，PPO 实现不错
- **rl_games**：功能更全，支持各种算法

以 rsl_rl 为例，训练命令大概长这样：

```bash
python scripts/train_rl.py --task OpenArmPickPlace --algo ppo --headless
```

训练过程可能需要几个小时到一天，取决于任务难度。训到成功率比较高（比如 80%+）的时候，就可以用来生成演示了。

为什么不直接用这个 RL 策略就好了？因为它是**任务特定**的——只能做 pick_place 这一个任务，换个任务就得重新训。而 VLA 模型是**通用**的——一个模型能做很多任务，靠语言指令来切换。

### 相机配置与图像采集

VLA 模型需要图像输入，所以得在仿真环境里配相机。

几个要点：

**相机位置**：一般放在机械臂的前上方或者手腕上（eye-in-hand）。桌面操作任务的话，前上方视角就够用了。

**图像分辨率**：默认 224×224，跟 OpenVLA-OFT 的输入尺寸对应。如果用更高清的，后面要 resize。

**渲染设置**：光线、纹理、阴影这些，尽量跟真实场景接近，不然 sim-to-real 会有 gap。

配置大概长这样：

```python
# Isaac Lab 相机配置
camera_cfg = {
    "position": [0.5, 0.0, 0.8],  # 相机位置
    "lookat": [0.0, 0.0, 0.2],    # 看向哪里
    "resolution": [224, 224],     # 图像尺寸
    "fov": 60,                    # 视场角
}
```

### 演示数据格式转换

用专家策略生成的轨迹数据一般是 npy 或者 pt 格式，得转换成 OpenVLA-OFT 要求的格式才能用。

转换的步骤：

**1. 生成轨迹**

```python
# 伪代码
for episode in range(num_episodes):
    obs = env.reset()
    done = False
    images = []
    actions = []
    success = False
    
    while not done:
        action = expert_policy(obs)
        obs, reward, done, info = env.step(action)
        images.append(obs["front_camera"])
        actions.append(action)
        if info.get("success"):
            success = True
    
    if success:  # 只存成功的轨迹
        save_episode(images, actions, task_name)
```

**2. 转换成 OpenVLA-OFT 格式**

```
task_name/
├── demo_0/
│   ├── front_camera/
│   │   ├── 0000.png
│   │   ├── 0001.png
│   │   └── ...
│   └── trajectory.json
├── demo_1/
│   └── ...
└── ...
```

trajectory.json 里存动作序列、语言指令、成功标记这些。

**3. 动作归一化**

转换的时候要把原始动作（比如关节角度、笛卡尔坐标）归一化到 [-1, 1] 之间。归一化参数（min 和 max）要记下来，推理的时候要反归一化。

### 可行种子预收集

RL 训练的时候，每个任务需要多个初始状态。这些初始状态可以从演示数据里来——每条演示的第一步就是一个初始状态。

但有时候演示数据不够多，或者想增加多样性，可以做**可行种子预收集**：

```python
# 伪代码：随机采样初始状态，检查是否可行
feasible_seeds = []
for _ in range(num_seeds):
    obs = env.reset(randomize=True)  # 随机化物体位置
    # 简单检查：物体在工作空间内，没有穿模
    if is_feasible(obs):
        feasible_seeds.append(env.get_state())

save(feasible_seeds, "feasible_seeds.npy")
```

训练的时候从这些可行种子里随机选，保证每个初始状态都是"合理的"——不会出现物体在半空中或者穿模的情况。

---

## 10.4.7.3 环境注册与包装器

### 在 rob_dataset.py 里加配置

第一步，在数据集注册字典里加上 OpenArm 的配置：

```python
# rob_dataset.py
DATASETS = {
    # ... 已有的配置 ...
    
    "openarm_pickplace": {
        "env_name": "openarm",
        "task_suite": "openarm_pickplace",
        "image_size": 224,
        "camera_names": ["front_camera"],
        "max_episode_length": 200,
        "action_dim": 8,
        "num_demos": 50,
        "data_root": "./data/openarm_pickplace",
    },
}
```

跟 LIBERO 的配置格式一样，就是参数值不一样。

### 在 rob_rollout.py 里加环境创建逻辑

第二步，在 `create_environment` 函数里加上 OpenArm 的分支：

```python
# rob_rollout.py
def create_environment(env_name, task_name, **kwargs):
    if env_name == "libero":
        from libero.envs import LiberoEnv
        env = LiberoEnv(task_name=task_name, **kwargs)
    elif env_name == "robotwin":
        from robotwin.envs import RoboTwinEnv
        env = RoboTwinEnv(task_name=task_name, **kwargs)
    elif env_name == "openarm":  # 新加的
        from openarm.envs import OpenArmEnv
        env = OpenArmEnv(task_name=task_name, **kwargs)
    else:
        raise ValueError(f"Unknown environment: {env_name}")
    
    env = RobEnvWrapper(env, **kwargs)
    return env
```

### OpenArmWrapper 包装器实现

第三步，写一个 OpenArm 的包装器，把环境接口统一成 veRL 期望的格式。

包装器主要做这些事：

**1. 统一 reset() 和 step() 的返回格式**

```python
class OpenArmWrapper:
    def __init__(self, env, **kwargs):
        self.env = env
        self.action_dim = kwargs.get("action_dim", 8)
        self.camera_names = kwargs.get("camera_names", ["front_camera"])
    
    def reset(self, initial_state=None):
        if initial_state is not None:
            self.env.set_state(initial_state)
        obs = self.env.reset()
        
        # 把图像整理成统一格式
        images = {}
        for cam in self.camera_names:
            images[cam] = obs[cam]
        
        return {"image": images[self.camera_names[0]], "images": images}
```

**2. 动作的编码和解码**

```python
    def step(self, action):
        # action 是归一化后的 [-1, 1]，要反归一化回原始范围
        action_denorm = self.denormalize_action(action)
        obs, reward, done, info = self.env.step(action_denorm)
        
        # 同样整理图像格式
        images = {}
        for cam in self.camera_names:
            images[cam] = obs[cam]
        
        return {"image": images[self.camera_names[0]], "images": images}, reward, done, info
```

**3. 图像预处理**

```python
    def _preprocess_image(self, image):
        # resize 到 224×224
        image = cv2.resize(image, (224, 224))
        # 归一化到 [0, 1] 或者 [-1, 1]，看模型要求
        image = image.astype(np.float32) / 255.0
        return image
```

### 成功检测与奖励函数

奖励是二元的，所以关键是**成功检测**——怎么判断任务完成了？

每个任务的成功判据不一样。比如：

**抓取放置任务**：
```python
def get_info(self):
    # 物体是否在目标区域内
    object_pos = self.env.get_object_position()
    target_pos = self.env.get_target_position()
    distance = np.linalg.norm(object_pos - target_pos)
    success = distance < 0.05  # 5cm 以内算成功
    
    return {"success": success}
```

**推杆任务**：
```python
def get_info(self):
    # 杆是否被推到目标位置
    # ...
    return {"success": success}
```

成功检测的设计很重要——太松了，模型会学到"作弊"的方法；太严了，模型很难成功，RL 学不动。

一般建议：
- 位置容差 3-5cm（桌面操作）
- 姿态容差 10-20 度
- 夹爪闭合状态也算一个判据

成功检测写在 `get_info()` 方法里，rollout 的时候会调这个方法来判断成功还是失败。

---

## 10.4.7.4 训练结果与失败分析

### 训练结果大概什么水平

OpenArm 上的训练结果，根据任务难度不同，大概在这个范围：

| 阶段 | 成功率 | 说明 |
|------|--------|------|
| SFT 基线 | ~20% | 跟 LIBERO 差不多，取决于任务难度 |
| SFT + RL | ~45-55% | RL 提升明显，相对提升 125%-175% |

为什么比 LIBERO 低？因为 OpenArm 的 8-DoF 控制更难，而且 Isaac Lab 的物理仿真更真实，容错率更低。

但提升幅度是显著的——从 20% 涨到 50% 左右，翻了一倍还多。这说明 RL 后训练在新机器人上也是有效的。

### 训练曲线的特点

跟 LIBERO 比，OpenArm 的训练曲线有几个特点：

**1. 收敛更慢**：可能需要几千步甚至上万步才能看到明显提升，因为任务更复杂。

**2. 波动更大**：成功率上下跳动比较明显，因为物理仿真的随机性更大。

**3. 更容易不稳定**：偶尔会出现成功率突然掉下来的情况，学习率可能需要调小一些。

建议的调参策略：
- 学习率从 5e-6 降到 2e-6 或者 1e-6
- 温度从 1.6 降到 1.2，减少探索的随机性
- 多存几个 checkpoint，挑最好的用

### 失败模式分析

训完之后，别光看成功率——分析一下失败模式更有价值。

可以写个简单的脚本，把失败的轨迹按原因分类：

```python
# 伪代码：失败模式分类
def analyze_failure(trajectory, info):
    # 1. 根本没碰到物体
    if not info.get("object_touched", False):
        return "miss_grasp"
    
    # 2. 碰到了但没抓住
    if info.get("object_touched") and not info.get("object_grasped"):
        return "grasp_failed"
    
    # 3. 抓住了但放错位置
    if info.get("object_grasped") and not info.get("success"):
        return "wrong_position"
    
    # 4. 超时了
    if info.get("timeout"):
        return "timeout"
    
    # 5. 碰撞了
    if info.get("collision"):
        return "collision"
    
    return "unknown"
```

常见的失败模式：

**miss_grasp（没抓到）**：最常见。抓手到了物体附近但差一点，或者角度不对。说明定位精度还不够。

**wrong_position（放错位置）**：抓到了，但放置的时候位置不对。说明放置阶段的控制还需要优化。

**timeout（超时）**：动作太慢，或者绕了远路，时间到了还没完成。

**collision（碰撞）**：机器人撞到了桌子或者其他物体。这种比较危险，实际部署的时候要避免。

### 基于失败类型的调优建议

不同的失败模式，调优方向不一样：

**如果大部分是 miss_grasp**：
- 增加抓取阶段的演示数据
- 调小学习率，让策略更新更精细
- 考虑增加相机视角（比如加个侧视相机）

**如果大部分是 wrong_position**：
- 检查放置目标的定义是不是太严格了
- 增加放置阶段的成功奖励权重（如果用密集奖励的话）
- 考虑把任务拆成"抓取"和"放置"两个阶段分别优化

**如果 timeout 很多**：
- 检查 max_steps 是不是设小了
- 看看模型是不是在"犹豫"——反复做同样的动作
- 可以适当调高温度，让模型更果断一些

**如果 collision 很多**：
- 这是比较危险的信号，说明策略在往危险的方向探索
- 降低学习率，减小更新幅度
- 考虑加一个碰撞惩罚项（虽然是二元奖励，但可以在环境层面加安全约束）

失败分析是个迭代的过程——分析 → 调参 → 再训练 → 再分析，几轮下来效果会越来越好。

---

## 小结

把 SimpleVLA-RL 适配到新机器人，核心就四步：

1. **动作空间适配**：优先试直接 8-DoF 映射，改的地方少，信息不丢
2. **仿真环境与数据收集**：Isaac Lab 搭环境，传统 RL 训专家策略，生成演示数据并转换格式
3. **环境注册与包装器**：在 rob_dataset.py 加配置，在 rob_rollout.py 加环境创建，写 OpenArmWrapper 统一接口
4. **训练结果与失败分析**：SFT 基线 ~20%，RL 后 ~45-55%；按失败模式分类分析，针对性调优

整个流程走下来，大概需要一两周的时间——环境搭一两天，数据收集一两天，训练跑几天，分析调优再几天。

下一节是最后一节，故障排查和索引——把常见的坑和关键参数汇总一下，方便查。
```
