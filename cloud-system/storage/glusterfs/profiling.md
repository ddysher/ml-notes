<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Prerequisites](#prerequisites)
  - [Information](#information)
  - [Installation](#installation)
- [Sequential write](#sequential-write)
  - [Raw device (fio)](#raw-device-fio)
  - [Replicated volume (fio)](#replicated-volume-fio)
  - [Simple "dd" result](#simple-dd-result)
- [Sequential read](#sequential-read)
  - [Raw device (fio)](#raw-device-fio-1)
  - [Replicated volume (fio)](#replicated-volume-fio-1)
- [Random write](#random-write)
  - [Raw device](#raw-device)
  - [Replicated volume](#replicated-volume)
- [Random read](#random-read)
  - [Raw device](#raw-device-1)
  - [Replicaed volume](#replicaed-volume)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Prerequisites

## Information

- Hardware: 4CPU, 8G Memory, 500G HDD
- OS: ubuntu 16.04.02.
- Kernel: 4.4.0-62-generic
- GlusterFS: 3.10.3

Disk write parameters using the following commands:

```
iops & lat: "cd /export/bricks && sudo sync; sudo fio --name=test --filename=test --size=128M --ioengine=libaio --direct=1 --bs=4k   --iodepth=1 --readwrite=randwrite"
throughput: "cd /export/bricks && sudo sync; sudo fio --name=test --filename=test --size=1G   --ioengine=libaio --direct=1 --bs=512k --iodepth=1 --readwrite=write"
```

- ubuntu-1: iops(139), lat(7.15ms), throughput(103338KB/s)
- ubuntu-2: iops(455), lat(2.18ms), throughput(99475KB/s)
- ubuntu-3: iops(248), lat(4.02ms), throughput(105970KB/s)

## Installation

**Create lvm device and brick directory**

On each host, create a logical volume, e.g. on ubuntu-1:

```
sudo lvcreate -L 20G -n lvtest ubuntu-1-vg
sudo mkfs.xfs /dev/ubuntu-1-vg/lvtest
sudo mkdir -p /export/bricks/brick1 && sudo mount -t xfs /dev/ubuntu-1-vg/lvtest /export/bricks
```

**Install and start glusterfs**

```
sudo add-apt-repository ppa:gluster/glusterfs-3.10
sudo apt-get install glusterfs-server
sudo systemctl start glusterfs-server.service

# On any of the servers, e.g. on 192.168.3.51
sudo gluster peer probe 192.168.3.52
sudo gluster peer probe 192.168.3.53
```

**Create and mount a replicated volume**

```
# On server machines
deyuan@ubuntu-1:~$ sudo gluster volume create testvol replica 3 transport tcp 192.168.3.51:/export/bricks/brick1 192.168.3.52:/export/bricks/brick1 192.168.3.53:/export/bricks/brick1
deyuan@ubuntu-1:~$ sudo gluster volume start testvol

# On client machine (not sure why "mount -t glusterfs 192.168.3.51:/testvol /mnt/glusterfs" is not working)
sudo mkdir -p /mnt/glusterfs && sudo glusterfs --volfile-id=/testvol --volfile-server=192.168.3.51 /mnt/glusterfs
```

**fio output**

An example fio test on raw device of ubuntu-1:

```
deyuan@ubuntu-1:~$ sudo sync; sudo fio --name=write --filename=/export/bricks/test --ioengine=libaio --iodepth=1 --rw=write --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
write: (g=0): rw=write, bs=4K-4K/4K-4K/4K-4K, ioengine=libaio, iodepth=1
...
fio-2.2.10
Starting 4 processes
write: Laying out IO file(s) (1 file(s) / 10240MB)
Jobs: 3 (f=3): [W(1),_(1),W(2)] [94.7% done] [0KB/294.7MB/0KB /s] [0/75.5K/0 iops] [eta 00m:10s]
write: (groupid=0, jobs=4): err= 0: pid=2536: Sat Aug  5 16:11:55 2017
  write: io=40960MB, bw=234699KB/s, iops=58674, runt=178710msec
    slat (usec): min=1, max=87870, avg=64.52, stdev=972.94
    clat (usec): min=0, max=5922, avg= 0.48, stdev= 3.14
     lat (usec): min=2, max=87872, avg=65.22, stdev=973.09
    clat percentiles (usec):
     |  1.00th=[    0],  5.00th=[    0], 10.00th=[    0], 20.00th=[    0],
     | 30.00th=[    0], 40.00th=[    0], 50.00th=[    0], 60.00th=[    1],
     | 70.00th=[    1], 80.00th=[    1], 90.00th=[    1], 95.00th=[    1],
     | 99.00th=[    1], 99.50th=[    1], 99.90th=[    3], 99.95th=[    3],
     | 99.99th=[    9]
    bw (KB  /s): min=20439, max=620736, per=25.47%, avg=59775.63, stdev=50394.49
    lat (usec) : 2=99.72%, 4=0.24%, 10=0.04%, 20=0.01%, 50=0.01%
    lat (usec) : 100=0.01%, 250=0.01%, 500=0.01%
    lat (msec) : 4=0.01%, 10=0.01%
  cpu          : usr=2.57%, sys=14.57%, ctx=4256637, majf=0, minf=48
  IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued    : total=r=0/w=10485760/d=0, short=r=0/w=0/d=0, drop=r=0/w=0/d=0
     latency   : target=0, window=0, percentile=100.00%, depth=1

Run status group 0 (all jobs):
  WRITE: io=40960MB, aggrb=234698KB/s, minb=234698KB/s, maxb=234698KB/s, mint=178710msec, maxt=178710msec

Disk stats (read/write):
    dm-2: ios=0/18197, merge=0/0, ticks=0/25313632, in_queue=25414292, util=98.82%, aggrios=35/18132, aggrmerge=1/533, aggrticks=6412/25211632, aggrin_queue=25321112, aggrutil=98.82%
  sda: ios=35/18132, merge=1/533, ticks=6412/25211632, in_queue=25321112, util=98.82%
```

Output:
- Test runs for 178710msec, for a total of 58674 iops (each io is 4KB).
- Total size is 40960 MB (roughly equals 234698x178.6).
- Average throughput is 234698KB/s (roughly equals 58674x4KB).
- Average completion latency (clat) is 65.22 us.

**Notes**

Since we are testing filesystem, we need to set fio's direct parameter to 0. Also, file size is set
to an amount (10G) larger than memory (8G) to minimize cache impact.

# Sequential write

## Raw device (fio)

Command:

```
sudo sync; sudo fio --name=write --filename=/export/bricks/test --ioengine=libaio --iodepth=1 --rw=write --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- ubuntu-1: throughput(236832KB/s), lat(0.48us), iops(59208)
- ubuntu-2: throughput(245077KB/s), lat(0.48us), iops(61269)
- ubuntu-3: throughput(193077KB/s), lat(0.47us), iops(48269)

## Replicated volume (fio)

```
sudo sync; sudo fio --name=write --filename=/mnt/glusterfs/test --ioengine=libaio --iodepth=1 --rw=write --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- gluster: throughput(1849KB/s), clat(2.39us), iops(462)

## Simple "dd" result

Command:

```
dd if=/dev/zero of=/mnt/glusterfs/testfile bs=128M count=1 oflag=direct
dd if=/dev/zero of=/mnt/glusterfs/testfile bs=4k count=10000 oflag=direct
dd if=/dev/zero of=/mnt/glusterfs/testfile bs=512 count=10000 oflag=direct
```

- For raw device, command results are: 100 MB/s, 1.160s, 3.37s
- For replicated, command results are: 4.0 MB/s, 10.51s, 1.32s

First two command results are the same as "fio"; but third command output is interesting, not exactly sure why.

# Sequential read

## Raw device (fio)

Command:

```
sudo sync; sudo fio --name=write --filename=/export/bricks/test --ioengine=libaio --iodepth=1 --rw=read --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- ubuntu-1: throughput(377019KB/s), lat(0.63us), iops(94254)
- ubuntu-2: throughput(378619KB/s), lat(0.64us), iops(94654)
- ubuntu-3: throughput(403624KB/s), lat(0.63us), iops(100906)

## Replicated volume (fio)

Command:

```
sudo sync; sudo fio --name=write --filename=/mnt/glusterfs/test --ioengine=libaio --iodepth=1 --rw=read --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- gluster:  throughput(11980KB/s), clat(1.02us), iops(2995)

# Random write

## Raw device

Command:

```
sudo sync; sudo fio --name=randwrite --filename=/export/bricks/test --ioengine=libaio --iodepth=1 --rw=randwrite --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- ubuntu-1: throughput(7392KB/s), lat(0.57us), iops(1848)
- ubuntu-2: throughput(7559KB/s), lat(0.61us), iops(1889)
- ubuntu-3: throughput(9334KB/s), lat(0.60us), iops(2333)

## Replicated volume

Command:

```
sudo sync; sudo fio --name=randwrite --filename=/mnt/glusterfs/test --ioengine=libaio --iodepth=1 --rw=randwrite --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- gluster: throughput(879KB/s), lat(1.72us), iops(219)

# Random read

## Raw device

Command:

```
sudo sync; sudo fio --name=randwrite --filename=/export/bricks/test --ioengine=libaio --iodepth=1 --rw=randread --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- ubuntu-1: TBD
- ubuntu-2: TBD
- ubuntu-3: TBD

## Replicaed volume

```
sudo sync; sudo fio --name=randwrite --filename=/mnt/glusterfs/test --ioengine=libaio --iodepth=1 --rw=randread --bs=4k --direct=0 --size=10240M --numjobs=4 --runtime=240 --group_reporting
```

- gluster: TBD

# References

For hdd device profile information, see "code/learning/linux/performance".
