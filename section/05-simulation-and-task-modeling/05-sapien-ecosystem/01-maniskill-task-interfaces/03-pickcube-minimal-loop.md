# PickCube 最小闭环

现在我们真正创建第一个 ManiSkill 任务。`PickCube-v1` 的场景很简单：机械臂面对桌面，桌上有一个方块，目标是把方块抓起来并放到目标位置附近。

![PickCube-v1 reset 后的任务画面](../../assets/maniskill_pickcube_reset.png)

这一页的重点不是训练一个成功策略，而是跑通最小闭环：创建环境、reset、step、读取 reward 和 `info`，最后关闭环境。只要这条闭环清楚，后面接 RL、IL 或评测时才知道自己在传递什么。

## 最小代码

第一次接触 ManiSkill 时，代码应该先保持短。下面这段程序只做一件事：创建 `PickCube-v1`，随机执行 50 步，然后关闭环境。代码里的关键调用和参数可以直接点击，像读源码一样跳到对应解释。

<div class="code-explorer" id="pickcube-code-explorer">
  <div class="code-explorer-header">
    <span class="code-explorer-kicker">可跳转代码</span>
    <span class="code-explorer-title" id="pickcube-code-title">最小代码：PickCube 闭环</span>
    <span class="code-explorer-actions">
      <button class="code-explorer-back" id="pickcube-code-back" type="button" hidden>上一步</button>
      <button class="code-explorer-reset" id="pickcube-code-reset" type="button" hidden>返回最小代码</button>
    </span>
  </div>
  <pre class="code-block language-python"><code class="language-python" id="pickcube-code-snippet"><span class="syntax-keyword">import</span> gymnasium <span class="syntax-keyword">as</span> gym
<a class="code-link" href="#pickcube-code-explorer" data-code-topic="mani-skill-import"><span class="syntax-keyword">import</span> mani_skill.envs</a>

env = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="gym-make">gym.make</a>(
    <a class="code-link syntax-string" href="#pickcube-code-explorer" data-code-topic="env-id">"PickCube-v1"</a>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="obs-mode">obs_mode</a>=<span class="syntax-string">"state"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="control-mode">control_mode</a>=<span class="syntax-string">"pd_ee_delta_pose"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="render-mode">render_mode</a>=<span class="syntax-string">"rgb_array"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="num-envs">num_envs</a>=<span class="syntax-number">1</span>,
)

obs, info = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="reset">env.reset</a>(<a class="code-link" href="#pickcube-code-explorer" data-code-topic="seed">seed</a>=<span class="syntax-number">0</span>)
<span class="syntax-keyword">for</span> _ <span class="syntax-keyword">in</span> <span class="syntax-builtin">range</span>(<span class="syntax-number">50</span>):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="step">env.step</a>(action)

env.close()</code></pre>
  <p class="code-explorer-note" id="pickcube-code-note">点击代码里的 `import mani_skill.envs`、`gym.make`、`obs_mode` 或 `env.step`，这个代码框会原地切换到对应展开代码。</p>
  <script>
    (() => {
      const mainCode = `<span class="syntax-keyword">import</span> gymnasium <span class="syntax-keyword">as</span> gym
<a class="code-link" href="#pickcube-code-explorer" data-code-topic="mani-skill-import"><span class="syntax-keyword">import</span> mani_skill.envs</a>

env = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="gym-make">gym.make</a>(
    <a class="code-link syntax-string" href="#pickcube-code-explorer" data-code-topic="env-id">"PickCube-v1"</a>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="obs-mode">obs_mode</a>=<span class="syntax-string">"state"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="control-mode">control_mode</a>=<span class="syntax-string">"pd_ee_delta_pose"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="render-mode">render_mode</a>=<span class="syntax-string">"rgb_array"</span>,
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="num-envs">num_envs</a>=<span class="syntax-number">1</span>,
)

obs, info = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="reset">env.reset</a>(<a class="code-link" href="#pickcube-code-explorer" data-code-topic="seed">seed</a>=<span class="syntax-number">0</span>)
<span class="syntax-keyword">for</span> _ <span class="syntax-keyword">in</span> <span class="syntax-builtin">range</span>(<span class="syntax-number">50</span>):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="step">env.step</a>(action)

env.close()`;

      const snippets = {
        "main": {
          title: "最小代码：PickCube 闭环",
          note: "点击代码里的 `import mani_skill.envs`、`gym.make`、`obs_mode` 或 `env.step`，这个代码框会原地切换到对应展开代码。",
          html: mainCode
        },
        "mani-skill-import": {
          title: "import mani_skill.envs：注册 ManiSkill 任务",
          note: "这一步的关键不是导入一个变量，而是执行 ManiSkill 的注册代码，把任务 ID 写入 Gymnasium registry。",
          html: `<span class="syntax-comment"># 教学化示意：mani_skill.envs 被导入时会注册内置任务</span>
<span class="syntax-keyword">from</span> gymnasium.envs.registration <span class="syntax-keyword">import</span> register

<a class="code-link" href="#pickcube-code-explorer" data-code-topic="register">register</a>(
    id=<span class="syntax-string">"PickCube-v1"</span>,
    entry_point=<span class="syntax-string">"mani_skill.envs.tasks.tabletop.pick_cube:PickCubeEnv"</span>,
    kwargs={...},
)

<span class="syntax-comment"># 注册后，gym.make("PickCube-v1") 才能在 registry 中找到它</span>`
        },
        "register": {
          title: "register()：把任务写进 registry",
          note: "register 把字符串 ID、entry_point 和默认参数打包成 EnvSpec，再放进全局 registry。",
          html: `<span class="syntax-keyword">def</span> register(id, entry_point, kwargs=None, **spec_kwargs):
    env_spec = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="env-spec">EnvSpec</a>(
        id=id,
        entry_point=entry_point,
        kwargs=kwargs <span class="syntax-keyword">or</span> {},
        **spec_kwargs,
    )
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="registry">registry</a>[env_spec.id] = env_spec`
        },
        "gym-make": {
          title: "gym.make()：进入 make 的创建流程",
          note: "这是一条可继续进入的链路：register -> registry -> EnvSpec -> kwargs -> entry_point -> creator -> wrappers -> env。",
          html: `<span class="syntax-keyword">def</span> make(id, max_episode_steps=None, disable_env_checker=None, **kwargs):
    <span class="syntax-comment"># 1. 用环境 ID 找到注册表里的 EnvSpec</span>
    <span class="syntax-keyword">if</span> isinstance(id, <a class="code-link" href="#pickcube-code-explorer" data-code-topic="env-spec">EnvSpec</a>):
        env_spec = id
    <span class="syntax-keyword">else</span>:
        env_spec = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="find-spec">_find_spec</a>(id)  <span class="syntax-comment"># "PickCube-v1" -> EnvSpec</span>

    <span class="syntax-comment"># 2. 合并注册默认参数与本次 gym.make 传入的参数</span>
    env_kwargs = copy.deepcopy(env_spec.kwargs)
    env_kwargs.update(<a class="code-link" href="#pickcube-code-explorer" data-code-topic="make-kwargs">kwargs</a>)

    <span class="syntax-comment"># 3. 把 entry_point 解析成真正的环境构造函数</span>
    <span class="syntax-keyword">if</span> env_spec.<a class="code-link" href="#pickcube-code-explorer" data-code-topic="entry-point">entry_point</a> <span class="syntax-keyword">is</span> None:
        <span class="syntax-keyword">raise</span> Error(<span class="syntax-string">"registered but entry_point is not specified"</span>)
    <span class="syntax-keyword">elif</span> callable(env_spec.entry_point):
        env_creator = env_spec.entry_point
    <span class="syntax-keyword">else</span>:
        env_creator = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="load-env-creator">load_env_creator</a>(env_spec.entry_point)

    <span class="syntax-comment"># 4. 调用 ManiSkill 注册的 creator，创建底层环境</span>
    env = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="env-creator">env_creator</a>(**env_kwargs)

    <span class="syntax-comment"># 5. 写回 spec，并套 Gymnasium 标准 wrapper</span>
    env.unwrapped.spec = EnvSpec(id=env_spec.id, kwargs=env_kwargs, ...)
    env = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="gym-wrappers">apply_wrappers</a>(env, env_spec, max_episode_steps)

    <span class="syntax-keyword">return</span> env`
        },
        "find-spec": {
          title: "_find_spec()：从 registry 找任务说明书",
          note: "registry 是 Gymnasium 的环境注册表；ManiSkill 导入时把 PickCube-v1 写进去，make 时再取出来。",
          html: `<span class="syntax-comment"># 教学化示意：真实 Gymnasium 还会处理 namespace、版本提示和错误信息</span>
<span class="syntax-keyword">def</span> _find_spec(env_id):
    env_id = <a class="code-link" href="#pickcube-code-explorer" data-code-topic="parse-env-id">parse_env_id</a>(env_id)  <span class="syntax-comment"># "PickCube-v1"</span>
    <span class="syntax-keyword">if</span> env_id <span class="syntax-keyword">not in</span> <a class="code-link" href="#pickcube-code-explorer" data-code-topic="registry">registry</a>:
        <span class="syntax-keyword">raise</span> Error(<span class="syntax-string">"environment is not registered"</span>)
    <span class="syntax-keyword">return</span> <a class="code-link" href="#pickcube-code-explorer" data-code-topic="registry">registry</a>[env_id]  <span class="syntax-comment"># EnvSpec</span>`
        },
        "parse-env-id": {
          title: "parse_env_id()：解析环境 ID",
          note: "Gymnasium 的环境 ID 约定包含可选 namespace、任务名和版本号。PickCube-v1 会被解析出 name=PickCube、version=1。",
          html: `<span class="syntax-comment"># 教学化示意：真实实现用正则处理 namespace/name/version</span>
<span class="syntax-keyword">def</span> parse_env_id(env_id):
    <span class="syntax-comment"># "PickCube-v1" -> namespace=None, name="PickCube", version=1</span>
    namespace, name, version = match_env_id(env_id)
    <span class="syntax-keyword">return</span> get_env_id(namespace, name, version)`
        },
        "registry": {
          title: "registry：Gymnasium 的环境注册表",
          note: "registry 把字符串 ID 映射到 EnvSpec。没有 import mani_skill.envs 这一步，PickCube-v1 通常不会出现在这里。",
          html: `<span class="syntax-comment"># 教学化示意：registry 是一个全局 dict</span>
registry = {
    <span class="syntax-string">"PickCube-v1"</span>: <a class="code-link" href="#pickcube-code-explorer" data-code-topic="env-spec">EnvSpec</a>(
        id=<span class="syntax-string">"PickCube-v1"</span>,
        entry_point=<span class="syntax-string">"mani_skill...:PickCubeEnv"</span>,
        kwargs={...},
    ),
    <span class="syntax-comment"># PushCube-v1、StackCube-v1 等任务也以同样方式注册</span>
}`
        },
        "env-spec": {
          title: "EnvSpec：环境注册说明书",
          note: "EnvSpec 不是真正的环境实例，而是创建环境所需的说明书。",
          html: `<span class="syntax-keyword">@dataclass</span>
<span class="syntax-keyword">class</span> EnvSpec:
    id: str                         <span class="syntax-comment"># "PickCube-v1"</span>
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="entry-point">entry_point</a>: str | Callable      <span class="syntax-comment"># 环境构造函数位置</span>
    <a class="code-link" href="#pickcube-code-explorer" data-code-topic="make-kwargs">kwargs</a>: dict                     <span class="syntax-comment"># 注册时默认参数</span>
    max_episode_steps: int | None
    order_enforce: bool
    disable_env_checker: bool
    additional_wrappers: tuple`
        },
        "make-kwargs": {
          title: "kwargs：把本次设置传给 ManiSkill 环境",
          note: "obs_mode、control_mode、render_mode、num_envs 不是 Gymnasium 自己消费掉，而是进入 env_kwargs 传给 ManiSkill 的环境构造函数。",
          html: `env_kwargs = copy.deepcopy(env_spec.kwargs)
env_kwargs.update({
    <span class="syntax-string">"obs_mode"</span>: <span class="syntax-string">"state"</span>,
    <span class="syntax-string">"control_mode"</span>: <span class="syntax-string">"pd_ee_delta_pose"</span>,
    <span class="syntax-string">"render_mode"</span>: <span class="syntax-string">"rgb_array"</span>,
    <span class="syntax-string">"num_envs"</span>: <span class="syntax-number">1</span>,
})`
        },
        "entry-point": {
          title: "entry_point：从 ID 指到环境类",
          note: "entry_point 是 registry 和真实 Python 类之间的桥。它通常是字符串路径，也可以直接是 callable。",
          html: `<span class="syntax-comment"># EnvSpec 中保存的是类似这样的入口</span>
entry_point = <span class="syntax-string">"mani_skill...:PickCubeEnv"</span>

<span class="syntax-comment"># Gymnasium 通过它找到真正的环境构造函数</span>
env_creator = load_env_creator(entry_point)`
        },
        "load-env-creator": {
          title: "load_env_creator()：导入 entry_point 指向的构造函数",
          note: "字符串 entry_point 会被拆成 module 和 attribute，然后动态 import。",
          html: `<span class="syntax-keyword">def</span> load_env_creator(entry_point):
    module_path, attr_name = entry_point.split(<span class="syntax-string">":"</span>)
    module = importlib.import_module(module_path)
    <span class="syntax-keyword">return</span> getattr(module, attr_name)  <span class="syntax-comment"># 例如 PickCubeEnv</span>`
        },
        "env-creator": {
          title: "env_creator(**env_kwargs)：创建 ManiSkill 环境实例",
          note: "到这一步才真正进入 ManiSkill 的任务层；Gymnasium 只是根据注册表找到并调用它。",
          html: `<span class="syntax-comment"># env_creator 近似等于 ManiSkill 注册的 PickCubeEnv 构造函数</span>
env = PickCubeEnv(
    obs_mode=<span class="syntax-string">"state"</span>,
    control_mode=<span class="syntax-string">"pd_ee_delta_pose"</span>,
    render_mode=<span class="syntax-string">"rgb_array"</span>,
    num_envs=<span class="syntax-number">1</span>,
)

<span class="syntax-comment"># 返回的 env 才拥有 reset / step / render / action_space</span>`
        },
        "gym-wrappers": {
          title: "wrappers：返回前套上 Gymnasium 标准外壳",
          note: "wrapper 不改变任务本体，但会补充检查、调用顺序约束、时间限制或渲染兼容层。",
          html: `<span class="syntax-keyword">if</span> should_check_env(disable_env_checker, env_spec):
    env = PassiveEnvChecker(env)
<span class="syntax-keyword">if</span> env_spec.order_enforce:
    env = OrderEnforcing(env)
<span class="syntax-keyword">if</span> needs_time_limit(max_episode_steps, env_spec):
    env = TimeLimit(env, max_episode_steps)

<span class="syntax-keyword">return</span> env`
        },
        "env-id": {
          title: "PickCube-v1：选择任务",
          note: "换 env_id 就是在换任务；后续 reset / step / success 接口保持同一风格。",
          code: `env = gym.make(
    "PickCube-v1",  # 任务 ID：抓起方块并放到目标附近
    obs_mode="state",
    control_mode="pd_ee_delta_pose",
)`
        },
        "obs-mode": {
          title: "obs_mode：选择观测",
          note: "state 适合第一轮接口学习；rgbd 会把相机数据纳入观测结构。",
          code: `env = gym.make("PickCube-v1", obs_mode="state")
obs, info = env.reset(seed=0)
print(env.observation_space)
print(getattr(env, "single_observation_space", None))`
        },
        "control-mode": {
          title: "control_mode：选择动作语义",
          note: "控制模式决定 action 的含义和维度，不能只把 action 当作普通数组。",
          code: `env = gym.make(
    "PickCube-v1",
    control_mode="pd_ee_delta_pose",
)
print(env.action_space)`
        },
        "render-mode": {
          title: "render_mode：选择展示输出",
          note: "render 面向截图和视频检查；策略观测由 obs_mode 决定。",
          code: `env = gym.make("PickCube-v1", render_mode="rgb_array")
obs, info = env.reset(seed=0)
frame = env.render()
print(frame.shape)`
        },
        "num-envs": {
          title: "num_envs：选择并行环境数",
          note: "即使 num_envs=1，ManiSkill 也可能保留 batch 维。",
          code: `env = gym.make("PickCube-v1", obs_mode="state", num_envs=1)
obs, info = env.reset(seed=0)
print(obs.shape)  # 例如 (1, 42)`
        },
        "reset": {
          title: "env.reset()：开始一个 episode",
          note: "reset 返回第一帧观测和初始化信息，是每个 episode 的入口。",
          code: `obs, info = env.reset(seed=0)
print(type(obs), getattr(obs, "shape", None))
print(sorted(info.keys()))`
        },
        "seed": {
          title: "seed：固定初始状态",
          note: "固定 seed 让截图、summary 和失败现象更容易复现和对照。",
          code: `obs, info = env.reset(seed=0)  # 教学和调试先固定 seed`
        },
        "step": {
          title: "env.step()：推进仿真一步",
          note: "step 返回训练信号、结束信号和任务评估信息；success 在 info 里。",
          code: `action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
print(reward, terminated, truncated)
print(info.get("success"))`
        }
      };

      const escapeHtml = (text) =>
        text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

      const root = document.getElementById("pickcube-code-explorer");
      const title = document.getElementById("pickcube-code-title");
      const snippet = document.getElementById("pickcube-code-snippet");
      const note = document.getElementById("pickcube-code-note");
      const back = document.getElementById("pickcube-code-back");
      const reset = document.getElementById("pickcube-code-reset");
      if (!root || !title || !snippet || !note || !back || !reset) return;
      const history = [];
      let currentTopic = "main";

      const renderSnippet = (topic, pushHistory = true) => {
        const item = snippets[topic] || snippets["main"];
        if (pushHistory && topic !== currentTopic) {
          history.push(currentTopic);
        }
        currentTopic = topic;
        title.textContent = item.title;
        snippet.innerHTML = item.html || escapeHtml(item.code);
        note.textContent = item.note;
        reset.hidden = topic === "main";
        back.hidden = history.length === 0;
      };

      root.addEventListener("click", (event) => {
        const link = event.target.closest("[data-code-topic]");
        if (!link || !root.contains(link)) return;
        event.preventDefault();
        renderSnippet(link.getAttribute("data-code-topic"));
      });

      back.addEventListener("click", () => {
        const previous = history.pop() || "main";
        renderSnippet(previous, false);
      });
      reset.addEventListener("click", () => {
        history.length = 0;
        renderSnippet("main", false);
      });
      renderSnippet("main", false);
    })();
  </script>
</div>

这段代码里最容易漏的是 `import mani_skill.envs`。它本身不会创建环境，但会把 ManiSkill 自带任务注册到 Gymnasium。注册完成后，`"PickCube-v1"` 才能像普通环境 ID 一样传给 `gym.make()`。

`reset(seed=0)` 把任务放到一个可复现的初始状态，并返回第一帧观测和初始化信息。`step(action)` 推进一步仿真，返回新的观测、reward、终止信号和 `info`。随机采样的 action 通常无法完成抓取，所以这段代码的目标不是获得成功策略，而是确认环境闭环可以运行。

<span id="pickcube-call-gym-make"></span>

### `gym.make()`：创建任务环境

`gym.make()` 是 Gymnasium 的环境创建入口。ManiSkill 通过 `import mani_skill.envs` 完成任务注册，因此这里可以直接用 `"PickCube-v1"` 创建环境。点击代码里的 `gym.make` 时，展开框展示的是 `make()` 的创建流程：从环境 ID 查注册表，找到 `EnvSpec`，加载 `entry_point`，调用 ManiSkill 注册的环境构造函数，再套上 Gymnasium 的标准 wrapper。这个流程解释的是“环境对象从哪里来”，不是单纯重复调用参数。

<span id="pickcube-param-env-id"></span>

### `"PickCube-v1"`：选择任务

`"PickCube-v1"` 是 Gymnasium 环境 ID。它指定这次创建的是 PickCube 任务：机械臂面对桌面方块，目标是把方块抓起并放到目标位置附近。换成其他环境 ID，例如 PushCube 或 StackCube，任务目标会变，但 `reset()`、`step()`、reward 和 `info["success"]` 这套接口仍然成立。

<span id="pickcube-param-obs-mode"></span>

### `obs_mode`：选择观测

`obs_mode="state"` 表示先使用低维状态观测。它适合第一轮学习，因为不用先处理相机、深度图和视觉张量。仓库随附的 probe 中，`PickCube-v1` 的 state 观测空间是 `Box(-inf, inf, (1, 42), float32)`：前面的 `1` 是 batch 维，`42` 是单个环境的 state 维度。

<span id="pickcube-param-control-mode"></span>

### `control_mode`：选择动作语义

`control_mode="pd_ee_delta_pose"` 表示 action 以末端执行器位姿增量的形式作用到机器人。它不是“随便 7 个数字”，而是一个有控制语义的命令。本例的 action space 是 `Box(-1.0, 1.0, (7,), float32)`；后面比较不同控制模式时，会看到 action 维度和含义都可能改变。

<span id="pickcube-param-render-mode"></span>

### `render_mode`：选择展示输出

`render_mode="rgb_array"` 让 `env.render()` 返回 RGB 图像数组，便于保存截图或视频。它面向人类检查和文档展示，不等同于策略观测。策略实际看到什么，由 `obs_mode` 决定；视觉任务里还要进一步区分 `env.render()` 和 `obs["sensor_data"]`。

<span id="pickcube-param-num-envs"></span>

### `num_envs`：选择并行环境数

`num_envs=1` 表示只创建一个环境，但 ManiSkill 仍可能保留 batch 维。因此你可能看到 `(1, 42)` 这样的 state shape。这里的 `1` 不是多出来的状态维度，而是并行环境数量；把 `num_envs` 改成 16 后，它会自然变成 `(16, 42)`。

<span id="pickcube-param-seed"></span>

### `seed`：固定初始状态

`env.reset(seed=0)` 用于让 episode 初始化尽量可复现。教学和调试时应先固定 seed，这样截图、summary 和失败现象更容易对照；真正评测时，再按 benchmark 或实验设计使用多组 seed。

<span id="pickcube-call-reset"></span>

### `env.reset()`：开始一个 episode

`env.reset(seed=0)` 会初始化场景并返回 `(obs, info)`。`obs` 是策略在第一帧能看到的观测；`info` 保存初始化时的辅助信息。第一次调试时，应先确认 reset 能稳定返回，再进入连续 step。

<span id="pickcube-call-step"></span>

### `env.step()`：推进仿真一步

`env.step(action)` 返回 `(obs, reward, terminated, truncated, info)`。其中 reward 是训练信号，`terminated` 和 `truncated` 表示 episode 是否结束，`info["success"]` 及其子条件用于判断任务是否完成。随机 action 通常不会完成 PickCube，但可以验证动作空间、仿真推进和评估字段是否连通。

## 用脚本保存证据

配套脚本会把第一次运行需要看的内容保存下来：

```bash
python labs/04-simulation/maniskill_pickcube_artifacts.py --steps 50 --skip-gpu
```

运行后先看结构化输出，再看视频：

| 产物 | 应该怎么看 |
|---|---|
| `runs/04-simulation/maniskill_pickcube_summary.json` | 任务 ID、观测/动作空间、reward、success、版本 |
| `runs/04-simulation/maniskill_pickcube_spaces.txt` | observation space 和 action space |
| `section/05-simulation-and-task-modeling/assets/maniskill_pickcube_reset.png` | reset 后场景是否符合预期 |
| `section/05-simulation-and-task-modeling/assets/maniskill_pickcube_rollout.mp4` | 随机动作下任务是否能连续推进 |

视频能帮助你确认“世界里看起来有什么”，但接口判断要回到 JSON 和 space 输出。比如 `num_envs=1` 时看到类似 `(1, 42)` 的 state shape，不说明状态错了；开头的 `1` 是 batch 维，后面会专门解释。

仓库随附的 `summary.json` 来自一次完整 probe。它记录了几个关键事实：`PickCube-v1` 的 state 观测空间是 `Box(-inf, inf, (1, 42), float32)`，`pd_ee_delta_pose` 动作空间是 `Box(-1.0, 1.0, (7,), float32)`，`info` 里包含 `is_grasped`、`is_obj_placed`、`is_robot_static` 和 `success`。随机 rollout 的 `last_success` 为 false，这正好提醒我们：跑通接口不等于得到成功策略。

## 一次运行里要读出的信息

从第一条 PickCube 记录里，至少要读出这些信息：

| 字段 | 它回答的问题 |
|---|---|
| `env_id` | 跑的是哪个任务 |
| `obs_mode` | 策略输入是什么类型 |
| `control_mode` | action 的语义是什么 |
| observation shape | 观测是否带 batch 维 |
| action shape | 控制命令有多少维 |
| reward | 随机动作得到怎样的训练信号 |
| `info["success"]` | 任务是否真的完成 |

随机 rollout 未能完成任务，并不意味着环境配置有误。随机动作的主要作用是验证环境闭环是否可执行：观测是否返回、动作是否被接受、仿真是否推进、`info` 是否给出评估结果。

`PickCube-v1` 是最小入口，不是 ManiSkill 的全部。完成这个闭环后，读者应形成一套可迁移的阅读方法：更换 `env_id` 后，仍然先检查 reset、step、观测、动作、reward 与 `info["success"]`。推动、堆叠、插入、放置、工具操作等任务在目标和场景上各不相同，但接口分析方法保持一致。

## 从 PickCube 推广到更多任务

下面这组视频来自 ManiSkill 官方 motion-planning 示例，覆盖若干典型操作任务。它们的作用是帮助读者把刚刚建立的最小闭环迁移到更多任务：先观察 PickCube，再比较 PushCube、StackCube、PlugCharger 等环境，注意任务目标如何变化，以及 `env_id`、控制模式、观测结构和成功判定如何继续构成实验记录的核心信息。

<div class="maniskill-demo-player" id="maniskill-official-demo-player">
  <label for="maniskill-official-demo-select">选择一个任务示例</label>
  <select id="maniskill-official-demo-select">
    <option value="../../assets/maniskill-official-success/panda_pick_cube_v1.mp4" data-meta="Panda / PickCube-v1 / 74 steps / success=true">Panda PickCube-v1 · 74 steps</option>
    <option value="../../assets/maniskill-official-success/panda_push_cube_v1.mp4" data-meta="Panda / PushCube-v1 / 71 steps / success=true">Panda PushCube-v1 · 71 steps</option>
    <option value="../../assets/maniskill-official-success/panda_stack_cube_v1.mp4" data-meta="Panda / StackCube-v1 / 107 steps / success=true">Panda StackCube-v1 · 107 steps</option>
    <option value="../../assets/maniskill-official-success/panda_peg_insertion_side_v1.mp4" data-meta="Panda / PegInsertionSide-v1 / 178 steps / success=true">Panda PegInsertionSide-v1 · 178 steps</option>
    <option value="../../assets/maniskill-official-success/panda_plug_charger_v1.mp4" data-meta="Panda / PlugCharger-v1 / 156 steps / success=true">Panda PlugCharger-v1 · 156 steps</option>
    <option value="../../assets/maniskill-official-success/panda_place_sphere_v1.mp4" data-meta="Panda / PlaceSphere-v1 / 121 steps / success=true">Panda PlaceSphere-v1 · 121 steps</option>
    <option value="../../assets/maniskill-official-success/panda_pull_cube_v1.mp4" data-meta="Panda / PullCube-v1 / 67 steps / success=true">Panda PullCube-v1 · 67 steps</option>
    <option value="../../assets/maniskill-official-success/panda_pull_cube_tool_v1.mp4" data-meta="Panda / PullCubeTool-v1 / 234 steps / success=true">Panda PullCubeTool-v1 · 234 steps</option>
    <option value="../../assets/maniskill-official-success/panda_lift_peg_upright_v1.mp4" data-meta="Panda / LiftPegUpright-v1 / 176 steps / success=true">Panda LiftPegUpright-v1 · 176 steps</option>
    <option value="../../assets/maniskill-official-success/panda_stack_pyramid_v1.mp4" data-meta="Panda / StackPyramid-v1 / 176 steps / success=true">Panda StackPyramid-v1 · 176 steps</option>
    <option value="../../assets/maniskill-official-success/so100_pick_cube_so100_v1.mp4" data-meta="SO100 / PickCubeSO100-v1 / 95 steps / success=true">SO100 PickCubeSO100-v1 · 95 steps</option>
    <option value="../../assets/maniskill-official-success/xarm6_pick_cube_v1.mp4" data-meta="xArm6 / PickCube-v1 / 81 steps / success=true">xArm6 PickCube-v1 · 81 steps</option>
    <option value="../../assets/maniskill-official-success/xarm6_push_cube_v1.mp4" data-meta="xArm6 / PushCube-v1 / 1196 steps / success=true">xArm6 PushCube-v1 · 1196 steps</option>
    <option value="../../assets/maniskill-official-success/xarm6_stack_cube_v1.mp4" data-meta="xArm6 / StackCube-v1 / 103 steps / success=true">xArm6 StackCube-v1 · 103 steps</option>
    <option value="../../assets/maniskill-official-success/xarm6_plug_charger_v1.mp4" data-meta="xArm6 / PlugCharger-v1 / 149 steps / success=true">xArm6 PlugCharger-v1 · 149 steps</option>
  </select>
  <video id="maniskill-official-demo-video" controls playsinline preload="metadata" poster="../../assets/maniskill-official-success/posters/panda_pick_cube_v1.jpg" src="../../assets/maniskill-official-success/panda_pick_cube_v1.mp4"></video>
  <p class="maniskill-demo-meta" id="maniskill-official-demo-meta">Panda / PickCube-v1 / 74 steps / success=true</p>
  <script>
    (() => {
      const root = document.getElementById("maniskill-official-demo-player");
      if (!root) return;
      const select = root.querySelector("#maniskill-official-demo-select");
      const video = root.querySelector("#maniskill-official-demo-video");
      const meta = root.querySelector("#maniskill-official-demo-meta");
      if (!select || !video || !meta) return;
      const posterFromVideo = (src) => src.replace(/([^/]+)\.mp4$/, "posters/$1.jpg");
      const updateDemo = () => {
        const option = select.selectedOptions[0];
        if (!option) return;
        video.poster = posterFromVideo(option.value);
        video.src = option.value;
        video.load();
        meta.textContent = option.dataset.meta || option.textContent;
      };
      select.addEventListener("change", updateDemo);
    })();
  </script>
</div>

这些轨迹说明，同一套任务接口可以统一描述不同类型的操作目标。需要注意的是，它们来自官方 motion-planning 示例，不是随机策略，也不等同于训练得到的通用策略。若本地运行未完成任务，排查仍然要回到 `summary.json`、`info["success"]` 和子条件上：是否抓住、是否放到目标、机器人是否静止，才是判断任务接口和控制策略的证据。

## 小结

- `PickCube-v1` 是理解 ManiSkill 操作任务的合适入口。
- 第一次跑通的目标是读懂接口，不是得到成功策略。
- 视频用于观察现象，summary 和 space 用于确认接口。
- 任务是否完成应该看 `info["success"]`，不要用 reward 或视频直觉代替。

## 导航

- 上一页：[安装与环境自检](02-install-and-env-check.md)
- 返回上级：[ManiSkill 任务接口与 PickCube 实战](../01-maniskill-task-interfaces.md)
- 下一页：[任务接口契约](04-task-interface-contract.md)
