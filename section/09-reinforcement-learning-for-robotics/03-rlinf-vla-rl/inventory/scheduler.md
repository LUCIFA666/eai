# RLINF 文件索引：scheduler

覆盖 `scheduler` 分组，共 `48` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/scheduler/__init__.py` | 62 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | channel, cluster, collective, hardware, manager, placement, worker |
| `rlinf/scheduler/channel/__init__.py` | 18 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | channel, channel_worker |
| `rlinf/scheduler/channel/channel.py` | 648 | 集群、worker、placement、channel 调度 | Channel | - | asyncio, cluster, collective, placement, ray, typing, uuid, worker |
| `rlinf/scheduler/channel/channel_worker.py` | 536 | 集群、worker、placement、channel 调度；远程 worker 执行单元 | WeightedItem, PeekQueue, LocalChannel, ChannelWorker | - | asyncio, channel, dataclasses, gc, typing, worker |
| `rlinf/scheduler/cluster/__init__.py` | 36 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | cluster, config, node, utils |
| `rlinf/scheduler/cluster/cluster.py` | 966 | 集群、worker、placement、channel 调度 | ClusterEnvVar, PathEnvMergeMode, Cluster | - | config, enum, importlib, logging, node, omegaconf, os, packaging |
| `rlinf/scheduler/cluster/config.py` | 602 | 集群、worker、placement、channel 调度；配置/参数定义 | NodeGroupEnvConfig, NodeGroupConfig, NsightConfig, ClusterConfig | - | dataclasses, hardware, omegaconf, typing, utils, yaml |
| `rlinf/scheduler/cluster/node.py` | 560 | 集群、worker、placement、channel 调度 | NodeInfo, NodeGroupInfo, NodeProbe, _RemoteNodeProbe | - | config, dataclasses, hardware, os, ray, sys, typing, warnings |
| `rlinf/scheduler/cluster/utils.py` | 637 | 集群、worker、placement、channel 调度；公共入口/工具 | DistributedRayLogCollector, DataclassProtocol | without_http_proxies, load_user_extension_module, parse_rank_config, dataclass_arg_check, extract_dataclass_tensor_fields, unflatten_dataclass_tensor_fields | atexit, contextlib, dataclasses, importlib, logging, os, pathlib, re |
| `rlinf/scheduler/collective/__init__.py` | 36 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | async_work, collective, collective_group |
| `rlinf/scheduler/collective/async_work.py` | 420 | 集群、worker、placement、channel 调度 | AsyncWork, AsyncFuncWork, AsyncCollWork, AsyncChannelWork, AsyncChannelCommWork, AsyncRayWork | - | asyncio, concurrent, ray, threading, time, torch, typing, worker |
| `rlinf/scheduler/collective/collective.py` | 96 | 集群、worker、placement、channel 调度 | Collective | - | cluster, collective_group, manager, time, typing, worker |
| `rlinf/scheduler/collective/collective_group.py` | 2430 | 集群、worker、placement、channel 调度 | TensorData, CollectiveGroupOptions, CollectiveWorkQueue, CollectiveGroup | - | async_work, cluster, contextlib, dataclasses, io, itertools, logging, manager |
| `rlinf/scheduler/collective/multi_channel_pg.py` | 927 | 集群、worker、placement、channel 调度 | MultiChannelProcessGroup | - | async_work, collective_group, datetime, hardware, logging, torch, typing |
| `rlinf/scheduler/dynamic_scheduler/__init__.py` | 13 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | - |
| `rlinf/scheduler/dynamic_scheduler/manager.py` | 1069 | 集群、worker、placement、channel 调度 | - | - | - |
| `rlinf/scheduler/dynamic_scheduler/scheduler_worker.py` | 129 | 集群、worker、placement、channel 调度；远程 worker 执行单元 | SchedulerWorker | - | omegaconf, rlinf |
| `rlinf/scheduler/dynamic_scheduler/utils.py` | 162 | 集群、worker、placement、channel 调度；公共入口/工具 | RolloutReport, RolloutAction, RolloutScheduleInfo, _DynamicSchedulerState | get_valid_dp_sizes, get_scheduler_channel, get_scheduler_request_queue, get_scheduler_response_queue, set_global_scheduer_state, get_global_scheduer_state | dataclasses, enum, omegaconf, typing |
| `rlinf/scheduler/hardware/__init__.py` | 55 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | accelerators, hardware, robots |
| `rlinf/scheduler/hardware/accelerators/__init__.py` | 31 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | accelerator, amd_gpu, ascend_npu, intel_gpu, musa_gpu, nvidia_gpu |
| `rlinf/scheduler/hardware/accelerators/accelerator.py` | 299 | 集群、worker、placement、channel 调度 | AcceleratorType, AcceleratorManager, Accelerator, AcceleratorUtil | - | enum, hardware, torch, typing |
| `rlinf/scheduler/hardware/accelerators/amd_gpu.py` | 143 | 集群、worker、placement、channel 调度 | AMDGPUManager | - | accelerator, os, ray, typing |
| `rlinf/scheduler/hardware/accelerators/ascend_npu.py` | 120 | 集群、worker、placement、channel 调度 | AscendNPUManager | - | accelerator, os, ray, typing |
| `rlinf/scheduler/hardware/accelerators/intel_gpu.py` | 113 | 集群、worker、placement、channel 调度 | IntelGPUManager | - | accelerator, os, ray, typing |
| `rlinf/scheduler/hardware/accelerators/musa_gpu.py` | 147 | 集群、worker、placement、channel 调度 | MUSAGPUManager | - | accelerator, os, typing |
| `rlinf/scheduler/hardware/accelerators/nvidia_gpu.py` | 203 | 集群、worker、placement、channel 调度 | NvidiaGPUManager | - | accelerator, os, ray, typing, warnings |
| `rlinf/scheduler/hardware/hardware.py` | 180 | 集群、worker、placement、channel 调度 | HardwareConfig, NodeHardwareConfig, HardwareInfo, HardwareResource, Hardware | - | dataclasses, typing, yaml |
| `rlinf/scheduler/hardware/robots/__init__.py` | 32 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | dosw1, dual_franka, franka, gim_arm, xsquare |
| `rlinf/scheduler/hardware/robots/dosw1.py` | 115 | 集群、worker、placement、channel 调度 | DOSW1HWInfo, DOSW1Robot, DOSW1HWConfig | - | __future__, dataclasses, hardware, typing |
| `rlinf/scheduler/hardware/robots/dual_franka.py` | 158 | 集群、worker、placement、channel 调度 | DualFrankaHWInfo, DualFrankaRobot, DualFrankaConfig | - | __future__, dataclasses, hardware, ipaddress, typing |
| `rlinf/scheduler/hardware/robots/franka.py` | 236 | 集群、worker、placement、channel 调度 | FrankaHWInfo, FrankaRobot, FrankaConfig | - | dataclasses, hardware, importlib, ipaddress, typing, warnings |
| `rlinf/scheduler/hardware/robots/gim_arm.py` | 134 | 集群、worker、placement、channel 调度 | GimArmHWInfo, GimArmRobot, GimArmConfig | - | dataclasses, hardware, os, typing, warnings |
| `rlinf/scheduler/hardware/robots/xsquare.py` | 86 | 集群、worker、placement、channel 调度 | Turtle2HWInfo, Turtle2Robot, Turtle2Config | - | dataclasses, hardware, typing |
| `rlinf/scheduler/manager/__init__.py` | 32 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | coll_manager, lock_manager, manager, node_manager, worker_manager |
| `rlinf/scheduler/manager/coll_manager.py` | 140 | 集群、worker、placement、channel 调度 | CollectiveGroupInfo, CollectiveManager | - | manager, typing, worker_manager |
| `rlinf/scheduler/manager/lock_manager.py` | 187 | 集群、worker、placement、channel 调度 | WorkerDeviceLock, DeviceLockManager, PortLockManager | - | asyncio, cluster, collections, manager, threading, time, worker_manager |
| `rlinf/scheduler/manager/manager.py` | 145 | 集群、worker、placement、channel 调度 | ManagerProxy, Manager | - | cluster, os, ray, time, typing |
| `rlinf/scheduler/manager/node_manager.py` | 46 | 集群、worker、placement、channel 调度 | NodeManager | - | cluster, manager, typing |
| `rlinf/scheduler/manager/worker_manager.py` | 318 | 集群、worker、placement、channel 调度；远程 worker 执行单元 | WorkerAddress, WorkerInfo, WorkerNode, WorkerManager | - | bisect, dataclasses, hardware, manager |
| `rlinf/scheduler/placement/__init__.py` | 27 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | flexible, node, packed, placement |
| `rlinf/scheduler/placement/flexible.py` | 277 | 集群、worker、placement、channel 调度 | FlexiblePlacementStrategy | - | cluster, hardware, placement, typing |
| `rlinf/scheduler/placement/node.py` | 205 | 集群、worker、placement、channel 调度 | NodePlacementStrategy | - | cluster, placement, typing |
| `rlinf/scheduler/placement/packed.py` | 335 | 集群、worker、placement、channel 调度 | PackedPlacementStrategy | - | cluster, hardware, placement, typing |
| `rlinf/scheduler/placement/placement.py` | 674 | 集群、worker、placement、channel 调度 | MultiNodeGroupResolver, Placement, PlacementStrategy, ComponentPlacement | - | cluster, dataclasses, hardware, logging, omegaconf, typing |
| `rlinf/scheduler/worker/__init__.py` | 24 | 集群、worker、placement、channel 调度；公共入口/工具 | - | - | worker, worker_group |
| `rlinf/scheduler/worker/lock.py` | 103 | 集群、worker、placement、channel 调度 | DeviceLock, PortLock | - | contextlib, manager, worker |
| `rlinf/scheduler/worker/worker.py` | 1232 | 集群、worker、placement、channel 调度；远程 worker 执行单元 | WorkerMeta, Worker | - | cluster, contextlib, ctypes, functools, hardware, inspect, logging, manager |
| `rlinf/scheduler/worker/worker_group.py` | 556 | 集群、worker、placement、channel 调度；远程 worker 执行单元 | WorkerGroup, HiddenWorkerGroupFunc, WorkerGroupFunc, WorkerGroupFuncResult | - | asyncio, cluster, dataclasses, hardware, numpy, os, placement, ray |
