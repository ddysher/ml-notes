<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Kubernetes](#kubernetes)
- [How calico and flannel fit together](#how-calico-and-flannel-fit-together)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 04/13/2017*

Canal is a community-driven initiative that aims to allow users to easily deploy Calico and Flannel
networking together as a unified networking solution - combining Calico's industry-leading network
policy enforcement with the rich superset of Calico and flannel overlay and non-overlay network
connectivity options.

# Kubernetes

*Date: 04/13/2017, calico v2.1, flannel 0.7.0*

- https://github.com/projectcalico/canal/blob/2d42923c8e4d81698f50f9f17989906127c32c11/InstallGuide.md
- https://github.com/projectcalico/canal/tree/2d42923c8e4d81698f50f9f17989906127c32c11/k8s-install

This is very similar to 'calico with kubernetes', see calico.md. One option is to setup an etcd
cluster; run a policy controller to translate kubernetes API object to calico API object and save to
etcd cluster; then felix watches that etcd cluster to update policies. The other option is to have
felix watches kubernetes API directly; thus eliminating the requirement of etcd cluster. In either
option, calico BGP networking needs to be turned off (by seeting `CALICO_NETWORKING_BACKEND` environment
variable to 'none'), and have flannel provide container connectivity.

Below are canal config and pod yaml file from a kubernetes cluster using canal:

```
[root@c1v41 ~]# cat /etc/cni/net.d/10-calico.conf
{
    "name": "k8s-pod-network",
    "type": "calico",
    "log_level": "info",
    "datastore_type": "kubernetes",
    "hostname": "kube-master-1",
    "ipam": {
        "type": "host-local",
        "subnet": "usePodCidr"
    },
    "policy": {
        "type": "k8s",
        "k8s_auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkZWZhdWx0LXRva2VuLXpveThxIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImRlZmF1bHQiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJlNWRlZTJhNi1kZmYwLTExZTYtOGQwNS01MjU0MDBkOTg3YmQiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06ZGVmYXVsdCJ9.l3aHAY1WNj_rS-lZ4sM6O6ssJBuELLBb-xFi2jVzeWleAeFBbgo9KX0SQ_KglcI58XDNVopNzSqaequdbIck0tubinvtksBL0D_tMT7C_kRcSxf_3k3MyVwLr3TKilNW94Hs-6ani7ox2Iwo2AUUthGzI48zo_qMufMVy48qiN1fFpGGfCwRbl5Ax4aXaEQUDTxL8-34EpHwFUdiPB626YLWzTaUWWqFqbXC3DQJMimWLIMXmSE5Bt1siOBxTv1RqQlJ1RowAwfZ9xvQOnRtj8lYhfP0bzJXQouMmxDFuNiCFM6_hyHeDo5tPXM6cpysIz7XuU521lNko0sEEAwHuA"
    },
    "kubernetes": {
        "k8s_api_root": "https://10.254.0.1:443",
        "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
    }
}
```

```
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubernetes.io/created-by: |
      {"kind":"SerializedReference","apiVersion":"v1","reference":{"kind":"DaemonSet","namespace":"kube-system","name":"canal","uid":"9dccd453-f5df-11e6-815c-525400d8fcb5","apiVersion":"extensions","resourceVersion":"19483252"}}
    scheduler.alpha.kubernetes.io/critical-pod: ""
    scheduler.alpha.kubernetes.io/tolerations: |
      [{"key": "dedicated", "value": "master", "effect": "NoSchedule" },
       {"key":"CriticalAddonsOnly", "operator":"Exists"}]
  creationTimestamp: 2017-02-18T13:39:08Z
  generateName: canal-
  labels:
    k8s-app: canal
  name: canal-xsts6
  namespace: kube-system
  resourceVersion: "61180532"
  selfLink: /api/v1/namespaces/kube-system/pods/canal-xsts6
  uid: 9f6a5c55-f5df-11e6-815c-525400d8fcb5
spec:
  containers:
  - env:
    - name: DATASTORE_TYPE
      value: kubernetes
    - name: FELIX_LOGSEVERITYSYS
      value: info
    - name: FELIX_DEFAULTENDPOINTTOHOSTACTION
      value: ACCEPT
    - name: FELIX_FELIXHOSTNAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: spec.nodeName
    - name: CALICO_NETWORKING_BACKEND
      value: none
    - name: CALICO_DISABLE_FILE_LOGGING
      value: "true"
    - name: IP
    - name: HOSTNAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: spec.nodeName
    image: cargo.caicloudprivatetest.com/caicloud/calico-node:v1.0.1
    imagePullPolicy: IfNotPresent
    name: calico-node
    resources: {}
    securityContext:
      privileged: true
    terminationMessagePath: /dev/termination-log
    volumeMounts:
    - mountPath: /lib/modules
      name: lib-modules
      readOnly: true
    - mountPath: /var/run/calico
      name: var-run-calico
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-zoy8q
      readOnly: true
  - command:
    - /install-cni.sh
    env:
    - name: CNI_NETWORK_CONFIG
      valueFrom:
        configMapKeyRef:
          key: cni_network_config
          name: canal-config
    - name: KUBERNETES_NODE_NAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: spec.nodeName
    image: cargo.caicloudprivatetest.com/caicloud/calico-cni:v1.5.6
    imagePullPolicy: IfNotPresent
    name: install-cni
    resources: {}
    terminationMessagePath: /dev/termination-log
    volumeMounts:
    - mountPath: /host/opt/cni/bin
      name: cni-bin-dir
    - mountPath: /host/etc/cni/net.d
      name: cni-net-dir
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-zoy8q
      readOnly: true
  - command:
    - /opt/bin/flanneld
    - --ip-masq
    - --kube-subnet-mgr
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.namespace
    - name: FLANNELD_IFACE
      valueFrom:
        configMapKeyRef:
          key: canal_iface
          name: canal-config
    - name: FLANNELD_IP_MASQ
      valueFrom:
        configMapKeyRef:
          key: masquerade
          name: canal-config
    image: cargo.caicloudprivatetest.com/caicloud/flannel:v0.7.0
    imagePullPolicy: IfNotPresent
    name: kube-flannel
    resources: {}
    securityContext:
      privileged: true
    terminationMessagePath: /dev/termination-log
    volumeMounts:
    - mountPath: /run
      name: run
    - mountPath: /etc/kube-flannel/
      name: flannel-cfg
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-zoy8q
      readOnly: true
  dnsPolicy: ClusterFirst
  hostNetwork: true
  nodeName: kube-node-69
  restartPolicy: Always
  securityContext: {}
  serviceAccount: default
  serviceAccountName: default
  terminationGracePeriodSeconds: 30
  volumes:
  - hostPath:
      path: /lib/modules
    name: lib-modules
  - hostPath:
      path: /var/run/calico
    name: var-run-calico
  - hostPath:
      path: /opt/cni/bin
    name: cni-bin-dir
  - hostPath:
      path: /etc/cni/net.d
    name: cni-net-dir
  - hostPath:
      path: /run
    name: run
  - configMap:
      defaultMode: 420
      name: canal-config
    name: flannel-cfg
  - name: default-token-zoy8q
    secret:
      defaultMode: 420
      secretName: default-token-zoy8q
```

# How calico and flannel fit together

Flannel works as usual: it setups a vxlan interface `flannel.1` and watches etcd (or kubernetes) for
leases. Calico-cni also works as usual: it is called from kubelet to setup pod network, so we can
see there are quite a few interfaces prefixed with `cali`, and specific routes for container.

For example, the following commands show that host `c1v41` has two pods with '10.100.15.26' and '10.100.15.27'
IP addresses. calico-cni uses 'host-local' to allocate addresses. The two routes '10.100.15.26' and
'10.100.15.27' are also setup by calico for the two pods.  For inter-host communication, there is the
route '10.100.0.0/16 dev flannel.1' which is setup by flannel daemon, i.e. if a pod access another
pod on the same host, use the specific route from calico; if accessing another pod on different host,
use flannel vxlan interface.

```
[root@c1v41 ~]# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
    link/ether 52:54:00:d8:fc:b5 brd ff:ff:ff:ff:ff:ff
    inet 192.168.16.41/20 brd 192.168.31.255 scope global ens3
       valid_lft forever preferred_lft forever
    inet 192.168.18.60/32 scope global ens3:vip
       valid_lft forever preferred_lft forever
    inet6 fe80::5054:ff:fed8:fcb5/64 scope link
       valid_lft forever preferred_lft forever
3: ens4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
    link/ether 52:54:00:70:f8:b1 brd ff:ff:ff:ff:ff:ff
4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN
    link/ether 02:42:f1:5a:7e:91 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 scope global docker0
       valid_lft forever preferred_lft forever
5: cali8bbc6be0dd2@if3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether ae:ee:c8:81:7d:1b brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet6 fe80::acee:c8ff:fe81:7d1b/64 scope link
       valid_lft forever preferred_lft forever
6: calie0d5b744072@if3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 8e:f7:37:51:f7:3f brd ff:ff:ff:ff:ff:ff link-netnsid 1
    inet6 fe80::8cf7:37ff:fe51:f73f/64 scope link
       valid_lft forever preferred_lft forever
7: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN
    link/ether d6:7a:7a:93:1b:1c brd ff:ff:ff:ff:ff:ff
    inet 10.100.15.0/32 scope global flannel.1
       valid_lft forever preferred_lft forever

[root@c1v41 ~]# ip r
default via 192.168.16.1 dev ens3  proto static  metric 100
10.100.0.0/16 dev flannel.1
10.100.15.26 dev cali8bbc6be0dd2  scope link
10.100.15.27 dev calie0d5b744072  scope link
172.17.0.0/16 dev docker0  proto kernel  scope link  src 172.17.0.1
192.168.16.0/20 dev ens3  proto kernel  scope link  src 192.168.16.41  metric 100
```
