# 系统与策略接口

RoboArena 的工程系统把策略推理、真实机器人执行、评测调度和结果存储拆成四类组件。policy server 由策略提交方维护，负责把 DROID 观测转成动作片段；evaluation client 运行在 evaluator 的 DROID 站点，负责采集观测、调用 policy server、执行动作和上传 rollout；central server 负责分配策略、维护 session 与 credit；database / object storage 保存 session metadata、episode 分数、视频和 proprioception/action 记录。

## 系统组件

| 组件 | 运行位置 | 主要职责 |
|---|---|---|
| policy server | 策略提交方或托管服务器 | 暴露 websocket endpoint，声明观测需求和动作空间，返回 action chunk |
| evaluation client | evaluator 的 DROID 机器人站点 | 连接 DROID `RobotEnv`、采集相机和本体状态、执行 A/B rollout、上传 episode |
| central server | RoboArena 后端 | 校验 evaluator、选择 A/B policy、创建 session、处理 timeout、维护 credit 和 leaderboard API |
| database / storage | 后端数据库和对象存储 | 保存 users、policies、sessions、episodes，以及 left/right/wrist video 和 `npz` 文件路径 |

这些组件让策略不必把权重上传到 evaluator 机器。policy server 可以运行在策略提交方维护的算力环境中，evaluation client 只承担真实机器人控制和数据记录。这个分工降低了 evaluator 端的算力要求，也让 closed-source policies 可以参与评测；代价是远程推理、网络连通性和 policy server 可用性会影响 rollout 行为并进入结果解释。

## policy server contract

策略侧实现 `BasePolicy.infer(obs)` 和可选 `reset(reset_info)`。`WebsocketPolicyServer` 启动后，首先向 client 发送 `PolicyServerConfig`，说明图像分辨率、是否需要 wrist camera、需要几个 external cameras、是否需要 stereo images、是否需要 `session_id`，以及动作空间是 `joint_position`、`joint_velocity`、`cartesian_position` 还是 `cartesian_velocity`。

策略端最小 contract 可以写成下面的删减片段。`PolicyServerConfig` 不是普通注释，它会在 websocket 连接建立后先发给 evaluation client，决定 client 端实际发送哪些 observation keys。

```python
@dataclasses.dataclass
class PolicyServerConfig:
    image_resolution: tuple[int, int] | None = (224, 224)
    needs_wrist_camera: bool = True
    n_external_cameras: int = 1
    needs_stereo_camera: bool = False
    needs_session_id: bool = False
    action_space: str = "joint_position"


class BasePolicy(abc.ABC):
    @abc.abstractmethod
    def infer(self, obs: dict) -> dict:
        ...

    def reset(self, reset_info: dict) -> None:
        pass
```

`infer` 的观测字典由 evaluation client 按 config 裁剪和重命名。图像字段包括 `observation/wrist_image_left`、`observation/wrist_image_right`、`observation/exterior_image_1_left`、`observation/exterior_image_2_left` 等；本体字段包括 `observation/joint_position`、`observation/cartesian_position` 和 `observation/gripper_position`；语言目标放在 `prompt`。stateful policy 可以要求 `session_id`，用 A/B session 和 policy label 组成唯一 rollout 标识。

策略返回值是包含 `actions` 的字典。`actions` 可以是一段 action chunk，shape 通常是 `(N, 8)` 或 `(N, 7)`：joint action 使用 7 维运动量加 gripper，cartesian action 使用 6 维位姿量加 gripper。evaluation client 会按顺序执行 chunk 中的低层动作，只有当前 chunk 消耗完后才再次向 policy server 请求推理。

一次 `infer` 调用中，policy 看到的不是完整 DROID 原始 observation，而是经过 config 过滤和重命名后的字段集合：

```python
obs = {
    "observation/exterior_image_1_left": image,  # if n_external_cameras >= 1
    "observation/wrist_image_left": wrist_image, # if needs_wrist_camera
    "observation/joint_position": joint_q,       # shape (7,)
    "observation/cartesian_position": ee_pose,   # shape (6,)
    "observation/gripper_position": gripper,     # shape (1,)
    "prompt": "put the red block in the bowl",
    "session_id": "session_uuid-A",              # if needs_session_id
}

return {"actions": actions}  # shape (N, 8) for joint action + gripper
```

`reset(reset_info)` 面向 stateful policies。A/B session 中 Policy A 和 Policy B 会拿到不同的 `session_id_x_policy`，例如 `session_uuid-A` 和 `session_uuid-B`；这个标识只区分同一次 A/B session 内的两个 rollout，不包含真实 policy name 或对手身份。策略如果缓存历史图像、语言状态或 recurrent state，reset 应清除对应 rollout 的状态，而不是清空所有并发 evaluator 的状态。

| config 字段 | client 发送行为 | 配置不匹配的后果 |
|---|---|---|
| `image_resolution` | client 端 resize 图像后再发给 policy server | 分辨率和训练预处理不一致时，视觉输入分布变化 |
| `needs_wrist_camera` | 发送 `observation/wrist_image_left` | wrist camera 缺失时，依赖近距离抓取视觉的策略会退化 |
| `n_external_cameras` | 发送 0、1 或 2 个 third-person left images | 策略请求 2 个外部相机而站点只有 1 个时，client 终止 session |
| `needs_stereo_camera` | 额外发送 right stereo image keys | stereo 标定或相机缺失会让观测 contract 无法满足 |
| `needs_session_id` | 发送唯一 rollout id | stateful policy 缺少 session id 时，历史状态可能串到另一个 rollout |
| `action_space` | 创建对应 `RobotEnv(action_space=...)` | action shape 或尺度不匹配会改变执行轨迹，严重时触发安全中断 |

## evaluation client

evaluation client 先读取 evaluator 的 YAML 配置，包括 evaluator email、institution、central server 地址、默认第三视角相机和 DROID camera ids。启动后它校验 client/server version 与 evaluator access code，打开 DROID `RobotEnv` 预览相机画面，并让 evaluator 确认左右相机是否对准机器人和工作区。自然语言任务指令在这个阶段输入，central server 在收到任务后才返回 A/B policy pair。

单个 policy rollout 使用独立的 `RobotEnv(action_space=...)`。client 每个控制周期读取原始 DROID observation，抽取 left/right/wrist images、joint position、cartesian position 和 gripper position，再按 policy server config 调整图像尺寸和字段集合。action chunk 为空或已经执行完时，client 调用远程 `infer`；得到 action 后，client 二值化 gripper 维度，在 `joint_velocity` 模式下把动作裁剪到 `[-1, 1]`，并以约 15 Hz 的节奏调用 `env.step(action)`。

运行循环的关键逻辑可以概括为下面的伪代码。`pred_action_chunk` 让 policy server 一次返回多步动作，client 在本地逐步消耗；只有 chunk 用完后才再次请求远程推理。

```python
env = RobotEnv(action_space=server_cfg["action_space"], gripper_action_space="position")
pred_action_chunk = None
actions_from_chunk_completed = 0

for t_step in range(max_timesteps):
    raw_obs = env.get_observation()
    obs = extract_observation(raw_obs, setting)
    log_video_frames(obs)

    if pred_action_chunk is None or actions_from_chunk_completed >= len(pred_action_chunk):
        request_data = {
            "observation/joint_position": obs["joint_position"],
            "observation/cartesian_position": obs["cartesian_position"],
            "observation/gripper_position": obs["gripper_position"],
            "prompt": lang_command,
        }
        request_data.update(select_images(obs, server_cfg, base_image))

        if server_cfg["needs_session_id"]:
            request_data["session_id"] = session_id_x_policy

        result = policy_client.infer(request_data)
        pred_action_chunk = np.asarray(result["actions"])
        actions_from_chunk_completed = 0

    action = pred_action_chunk[actions_from_chunk_completed].astype(np.float32)
    actions_from_chunk_completed += 1
    action[-1] = 1.0 if action[-1] > 0.5 else 0.0

    if action_space == "joint_velocity":
        action = np.clip(action, -1, 1)

    env.step(action)
    episode_data.append({"joint_position": obs["joint_position"], "action": action})
    sleep_to_maintain_15hz()
```

这段循环把模型推理频率和机器人执行频率分开。`N` 步 action chunk 越长，policy server 调用越少，远程延迟影响越小；同时，chunk 越长，策略在执行过程中基于新观测修正动作的机会越少。RoboArena 的结果解释因此需要同时看 action space、chunk 行为、平均推理延迟和 episode video。

运行过程中，client 保存 left、right、wrist 视频帧、每步本体状态和实际执行动作。rollout 结束后，evaluator 输入 partial success；Policy B 结束后，client 继续收集 A/B preference 和 long-form feedback。每个 policy episode 通过 `/upload_eval_data` 上传视频和压缩 `npz`，session 结束时通过 `/terminate_session` 上传 valid 标记、preference 和 long-form feedback。

## central server

central server 的 session 创建发生在 `/get_policies_to_compare`。它先清理 stale sessions，校验 evaluator 身份，查询带 IP 和 port 的 policy pool，并用 websocket liveness check 过滤不可用 policy server。候选策略中，拥有 evaluation credit 的 policy 更容易被采样；server 选择一个需要消耗 credit 的 policy 和一个随机 peer，再随机分配可见 A/B 标签，创建 `evaluation_type == "A/B"` 的 session。

后端采样逻辑的删减片段如下。`ucb_policy` 是需要消耗 evaluation credit 的策略，`uniform_peer` 是随机对手；visible A/B 标签会再随机交换一次，evaluator 端不会看到哪个策略是 credit sampling 选出的目标。

```python
candidates = db.query(PolicyModel).filter(
    PolicyModel.ip_address.isnot(None),
    PolicyModel.port.isnot(None),
).all()
alive = [p for p in candidates if _ws_policy_alive(p.ip_address, p.port)]

eligible = [
    p for p in alive
    if p.owner_name == INFINITE_CREDIT_OWNER
    or get_user(p.owner_name).eval_credit > 0
]

ucb_policy = sample_with_ucb_weight(eligible)
uniform_peer = random.choice([p for p in alive if p != ucb_policy])
visible_A, visible_B = randomize_labels(ucb_policy, uniform_peer)

session = SessionModel(
    session_uuid=uuid.uuid4(),
    evaluation_type="A/B",
    evaluation_location=eval_location,
    evaluator_name=evaluator_email,
    robot_name="DROID",
    policyA_name=visible_A.unique_policy_name,
    policyB_name=visible_B.unique_policy_name,
    evaluation_notes=f"UCB_POLICY={ucb_policy.unique_policy_name}",
)
```

上传路径把 episode 和 session 分开保存。`/upload_eval_data` 根据 session uuid 和 policy letter 解析真实 policy name，保存 command、binary success、partial success、duration、policy IP/port、第三视角相机类型、视频对象存储路径和 `npz` 路径。`/terminate_session` 写入 session completion timestamp，把 evaluator preference 和 long-form feedback 追加到 `evaluation_notes`，并在 valid session 下增加两个策略的 A/B 次数、扣减被采样策略 owner 的 credit、奖励 evaluator credit。

`EpisodeModel` 的创建只保存单个 policy rollout，不保存整次 A/B comparison 的 preference。preference 在 session 结束时进入 `SessionModel.evaluation_notes`；这也是数据分析时先按 session 聚合 episodes 的原因。

```python
episode = EpisodeModel(
    session_id=session.id,
    policy_name=policy_name,
    command=form["command"],
    binary_success=int(form["binary_success"]),
    partial_success=float(form["partial_success"]),
    duration=int(form["duration"]),
    gcs_left_cam_path=upload_if_present("video_left"),
    gcs_right_cam_path=upload_if_present("video_right"),
    gcs_wrist_cam_path=upload_if_present("video_wrist"),
    npz_file_path=upload_if_present("npz_file"),
    policy_ip=form["policy_ip"],
    policy_port=int(form["policy_port"]),
    third_person_camera_type=form["third_person_camera_type"],
)
```

## 数据表与 artifacts

后端 schema 的核心对象是 `UserModel`、`PolicyModel`、`SessionModel` 和 `EpisodeModel`。`PolicyModel` 保存 policy name、IP、port、open-source flag、A/B 次数、owner email 和 robot arm type。`SessionModel` 保存 session uuid、evaluation location、evaluator、robot name、A/B policy names 和 evaluation notes。`EpisodeModel` 保存单个 policy rollout 的 command、success fields、duration、视频路径、`npz` 路径、policy endpoint 和第三视角相机信息。

episode artifacts 把分数还原到现场材料。left/right/wrist videos 记录外部视角和腕部视角，`npz` 保存每步 `cartesian_position`、`joint_position`、`gripper_position` 和实际执行 action。leaderboard 或 A/B evaluation UI 可以从 database 取出 session、preference、long-form feedback 和视频 URL，把一个 ranking 判断追溯到具体 rollout。

## 接口风险

远程 policy server 让策略提交方保留推理环境，但也把网络、端口转发、policy server 版本和 action space 声明带入评测。policy server 如果声明两个 external cameras，而 evaluator 站点只有一个对应相机，client 会终止该 session。网络防火墙或 websocket 连接失败会导致 policy assignment 或 rollout 无法完成。远程推理延迟在静态桌面 manipulation 中影响可能较小，但动态任务或高频控制任务会更敏感。

接口配置也会影响结果解释。同一个策略在不同图像分辨率、wrist camera 需求、external camera 数量、stereo 设置、action space 和 action chunk 长度下，可能表现不同。RoboArena 的结果材料至少应能回到 policy server config、client version、session id、camera ids、action space、partial success、preference 和 episode videos。

## 小结

RoboArena 的系统接口把策略推理保持在远程 policy server，把真实机器人控制保持在 evaluator client。central server 只调度 session、检查可用策略、维护 credit 和保存结果；episode artifacts 则把 preference ranking 连接到视频、本体状态和动作记录。这个拆分支持分布式参与，ranking 解释也会同时受到 policy server contract、evaluation client 运行循环、session 有效性和上传材料完整性约束。

## 导航

- 返回上级：[RoboArena](../02-roboarena-benchmark.md)
- 上一页：[分布式评测协议](01-decentralized-protocol.md)
- 下一页：[preference ranking 与分数口径](03-preference-ranking-and-scores.md)
