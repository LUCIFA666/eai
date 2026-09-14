# SimpleVLA-RL 文件索引：single-controller

覆盖 `single-controller` 分组，共 `17` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/single_controller/__init__.py` | 20 | Ray/worker group 控制层；公共入口/工具 | - | - | os |
| `verl/single_controller/base/__init__.py` | 16 | Ray/worker group 控制层；公共入口/工具 | - | - | worker, worker_group |
| `verl/single_controller/base/decorator.py` | 410 | Ray/worker group 控制层 | Dispatch, Execute | _split_args_kwargs_data_proto, dispatch_one_to_all, dispatch_all_to_all, collect_all_to_all, dispatch_megatron_compute, collect_megatron_compute, dispatch_megatron_compute_data_proto, _concat_data_proto_or_future, collect_megatron_compute_data_proto, dispatch_megatron_pp_as_dp | enum, functools, types, typing, verl |
| `verl/single_controller/base/dp.py` | 47 | Ray/worker group 控制层 | DPEngineWorker | - | verl |
| `verl/single_controller/base/megatron/__init__.py` | 13 | Ray/worker group 控制层；公共入口/工具 | - | - | - |
| `verl/single_controller/base/megatron/worker.py` | 39 | Ray/worker group 控制层；远程 worker 执行单元 | MegatronWorker | - | dataclasses, os, verl |
| `verl/single_controller/base/megatron/worker_group.py` | 51 | Ray/worker group 控制层；远程 worker 执行单元 | MegatronWorkerGroup | - | typing, verl, worker |
| `verl/single_controller/base/register_center/__init__.py` | 13 | Ray/worker group 控制层；公共入口/工具 | - | - | - |
| `verl/single_controller/base/register_center/ray.py` | 29 | Ray/worker group 控制层 | WorkerGroupRegisterCenter | create_worker_group_register_center | ray |
| `verl/single_controller/base/worker.py` | 181 | Ray/worker group 控制层；远程 worker 执行单元 | DistRankInfo, DistGlobalInfo, WorkerHelper, WorkerMeta, Worker | - | dataclasses, os, socket, verl |
| `verl/single_controller/base/worker_group.py` | 196 | Ray/worker group 控制层；远程 worker 执行单元 | ResourcePool, ClassWithInitArgs, WorkerGroup | check_workers_alive | logging, signal, threading, time, typing, verl |
| `verl/single_controller/ray/__init__.py` | 16 | Ray/worker group 控制层；公共入口/工具 | - | - | base, megatron |
| `verl/single_controller/ray/base.py` | 457 | Ray/worker group 控制层 | RayResourcePool, RayClassWithInitArgs, RayWorkerGroup | get_random_string, func_generator, extract_pg_from_exist, merge_resource_pool, _bind_workers_method_to_parent, _unwrap_ray_remote, create_colocated_worker_cls | os, ray, time, typing, unittest, verl |
| `verl/single_controller/ray/decorator.py` | 65 | Ray/worker group 控制层 | - | maybe_remote | functools, json, os, ray, verl |
| `verl/single_controller/ray/dist_data_pass_protocol.py` | 23 | Ray/worker group 控制层；数据读取/组织 | DistDataProto | - | ray, tensordict, verl |
| `verl/single_controller/ray/dp.py` | 93 | Ray/worker group 控制层 | RefBasicRayActor, DPEngineRayWorkerGroup | - | ray, verl |
| `verl/single_controller/ray/megatron.py` | 62 | Ray/worker group 控制层 | NVMegatronRayWorkerGroup, MegatronRayWorkerGroup | - | base, ray, typing, verl |
