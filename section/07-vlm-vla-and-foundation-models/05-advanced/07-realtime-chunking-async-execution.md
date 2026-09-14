# 实时分块与异步执行

本节介绍 action chunking 在真机部署时的执行时间轴问题与解法：开环执行窗口内环境已经变化、chunk 切换处的动作抖动、推理延迟挤占控制周期。Real-Time Chunking（RTC）一类方法把 chunk 生成视为带 inpainting 的实时补全问题，在执行当前 chunk 的同时生成下一个 chunk，并保证边界一致性；异步推理则把模型推理与动作执行解耦到不同线程/进程。

## 需要覆盖

- Action chunking 的执行语义：开环窗口、重规划频率与延迟预算的关系。
- RTC：实时分块的问题设定、soft masking / inpainting 式衔接、对高延迟的鲁棒性；参考 Physical Intelligence "Real-Time Action Chunking" https://www.pi.website/research/real_time_chunking 。
- 异步推理：SmolVLA 的 async inference 设计（见常用库 LeRobot/SmolVLA 页），queue 深度与丢帧策略。
- 切换抖动的度量与验收：边界处速度/加速度连续性、任务成功率对延迟注入的敏感性曲线。
- 与本章部署推理一节（延迟预算、推理加速）的分工：那边讲"算得快"，本节讲"接得稳"。
