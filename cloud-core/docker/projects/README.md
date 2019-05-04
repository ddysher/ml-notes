<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Image](#image)
  - [watchtower](#watchtower)
- [Testing](#testing)
  - [pumba](#pumba)
- [Plugins](#plugins)
  - [hostnic](#hostnic)
  - [shrike](#shrike)
- [Kits](#kits)
  - [infrakit](#infrakit)
  - [datakit](#datakit)
  - [vpnkit](#vpnkit)
  - [hyperkit](#hyperkit)
  - [linuxkit](#linuxkit)
  - [swarmkit](#swarmkit)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Image

## watchtower

[Watchtower](https://github.com/v2tec/watchtower) is an application that will monitor your running
Docker containers and watch for changes to the images (in the registry) that those containers were
originally started from. If watchtower detects that an image has changed, it will automatically
restart the container using the new image.

# Testing

## pumba

[Pumba](https://github.com/gaia-adm/pumba) is a resilience testing tool, that helps applications
tolerate random Docker container failures: process, network and performance.

# Plugins

## hostnic

ref: [hostnic](./hostnic.md)

## shrike

ref: [shrike](./shrike.md)

# Kits

## infrakit

*References*

- https://blog.docker.com/2016/10/introducing-infrakit-an-open-source-toolkit-for-declarative-infrastructure/
- http://kunalkushwaha.github.io/2016/10/14/understanding-infrakit/

## datakit

N/A

## vpnkit

*Date: 05/20/2017*

[VPNKit](https://github.com/moby/vpnkit) is a networking library that translates between raw Ethernet
network traffic and their equivalent socket calls in MacOS X or Windows, i.e. it operates by
reconstructing Ethernet traffic from the VM and translating it into the relevant socket API calls on
OSX or Windows. It helps HyperKit VMs interoperate with host VPN configurations. For more details, ref:
- https://github.com/moby/vpnkit/blob/master/docs/ethernet.md
- https://github.com/moby/vpnkit/blob/master/docs/ports.md

## hyperkit

*Date: 05/20/2017*

[HyperKit](https://github.com/moby/hyperkit) is docker's (the company) solution to bring native docker
(the project) experience to Mac. It includes a hypervisor derived from xhyve, which in turn was derived
from bhyve and uses `Hyervisor.Framework` in mac. hvdos is a simple emulator using `Hypervisor.Framework`.
hyperkit is designed to be interfaced with higher-level components such as the VPNKit and DataKit.

From docker blog:

> HyperKit is based around a lightweight approach to virtualization that is possible due to the
> Hypervisor framework being supplied with MacOS X 10.10 onwards. HyperKit applications can take
> advantage of hardware virtualization to run VMs, but without requiring elevated privileges or
> complex management tool stacks. HyperKit is built on the xHyve and bHyve projects, with additional
> functionality to make it easier to interface with other components such as the VPNKit or DataKit.
> Since HyperKit is broadly structured as a library, linking it against unikernel libraries is
> straightforward. For example, we added persistent block device support that uses the MirageOS QCow
> libraries written in OCaml.

*References*

- xhyve: https://github.com/mist64/xhyve
- bhyve: http://www.bhyve.org
- Hyervisor.Framework: https://developer.apple.com/reference/hypervisor
- hvdos: https://github.com/mist64/hvdos

## linuxkit

ref: [linuxkit](./linuxkit.md)

## swarmkit

ref: [swarmkit](./swarmkit.md)
