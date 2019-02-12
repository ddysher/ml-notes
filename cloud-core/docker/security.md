<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [docker with selinux](#docker-with-selinux)
- [privileged container (device access)](#privileged-container-device-access)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# docker with selinux

**docker processes and files**

All docker container processes will have the same domain `svirt_lxc_net_t`. And each container has a
unique MCS label, e.g. s0:c522,c911. Similarly, files have same type `svirt_sandbox_file_t`, but the
same unique MCS label, see below digest:

     [vagrant@localhost ~]$ sudo docker run -itd nginx:1.13

     [vagrant@localhost ~]$ sudo docker exec -it fe bash
     root@fe907b3aae84:/# ps -Z
     LABEL                             PID TTY          TIME CMD
     system_u:system_r:svirt_lxc_net_t:s0:c522,c911 327 ? 00:00:00 bash
     system_u:system_r:svirt_lxc_net_t:s0:c522,c911 330 ? 00:00:00 ps
     root@fe907b3aae84:/# ls -Z
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 bin   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 lib32                           system_u:object_r:proc_t:s0 proc	system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 tmp
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 boot  system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 lib64   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 root	system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 usr
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 dev   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 libx32  system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 run	system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 var
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 etc   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 media   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 sbin
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 home  system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 mnt     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 srv
     system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 lib   system_u:object_r:svirt_sandbox_file_t:s0:c522,c911 opt                            system_u:object_r:sysfs_t:s0 sys

**docker volume**

By default, mounting host volume to container in selinux enabled system won't work, because of type
enforcement in selinux:

     [vagrant@localhost ~]$ touch /tmp/abc
     [vagrant@localhost ~]$ docker run --rm -it -v /tmp/abc:/tmp/abc ubuntu:16.04
     /root@8e41541610c7:/# cat /tmp/abc
     cat: /tmp/abc: Permission denied

To 'fix' this problem, we can change the type of '/tmp/abc' to container's MCS:

     [vagrant@localhost ~]$ docker inspect 82 | grep Label
             "MountLabel": "system_u:object_r:svirt_sandbox_file_t:s0:c511,c694",
             "ProcessLabel": "system_u:system_r:svirt_lxc_net_t:s0:c511,c694",
                 "Labels": {}
     [vagrant@localhost ~]$ chcon -Rt svirt_sandbox_file_t -l s0:c511,c694 /tmp/abc

After docker 1.7, this is done automatically in docker daemon when mounting, provided we give mount
options to docker:

     [vagrant@localhost ~]$ touch /tmp/xyz
     [vagrant@localhost ~]$ docker run --rm -it -v /tmp/xyz:/tmp/xyz:Z ubuntu:16.04
     /root@aa6e6f6c8ee4:/# cat /tmp/xyz
     /root@aa6e6f6c8ee4:/#

     [vagrant@localhost ~]$ ls -Z /tmp/xyz
     -rw-rw-r--. vagrant vagrant system_u:object_r:svirt_sandbox_file_t:s0:c480,c934 /tmp/xyz

We can see from "ls" output that "/tmp/xyz" file is correctly labeled. Note that we are using `:Z`
option here, which means label the content inside the container with the exact MCS label that the
container run with. This means that the volume cannot be shared with other containers. If we do want
to share it with other containers, then we can use `:z` (lowercase), which will justlabel contents
with "s0" (MCS label is removed).


     [vagrant@localhost ~]$ touch /tmp/uvw
     [vagrant@localhost ~]$ docker run -itd -v /tmp/xyz:/tmp/xyz:z ubuntu:16.04
     [vagrant@localhost ~]$ ls -Z /tmp/uvw
     -rw-rw-r--. vagrant vagrant unconfined_u:object_r:user_tmp_t:s0 /tmp/uvw

     # volume can be shared with other container.
     [vagrant@localhost ~]$ docker run --rm -it -v /tmp/xyz:/tmp/xyz:z ubuntu:16.04 bash
     /root@b5e5ba3d5aed:/# cat /tmp/xyz

**custom selinux label**

It's possible to assign custom selinux label to run a docker container:

    [vagrant@localhost ~]$ docker run -itd --security-opt label=level:s0:c11,c22 nginx:1.13
    9b010fff0b70595ac7b450b67a07c21a41a5e681829f8f46026b0eb6733c6f01
    [vagrant@localhost ~]$ sudo docker inspect 9b | grep Label
            "MountLabel": "system_u:object_r:svirt_sandbox_file_t:s0:c11,c22",
            "ProcessLabel": "system_u:system_r:svirt_lxc_net_t:s0:c11,c22",
                "Labels": {},

*References*

- http://www.projectatomic.io/blog/2015/06/using-volumes-with-docker-can-cause-problems-with-selinux/

# privileged container (device access)

For privileged container, docker will pass all devices to allowed cgroup devices. Otherwise, to give
container access to devices, we need to use `--device` option and docker will pass individual device
to device cgroup:

    // docker/daemon/oci_linux.go
    func setDevices(s *specs.Spec, c *container.Container) error {
      // Build lists of devices allowed and created within the container.
      var devs []specs.Device
      devPermissions := s.Linux.Resources.Devices
      if c.HostConfig.Privileged {
        hostDevices, err := devices.HostDevices()
        if err != nil {
          return err
        }
        for _, d := range hostDevices {
          devs = append(devs, specDevice(d))
        }
        rwm := "rwm"
        devPermissions = []specs.DeviceCgroup{
          {
            Allow:  true,
            Access: &rwm,
          },
        }
      } else {
        for _, deviceMapping := range c.HostConfig.Devices {
          d, dPermissions, err := getDevicesFromPath(deviceMapping)
          if err != nil {
            return err
          }
          devs = append(devs, d...)
          devPermissions = append(devPermissions, dPermissions...)
        }
      }

      s.Linux.Devices = append(s.Linux.Devices, devs...)
      s.Linux.Resources.Devices = devPermissions
      return nil
    }
