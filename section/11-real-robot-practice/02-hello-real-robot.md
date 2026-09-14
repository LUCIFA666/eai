# Hello Real Robot：最小真机闭环

本节是真机实战的 Hello World：不训练任何模型，只完成一次最小闭环——连接机器人、读取关节状态、发送一个低速安全动作、读取相机图像、保存一帧 observation、回到 home pose。代码使用 LeRobot 统一的 Robot 抽象接口，核心四个方法 `robot.connect()` / `get_observation()` / `send_action()` / `disconnect()` 即可覆盖全流程。本节提供两个版本：DummyRobot 让你在没有硬件的情况下也能理解控制循环的每一环；SO-ARM 真机实现则面向 LeRobot 生态下的低成本舵机臂。读完本节应能清晰说出 `observation → action → state update` 这条闭环中数据如何流动。

参考：LeRobot 统一 Robot 接口与 Bring Your Own Hardware 教程 https://huggingface.co/docs/lerobot/integrate_hardware 。

## 最小真机闭环流程

一次不依赖模型的最小闭环可以用不到十行伪代码表达：连接机器人，读取当前 observation，据此产生 action，下发执行，最后断开连接。使用 LeRobot 统一的 Robot 接口后，Dummy 与真机之间切换只改变实例化时的类名，上层逻辑完全一致。

```python
from lerobot.robots.utils import make_robot_from_config

config = SO101FollowerConfig(port="/dev/ttyACM0")
robot = make_robot_from_config(config)
robot.connect()
obs = robot.get_observation()
action = policy(obs)         # 或手动构造低速安全 action
robot.send_action(action)
robot.disconnect()
```

## DummyRobot：无硬件理解控制循环

DummyRobot 模拟一个 6 关节臂加 1 台相机，内部维护虚拟关节位置。它不依赖任何真实硬件，任何输入动作都会被裁剪到 [-1.0, 1.0] 范围并按 0.01 的步长积分更新关节角，同时返回一张全黑图像作为虚拟相机画面。这个极简实现足以让你在部署真机之前逐行调试控制循环：`connect()` 之后调用 `get_observation()` 拿到初始状态，手动构造一组小数值的 action 传给 `send_action()`，再调用一次 `get_observation()` 观察关节角的变化，验证状态更新是否符合预期。

```python
import numpy as np

class DummyRobot:
    def __init__(self):
        self.joint_pos = [0.0] * 6
        self.connected = False

    def connect(self):
        self.connected = True
        print("DummyRobot connected (no hardware)")

    def get_observation(self):
        return {
            "joint_pos": self.joint_pos.copy(),
            "image": np.zeros((480, 640, 3), dtype=np.uint8)
        }

    def send_action(self, action):
        for i in range(6):
            self.joint_pos[i] = max(-1.0, min(1.0, self.joint_pos[i] + 0.01 * action[i]))

    def disconnect(self):
        self.connected = False
```

## SO-ARM 真机实现

SO-ARM（SO-100/SO-101）是 LeRobot 官方原生支持的低成本舵机臂，使用 Feetech 串口总线舵机驱动，3D 打印臂体。LeRobot 源码中 `lerobot/robots/so_follower/` 目录下提供了完整的 `SOFollower` 实现，以下按源码结构拆解配置类与 Robot 子类的关键部分。完成子类后，标定、遥操作和数据录制均由 LeRobot 命令行工具接管，无需自行编写采集主循环。完整的遥操作技巧、数据采集注意事项和故障排查见第 6 章 SO-ARM 适配页。

## 配置类

`SOFollowerRobotConfig` 同时继承 `RobotConfig`（提供 `id` 和 `calibration_dir`）与 `SOFollowerConfig`（提供串口、电机与相机参数），并通过 `@RobotConfig.register_subclass` 装饰器同时注册为 `so100_follower` 和 `so101_follower` 两个类型名。LeRobot 的命令行工具会依据 `--robot.type` 参数自动匹配对应的配置类并实例化。`cameras` 字段接收一个字典，键为相机名称，值为任意 `CameraConfig` 子类实例（如 `OpenCVCameraConfig`），`make_cameras_from_configs` 会根据类型自动创建对应的相机驱动。

```python
from dataclasses import dataclass, field
from lerobot.robots.config import RobotConfig
from lerobot.cameras.configs import CameraConfig

@dataclass
class SOFollowerConfig:
    port: str
    disable_torque_on_disconnect: bool = True
    max_relative_target: float | dict[str, float] | None = None
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    use_degrees: bool = True

@RobotConfig.register_subclass("so101_follower")
@RobotConfig.register_subclass("so100_follower")
@dataclass
class SOFollowerRobotConfig(RobotConfig, SOFollowerConfig):
    pass
```

## Robot 子类实现

`SOFollower` 继承 LeRobot 的 `Robot` 基类，核心是在 `__init__` 中组装两条数据链路：`FeetechMotorsBus` 负责通过串口与 6 个 Feetech STS3215 舵机通信（肩部 pan/lift、肘部 flex、腕部 flex/roll、夹爪），`make_cameras_from_configs` 根据配置字典创建相机实例。`observation_features` 和 `action_features` 使用 `cached_property` 缓存，以字典形式声明各字段的名称与数据类型——前者包含 6 个关节位置键和若干相机图像键，后者仅包含 6 个关节位置键。Motor 的 `norm_mode` 在 `use_degrees=True`（默认）时采用 `MotorNormMode.DEGREES` 角度模式，夹爪始终使用 `RANGE_0_100`。

`get_observation()` 通过 `bus.sync_read("Present_Position")` 一次性读取全部舵机的当前位置，再逐相机调用 `read_latest()` 获取最新图像帧，所有数据合并为一个扁平的 observation 字典。`send_action()` 将 action 字典中带 `.pos` 后缀的键值提取出来，去掉后缀后组装为目标位置字典。如果配置了 `max_relative_target`，会先读取当前位置并调用 `ensure_safe_goal_position` 对相对位移做安全裁剪，防止单步动作过大；最后通过 `bus.sync_write("Goal_Position", ...)` 统一下发，并返回实际发送的 action 字典。

```python
from functools import cached_property
from lerobot.robots.robot import Robot
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode
from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.cameras import make_cameras_from_configs

class SOFollower(Robot):
    config_class = SOFollowerRobotConfig
    name = "so_follower"

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        norm_mode_body = MotorNormMode.DEGREES if config.use_degrees else MotorNormMode.RANGE_M100_100
        self.bus = FeetechMotorsBus(
            port=config.port,
            motors={
                "shoulder_pan":  Motor(1, "sts3215", norm_mode_body),
                "shoulder_lift": Motor(2, "sts3215", norm_mode_body),
                "elbow_flex":    Motor(3, "sts3215", norm_mode_body),
                "wrist_flex":    Motor(4, "sts3215", norm_mode_body),
                "wrist_roll":    Motor(5, "sts3215", norm_mode_body),
                "gripper":       Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self.calibration,
        )
        self.cameras = make_cameras_from_configs(config.cameras)

    @cached_property
    def observation_features(self):
        return {
            **{f"{motor}.pos": float for motor in self.bus.motors},
            **{cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
               for cam in self.cameras}
        }

    @cached_property
    def action_features(self):
        return {f"{motor}.pos": float for motor in self.bus.motors}

    @property
    def is_connected(self):
        return self.bus.is_connected and all(cam.is_connected for cam in self.cameras.values())

    def connect(self, calibrate=True):
        self.bus.connect()
        if not self.is_calibrated and calibrate:
            self.calibrate()
        for cam in self.cameras.values():
            cam.connect()
        self.configure()

    @property
    def is_calibrated(self):
        return self.bus.is_calibrated

    def calibrate(self):
        # 若已有标定文件，询问用户是否沿用；否则重新标定并保存
        # 详见 lerobot/robots/so_follower/so_follower.py
        pass

    def configure(self):
        with self.bus.torque_disabled():
            self.bus.configure_motors()
            for motor in self.bus.motors:
                self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
                self.bus.write("P_Coefficient", motor, 16)

    def get_observation(self):
        obs_dict = self.bus.sync_read("Present_Position")
        obs_dict = {f"{motor}.pos": val for motor, val in obs_dict.items()}
        for cam_key, cam in self.cameras.items():
            obs_dict[cam_key] = cam.read_latest()
        return obs_dict

    def send_action(self, action):
        goal_pos = {key.removesuffix(".pos"): val for key, val in action.items() if key.endswith(".pos")}
        if self.config.max_relative_target is not None:
            present_pos = self.bus.sync_read("Present_Position")
            goal_pos = ensure_safe_goal_position(
                {k: (goal_pos[k], present_pos[k]) for k in goal_pos},
                self.config.max_relative_target
            )
        self.bus.sync_write("Goal_Position", goal_pos)
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}

    def disconnect(self):
        self.bus.disconnect()
        for cam in self.cameras.values():
            cam.disconnect()

SO100Follower = SOFollower
SO101Follower = SOFollower
```

`FeetechMotorsBus` 封装了串口通信协议与 STS3215 舵机的控制表，`sync_read` 和 `sync_write` 方法通过 `GroupSyncRead`/`GroupSyncWrite` 指令一次性操作全部舵机，避免了逐个轮询的延迟。`configure()` 在扭矩关闭的安全状态下写入 P 系数等 PID 参数，夹爪额外限制了最大扭矩和保护电流以防烧毁。

## 标定、遥操作与数据采集

完成 Robot 子类后，标定、遥操作和数据录制均通过 LeRobot 命令行工具完成。标定的目的是让 leader 臂和 follower 臂在相同物理位置时读数一致——先调用 `set_half_turn_homings` 将各关节当前位置设为零点中点，再通过 `record_ranges_of_motion` 手动转动各关节记录运动范围，最终生成的 `MotorCalibration` 同时写入舵机 EEPROM 和本地 JSON 文件（路径为 `~/.cache/huggingface/lerobot/calibration/robots/<name>/<id>.json`）。如果需要重新标定，删除对应 JSON 文件后重新运行标定命令，或在终端提示时输入 `c` 进入重新标定流程。

```bash
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm

lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm
```

遥操作命令将 leader 臂的关节角实时映射到 follower 臂，同时显示相机画面。拖动 leader 臂即可控制 follower 执行抓取、放置等动作。`--robot.cameras` 参数以 YAML 内联格式指定相机配置，包括类型、设备索引、分辨率和帧率。相机应优先使用 USB 3.0 接口直连电脑，多个相机避免共用一个 USB HUB，否则带宽不足会导致帧率下降甚至无法读取。

```bash
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.cameras='{wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}' \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --display_data=true
```

数据录制时指定任务描述、episode 数量和每个 episode 的时长，LeRobot 自动管理时间戳对齐并以 HDF5 格式存储。`get_observation()` 每次被调用时同时读取关节位置和相机图像，框架层面保证同一帧内各数据来源的时间一致性。数据集默认保存在 `~/.cache/huggingface/lerobot/data/<repo_id>` 下，不要事先手动创建该目录。录制过程中可以使用键盘方向键控制流程：右箭头提前结束当前 episode 进入下一个，左箭头舍弃当前 episode 重新录制，ESC 停止会话。如果操作中途不慎将物体碰落或出现明显失败动作，按左箭头即可丢弃该段数据，避免污染数据集。正式采集前建议先只开遥操作练习几次，将动作练熟后再开始录制。

```bash
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.cameras='{wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}' \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --dataset.repo_id=data/test \
    --dataset.num_episodes=5 \
    --dataset.single_task="Put the blue ball into the bowl" \
    --dataset.episode_time_s=30
```
