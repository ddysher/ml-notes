<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [CloudCore](#cloudcore)
  - [EdgeCore](#edgecore)
  - [Mapper](#mapper)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

边缘计算 4 大场景驱动
- 低延迟
- 海量数据
- 隐私安全
- 本地自治

KubeEdge 对边缘计算的观点
- 边缘是云的延伸：云端统一协调
- 云-边双向通信
- 云-边松耦合：边缘自治、去中心化
- 边缘节点异构：设备异构、资源局限

KubeEdge 核心理念
- 云边协同
  - 双向多路复用消息通道，支持边缘节点位于私有网络
  - Websocket + 消息封装，大幅减少通信压力，高时延下仍可正常工作
- 边缘离线自治
  - 节点元数据持久化，实现节点级离线自治
  - 节点故障恢复无需 List-watch，降低网络压力，快速启动
- 极致轻量
  - 重组 Kubelet 功能模块，极致轻量化（～10mb 内存占用）
    - e.g. 移除 static pod、移除内置存储驱动
  - 支持 CRI 集成 Containerd、CRI-O 优化 Runtime 资源消耗

*Reference*

- https://www.bilibili.com/video/BV1LJ411D7t1?p=1

# Architecture

边缘计算的设计抉择？（Kubedge 采用后者）
- Kubernetes 集群整体跑在边缘，即边缘集群（调研显示 30% 用户采用此方案）
- Kubernetes 集群跑在云端，边缘仅运行节点，即边缘节点（调研显示 70% 用户采用此方案）

架构核心分层
- 云端
  - 云端运行完整的 Kubernetes 集群，在其上运行核心组件 CloudCore，本质上是 Kubernetes Operator
  - CloudCore 通过 Kubernetes Deployment 部署，包含多个组件但是是单进程应用
  - CloudCore 管理多个远程节点，其设计类似 VirtualKubelet，即像伪装底层的 Node 资源，但 VirtualKubelet 仅对应一个节点
  - CloudCore 与 EdgeCore 默认通过 WebSocket 通信，同时也可以支持 QUIC 等协议
  - CloudCore 负责维护所有边缘的状态，有三个核心组件（以 Goroutine 运行）：EdgeController、DeviceController 和 CloudHub
    - CloudHub：云边系统的消息化封装，以及 Websocket 通信维护
    - EdgeController：边缘节点管理，以及应用状态（Pod）数据云边协同
    - DeviceController：边缘设备的管理
  - CloudCore 还包含其他组件：Admission Webhook、CSI Driver
  - Kubernetes 控制面不关心底层节点具体运行位置（云端或者边缘）
- 边缘节点
  - 边缘运行 EdgeCore，包括：
    - EdgeHub（与 CloudHub 对等）
    - MetaManager，元数据本地持久化，默认使用 SQLite
    - Edged，即 kubelet-lite
    - DeviceTwin，同步设备信息到云端，例如传感器的值
    - EventBus：MQTT client
    - ServiceBus：HTTP client
  - 支持 CRI+CNI 来支持除 Docker 之外的运行时，存储接入使用 CSI
  - 通过 EdgeMesh 解决断连之后 Pod 之前的通信问题
- 边缘设备
  - 专有设备通过 MQTT 协议通信
  - 边缘设备在 Kubernetes 集群中通过 CRD 表达：
    - DeviceModel：通用设备信息
    - Device：具体表示一个接入的实体，从 DeviceModel 继承

KubeEdge 同时也提供边缘集群方案，取名 EdgeSite，即在边缘运行（轻量化）Kubernetes 集群，支持边缘设备管理。

## CloudCore

**Edge Controller**

Upstream Controller：从下往上同步状态，包括：
- NodeStatus
- PodStatus

Downstream Controller：从上往下同步信息，包括
- Pod
- Secret
- Configmap
- Serivce
- Endpoint

从上往下同步信息，只会同步一部分；不会像 Kubelet 那样 List-watch；基于 websocket，不会全量同步数据，只向节点同步需要的数据，边缘节点可以从本地恢复数据。

EdgeController 发现是自己管理的边缘节点，会调用 CloudHub -> EdgeHub；EdgeHub 看到是 Pod 信息，会发送到 MetaManager 保存本地元数据到 SQLite（理解为 apiserver 子集）；Edged（轻量级 Kubelet）根据 Pod 信息启动容器。

**Device Controller**

管理 DeviceModel & Device CRD；所有的边缘节点与设备通信，需要设备与节点关联。

可以关联多个，如果是幂等操作（比如发送 0 & 1），那么多个节点没有问题。

Upstream Controller
- DeviceStatus
- /DeviceTwin
- /Reported

Downstream Controller
- DeviceInstance
- /DeviceTwin
- /Desired

**CSI Driver**

Master 运行在在云上，存储工作量比较大。做一个 CSI Driver Hook，劫持到消息后去调用边缘节点，而不是边缘节点去 list-watch 云端。

Volume 的创建和挂载，都是在边缘处理。向 Kubernetes External Provisioner 和 External Attacher 伪装一个 CSI Driver；劫持到他们的 CSI 调用后，直接访问 CloudHub，然后通过 EdgeHub 将请求发送给 Edged (with in-tree CSI volume)。后续 Provision 和 Attach 走标准的 CIS 接口。

**CloudHub (and EdgeHub)**

下行，MessageDispatcher 发送至 MessageQueueN，每个边缘节点对应一个 Queue。

上行，直接返回至 EdgeController 或者 DeviceController。

消息封装
- Header
- Router
- Content (Full Kubernetes API Object)

## EdgeCore

每个节点 Proxy，内置解析资源不依赖云端；还可以通过 istio 管理边缘路由。

EdgeCore 组件
- EdgeHub：与 CloudHub 通信
- MetaManager：管理元数据；接收 EdgeHub 信息，持久化之后传递给 Edged
- Edged：轻量级 Kubelet
- DeviceTwin 通过 EdgeStore 持久化，然后与 EventBus 通信。
- EventBus 很简单就是 MQTT Client

MetaManager & Edge & EdgeHub 等上述组件运行在一个进程中（EdgeCore）。

上行
- Edged -> MetaManager -> EdgeHub -> CloudHub
- EventBus -> DeviceTwin -> EdgeHub -> CloudHub
（EventBus 可以直接发送给 EdgeHub，不通过 DeviceTwin，例如图片数据之类，不需要状态汇报）

云边断连的情况下，Edged 将从 MetaManager 拿取数据。

## Mapper

边缘端的 Mapper 是独立运行的组件（非 EdgeCore 一部分）
- 上面对接 MQTT，下面对接 Device（设备支持 MQTT 的话，Mapper 就不需要了）
- Device 中的信息，最终传给 Mapper 使用来连接边缘 Node。
- Mapper 与 EdgeCore 是两个独立的进程；Mapper 包含设备驱动组件，用户可以自定义
- Mappter 运行在边缘节点上，可以连接任何形式的设备，将设备数据转化成 MQTT 协议 Publish 到 MQTT broker 中即可。
- 设备都是挂在边缘节点，与设备相关的操作都是要与节点关联。
- 设备孪生，Desired vs. Reported
  - 有些无 desired，例如温度传感器
