# RGB 相机部署

本节介绍 RGB 相机部署。相机是视觉策略的唯一输入源，安装位置、遮挡、标定、内参直接决定数据质量。

## 1. 相机选型建议

- 推荐 USB3.0 RGB 相机（全局快门优先）：Intel RealSense D435i、Orbbec Astra、普通USB单目相机
- 分辨率与帧率：640x480，30fps
- 大部分主流VLA模型没有深度图的需求，不要求相机有点云采集能力

## 2. 安装位置与数量

常用 SO-Arm 单臂相机配置：

- wrist（腕部）：夹爪正上方，视野随末端移动，适合近距离操作
- front（前方）：固定在底座前方，覆盖整个工作空间
- overhead（顶置）：顶视相机，减少遮挡，适合桌面任务

多相机时需保证至少两个视角能同时看到目标物体。

## 3. 避免遮挡与刚性支架

- 使用 3D 打印或铝型材制作刚性支架，震动幅度 < 0.5mm
- 相机与支架之间加防松螺母或螺纹胶
- 相机与工作台的相对位置要固定，距离和高度不要变化太大

## 4. 内参与连接检查

使用 OpenCV 或相机 SDK 获取内参：

```python
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(frame.shape)  # 确认分辨率
```

相机标定方法参见第四章，如果使用最基本的ACT/DP来进行训练，不需要相机的内参矩阵，在后面的数据采集章节会进行介绍

LeRobot 中普通USB相机配置示例，在后续使用的时候会采用命令行传参数的方法进行相机的配置：

```python
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.configs import ColorMode, Cv2Rotation

# Construct an `OpenCVCameraConfig` with your desired FPS, resolution, color mode, and rotation.
config = OpenCVCameraConfig(
    index_or_path=0,
    fps=15,
    width=1920,
    height=1080,
    color_mode=ColorMode.RGB,
    rotation=Cv2Rotation.NO_ROTATION
)

# Instantiate and connect an `OpenCVCamera`, performing a warm-up read (default).
with OpenCVCamera(config) as camera:

    # Read a frame synchronously — blocks until hardware delivers a new frame
    frame = camera.read()
    print(f"read() call returned frame with shape:", frame.shape)

    # Read a frame asynchronously with a timeout — returns the latest unconsumed frame or waits up to timeout_ms for a new one
    try:
        for i in range(10):
            frame = camera.async_read(timeout_ms=200)
            print(f"async_read call returned frame {i} with shape:", frame.shape)
    except TimeoutError as e:
        print(f"No frame received within timeout: {e}")

    # Instantly return a frame - returns the most recent frame captured by the camera
    try:
        initial_frame = camera.read_latest(max_age_ms=1000)
        for i in range(10):
            frame = camera.read_latest(max_age_ms=1000)
            print(f"read_latest call returned frame {i} with shape:", frame.shape)
            print(f"Was a new frame received by the camera? {not (initial_frame == frame).any()}")
    except TimeoutError as e:
        print(f"Frame too old: {e}")

```

连接后运行检测相机连接效果与实际帧率。

```bash
lerobot-find-cameras opencv # 如果使用Realsense相机的话，换成realsense
```

运行后结果应如下面所示，然后可以在 ~/lerobot/outputs/captured_images 目录中找到每台摄像头拍摄的图片

```bash
--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ 0
  Type: OpenCV
  Id: 0
  Backend api: AVFOUNDATION
  Default stream profile:
    Format: 16.0
    Width: 1920
    Height: 1080
    Fps: 15.0
--------------------
(more cameras ...)
```
