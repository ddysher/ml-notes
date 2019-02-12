## Docker resource management

- [CFS Bandwidth Control](https://www.kernel.org/doc/Documentation/scheduler/sched-bwc.txt)
- [Resource Management in Docker](https://goldmann.pl/blog/2014/09/11/resource-management-in-docker/)

#### CPU Share

CGroups does not limit the processes upfront (for example by not allowing them
to run fast, even if there are free resources). Instead it gives as much as it
can and limits only when necessary (for example when many processes start to
use the CPU heavily at the same time).

When people talk about CPU time, it is not specific to any individual CPU time.
On a system with 8 CPUs (4 core x 2 HT), one can use up to 800% CPU time.

CPU share is a relative weight and has nothing to do with the actual processor
speed. This value does not mean anything, when speaking of it alone. Also, share
enforcement will only take place when the processes are run on the same core.
This means that if you pin one container to the first core and the other container
to the second core, both will use 100% of each core, even if they have different
CPU share value set. Default share is 1024.

For example, on a machine with 8 CPUs, if we run:

```
docker run -it --rm fedora:stress --cpu 4
docker run -it --rm fedora:stress --cpu 4
```

*Both* will use around 400% (<400% considering other processes) of CPU time. And
if we adjust CPU share of one container, *both* will use similar CPU time, since
we haven't used up all CPU time yet, kernel is able to schedule task to different
CPUs. Remember share only has meaning when running on the same core.

```
docker run -it --rm -c 512 fedora:stress --cpu 4
docker run -it --rm fedora:stress --cpu 4
```

Now if we change stress to use 8 CPUs, in the second case, the first container
can only use 266% while the second container can use 533% (assuming no other
processes). The CPU usages can be best visualized via `systemd-cgtop`.

#### CPU affinity

In the above experiment, stress is not pinned on any CPU. In fact, a single process
can switch between different CPUs quite often (use htop, press F2, then add 'CPU'
column). For example, htop shows `chrome` process runs on different CPU every few
seconds.

We can use following command to set cpu affinity:

```
docker run -it --rm --cpuset-cpus 0 --cpu-shares 512 fedora:stress --cpu 1
```

The process will use 100% of CPU 0. Use `htop` to see CPU load. If we run another
container on CPU 1, then no matter the value of share, it will use 100% of CPU 1;
share matters only when we also ping the second container to CPU 0.

#### CPU Period and Quota

- `cpu.cfs_quota_us`: the total available run-time within a period (in microseconds)
- `cpu.cfs_period_us`: the length of a period (in microseconds)
- `cpu.stat`: exports throttling statistics

The default values are:
- cpu.cfs_period_us = 100ms
- cpu.cfs_quota = -1

To limit a group to 2 CPUs worth of runtime on a multi-CPU machine. We can set
500ms period and 1000ms quota, the group can get 2 CPUs worth of runtime every
500ms.

```
# echo 1000000 > cpu.cfs_quota_us /* quota = 1000ms */
# echo 500000 > cpu.cfs_period_us /* period = 500ms */
```

The larger period here allows for increased burst capacity.

#### Memory

A container can use all of the memory on the host with the default settings. Use
`-m` option to limit memory usage in docker:

```
docker run -it --rm -m 128m fedora:stress --vm 1 --vm-bytes 128M --vm-hang 0
```

The above container will run without problem. If we see the following message, we
need to enable swap limit via kernel configuration (from grub):

```
Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
```

For detail, see [link](https://github.com/moby/moby/issues/847#issuecomment-23306247).
If the configuration is not enabled, memory swap limit is useless; which means if
swap is `on` system-wide, container can use up all swap space; if swap is `off`
then container will be killed as soon as it reached memory limit. swappiness status
can be seen from command `sudo swapon -s`.

By default, docker will set swap limit twice as much as memory limit, thus, this works

```
docker run -it --rm -m 128m fedora:stress --vm 1 --vm-bytes 200M --vm-hang 0
```

while this doesn't:

```
docker run -it --rm -m 128m fedora:stress --vm 1 --vm-bytes 300M --vm-hang 0
```

cgroup info:

```
$ cat /sys/fs/cgroup/memory/docker/a9b361dbe037a7c052869b3c5f353990de471676c8d6d275e9e528acf49a7472/memory.limit_in_bytes
134217728

$ cat /sys/fs/cgroup/memory/docker/a9b361dbe037a7c052869b3c5f353990de471676c8d6d275e9e528acf49a7472/memory.memsw.limit_in_bytes
268435456
```

`memory.memsw.limit_in_bytes` is a sum of memory and swap. This means that Docker
will assign to the container -m amount of memory as well as -m amount of swap.

#### Block IO

`--blkio-weight` is similar to `--cpu-shares`, i.e. relative weight. Some other
options are:

- `--device-read-bps`, restrict read bps of a device
- `--device-write-bps`, restrict write bps of a device
- `--device-read-iops`, restrict read iops of a device
- `--device-write-iops`, restrict write iops of a device

```
$ docker run -it fedora:26 bash
[root@ecbcedcaa83c /]# dd if=/dev/zero of=/root/testfile bs=512M count=1 oflag=direct
1+0 records in
1+0 records out
536870912 bytes (537 MB, 512 MiB) copied, 1.062 s, 506 MB/s
[root@ecbcedcaa83c /]# exit

$ docker run -it --device-write-bps /dev/sda:30MB fedora:26 bash
[root@e456ee502a94 /]# dd if=/dev/zero of=/root/testfile bs=512M count=1 oflag=direct
1+0 records in
1+0 records out
536870912 bytes (537 MB, 512 MiB) copied, 17.1162 s, 31.4 MB/s

$ cat /sys/fs/cgroup/blkio/docker/e456ee502a9454e5c8cd1d27b8466ab1d83308b3cd4abeb93b799aa2cdc92f0c/blkio.throttle.write_bps_device
8:0 31457280
```
