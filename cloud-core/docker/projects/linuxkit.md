<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 05/21/2017, no official release yet*

[LinuxKit](https://github.com/linuxkit/linuxkit) is a toolkit for building custom minimal, immutable
Linux distributions. LinuxKit uses the moby tool for image builds, and the linuxkit tool for pushing
and running VM images.

**Build binaries**

Just clone linuxkit and run `make`, we'll have three binarie: `sbin/rtf`, `bin/moby` and `bin/linuxkit`.

**Build bootable images**

Use moby tool to convert yaml specification into one or more bootable images. Here, we run `moby build`
with linuxkit.yml (an example config under root):

```
$ moby build linuxkit.yml
Extract kernel image: linuxkit/kernel:4.9.x
Pull image: linuxkit/kernel:4.9.x
Add init containers:
Process init image: linuxkit/init:cbd7ae748f0a082516501a3e914fa0c924ee941e
Pull image: linuxkit/init:cbd7ae748f0a082516501a3e914fa0c924ee941e
Process init image: linuxkit/runc:24dfe632ed3ff53a026ee3fac046fd544434e2d6
Pull image: linuxkit/runc:24dfe632ed3ff53a026ee3fac046fd544434e2d6
Process init image: linuxkit/containerd:1c71f95fa36040ea7e987deb98a7a2a363853f01
Pull image: linuxkit/containerd:1c71f95fa36040ea7e987deb98a7a2a363853f01
Process init image: linuxkit/ca-certificates:4e9a83e890e6477dcd25029fc4f1ced61d0642f4
Pull image: linuxkit/ca-certificates:4e9a83e890e6477dcd25029fc4f1ced61d0642f4
Add onboot containers:
  Create OCI config for linuxkit/sysctl:2cf2f9d5b4d314ba1bfc22b2fe931924af666d8c
  Create OCI config for linuxkit/binfmt:548f7f044f5411a8938913527c5ce55d9876bb07
  Create OCI config for linuxkit/dhcpcd:cb96c09a33c166eca6530f166f0f79927c3e83b0
Add service containers:
  Create OCI config for linuxkit/rngd:c97ef16be340884a985d8b025983505a9bcc51f0
  Create OCI config for nginx:alpine
Add files:
  etc/docker/daemon.json
Create outputs:
  linuxkit-kernel linuxkit-initrd.img linuxkit-cmdline
  linuxkit.iso
  linuxkit-efi.iso
```

<details><summary>Yaml file</summary><p>

```yaml
kernel:
  image: "linuxkit/kernel:4.9.x"
  cmdline: "console=ttyS0 console=tty0 page_poison=1"
init:
  - linuxkit/init:cbd7ae748f0a082516501a3e914fa0c924ee941e
  - linuxkit/runc:24dfe632ed3ff53a026ee3fac046fd544434e2d6
  - linuxkit/containerd:1c71f95fa36040ea7e987deb98a7a2a363853f01
  - linuxkit/ca-certificates:4e9a83e890e6477dcd25029fc4f1ced61d0642f4
onboot:
  - name: sysctl
    image: "linuxkit/sysctl:2cf2f9d5b4d314ba1bfc22b2fe931924af666d8c"
    net: host
    pid: host
    ipc: host
    capabilities:
     - CAP_SYS_ADMIN
    readonly: true
  - name: binfmt
    image: "linuxkit/binfmt:548f7f044f5411a8938913527c5ce55d9876bb07"
    binds:
     - /proc/sys/fs/binfmt_misc:/binfmt_misc
    readonly: true
  - name: dhcpcd
    image: "linuxkit/dhcpcd:cb96c09a33c166eca6530f166f0f79927c3e83b0"
    binds:
     - /var:/var
     - /tmp/etc:/etc
    capabilities:
     - CAP_NET_ADMIN
     - CAP_NET_BIND_SERVICE
     - CAP_NET_RAW
    net: host
    command: ["/sbin/dhcpcd", "--nobackground", "-f", "/dhcpcd.conf", "-1"]
services:
  - name: rngd
    image: "linuxkit/rngd:c97ef16be340884a985d8b025983505a9bcc51f0"
    capabilities:
     - CAP_SYS_ADMIN
    oomScoreAdj: -800
    readonly: true
  - name: nginx
    image: "nginx:alpine"
    capabilities:
     - CAP_NET_BIND_SERVICE
     - CAP_CHOWN
     - CAP_SETUID
     - CAP_SETGID
     - CAP_DAC_OVERRIDE
    net: host
files:
  - path: etc/docker/daemon.json
    contents: '{"debug": true}'
trust:
  image:
    - linuxkit/kernel
    - linuxkit/binfmt
    - linuxkit/rngd
outputs:
  - format: kernel+initrd
  - format: iso-bios
  - format: iso-efi
```

</p></details></br>

This will create a number of OS formats that you can run on various platforms. Under the hood, moby
extracts contents from given images, e.g. linuxkit/kernel:4.9.x,  linuxkit/init:cbd7ae748f0a082516501a3e914fa0c924ee941e,
etc. It then outputs the combined data to whatever formats we required:

```
$ ls -lh linuxkit*
-rw-r--r--  1 deyuandeng  staff    40B May 21 19:31 linuxkit-cmdline
-rw-r--r--  1 deyuandeng  staff    41M May 21 19:32 linuxkit-efi.iso
-rw-r--r--  1 deyuandeng  staff    33M May 21 19:31 linuxkit-initrd.img
-rw-r--r--  1 deyuandeng  staff   7.2M May 21 19:31 linuxkit-kernel
-rw-r--r--  1 deyuandeng  staff    41M May 21 19:32 linuxkit.iso
-rw-r--r--  1 deyuandeng  staff   1.6K May 20 15:54 linuxkit.yml

linuxkit-state:
total 16
srwxr-xr-x  1 deyuandeng  staff     0B May 21 21:14 @connect
-rw-r--r--  1 deyuandeng  staff   1.3K May 21 21:14 hyperkit.json
-rw-r--r--  1 deyuandeng  staff     5B May 21 21:14 hyperkit.pid
```

Note that internally, moby creates a large tarball representing all the images; but selectively (using
tar header) outputs data based on output format. `linuxkit-kernel` size is relavant to kernel section
and `linuxkit-initrd.img` size is relavant to init, onboot, services and files section.

**Run linuxkit VM**

Now it's possible to run the custom kernel with (the second linuxkit is the name of our build in
`moby build`, which is first part of `linuxkit.yml`):

```
$ linuxkit run linuxkit
......
......
Welcome to LinuxKit

                        ##         .
                  ## ## ##        ==
               ## ## ## ## ##    ===
           /"""""""""""""""""\___/ ===
      ~~~ {~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~
           \______ o           __/
             \    \         __/
              \____\_______/


/ # [    2.157791] tsc: Refined TSC clocksource calibration: 1990.566 MHz
[    2.158295] clocksource: tsc: mask: 0xffffffffffffffff max_cycles: 0x3962bca1aaa, max_idle_ns: 881590412723 ns
[    2.210771] IPVS: Creating netns size=2104 id=1
[    2.211253] IPVS: ftp: loaded support on port[0] = 21
[    2.450907] IPVS: Creating netns size=2104 id=2
[    2.451505] IPVS: ftp: loaded support on port[0] = 21
```

Under the hood, linuxkit passes the build artifacts from above step to vm backend, e.g. for hyperkit
on mac os, it passes:

```go
h.Kernel = prefix + "-kernel"
h.Initrd = prefix + "-initrd.img"
```

*References*

- https://medium.com/contino-io/dockers-linuxkit-2c460769f522
- http://www.nebulaworks.com/blog/2017/04/23/getting-started-linuxkit-mac-os-x-xhyve/
