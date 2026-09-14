# 推理服务与运行时

本节介绍如何把训练好的 VLA 接成可调用的推理服务，并对接机器人控制循环。要写清的技术：

- 推理服务 / policy server：client-server 部署（openpi 的 `serve_policy`、LeRobot 的 `PolicyServer`/`RobotClient`）、观测与动作的接口契约。仓库：openpi https://github.com/Physical-Intelligence/openpi ；LeRobot https://github.com/huggingface/lerobot
- 动作运行时：动作分块（action chunking）、观测/动作队列、时序聚合（temporal ensembling）、控制频率匹配
- 异步推理与实时分块：异步推理（async inference，LeRobot）、Real-Time Chunking（RTC）。仓库：RTC https://github.com/Physical-Intelligence/real-time-chunking-kinetix
