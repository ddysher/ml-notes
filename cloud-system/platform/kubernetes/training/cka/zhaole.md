# CKA 考题分享

## 考试范围

The online exam consists of a set of performance-based items (problems) to be solved in a command line running **Version 1.8.2** and candidates have 3 hours to complete the tasks.

The Certification focuses on the skills required to be a successful Kubernetes Administrator in industry today. This includes these general domains and their weights on the exam:

*   Application Lifecycle Management 8%
*   Installation, Configuration & Validation 12%
*   Core Concepts 19%
*   Networking 11%
*   Scheduling 5%
*   Security 12%
*   Cluster Maintenance 11%
*   Logging / Monitoring 5%
*   Storage 7%
*   Troubleshooting 10%

## 考题分类

- 常用运维操作
- 核心概念
- 诊断问题
- 集群部署运维操作
- 网络
- 存储

## 真题分析

### 常用运维操作

- x ［日志］查找某个 pod 的日志，过滤与关键字 X 相关的所有日志，并保存输出到指定位置
- x ［操作］找出包含某个 label 的所有 pod，并保存输出到指定位置
- x ［操作］deployment 的升级回滚
- x ［操作］某个节点不可用或者需要下线运维，需要1.节点不能再调度任务上去；2.节点上现存的服务也需要迁移	Tips: kubectl drain
- x ［操作］统计不可用节点的数量
- x ［操作］找出某类 pod，并按照 pod 名字排序
- x ［操作］找出某类 pv，并按照 pv 名字排序
- x ［操作］列出 node

### 核心概念

- x ［pv］创建一个 pv，需要挂载宿主机某个目录（hostpath）
- x ［secret］创建一个 secret，以文件形式挂载到 pod A；以 env 形式传给 pod B
- x ［init container］需要修改某个应用的 yaml，达到每次应用运行前，先在指定目录创建一个文件（注：这里的路径通过 volume 与 init 容器共享）
- x ［static pod］创建一个 pod，会有一个描述需求，最后会需要使用 static pod 来做
- x ［daemonset］提供一个需求创建应用，或者明确要求创建一个 daemonset
- x ［pod］创建一个 pod，包含多个容器
- x ［job］创建一个 job，输出一个字符串，然后跑 n 个，并行度 m ，跑完确保 pod 状态是 completed
- x ［dns］通过 nslookup 查找某个服务的 ip；通过 nsloopup 查找某个 pod 的 ip；需要在宿主机上查询，所以需要先找到 dns service 的 ip。 Tips：kubernetes fqdn
- x ［service］创建一个服务，关联到指定应用。
- x ［node selector］调度某个应用到指定节点


### 诊断问题

- x ［kubelet］提供一个集群环境，需要自己诊断制定服务为什么不工作；这里可能是
	- `kubectl get node` 看不到 node，kubelet 没跑起来
- x ［service］某个服务不可用，最后检查后发现是 iptables 的原因，然后发现是一个 daemonset 在干坏事，删了这个 daemonset 服务就恢复了
- x ［controller］某个应用／服务没起来，查看后发现 pod 不存在，deployment 存在，最后检查发现是 kube controller 没起来，把服务跑起来就 ok 了

### 集群部署运维操作（难题／费时间）

- x nodes 存在，配置好 master 。给出了证书，还有 k8s 源码 tar 包，binary 还要自己获取。
- x master 存在，配置好 node
- x 把集群 auth 改成 https ，master 和 node 配置都需要改
- x 提供集群，部署整个集群


### 网络

- x ［网络策略］有一个安全的 namespace，里面默认的网络策略是 deny，现在需要允许 pod A 能访问 pod B 的特定协议端口（注：1.8 networkpolicy 有大的改动）
- x ［ingress］部署 ingress controller 这个给出了 yaml ，配置 ingress，并用域名访问

### 存储

- x 给 pod 添加 pvc

## Tips

- 需要有英文的证件
- 在 chrome 上，全程会开摄像头，并分享屏幕
- 考试前先把其他程序退掉
- 考试环境需要桌面没其他东西
- 可以来一个新的 tab 查资料
- 考试页面左边是题目，右边是 ssh 终端
- 默认在一个跳板机上，记得切换环境
- 保存到指定地方文件，需要 sudo
- 注意熟悉系统环境和 k8s 版本
- 题目有操作题，有写 yaml 保存到指定位置，有给某个操作的结果保存到文件
- 题目，顺序和难度无关
- 有个 nodepad 可以保存笔记什么的
- 题目不一定直接对应到 k8s 的某个概念
- 诊断类问题，通常指给一个环境，问题描述比较简单，需要自己查原因
- 确保在正确的集群上操作
- 熟悉 systemctl journalctl 等命令
- web ssh 操作要熟悉，多行复制可能有问题
- 熟悉 yaml 怎么写，好多写 yaml 的，预先找找哪里有快速参考 yaml 模板
- 网络稳，自备翻墙
- 大部分题目很快可以做完，先把这些做了，部署题、调试题放最后
