<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)
  - [bundle](#bundle)
  - [start.go](#startgo)
  - [container init process](#container-init-process)
  - [network](#network)
- [Workflow](#workflow-1)
  - [update as ov v1.0.0-rc1](#update-as-ov-v100-rc1)
- [Experiments](#experiments)
  - [Get runc binary](#get-runc-binary)
  - [Install docker](#install-docker)
  - [Create OCI bundle](#create-oci-bundle)
  - [Run container](#run-container)
  - [Create/Start container](#createstart-container)
  - [Rootless container](#rootless-container)
  - [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

runc is a CLI tool for spawning and running containers according to the OCI specification.

# Workflow

*Date: 01/17/2016, v0.0.6*

## bundle

- `config.json` contains host-independent configuration of a container.
- `runtime.json` is host-dependent runtime configuration of a container.

For example, runtime.json contains information about how's devices get mounted. config.json will
just give mount name and path. Another example, runtime.json tells what kinds of namespace is
supported. Note, runtime.json and config.json are merged into one config in newer release, because
it's hard to define what kind of config is host independent.

## start.go

- TODO: setupSdNotify(spec, rspec, notifySocket)
- TODO: setupSocketActivation(spec, listenFds)
- TODO: newTty
- TODO: what's the difference between setup in `runc start` and `runc init`

Function call "status, err := startContainer(context, spec, rspec)" sets up all
environment and start container.

In startContainer, a configs.Config is created, which is defined in libcontainer.
It is a container configuration. Information in this config is copied from config.json
and runtime.json. (see createLibcontainerConfig).

startContainer then uses libcontainer/factory* to create a container factory. When
creating container, the factory will be passed a container id and config (libcontainer
config). It will be responsible of creating a virtual container (a Container interface
in libcontainer).

startContainer uses a function Cgroupfs() in factory_linux.go. The function tells
runtime to use linux file API to manage cgroups, i.e. to apply memeory limit, set
the value to file path directly, e.g. /sys/fs/cgroup/memory.

runc uses something called 'option func' to configure the factory, like the above
Cgroupfs(). There is another such option func: InitArgs. It provides parameters
for the init process of the container. It uses "/proc/self/exe" as the init process;
since use 'runc' to start current process, "/proc/self/exe" links to /usr/local/bin/runc.

In runc, containerRoot is "/run/opencontainer/containers/{id}".

After creating container object (linuxContainer, which implements Container interface),
runc then calls "container.Start(process)" to start container. process is an object
created based on config.json.

In container.Start(), container status is checked at first. If there is a file
'checkpoint' under container root, then container status is Checkpointed. If initProcess
is nil, then container status is Destroyed.

For starting a new container, the status will be Destroyed. runc (libcontainer)
then creates a newInitProcess (called from newParentProcess). The init process's
cmd.Path is "/proc/self/exec" (which is runc); cmd.Args is ["/usr/local/bin/runc", "init"]

Thereafter, initProcess.start is called. It uses cmd.Start() to start the init
process. Up to this point, user command hasn't been ran yet, i.e.
```
$ ps aux | grep runc
root      4389  0.0  0.1  65732  2116 pts/2    S+   03:19   0:00 sudo runc --id busybox start
root      4390 92.6  0.1 195540  3516 pts/2    Sl+  03:19   0:07 runc --id busybox start
root      4398  0.0  0.1  39880  2992 pts/2    Sl+  03:19   0:00 /usr/local/bin/runc init
```
The newly forked process is "/usr/local/bin/runc init". In summary, initProcess.cmd
is "runc init", while user command is in initProcess.config. "runc init" is the
init process in container. "run start" is the parent process of "run init".

Once "runc init" (above process 4398) gets started, "runc start" (above process
4390) starts setting up it.
 1. records "runc init"'s file descriptors;
 2. apply cgroup to it;
 3. call hooks from runtime.json;
 4. create network interface config;
 5. send init config. The init config is the config used to start user command
    (config.json), e.g. "sh" for running busybox directly. Config is sent via
    socketpair: "runc init" has child pipe and "runc start" has parent pipe.
 6. After config is sent, "runc start" waits for the child process to fully complete.
    Just as sending config, it waits by reading from parent pipe. This waiting will
    finish quickly, since it is waiting for "runc init", not "sh". (i.e. wait init
    process, not user process).

init process resides in start.go#init(). It reads config from parent and setup
the container. It then uses initProcess.config to start user program, i.e.
  system.Execv(l.config.Args[0], l.config.Args[0:], os.Environ())
The code located in standard_init_linux.go.

"runc start" will then wait for user process to finish (range signals in file signals.go).

## container init process

To summarize above start.go. "runc start" prepares a ParentProcess for the container.
The ParentProcess sits outside of the container. For start, the ParentProcess
is also called InitProcess; for join container, the ParentProcess is called
SetnsProcess. After ParentProcess is created (a struct, not an actual process),
it runs p.cmd.Start(). 'p' is the ParentProcess; cmd is the command struct for
the init process in container (runc init). Real user command is in p.config.
Note here ParentProcess == InitProcess, and the real init process in container
is ParentProcess.cmd.

Now init process starts running (start.go#init). It mainly calls factory_linux.go#StartInitialization
to finish its job. StartInitialization loads a container by opening the pipe
fd from the parent to read the configuration and state. In StartInitialization(),
the init process still runs in host environment; we can verify this by doing
"ioutil.WriteFile("/tmp/abc", []byte("abc"), 777)", which will write to host
filesystem. standard_init_linux.go#Init() is the place where the actual container
environment is setup; we can verity this by also writing a file: this time, the
file will be written to container filesystem. Note, to write file in this case,
we need to make sure container user has the right privilege. For busybox example,
config.json#process.user.uid=100, process.user.gid=100.

## network

Parent process network setup is p.createNetworkInterfaces(), which fills in
libcontainer network config struct and creates network interfaces (e.g. lo, veth);
the real work of network setup is in the init process of the container, i.e.
in standard_init_linux.go#Init. Note network setup here only deals with container's
network namespace; for inter-container communication, the work is done in other
places, e.g. libnetwork, cni.

# Workflow

## update as ov v1.0.0-rc1

*Update on 08/14/2016, v1.0.0-rc1, changes since v0.0.6*

Basic idea is the same, e.g. use `runc run` is the parent process of the new container; it uses
cmd.Start() to start `runc init`, which is the init process of the container; `runc init` does
quite a few setup then exec user command.

A brief scan yields the following major difference:
- bundle: only a single config.json
- start.go: semantic has changed to run.go, i.e. `runc start` -> `runc run`
- `runc init` code resides in main_unix.go, main_solarios.go, etc

# Experiments

*Date 03/18/2018, v1.0.0-rc5*

## Get runc binary

Download latest version of runc:

    $ wget https://github.com/opencontainers/runc/releases/download/v1.0.0-rc5/runc.amd64
    $ sudo chmod u+x runc.amd64 && mv runc.amd64 /usr/local/bin/runc

## Install docker

To make it easy to run 'runc' container, we simply use docker to create OCI bundle.

    $ sudo apt-get update
    $ sudo apt-get install \
          apt-transport-https \
          ca-certificates \
          curl \
          software-properties-common
    $ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    $ sudo add-apt-repository \
         "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
         $(lsb_release -cs) \
         stable"
    $ sudo apt-get update
    $ sudo apt-get install docker-ce
    $ sudo groupadd docker
    $ sudo usermod -aG docker $USER

## Create OCI bundle

Create our container root filesystem:

    # create the top most bundle directory
    mkdir /tmp/mycontainer
    cd /tmp/mycontainer

    # create the rootfs directory
    mkdir rootfs

    # export busybox via Docker into the rootfs directory
    docker export $(docker create busybox) | tar -C rootfs -xvf -

After a root filesystem is populated you just generate a spec in the format of a 'config.json'
file inside your bundle.

    $ runc spec

## Run container

Using the following command will start our container:

    $ sudo runc run mycontainerid
    / #

Note that we get a tty from runc. If we run `ps` from another terminal, we'll see two processes:

    root      4391  0.0  0.0  51420  4012 pts/0    S+   15:15   0:00 sudo runc run mycontainerid
    root      4392  0.0  0.1 675544  6700 pts/0    Sl+  15:15   0:00 runc run mycontainerid

The second process is created from 'sudo' (sudo calls setuid and forks a child
to actually execute our program). Remember that runc is a command line tool.
In our example above, we recieve a tty from runc thus we can execute command
in the terminal. If we set terminal to false in config.json and change command
arg to something like ['sleep', '15'], our runc container will run in foreground
and will return in 10s, just like executing 'sleep 15' directly in terminal.

## Create/Start container

In addition to directly run a container, we can also create a container and
start it. As mentioned in README, we need to edit 'config.json' to remove
"terminal:true" as well as adding container arguments (sleep 15). Once edited,
we are able to list containers.

    $ sudo runc create mycontainerid
    $ sudo runc list
    ID              PID         STATUS      BUNDLE             CREATED                          OWNER
    mycontainerid   5494        created     /tmp/mycontainer   2018-03-18T02:54:47.765527187Z   root

    # container is not running
    $ ps aux | grep runc
    root      4522  0.0  0.2 451724  9188 ?        Ssl  16:01   0:00 runc init
    vagrant   4543  0.0  0.0  12944   980 pts/0    S+   16:01   0:00 grep --color=auto runc

    # start the process inside the container; container is running in background
    $ sudo runc start mycontainerid
    $ ps aux | grep sle
    root      5494  0.0  0.0   1228     4 ?        Ss   02:54   0:00 sleep 15
    vagrant   5522  0.0  0.0  12944  1028 pts/0    S+   02:55   0:00 grep --color=auto sle

    # after 15 seconds view that the container has exited and is now in the stopped state
    $ sudo runc list
    ID              PID         STATUS      BUNDLE             CREATED                          OWNER
    mycontainerid   0           stopped     /tmp/mycontainer   2018-03-18T02:54:47.765527187Z   root

    # now delete the container
    $ sudo runc delete mycontainerid
    #+END_SRC

## Rootless container

Follow runc README to start a rootless container, we'll see that runc starts the container with
normal user, and there is only one process running (instead of two processes started from sudo,
as above).

    vagrant   4952  0.0  0.2 675896  9684 pts/0    Sl+  01:50   0:00 runc --root /tmp/runc run mycontainerid

## References

https://github.com/opencontainers/runc/tree/v1.0.0-rc5
