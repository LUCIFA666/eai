# 平台适配页模板

本页是所有平台适配页的写作模板，固定 11 段结构：

1. 适用场景（单臂/双臂/人形/移动操作，推荐与不适合的任务）
2. 硬件清单（机械臂/夹爪/相机/控制电脑/线缆电源）
3. 软件环境（OS、SDK、ROS/ROS2 driver、Python wrapper、firmware）
4. Bring-up（上电、连接、读状态、home、stop、急停恢复）
5. Observation schema（关节/夹爪/相机/力觉）
6. Action schema（控制空间、频率、限幅）
7. 标定（关节零点、TCP、内参、手眼、workspace）
8. 遥操作（推荐设备、控制模式、deadman、reset）
9. 数据采集（record 命令、配置样例、metadata、replay、常见失败）
10. 真机推理（输入输出映射、safety filter、延迟预算）
11. 故障排查（连接/夹爪/掉帧/抖动/延迟）

贡献新平台页时复制本模板逐段填写，缺项明确写"未验证"。
