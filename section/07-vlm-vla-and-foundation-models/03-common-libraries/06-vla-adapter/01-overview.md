# 认识 VLA-Adapter

目标：了解本模块如何从概念、架构、源码和学习路线四个角度认识 VLA-Adapter。

进入安装、训练和评测之前，可以先通过这几页对 VLA-Adapter 有一个整体印象：它关注什么问题，主要组件如何衔接，源码大致分布在哪里，后续章节适合按什么顺序阅读。

配置和排查细节会放到后续章节展开。这里先区分两条主线：LIBERO eval 用于 benchmark 验证，policy server 用于部署接口验证。

## 学习路径

| 页面 | 这一页解决什么 | 阅读线索 |
| --- | --- | --- |
| [VLA-Adapter 是什么](01-overview/01-what-is-vla-adapter.md) | 先理解 VLA-Adapter 关注的问题 | 方法定位、condition、Policy |
| [架构与组件](01-overview/02-architecture-and-components.md) | 再看架构图里的组件关系 | VLM、Bridge Attention、proprio、action chunk |
| [代码地图](01-overview/03-code-map.md) | 找到主要源码入口 | 数据、模型、训练、评测、部署 |
| [学习路线图](01-overview/04-roadmap.md) | 安排后续阅读顺序 | 跑通闭环、理解组件、训练、评测、部署 |

## 先形成几个判断

读完这几页后，可以先形成几个基本判断：

- VLA-Adapter 关注视觉语言表征如何进入动作策略。
- 架构组件和源码入口可以分开看，先理解组件关系，再去代码地图里找文件。
- 训练、评测和部署分别在后续章节展开，遇到具体问题时可以回到对应页面继续查。
- LIBERO eval 和 policy server 角色不同，一个用于 benchmark 验证，一个用于部署接口验证。

## 导航

- 上一节：[VLA-Adapter](../06-vla-adapter.md)
- 返回上级：[VLA-Adapter](../06-vla-adapter.md)
- 下一节：[VLA-Adapter 是什么](01-overview/01-what-is-vla-adapter.md)
