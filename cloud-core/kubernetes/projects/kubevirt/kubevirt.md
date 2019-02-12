<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 10/03/2018, v0.8.0*

kubevirt is created from RedHat.

kubevirt provides virtualization API and runtime in Kubernetes, in order to define and manage virtual
machines. kubevirt extends Kubernetes API with three CRDs:
- VirtualMachine (vm)
- VirtualMachineInstance (vmi)
- VirtualMachineInstanceReplicaSet
- VirtualMachinePreset

kubevirt only provides virtualization functionality, while scheduling, networking, and storage are
all delegated to Kubernetes. kubevirt contains four core components:
- virt-api: run as deployment, api gateway
- virt-controller: run as deployment, cluster-wide component
- virt-handler: run as daemontset
- virt-launcher (with libvirtd): one per VM, running in Pod, i.e. VM is created inside of a Pod

# Experiment

Components after installing kubevirt:

```
$ kubectl get pods -n kube-system
kube-dns-7b479ccbc6-5nrhw          3/3       Running   0          4h
virt-api-79c6f4d756-msf4x          1/1       Running   0          4h
virt-api-79c6f4d756-n85zc          1/1       Running   0          4h
virt-controller-559c749968-5zrgz   1/1       Running   0          4h
virt-controller-559c749968-hb488   1/1       Running   0          4h
virt-handler-b6s5r                 1/1       Running   0          4h
```

Now that since we didn't create vm, there is no virt-launcher pod. If we launch a VM and start it,
we'll see a launcher pod:

```
$ kubectl apply -f https://raw.githubusercontent.com/kubevirt/demo/master/manifests/vm.yaml
$ kubectl get pods
No resources found.
$ kubectl get vm
NAME      AGE
testvm    4h
$ kubectl get vmi
No resources found.

$ ./virtctl start testvm

$ kubectl get pods
NAME                         READY     STATUS    RESTARTS   AGE
virt-launcher-testvm-8lwv8   2/2       Running   0          4h
$ kubectl get vm
NAME      AGE
testvm    4h
$ kubectl get vmi
NAME      AGE
testvm    4h

$ kubectl exec -it virt-launcher-testvm-8lwv8 -c compute bash
[root@testvm /]# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  13940  2920 ?        Ss   03:39   0:07 /bin/bash /usr/share/kubevirt/virt-launcher/entrypoint.sh --qemu-timeout 5m --name testvm --uid e4204803-c6bd-11e8-9fba-2c4d54ed3845 --namespace default --kubevirt-share-dir /var/run/kubevirt --readiness-fil
root        11  0.0  0.2 2012860 41364 ?       Sl   03:39   0:09 virt-launcher --qemu-timeout 5m --name testvm --uid e4204803-c6bd-11e8-9fba-2c4d54ed3845 --namespace default --kubevirt-share-dir /var/run/kubevirt --readiness-file /tmp/healthy --grace-period-seconds 45 --h
root        25  0.0  0.0  13940  2984 ?        S    03:39   0:00 /bin/bash /usr/share/kubevirt/virt-launcher/libvirtd.sh
root        26  0.0  0.0 144868  9876 ?        S    03:39   0:00 /usr/sbin/virtlogd -f /etc/libvirt/virtlogd.conf
root        39  0.0  0.2 1751200 37668 ?       Sl   03:39   0:00 /usr/sbin/libvirtd
qemu       207  0.0  0.5 2382320 96356 ?       Sl   03:40   0:08 /usr/bin/qemu-system-x86_64 -machine accel=kvm -name guest=default_testvm,debug-threads=on -S -object secret,id=masterKey0,format=raw,file=/var/lib/libvirt/qemu/domain-1-default_testvm/master-key.aes -machin
root      7257  0.0  0.0  13940  2980 pts/1    Ss+  08:00   0:00 /bin/bash /usr/share/kubevirt/virt-launcher/sock-connector /var/run/kubevirt-private/e4204803-c6bd-11e8-9fba-2c4d54ed3845/virt-serial0
root      7275  0.0  0.0  27172  2196 pts/1    S+   08:00   0:00 socat unix-connect://var/run/kubevirt-private/e4204803-c6bd-11e8-9fba-2c4d54ed3845/virt-serial0 stdio,cfmakeraw
root     11523  0.0  0.0  16992  3656 pts/0    Ss   08:15   0:00 bash
root     11546  0.0  0.0  22948  1296 ?        S    08:15   0:00 /usr/bin/coreutils --coreutils-prog-shebang=sleep /usr/bin/sleep 1
root     11547  0.0  0.0  48840  3668 pts/0    R+   08:15   0:00 ps aux
```

Following is the example yaml content:

<details><summary>vm.yaml content</summary><p>

```yaml
apiVersion: kubevirt.io/v1alpha2
kind: VirtualMachine
metadata:
  name: testvm
spec:
  running: false
  selector:
    matchLabels:
      guest: testvm
  template:
    metadata:
      labels:
        guest: testvm
        kubevirt.io/size: small
    spec:
      domain:
        devices:
          disks:
            - name: registrydisk
              volumeName: registryvolume
              disk:
                bus: virtio
            - name: cloudinitdisk
              volumeName: cloudinitvolume
              disk:
                bus: virtio
      volumes:
        - name: registryvolume
          registryDisk:
            image: kubevirt/cirros-registry-disk-demo
        - name: cloudinitvolume
          cloudInitNoCloud:
            userDataBase64: SGkuXG4=
---
apiVersion: kubevirt.io/v1alpha2
kind: VirtualMachineInstancePreset
metadata:
  name: small
spec:
  selector:
    matchLabels:
      kubevirt.io/size: small
  domain:
    resources:
      requests:
        memory: 64M
    devices: {}
```

</p></details></br>

Following is vm pod yaml, pay attention that network & storage are all managed via Kubernetes:

<details><summary>detailed vm pod yaml</summary><p>

```yaml
$ kubectl get pods -n default virt-launcher-testvm-8lwv8 -o yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubevirt.io/domain: testvm
    kubevirt.io/owned-by: virt-handler
  creationTimestamp: 2018-10-03T03:39:11Z
  generateName: virt-launcher-testvm-
  labels:
    guest: testvm
    kubevirt.io: virt-launcher
    kubevirt.io/created-by: e4204803-c6bd-11e8-9fba-2c4d54ed3845
    kubevirt.io/size: small
  name: virt-launcher-testvm-8lwv8
  namespace: default
  resourceVersion: "2612"
  selfLink: /api/v1/namespaces/default/pods/virt-launcher-testvm-8lwv8
  uid: e421de6f-c6bd-11e8-9fba-2c4d54ed3845
spec:
  containers:
  - command:
    - /entry-point.sh
    env:
    - name: COPY_PATH
      value: /var/run/libvirt/kubevirt-ephemeral-disk/registry-disk-data/default/testvm/disk_registryvolume/disk-image
    image: kubevirt/cirros-registry-disk-demo
    imagePullPolicy: IfNotPresent
    name: volumeregistryvolume
    readinessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      failureThreshold: 5
      initialDelaySeconds: 2
      periodSeconds: 5
      successThreshold: 2
      timeoutSeconds: 5
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/run/libvirt
      name: libvirt-runtime
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-b2vzv
      readOnly: true
  - command:
    - /usr/share/kubevirt/virt-launcher/entrypoint.sh
    - --qemu-timeout
    - 5m
    - --name
    - testvm
    - --uid
    - e4204803-c6bd-11e8-9fba-2c4d54ed3845
    - --namespace
    - default
    - --kubevirt-share-dir
    - /var/run/kubevirt
    - --readiness-file
    - /tmp/healthy
    - --grace-period-seconds
    - "45"
    - --hook-sidecars
    - "0"
    image: docker.io/kubevirt/virt-launcher:v0.8.0
    imagePullPolicy: IfNotPresent
    name: compute
    readinessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      failureThreshold: 5
      initialDelaySeconds: 2
      periodSeconds: 2
      successThreshold: 1
      timeoutSeconds: 5
    resources:
      limits:
        devices.kubevirt.io/kvm: "1"
        devices.kubevirt.io/tun: "1"
      requests:
        devices.kubevirt.io/kvm: "1"
        devices.kubevirt.io/tun: "1"
        memory: "161679432"
    securityContext:
      capabilities:
        add:
        - NET_ADMIN
      privileged: false
      runAsUser: 0
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/run/kubevirt
      name: virt-share-dir
    - mountPath: /var/run/libvirt
      name: libvirt-runtime
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-b2vzv
      readOnly: true
  dnsPolicy: ClusterFirst
  hostname: testvm
  nodeName: 127.0.0.1
  nodeSelector:
    kubevirt.io/schedulable: "true"
  priority: 0
  restartPolicy: Never
  schedulerName: default-scheduler
  securityContext:
    runAsUser: 0
    seLinuxOptions:
      type: spc_t
  serviceAccount: default
  serviceAccountName: default
  terminationGracePeriodSeconds: 60
  tolerations:
  - effect: NoExecute
    key: node.kubernetes.io/not-ready
    operator: Exists
    tolerationSeconds: 300
  - effect: NoExecute
    key: node.kubernetes.io/unreachable
    operator: Exists
    tolerationSeconds: 300
  volumes:
  - hostPath:
      path: /var/run/kubevirt
      type: ""
    name: virt-share-dir
  - emptyDir: {}
    name: libvirt-runtime
  - name: default-token-b2vzv
    secret:
      defaultMode: 420
      secretName: default-token-b2vzv
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: 2018-10-03T03:39:11Z
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: 2018-10-03T03:40:02Z
    status: "True"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: null
    status: "True"
    type: ContainersReady
  - lastProbeTime: null
    lastTransitionTime: 2018-10-03T03:39:11Z
    status: "True"
v    type: PodScheduled
  containerStatuses:
  - containerID: docker://6eb634b2c5ec85633afe855051729acb4b25b3ef63a231b32fd6a55d7a04162a
    image: kubevirt/virt-launcher:v0.8.0
    imageID: docker-pullable://kubevirt/virt-launcher@sha256:e631f3f5f5d4f5dac369a227e6a86169afcbf86c2426dd590d145dafc7ad02e2
    lastState: {}
    name: compute
    ready: true
    restartCount: 0
    state:
      running:
        startedAt: 2018-10-03T03:39:50Z
  - containerID: docker://61212797207b7815275bb8883310519d4aaf516add1c5dfe23803bc7989b044b
    image: kubevirt/cirros-registry-disk-demo:latest
    imageID: docker-pullable://kubevirt/cirros-registry-disk-demo@sha256:936840c4117283e21fce4445602a211bb686496c8d29a501b8cd84825509a896
    lastState: {}
    name: volumeregistryvolume
    ready: true
    restartCount: 0
    state:
      running:
        startedAt: 2018-10-03T03:39:26Z
  hostIP: 127.0.0.1
  phase: Running
  podIP: 172.17.0.8
  qosClass: Burstable
  startTime: 2018-10-03T03:39:11Z
```

</p></details></br>

*References*

- [architecture](https://github.com/kubevirt/kubevirt/blob/v0.8.0/docs/architecture.md)
- [commponents](https://github.com/kubevirt/kubevirt/blob/v0.8.0/docs/components.md)
- [demo for v0.8.0](https://github.com/kubevirt/demo/tree/c4209aa0f81773b283f2bcafb79fa0b31693d62a)
- https://kubevirt.io/
- https://kubernetes.io/blog/2018/07/27/kubevirt-extending-kubernetes-with-crds-for-virtualized-workloads/
- https://opensource.com/article/18/3/you-got-your-vm-my-container
