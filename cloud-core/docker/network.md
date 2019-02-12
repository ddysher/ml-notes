<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Docker Network Basics](#docker-network-basics)
- [Docker (1.11.2) overlay network](#docker-1112-overlay-network)
- [Docker (1.12) macvlan network driver](#docker-112-macvlan-network-driver)
- [Docker proxy (v1.11)](#docker-proxy-v111)
- [Docker libnetwork](#docker-libnetwork)
- [Libnetwork and CNI](#libnetwork-and-cni)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Docker Network Basics

*Date: 05/30/2015*

**bridge mode**

When docker daemon is installed and running, a linux kernel bridge is created (typically named `docker0`), e.g

     $ brctl show
     bridge name     bridge id               STP enabled     interfaces
     docker0         8000.56847afe9799       no

Nothing connects to the bridge yet. Note that the bridge has an ip address attached to it, we'll be
able to list it using ifconfig and ip route.

     $ ifconfig
     docker0   Link encap:Ethernet  HWaddr 56:84:7a:fe:97:99
               inet addr:172.17.42.1  Bcast:0.0.0.0  Mask:255.255.0.0
               inet6 addr: fe80::5484:7aff:fefe:9799/64 Scope:Link
               UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
               RX packets:83 errors:0 dropped:0 overruns:0 frame:0
               TX packets:84 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:0
               RX bytes:5388 (5.3 KB)  TX bytes:11924 (11.9 KB)
     wlan0     Link encap:Ethernet  HWaddr 10:fe:ed:98:7a:a0
               inet addr:10.0.0.3  Bcast:10.0.0.255  Mask:255.255.255.0
               inet6 addr: fe80::12fe:edff:fe98:7aa0/64 Scope:Link
               UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
               RX packets:2034345 errors:0 dropped:0 overruns:0 frame:0
               TX packets:1931934 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:1000
               RX bytes:1696951785 (1.6 GB)  TX bytes:1259956169 (1.2 GB)

     $ ip route show
     default via 10.0.0.1 dev wlan0  proto static
     10.0.0.0/24 dev wlan0  proto kernel  scope link  src 10.0.0.3  metric 9
     172.17.0.0/16 dev docker0  proto kernel  scope link  src 172.17.42.1

172.17.0.0/16 subnet is the default value chosen by docker, and the bridge has address `172.17.42.1`
by default. Now when we create a container, e.g. `docker run -rm -it busybox`, docker will create a
veth pair: one attached to the new container, the other attached to docker0 bridge. Now list the bridge:

     $ brctl show
     bridge name     bridge id               STP enabled     interfaces
     docker0         8000.56847afe9799       no              veth5969c85

List the interfaces in HOST:

     $ ifconfig
     docker0   Link encap:Ethernet  HWaddr 56:84:7a:fe:97:99
               inet addr:172.17.42.1  Bcast:0.0.0.0  Mask:255.255.0.0
               inet6 addr: fe80::5484:7aff:fefe:9799/64 Scope:Link
               UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
               RX packets:83 errors:0 dropped:0 overruns:0 frame:0
               TX packets:84 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:0
               RX bytes:5388 (5.3 KB)  TX bytes:11924 (11.9 KB)
     veth5969c85 Link encap:Ethernet  HWaddr 72:74:60:f8:9e:e7
               inet6 addr: fe80::7074:60ff:fef8:9ee7/64 Scope:Link
               UP BROADCAST RUNNING  MTU:1500  Metric:1
               RX packets:12 errors:0 dropped:0 overruns:0 frame:0
               TX packets:17 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:0
               RX bytes:928 (928.0 B)  TX bytes:1423 (1.4 KB)

Inside busybox CONTAINER:

     / # ifconfig
     eth0      Link encap:Ethernet  HWaddr 02:42:AC:11:00:06
               inet addr:172.17.0.6  Bcast:0.0.0.0  Mask:255.255.0.0
               UP BROADCAST RUNNING  MTU:1500  Metric:1
               RX packets:6 errors:0 dropped:0 overruns:0 frame:0
               TX packets:6 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:0
               RX bytes:508 (508.0 B)  TX bytes:508 (508.0 B)
     lo        Link encap:Local Loopback
               inet addr:127.0.0.1  Mask:255.0.0.0
               UP LOOPBACK RUNNING  MTU:65536  Metric:1
               RX packets:0 errors:0 dropped:0 overruns:0 frame:0
               TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
               collisions:0 txqueuelen:0
               RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)

     / # ip route show
     default via 172.17.42.1 dev eth0
     172.17.0.0/16 dev eth0  proto kernel  scope link  src 172.17.0.6

When container exits, veth pair is deleted.

**iptables**

After running docker, following iptables rules will be created:

     vagrant@vagrant-ubuntu-trusty-64:~$ sudo iptables-save
     # Generated by iptables-save v1.4.21 on Wed Aug 10 03:03:23 2016
     *nat
     :PREROUTING ACCEPT [5:460]
     :INPUT ACCEPT [5:460]
     :OUTPUT ACCEPT [14:942]
     :POSTROUTING ACCEPT [14:942]
     :DOCKER - [0:0]
     -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
     -A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
     -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
     -A DOCKER -i docker0 -j RETURN
     COMMIT
     # Completed on Wed Aug 10 03:03:23 2016
     # Generated by iptables-save v1.4.21 on Wed Aug 10 03:03:23 2016
     *filter
     :INPUT ACCEPT [278:19553]
     :FORWARD ACCEPT [0:0]
     :OUTPUT ACCEPT [244:21824]
     :DOCKER - [0:0]
     :DOCKER-ISOLATION - [0:0]
     -A FORWARD -j DOCKER-ISOLATION
     -A FORWARD -o docker0 -j DOCKER
     -A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
     -A FORWARD -i docker0 ! -o docker0 -j ACCEPT
     -A FORWARD -i docker0 -o docker0 -j ACCEPT
     -A DOCKER-ISOLATION -j RETURN
     COMMIT
     # Completed on Wed Aug 10 03:03:23 2016

Kernel routing table:

     vagrant@vagrant-ubuntu-trusty-64:~$ ip route show
     default via 10.0.2.2 dev eth0
     10.0.2.0/24 dev eth0  proto kernel  scope link  src 10.0.2.15
     172.17.0.0/16 dev docker0  proto kernel  scope link  src 172.17.0.1
     192.168.33.0/24 dev eth1  proto kernel  scope link  src 192.168.33.33

A new chain `DOCKER` is created in `NAT` table, with couple of rules:

Rule1: `-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE`

This rule provides container external network access via NAT. It can be translated as "After routing,
if the packet has source address 172.17.0.0/16 and the interface it will be sent out is not 'docker0',
then masquerate it". When a packet is sent from a docker container, it will have source address in
172.17.0.0/16. If the packet is destinated to external address, then based on the routing table, it
will be sent via eth0 (thus match the condition of not to be sent out via 'docker0'). iptables will
masquerade the packet's source address to host address; therefore, container can have external access.

On the other hand, if the packet is destinated to another container on the same host, then it will
have destination address within 172.17.0.0/16, which based on routing table, the packet will be sent
out through docker0, so iptables won't do anything; thus container can see its peer's real ip address.

*References*

- https://success.docker.com/article/networking
- http://www.dockone.io/article/402

# Docker (1.11.2) overlay network

**Overview**

Newer docker provides an 'overlay' network out-of-box to provide cross host container communication.
Following is the experiment. Note the experiment setups overlay network manually; docker swarm mode
does this automatically, e.g. no need to run store like etcd.

**Run two VMs**

Create two VMs (vagrant and virtualbox) for experiment, and install docker. First VM has eth1 IP set
to `192.168.205.10`, and second VM has eth1 set to `192.168.205.11`.

**Run etcd on VM1**

```
$ export HostIP="192.168.205.10"
$ docker run -d -p 4001:4001 -p 2380:2380 -p 2379:2379 \
 --name etcd index.caicloud.io/etcd:v2.2.0 \
 -name etcd0 \
 -advertise-client-urls http://${HostIP}:2379,http://${HostIP}:4001 \
 -listen-client-urls http://0.0.0.0:2379,http://0.0.0.0:4001 \
 -initial-advertise-peer-urls http://${HostIP}:2380 \
 -listen-peer-urls http://0.0.0.0:2380 \
 -initial-cluster-token etcd-cluster-1 \
 -initial-cluster etcd0=http://${HostIP}:2380 \
 -initial-cluster-state new
```

After this, use `etcdctl cluster-health` to check if etcd is running properly.

**Configure docker to use etcd as cluster store**

Once etcd is up and running, add the following line to `/etc/default/docker`:

On the first VM:
```
DOCKER_OPTS="--cluster-store=etcd://192.168.205.10:2379 --cluster-advertise=192.168.205.10:2379"
```

Then the second VM:
```
DOCKER_OPTS="--cluster-store=etcd://192.168.205.10:2379 --cluster-advertise=192.168.205.11:2379"
```

The only difference is cluster-advertise address. Now restart docker. Note etcd container might be
stopped due to docker restart, so it needs to be restarted as well.

**Create overlay network**

Create an overlay network using the following command:
```
$ docker network create --driver=overlay --subnet=10.0.10.0/24 overlayred
```

And we can list it on two VMs (the info is synced via etcd):
```
$ docker network ls
```

The `--subnet` option is optional, but we set it here for better inspection.

**Run two containers**

Create two containers on two VMs and verify they can ping each other:
```
$ docker run --net overlayred -it index.caicloud.io/busybox
```

**Multi-tenancy**

If we create another overlay network:
```
$ docker network create --driver=overlay --subnet=10.0.10.0/24 overlayanother
```

And run another two containers in this overlay:
```
$ docker run --net overlayred -it index.caicloud.io/busybox
```

Suppose the previous two containers have address 10.0.10.4 and 10.0.10.5; and the new containers have
address 10.0.10.7 and 10.0.10.8. Then we can't ping, e.g. from 10.0.10.7 to 10.0.10.5. This is
because underneath, the two overlay networks use different VNI number.

*References*

- https://www.singlestoneconsulting.com/~/media/files/whitepapers/dockernetworking2.pdf

**etcd information**

If we look at etcd, we'll see the network:

    $ etcdctl ls /docker/network/v1.0/network
    /docker/network/v1.0/network/04d1c111ead64e875005038696deb4a017ffa7f7f3365b119c9b16d63895ee52

This matches our docker network ls output (the ID part `04d1c111ead6`):

     vagrant@server1:~$ docker network ls
     NETWORK ID          NAME                DRIVER
     7cea82001cb7        bridge              bridge
     e0e81eeee8a4        docker_gwbridge     bridge
     eafd17e32789        host                host
     6a897308c6f8        none                null
     04d1c111ead6        overlayred          overlay

Looking around etcd more will give us more information, e.g container endpoints.

**Two interfaces in container**

When we start a container, we'll see two interfaces in this CONTAINER:

     / # ip addr
     1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue
         link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
         inet 127.0.0.1/8 scope host lo
            valid_lft forever preferred_lft forever
         inet6 ::1/128 scope host
            valid_lft forever preferred_lft forever
     11: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue
         link/ether 02:42:0a:00:0a:05 brd ff:ff:ff:ff:ff:ff
         inet 10.0.10.5/24 scope global eth0
            valid_lft forever preferred_lft forever
         inet6 fe80::42:aff:fe00:a05/64 scope link
            valid_lft forever preferred_lft forever
     13: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue
         link/ether 02:42:ac:12:00:02 brd ff:ff:ff:ff:ff:ff
         inet 172.18.0.2/16 scope global eth1
            valid_lft forever preferred_lft forever
         inet6 fe80::42:acff:fe12:2/64 scope link
            valid_lft forever preferred_lft forever

Following is the output from `ip link` running in the HOST:

     vagrant@server1:~$ ip link
     1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default
         link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
     2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
         link/ether 08:00:27:62:76:11 brd ff:ff:ff:ff:ff:ff
     3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
         link/ether 08:00:27:08:f2:4b brd ff:ff:ff:ff:ff:ff
     4: docker_gwbridge: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
         link/ether 02:42:42:04:ca:4f brd ff:ff:ff:ff:ff:ff
     5: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
         link/ether 02:42:08:92:ea:e1 brd ff:ff:ff:ff:ff:ff
     7: veth3b9abad: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master docker0 state UP mode DEFAULT group default
         link/ether b2:1f:de:0f:e9:79 brd ff:ff:ff:ff:ff:ff
     9: ov-000100-04d1c: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP mode DEFAULT group default
         link/ether 22:ae:ab:95:fe:3b brd ff:ff:ff:ff:ff:ff
     10: vx-000100-04d1c: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master ov-000100-04d1c state UNKNOWN mode DEFAULT group default
         link/ether 22:ae:ab:95:fe:3b brd ff:ff:ff:ff:ff:ff
     12: veth7fcabcd: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master ov-000100-04d1c state UP mode DEFAULT group default
         link/ether 32:4b:b2:2e:18:09 brd ff:ff:ff:ff:ff:ff
     14: veth0d85899: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master docker_gwbridge state UP mode DEFAULT group default
         link/ether 82:40:09:8f:18:a1 brd ff:ff:ff:ff:ff:ff

Below is the kernel routing table and iptables in the HOST:

     vagrant@server1:~$ ip route
     default via 10.0.2.2 dev eth0
     10.0.2.0/24 dev eth0  proto kernel  scope link  src 10.0.2.15
     10.0.10.0/24 dev ov-000100-04d1c  proto kernel  scope link  src 10.0.10.1
     172.17.0.0/16 dev docker0  proto kernel  scope link  src 172.17.0.1
     172.18.0.0/16 dev docker_gwbridge  proto kernel  scope link  src 172.18.0.1
     192.168.205.0/24 dev eth1  proto kernel  scope link  src 192.168.205.10

     vagrant@server1:~$ sudo iptables -L -t nat
     Chain PREROUTING (policy ACCEPT)
     target     prot opt source               destination
     DOCKER     all  --  anywhere             anywhere             ADDRTYPE match dst-type LOCAL

     Chain INPUT (policy ACCEPT)
     target     prot opt source               destination

     Chain OUTPUT (policy ACCEPT)
     target     prot opt source               destination
     DOCKER     all  --  anywhere            !127.0.0.0/8          ADDRTYPE match dst-type LOCAL

     Chain POSTROUTING (policy ACCEPT)
     target     prot opt source               destination
     MASQUERADE  all  --  172.17.0.0/16        anywhere
     MASQUERADE  all  --  172.18.0.0/16        anywhere
     MASQUERADE  tcp  --  172.17.0.2           172.17.0.2           tcp dpt:4001
     MASQUERADE  tcp  --  172.17.0.2           172.17.0.2           tcp dpt:2380
     MASQUERADE  tcp  --  172.17.0.2           172.17.0.2           tcp dpt:2379

     Chain DOCKER (2 references)
     target     prot opt source               destination
     RETURN     all  --  anywhere             anywhere
     RETURN     all  --  anywhere             anywhere
     DNAT       tcp  --  anywhere             anywhere             tcp dpt:4001 to:172.17.0.2:4001
     DNAT       tcp  --  anywhere             anywhere             tcp dpt:2380 to:172.17.0.2:2380
     DNAT       tcp  --  anywhere             anywhere             tcp dpt:2379 to:172.17.0.2:2379
     #+END_SRC

And below is the routing table in the CONTAINER:

     / # ip route
     default via 172.18.0.1 dev eth1
     10.0.10.0/24 dev eth0  src 10.0.10.5
     172.18.0.0/16 dev eth1  src 172.18.0.2

**Interface eth1**

As we can see, there is a new bridge called `docker_gwbridge` (index 4); and a veth (index 14) is
added to it. If we inspect the veth, we'll see that its pair is interface index 13:

     vagrant@server1:~$ ethtool -S veth0d85899
     NIC statistics:
          peer_ifindex: 13

And this is exactly the interface in the above container's interface `eth1`, which is assigned the
address 172.18.0.2/16. The reason to have interface is to allow container to access outside world.
If there is only one interface in this container, i.e. `eth0` for the overlay; then we need something
(act as a VTEP) to terminate the overlay traffic and route that traffic out to the world. Instead,
docker made the decision to create a `docker_gwbridge` on each host independently, and send all
traffic headed outside of the overlay through the local host. The relationship between container
`eth1` and host `docker_gwbridge` is similar to the relationship between container `eth0` and host
`docker0` in local bridge mode.

**Interface eth0**

Also, as we can see from above output, there is a new bridge called `ov-000100-04d1c` (index 9); and
a veth (index 12) is added to it. If we inspect the veth, we'll see that its pair is interface index
11:

     vagrant@server1:~$ ethtool -S veth7fcabcd:
     NIC statistics:
          peer_ifindex: 11

And this is exactly the interface in container's `eth0`, which is assigned address 10.0.10.5/24.
Also note that MTU of `eth0` is 1450, while `eth1` is 1500. This hints us that docker is using VxLAN
for `eth0`: 50 bytes is exactly size of VxLAN header.

**Example use of eth1**

If we run `ping baidu.com` in the container and run tcpdump on 'docker_gwbridge', we'll see:

     vagrant@server1:~$ sudo tcpdump -i docker_gwbridge
     tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
     listening on docker_gwbridge, link-type EN10MB (Ethernet), capture size 65535 bytes
     03:23:13.336664 IP 172.18.0.2.58607 > 10.0.2.3.domain: 19005+ AAAA? baidu.com. (27)
     03:23:13.340734 IP 10.0.2.3.domain > 172.18.0.2.58607: 19005 0/1/0 (70)
     03:23:13.340935 IP 172.18.0.2.58607 > 10.0.2.3.domain: 14389+ A? baidu.com. (27)
     03:23:13.346093 IP 10.0.2.3.domain > 172.18.0.2.58607: 14389 4/5/5 A 111.13.101.208, A 220.181.57.217, A 180.149.132.47, A 123.125.114.144 (261)
     03:23:13.346383 IP 172.18.0.2 > 111.13.101.208: ICMP echo request, id 2304, seq 0, length 64
     03:23:13.378834 IP 111.13.101.208 > 172.18.0.2: ICMP echo reply, id 2304, seq 0, length 64
     03:23:18.355778 ARP, Request who-has 172.18.0.2 tell server1, length 28
     03:23:18.355810 ARP, Reply 172.18.0.2 is-at 02:42:ac:12:00:02 (oui Unknown), length 28

When we send ping request to '111.13.101.208', based on container routing table, packet should be sent
to gateway 172.18.0.1, i.e. `docker_gwbridge` on eth1, and packet will get source address 172.18.0.2.
When `docker_gwbridge` receives the packet (via veth pair), based on host routing table, it will send
the packet to gateway 10.0.2.2. After routing, the packet is masqueraded according to iptable rules.

**Example use of eth0**

If we run `ping 10.0.10.4`, which is a container running in another host (source container has address
10.0.10.5), i.e. ping from 10.0.10.5 to 10.0.10.4. Based on container routing table, the packet needs
to be sent to eth0, and has source address 10.0.10.5. The packet flows from eth0 to veth index12 on
`ov-000100-04d1c`.

Apart from veth index12, there is another interface `vx-000100-04d1c` connected to the bridge. If we
look at the forwarding db of `ov-000100-04d1c`:

     vagrant@server1:~$ bridge fdb show ov-000100-04d1c
     01:00:5e:00:00:01 dev eth0 self permanent
     33:33:00:00:00:01 dev eth0 self permanent
     33:33:ff:62:76:11 dev eth0 self permanent
     01:00:5e:00:00:01 dev eth1 self permanent
     33:33:00:00:02:02 dev eth1 self permanent
     33:33:00:00:00:01 dev eth1 self permanent
     33:33:ff:08:f2:4b dev eth1 self permanent
     82:40:09:8f:18:a1 dev veth0d85899 vlan 0 permanent
     02:42:42:04:ca:4f dev docker_gwbridge vlan 0 permanent
     02:42:08:92:ea:e1 dev docker0 vlan 0 permanent
     b2:1f:de:0f:e9:79 dev veth3b9abad vlan 0 permanent
     02:42:ac:11:00:02 dev veth3b9abad vlan 0
     33:33:00:00:00:01 dev veth3b9abad self permanent
     01:00:5e:00:00:01 dev veth3b9abad self permanent
     33:33:ff:0f:e9:79 dev veth3b9abad self permanent
     32:4b:b2:2e:18:09 dev veth7fcabcd vlan 0 permanent
     22:ae:ab:95:fe:3b dev vx-000100-04d1c vlan 0 permanent
     02:42:0a:00:0a:04 dev vx-000100-04d1c dst 192.168.205.11 self permanent
     33:33:00:00:00:01 dev veth7fcabcd self permanent
     01:00:5e:00:00:01 dev veth7fcabcd self permanent
     33:33:ff:2e:18:09 dev veth7fcabcd self permanent
     33:33:00:00:00:01 dev veth0d85899 self permanent
     01:00:5e:00:00:01 dev veth0d85899 self permanent
     33:33:ff:8f:18:a1 dev veth0d85899 self permanent

From this line `02:42:0a:00:0a:04 dev vx-000100-04d1c dst 192.168.205.11 self permanent`, we see that
`vx-000100-04d1c` interface knows that 02:42:0a:00:0a:04 can be reached via VxLAN tunnel 192.168.205.11.
Following is the output from dumping bridge `tcpdump ov-000100-04d1c`:

     vagrant@server1:~$ sudo tcpdump -i ov-000100-04d1c
     tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
     listening on ov-000100-04d1c, link-type EN10MB (Ethernet), capture size 65535 bytes
     05:18:00.349398 IP 10.0.10.5 > 10.0.10.4: ICMP echo request, id 5376, seq 0, length 64
     05:18:00.350180 IP 10.0.10.4 > 10.0.10.5: ICMP echo reply, id 5376, seq 0, length 64
     05:18:05.363757 ARP, Request who-has 10.0.10.4 tell 10.0.10.5, length 28
     05:18:05.363764 ARP, Reply 10.0.10.4 is-at 02:42:0a:00:0a:04 (oui Unknown), length 28

Following is the output from listening VxLAN in host `eth1`:

     vagrant@server1:~$ sudo tcpdump -i eth1 udp port 4789
     tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
     listening on eth1, link-type EN10MB (Ethernet), capture size 65535 bytes
     06:27:14.473580 IP server1.57037 > 192.168.205.11.4789: VXLAN, flags [I] (0x08), vni 256
     IP 10.0.10.5 > 10.0.10.4: ICMP echo request, id 7168, seq 0, length 64
     06:27:14.473607 IP 192.168.205.11.56482 > server1.4789: VXLAN, flags [I] (0x08), vni 256
     IP 10.0.10.4 > 10.0.10.5: ICMP echo reply, id 7168, seq 0, length 64

*References*

- https://www.singlestoneconsulting.com/~/media/files/whitepapers/dockernetworking2.pdf

Note, in this article, there is no such device called `vx-000100-04d1c` and `ov-000100-04d1c`. To
find the vxlan device, we have to run `ip` command in the overlay's net namespace. Repeating the
experiment on MacOS virtualbox environment does align with the article (the above experiment was
done in Linux virtual box environment), e.g.

     vagrant@server2:~$ sudo ip netns exec 1-03a0f9cff1 ip addr
     1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
         link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
         inet 127.0.0.1/8 scope host lo
            valid_lft forever preferred_lft forever
         inet6 ::1/128 scope host
            valid_lft forever preferred_lft forever
     2: br0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default
         link/ether 26:e1:91:dc:a4:a2 brd ff:ff:ff:ff:ff:ff
         inet 10.0.10.1/24 scope global br0
            valid_lft forever preferred_lft forever
         inet6 fe80::38e2:b4ff:fe3e:f97e/64 scope link
            valid_lft forever preferred_lft forever
     6: vxlan1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br0 state UNKNOWN group default
         link/ether 26:e1:91:dc:a4:a2 brd ff:ff:ff:ff:ff:ff
         inet6 fe80::24e1:91ff:fedc:a4a2/64 scope link
            valid_lft forever preferred_lft forever
     8: veth2@if7: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master br0 state UP group default
         link/ether da:00:25:49:e9:47 brd ff:ff:ff:ff:ff:ff
         inet6 fe80::d800:25ff:fe49:e947/64 scope link
            valid_lft forever preferred_lft forever

# Docker (1.12) macvlan network driver

In the setup, router subnet is 192.168.3.0/24, and higher address space is not used. Docker daemon
runs at 192.168.3.22. First create a network with macvlan driver:

    docker network create -d macvlan \
      --subnet=192.168.3.0/24 --gateway=192.168.3.1 \
      --ip-range=192.168.3.128/26 -o parent=enp1s0 testnet

Then create a container:

    $ docker run -it --network=testnet busybox sh
    / # ip addr
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue qlen 1
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        inet 127.0.0.1/8 scope host lo
           valid_lft forever preferred_lft forever
        inet6 ::1/128 scope host
           valid_lft forever preferred_lft forever
    19: eth0@if2: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue
        link/ether 02:42:c0:a8:03:80 brd ff:ff:ff:ff:ff:ff
        inet 192.168.3.128/24 scope global eth0
           valid_lft forever preferred_lft forever
        inet6 fe80::42:c0ff:fea8:380/64 scope link
           valid_lft forever preferred_lft forever
    / #

The container will have an address in the physical network. However, because of properties of macvlan
driver, we can't reach the container from the host; but we can access it from other hosts in the subnet.

    $ ping -c 1 192.168.3.128
    PING 192.168.3.128 (192.168.3.128) 56(84) bytes of data.
    ^C
    --- 192.168.3.128 ping statistics ---
    1 packets transmitted, 0 received, 100% packet loss, time 0ms

    $ ping -c 1 192.168.3.128
    PING 192.168.3.128 (192.168.3.128): 56 data bytes
    64 bytes from 192.168.3.128: icmp_seq=0 ttl=64 time=2.888 ms
    --- 192.168.3.128 ping statistics ---
    1 packets transmitted, 1 packets received, 0.0% packet loss
    round-trip min/avg/max/stddev = 2.888/2.888/2.888/0.000 ms

**macvlan with vlan**

The following commands create a container using macvlan, which is part of a vlan.

    sudo modprobe 8021q
    sudo apt-get install vlan
    docker network create -d macvlan --subnet=192.168.0.0/16 \
      --ip-range=192.168.2.0/24 -o macvlan_mode=bridge -o parent=eth2.70 macvlan70

*References*

- [Basic experiment](http://hicu.be/docker-networking-macvlan-bridge-mode-configuration)

# Docker proxy (v1.11)

**Overview**

When publishing docker port on host using -P or -p, a docker-proxy process is started to proxy traffic.
The process will be deprecated, but existed for two main reasons:
- allows localhost <-> localhost routing
- allows docker instance to call its published port with host ip

Both can be done using kernel feature, but it exists in case kernel support is not available.

The following experiment demonstrates kernel network feature that's used to deprecate the `docker-proxy`
process. First of all, let's disable userland proxy by adding flag `--userland-proxy=false`; then run
an nginx docker conainer:

     $ docker run -d -p 8080:80 index.caicloud.io/nginx:1.9.4

If userland proxy is not disabled, the following experiment won't work as all traffic will go to the
proxy.

**localhost <-> localhost**

localhost <-> localhost means that we can simply do "curl localhost:8080" in host without any problem.
This seems obvious, but since linux doesn't route traffic for localhost by default, we must enable
it via setting "route_localnet":

     $ sysctl net.ipv4.conf.docker0.route_localnet

The output value is 1. If we set it to 0, then `curl localhost:8080` in host network doesn't work .

     $ sysctl -w net.ipv4.conf.docker0.route_localnet=0

**allows docker instance to call its published port with host ip**

This means that inside docker container, we can call ourself using host ip. In the experiment, host
ip is 192.168.33.33, and container ip is 172.17.0.2. Now exec into the previous container and run
`curl 192.168.33.33:8080`, we'll get response from nginx. This works because docker enables `hairpin_mode`
for our container interface. Suppose peer veth name of the container's eth0 interface is "veth0a95d8e"
on the host; we can check hairpin mode via:

     $ cat /sys/class/net/veth0a95d8e/brport/hairpin_mode

The result is 1. Now if we set the value to 0:

     $ echo 0 > /sys/class/net/veth0a95d8e/brport/hairpin_mode

If we do `curl 192.168.33.33:8080` in the container again, we won't get any response. The reason is
that when container send a packet in this command, the packet has source address 172.17.0.2:XXXXX and
destination address 192.168.33.33:8080. When `veth0a95d8e` sees the packet, it knows that 192.168.33.33
is the host's address; if hairpin mode is enabled, it changes the address to 172.17.0.2:80, i.e.
through `veth0a95d8e` hairpin, the address changes:

    from:
      172.17.0.2:XXXXX -> 192.168.33.33:8080
    to:
      172.17.0.2:XXXXX -> 172.17.0.2:80

This is done with following rule:

      Chain PREROUTING (policy ACCEPT)
      target     prot opt source               destination
      DOCKER     all  --  anywhere             anywhere             ADDRTYPE match dst-type LOCAL
      ...
      Chain DOCKER (2 references)
      target     prot opt source               destination
      DNAT       tcp  --  anywhere             anywhere             tcp dpt:http-alt to:172.17.0.2:80

During post routing, we masquerade the address in container (last rule). This means that in the
container, we'll see the request comming from docker0's address, i.e. 172.17.0.1.46106 -> 172.17.0.2.80

      Chain POSTROUTING (policy ACCEPT)
      target     prot opt source               destination
      MASQUERADE  all  --  anywhere             anywhere             ADDRTYPE match src-type LOCAL
      MASQUERADE  all  --  172.17.0.0/16        anywhere
      MASQUERADE  tcp  --  172.17.0.2           172.17.0.2           tcp dpt:http

NOTE, the above analysis can be flawed due to lack of background, see:

- https://github.com/docker/docker/pull/6810
- https://github.com/docker/docker/issues/8356

**References**

- http://windsock.io/tag/docker-proxy/
- [why docker proxy](http://serverfault.com/questions/633604/what-is-the-point-of-the-docker-proxy-process-why-is-a-userspace-tcp-proxy-need)

# Docker libnetwork

**Overview**

Libnetwork provides a native Go implementation for connecting containers. The goal of libnetwork is
to deliver a robust Container Network Model that provides a consistent programming interface and the
required network abstractions for applications. Libnetwork aims to provide the abstraction via a
`driver/plugin` model.
- Keep networking as a library separate from the Container runtime.
- Provide container connectivity in the same host as well as across hosts.
- Networking implementation will be done as a plugin implemented by drivers. The plugin mechanism is provided to add new third-party drivers easily.
- Control IP address assignment for the Containers using local IPAM drivers and plugins.
- Supported local drivers are bridge, overlay, macvlan, ipvlan. Supported remote drivers are Weave, calico etc.

**Data Model**

Libnetwork data model contains 'Sandbox', 'Endpoint' and 'Network'.
- A Sandbox contains the configuration of a container's network stack, e.g. Linux Network Namespace, a FreeBSD Jail, etc.
- An Endpoint joins a Sandbox to a Network, e.g veth pair.
- A Network is a group of Endpoints that are able to communicate with each other directly, e.g. Linux bridge.

From the above comparison, the data model is a high level abstraction of bridge mode in docker
engine; which allows more diverse implementations. bridge mode is one of the many implementations.

**Driver API**

A libnetwork driver implements the driver API and registers itself. There are builtin drivers like
bridge, overlay, none, host, etc, as well as a remote driver for plugin development. Drivers are
essentially an extension of libnetwork and provide the actual implementation for all of the
libnetwork APIs. Hence there is an 1-1 correspondence for all the Network and Endpoint APIs, which
includes (but not limited to):
- driver.Config
- driver.CreateNetwork
- driver.DeleteNetwork
- driver.CreateEndpoint
- driver.DeleteEndpoint
- driver.Join
- driver.Leave

For example, in bridge plugin. CreateNetwork will create brige interface on docker host (similar to
docker0), DeleteNetwork will delete it. CreateEndpoint will create veth pair, and attach the host
side of veth into bridge interface. Join will setup gateway, routes for the container.

*References*

- https://github.com/docker/libnetwork
- https://github.com/docker/libnetwork/blob/master/docs/design.md
- [example plugin](./experiments/libnetwork)

# Libnetwork and CNI

Both libnetwork and cni have similar objectives of creating extensible container networking model,
but with different approaches. Their design is different so it's not yet possible for them to converge.
- In general, cni is much simpler than libnetwork.
- cni's plugin is implemented as a binary; cni spec defines the set of parameters and environment
  variables passed to it. On the other hand, libnetwork's API is defined as a golang interface, or
  in another word, a library: driver must implement the interface and register itself; this kind of
  driver is called 'builtin driver'. Another type is remote driver, which provides a server for
  libnetwork to call, using predefined API structure.
- cni has bridge, ipvlan, macvlan; libnetwork also has them. libnetwork has a builtin overlay driver
  which provides connections between hosts via vxlan, see network.org. However, it requires a libkv
  store which posses some problems for certain platform. On the other hand, cni doesn't provide such
  solution out-out-box; it is also accomplished via plugin, e.g. the flannel meta plugin.

*References*

- [kubernetes uses cni](http://blog.kubernetes.io/2016/01/why-Kubernetes-doesnt-use-libnetwork.html)
  - Note it is possible to use docker's overlay in kubernetes. You need to configure docker to use
    overlay network, and configure kubernetes to do nothing about container networking. Then, it
    just works. However, this can only work in docker and involves a lot of manual setup.
- [overview of container standard](https://sreeninet.wordpress.com/2016/06/11/container-standards)
