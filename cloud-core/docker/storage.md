<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Mount propagation in docker](#mount-propagation-in-docker)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Mount propagation in docker

For general mount propagation concept, see `learning/storage/mount. Below is a list of practices to
experiment how mount propagation work in docker.

**Run normal docker container with hostpath**

If we run a normal container, we can't do mount:

    $ docker run -itd -v /tmp:/tmp nginx:1.13
    b790263063a07510d142ef9319944d1c36d3e5a0335cdd6a19884cdd481a9566

    $ docker ps
    CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS              PORTS               NAMES
    b790263063a0        nginx:1.13          "nginx -g 'daemon ..."   6 seconds ago        Up 5 seconds        80/tcp              cranky_mcnulty

    $ docker exec -it b79 bash
    root@b790263063a0:/# mkdir /tmp/bindbind
    root@b790263063a0:/# mount --bind /etc /tmp/bindbind
    mount: permission denied

**Run privileged container without mount option**

Running just privileged container allows us to mount to hostpath, but because the default mount
propagation mode is `private`, host is not able to see mount event in container.

    ##### From HOST
    $ docker run -itd --privileged -v /tmp/host:/tmp/container nginx:1.13
    6bceddbac6673135afe9a9778bbefb3f72fb96ff4d87694c0d2bc43111f72b07

    $ sudo mountpoint /tmp/host
    /tmp/host is not a mountpoint

    $ ls /tmp/container
    ls: cannot access '/tmp/container': No such file or directory

    ##### From CONTAINER
    $ docker exec -it 721 bash
    root@721d61dbf4e6:/# ls
    bin  boot  dev  etc  home  lib  lib32  lib64  libx32  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
    root@721d61dbf4e6:/# ls /tmp/
    container

    root@721d61dbf4e6:/# mountpoint /tmp/container
    /tmp/container is a mountpoint
    root@721d61dbf4e6:/# findmnt -o SOURCE,TARGET,PROPAGATION /tmp/container
    SOURCE       TARGET         PROPAGATION
    tmpfs[/host] /tmp/container private

From here we know that what docker does is a bind mount, below is an example:

    $ mkdir /tmp/test /tmp/nottest
    $ sudo mount --bind /tmp/test /tmp/nottest
    $ touch /tmp/test/abc
    $ ls /tmp/nottest
    abc

    $ sudo mountpoint /tmp/test
    /tmp/test is not a mountpoint
    $ sudo mountpoint /tmp/nottest
    /tmp/nottest is a mountpoint

    $ sudo findmnt -o SOURCE,TARGET,PROPAGATION /tmp/test

    $ sudo findmnt -o SOURCE,TARGET,PROPAGATION /tmp/nottest
    SOURCE       TARGET       PROPAGATION
    tmpfs[/test] /tmp/nottest shared

Here, '/tmp/container' is a private mount, what this means is that mount events under '/tmp/host'
will not propagate to '/tmp/container', and mount events under '/tmp/container' will not propagate
to '/tmp/host' as well. Following is a demonstration:

    ##### From CONTAINER
    root@721d61dbf4e6:/# mkdir /tmp/container/bind
    root@721d61dbf4e6:/# mount --bind /etc /tmp/container/bind
    root@721d61dbf4e6:/# ls /tmp/container/bind
    adduser.conf            debian_version  gai.conf   hosts        ld.so.conf     motd           os-release  protocols  rc6.d        selinux                    subgid
    alternatives            default         group      init.d       ld.so.conf.d   mtab           pam.conf    rc0.d      rcS.d        services                   subuid
    apt                     deluser.conf    group-     iproute2     libaudit.conf  network        pam.d       rc1.d      resolv.conf  shadow                     systemd
    bash.bashrc             dpkg            gshadow    issue        localtime      networks       passwd      rc2.d      rmt          shadow-                    terminfo
    bindresvport.blacklist  environment     gshadow-   issue.net    login.defs     nginx          passwd-     rc3.d      rpc          shells                     timezone
    cron.daily              fonts           host.conf  kernel       logrotate.d    nsswitch.conf  profile     rc4.d      securetty    skel                       ucf.conf
    debconf.conf            fstab           hostname   ld.so.cache  mke2fs.conf    opt            profile.d   rc5.d      security     staff-group-for-usr-local  update-motd.d

    ##### From HOST
    $ ls /tmp/host/
    bind
    $ ls /tmp/host/bind

Likewise, mount in host won't propagate to container:

    ##### From HOST
    $ sudo mkdir /tmp/host/anotherbind
    $ sudo mount --bind /etc /tmp/host/anotherbind
    $ ls /tmp/host/anotherbind
    adjtime           dhcpcd.conf    group-          iproute2       locale.gen       modprobe.d      pacman.conf    protocols          services           tmpfiles.d
    arch-release      dhcpcd.duid    group.pacnew    ipset.conf     localtime        modules-load.d  pacman.d       proxychains.conf   shadow             trusted-key.key
    asound.conf       dhcpcd.secret  grub.d          iptables       login.defs       motd            pam.d          pulse              shadow-            ts.conf
    audisp            docker         gshadow         issue          logrotate.conf   mtab            papersize      rc_keymaps         shadow.pacnew      udev
    ......

    ##### From CONTAINER
    root@721d61dbf4e6:/# ls /tmp/container
    anotherbind  bind
    root@721d61dbf4e6:/# ls /tmp/container/anotherbind/

**Run privileged container with rshared**

Now running privileged container with `rshared` mount option allows host to see mount event from container.

     $ docker run -itd --privileged -v /tmp/host:/tmp/container:rshared nginx:1.13
     a7150dafab5fe67ffcb9de0f07fe03746cd3ad7e3e64fa4d9eed97474c18710b

     ##### From CONTAINER
     $ docker exec -it 5c2 bash
     root@5c255a10de0f:/# mkdir /tmp/container/bind
     root@5c255a10de0f:/# mount --bind /etc /tmp/container/bind
     root@5c255a10de0f:/# ls /tmp/container/bind/
     adduser.conf            debian_version  gai.conf   hosts        ld.so.conf     motd           os-release  protocols  rc6.d        selinux                    subgid
     alternatives            default         group      init.d       ld.so.conf.d   mtab           pam.conf    rc0.d      rcS.d        services                   subuid
     apt                     deluser.conf    group-     iproute2     libaudit.conf  network        pam.d       rc1.d      resolv.conf  shadow                     systemd
     bash.bashrc             dpkg            gshadow    issue        localtime      networks       passwd      rc2.d      rmt          shadow-                    terminfo
     bindresvport.blacklist  environment     gshadow-   issue.net    login.defs     nginx          passwd-     rc3.d      rpc          shells                     timezone
     cron.daily              fonts           host.conf  kernel       logrotate.d    nsswitch.conf  profile     rc4.d      securetty    skel                       ucf.conf
     debconf.conf            fstab           hostname   ld.so.cache  mke2fs.conf    opt            profile.d   rc5.d      security     staff-group-for-usr-local  update-motd.d

     ##### From HOST
     $ ls /tmp/host/bind
     adduser.conf            debian_version  gai.conf   hosts        ld.so.conf     motd           os-release  protocols  rc6.d        selinux                    subgid
     alternatives            default         group      init.d       ld.so.conf.d   mtab           pam.conf    rc0.d      rcS.d        services                   subuid
     apt                     deluser.conf    group-     iproute2     libaudit.conf  network        pam.d       rc1.d      resolv.conf  shadow                     systemd
     bash.bashrc             dpkg            gshadow    issue        localtime      networks       passwd      rc2.d      rmt          shadow-                    terminfo
     bindresvport.blacklist  environment     gshadow-   issue.net    login.defs     nginx          passwd-     rc3.d      rpc          shells                     timezone
     cron.daily              fonts           host.conf  kernel       logrotate.d    nsswitch.conf  profile     rc4.d      securetty    skel                       ucf.conf
     debconf.conf            fstab           hostname   ld.so.cache  mke2fs.conf    opt            profile.d   rc5.d      security     staff-group-for-usr-local  update-motd.d

Likewise, mount in host will propagate to container:

     ##### From HOST
     $ sudo mkdir /tmp/host/anotherbind
     $ sudo mount --bind /etc /tmp/host/anotherbind
     $ ls /tmp/host/anotherbind
     adjtime           dhcpcd.conf    group-          iproute2       locale.gen       modprobe.d      pacman.conf    protocols          services           tmpfiles.d
     arch-release      dhcpcd.duid    group.pacnew    ipset.conf     localtime        modules-load.d  pacman.d       proxychains.conf   shadow             trusted-key.key
     asound.conf       dhcpcd.secret  grub.d          iptables       login.defs       motd            pam.d          pulse              shadow-            ts.conf
     audisp            docker         gshadow         issue          logrotate.conf   mtab            papersize      rc_keymaps         shadow.pacnew      udev
     ...

     ##### From CONTAINER
     $ docker exec -it 5c2 bash
     root@5c255a10de0f:/# ls /tmp/container/anotherbind/
     ImageMagick-6     crypttab       gconf           ifplugd        libpaper.d      mke2fs.conf      os-release     profile            securetty          sysctl.d
     NetworkManager    dbus-1         gdm             initcpio       libreoffice     mkinitcpio.conf  ownCloud       profile.d          security           systemd
     UPower            default        geoclue         inputrc        locale.conf     mkinitcpio.d     pacman.conf    protocols          services           tmpfiles.d
     X11               depmod.d       group           iproute2       locale.gen      modprobe.d       pacman.d       proxychains.conf   shadow             trusted-key.key
     adjtime           dhcpcd.conf    group-          ipset.conf     localtime       modules-load.d   pam.d          pulse              shadow-            ts.conf
     arch-release      dhcpcd.duid    group.pacnew    iptables       login.defs      motd             papersize      rc_keymaps         shadow.pacnew      udev
     ...

Here, '/tmp/container' is a shared mount, what this means is that mount events under '/tmp/host' will
propagate to '/tmp/container', and mount events under '/tmp/container' will propagate to '/tmp/host'
as well.

**Run privileged container with rslave**

The same applies to rslave:

    docker run -itd --privileged -v /tmp/host:/tmp/container:rslave nginx:1.13

**Host mount source assumption**

It's important to note that in previous experiments, '/tmp' is shared mount. If we change it to
something else, docker won't run our container:

    $ docker run -itd --privileged -v /tmp/host:/tmp/container:rshared nginx:1.13
    74621f2066eda216ae484e066f24dd07c7420035074b562e785c7e2d79e19a5c
    docker: Error response from daemon: linux mounts: Path /tmp/host is mounted on /tmp but it is not a shared mount.

This is required since if '/tmp' is a private mount, then mount events will not propagate in both
direction. For example, below we have a mountpoint '/tmp/test1' with tmpfs, and then bind mount
'/tmp/test2' to it. After bind mount, we make '/tmp/test1' private and '/tmp/test2' shared. With
this setup, mount event under both '/tmp/test1' and '/tmp/test2' will not propagate.

    $ sudo mkdir /tmp/test1 /tmp/test2
    $ sudo mount -t tmpfs none /tmp/test1
    $ sudo mount --make-private /tmp/test1
    $ sudo mount --bind /tmp/test1 /tmp/test2
    $ sudo mount --make-shared /tmp/test2

    $ sudo findmnt -o source,target,propagation /tmp/test1
    SOURCE TARGET     PROPAGATION
    none   /tmp/test1 private
    $ sudo findmnt -o source,target,propagation /tmp/test2
    SOURCE TARGET     PROPAGATION
    none   /tmp/test2 shared

    $ sudo mkdir /tmp/test1/bind1 && sudo mount --bind /etc /tmp/test1/bind1
    $ ls /tmp/test1/bind1/
    adjtime           dhcpcd.conf    group-          iproute2       locale.gen       modprobe.d      pacman.conf    protocols          services           tmpfiles.d
    arch-release      dhcpcd.duid    group.pacnew    ipset.conf     localtime        modules-load.d  pacman.d       proxychains.conf   shadow             trusted-key.key
    asound.conf       dhcpcd.secret  grub.d          iptables       login.defs       motd            pam.d          pulse              shadow-            ts.conf
    audisp            docker         gshadow         issue          logrotate.conf   mtab            papersize      rc_keymaps         shadow.pacnew      udev
    audit             drirc          gshadow-        kernel         logrotate.d      nanorc          passwd         rc_maps.cfg        shadowsocks        udisks2
    ....
    $ ls /tmp/test2/bind1

    $ sudo mkdir /tmp/test2/bind2 && sudo mount --bind /etc /tmp/test2/bind2
    $ ls /tmp/test2/bind2
    adjtime           dhcpcd.conf    group-          iproute2       locale.gen       modprobe.d      pacman.conf    protocols          services           tmpfiles.d
    arch-release      dhcpcd.duid    group.pacnew    ipset.conf     localtime        modules-load.d  pacman.d       proxychains.conf   shadow             trusted-key.key
    asound.conf       dhcpcd.secret  grub.d          iptables       login.defs       motd            pam.d          pulse              shadow-            ts.conf
    audisp            docker         gshadow         issue          logrotate.conf   mtab            papersize      rc_keymaps         shadow.pacnew      udev
    audit             drirc          gshadow-        kernel         logrotate.d      nanorc          passwd         rc_maps.cfg        shadowsocks        udisks2
    ....
    $ ls /tmp/test1/bind2
