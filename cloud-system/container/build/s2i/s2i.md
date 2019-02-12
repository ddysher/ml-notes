<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Source-to-Image (S2I) is a toolkit and workflow for building reproducible Docker images from source
code. S2I produces ready-to-run images by injecting source code into a Docker container and letting
the container prepare that source code for execution.

# Workflow

Following is a short analysis of the workflow behind command:

```sh
s2i build https://github.com/openshift/django-ex centos/python-35-centos7 hello-python
```

The first argument to `s2i build` is the source repository, second argument is the build image.
For dynamic language, this is also the runtime image; for static language, we can pass "--runtime-image"
parameter.

As required by s2i, builder image must contain scripts named `assemble`, `run`, etc. For image
`centos/python-35-centos7`, it has `assemble`, `run` and `usage` scripts, located at `/usr/libexec/s2i`.
For more information, see:
- https://github.com/openshift/source-to-image/blob/v1.1.11/docs/builder_image.md
- https://github.com/openshift/source-to-image/blob/v1.1.11/docs/runtime_image.md

The command above will generate Dockerfile (using string concatenation) and build an image using
this Dockerfile:

<details><summary>Build process</summary><p>

```
$ s2i build https://github.com/openshift/django-ex centos/python-35-centos7 hello-python --loglevel 5
I0708 09:03:32.164680   27226 build.go:50] Running S2I version "unknown"
I0708 09:03:32.164824   27226 util.go:58] Getting docker credentials for centos/python-35-centos7
I0708 09:03:32.164848   27226 util.go:74] Using  credentials for pulling centos/python-35-centos7
I0708 09:03:32.167926   27226 docker.go:485] Using locally available image "centos/python-35-centos7:latest"
I0708 09:03:32.170145   27226 build.go:165]
Builder Name:                   Python 3.5
Builder Image:                  centos/python-35-centos7
Builder Image Version:          "577297a"
Source:                         https://github.com/openshift/django-ex
Output Image Tag:               hello-python
Environment:
Labels:
Incremental Build:              disabled
Remove Old Build:               disabled
Builder Pull Policy:            if-not-present
Previous Image Pull Policy:     if-not-present
Quiet:                          disabled
Layered Build:                  disabled
Docker Endpoint:                unix:///var/run/docker.sock
Docker Pull Config:             /home/deyuan/.docker/config.json
Docker Pull User:               ddysher

I0708 09:03:32.171839   27226 docker.go:485] Using locally available image "centos/python-35-centos7:latest"
I0708 09:03:32.176059   27226 docker.go:485] Using locally available image "centos/python-35-centos7:latest"
I0708 09:03:32.176077   27226 docker.go:716] Image sha256:7847001b4856d42eaf5a0cf9ca4236b653616637c089c96f1ed42e2b6708a2ac contains io.openshift.s2i.scripts-url set to "image:///usr/libexec/s2i"
I0708 09:03:32.176097   27226 scm.go:20] DownloadForSource https://github.com/openshift/django-ex
I0708 09:03:32.176127   27226 sti.go:199] Preparing to build hello-python
I0708 09:03:32.176202   27226 clone.go:36] Downloading "https://github.com/openshift/django-ex" ...
I0708 09:03:32.176214   27226 clone.go:40] Cloning sources into "/tmp/s2i718143045/upload/src"
Your branch is up to date with 'origin/master'.
I0708 09:03:34.847128   27226 clone.go:56] Checked out "HEAD"
I0708 09:03:34.878468   27226 clone.go:62] Updated submodules for "HEAD"
I0708 09:03:34.888504   27226 install.go:261] Using "assemble" installed from "image:///usr/libexec/s2i/assemble"
I0708 09:03:34.888535   27226 install.go:261] Using "run" installed from "image:///usr/libexec/s2i/run"
I0708 09:03:34.888547   27226 install.go:261] Using "save-artifacts" installed from "image:///usr/libexec/s2i/save-artifacts"
I0708 09:03:34.888560   27226 ignore.go:64] .s2iignore file does not exist
I0708 09:03:34.888566   27226 sti.go:208] Clean build will be performed
I0708 09:03:34.888571   27226 sti.go:211] Performing source build from https://github.com/openshift/django-ex
I0708 09:03:34.888576   27226 sti.go:222] Running "assemble" in "hello-python"
I0708 09:03:34.888580   27226 sti.go:562] Using image name centos/python-35-centos7
I0708 09:03:34.891650   27226 docker.go:485] Using locally available image "centos/python-35-centos7:latest"
I0708 09:03:34.891688   27226 sti.go:448] No user environment provided (no environment file found in application sources)
I0708 09:03:34.891717   27226 sti.go:676] starting the source uploading ...
I0708 09:03:34.891730   27226 tar.go:217] Adding "/tmp/s2i718143045/upload" to tar ...
I0708 09:03:34.891865   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/scripts as scripts
I0708 09:03:34.893968   27226 docker.go:716] Image sha256:7847001b4856d42eaf5a0cf9ca4236b653616637c089c96f1ed42e2b6708a2ac contains io.openshift.s2i.scripts-url set to "image:///usr/libexec/s2i"
I0708 09:03:34.893977   27226 docker.go:790] Base directory for S2I scripts is '/usr/libexec/s2i'. Untarring destination is '/tmp'.
I0708 09:03:34.893985   27226 docker.go:947] Setting "/bin/sh -c tar -C /tmp -xf - && /usr/libexec/s2i/assemble" command for container ...
I0708 09:03:34.894041   27226 docker.go:956] Creating container with options {Name:"s2i_centos_python_35_centos7_57241fc0" Config:{Hostname: Domainname: User: AttachStdin:fal
se AttachStdout:true AttachStderr:false ExposedPorts:map[] Tty:false OpenStdin:true StdinOnce:true Env:[] Cmd:[/bin/sh -c tar -C /tmp -xf - && /usr/libexec/s2i/assemble] Heal
thcheck:<nil> ArgsEscaped:false Image:centos/python-35-centos7:latest Volumes:map[] WorkingDir: Entrypoint:[] NetworkDisabled:false MacAddress: OnBuild:[] Labels:map[] StopSi
gnal: StopTimeout:<nil> Shell:[]} HostConfig:&{Binds:[] ContainerIDFile: LogConfig:{Type: Config:map[]} NetworkMode: PortBindings:map[] RestartPolicy:{Name: MaximumRetryCount
:0} AutoRemove:false VolumeDriver: VolumesFrom:[] CapAdd:[] CapDrop:[] DNS:[] DNSOptions:[] DNSSearch:[] ExtraHosts:[] GroupAdd:[] IpcMode: Cgroup: Links:[] OomScoreAdj:0 Pid
Mode: Privileged:false PublishAllPorts:false ReadonlyRootfs:false SecurityOpt:[] StorageOpt:map[] Tmpfs:map[] UTSMode: UsernsMode: ShmSize:67108864 Sysctls:map[] Runtime: Con
soleSize:[0 0] Isolation: Resources:{CPUShares:0 Memory:0 NanoCPUs:0 CgroupParent: BlkioWeight:0 BlkioWeightDevice:[] BlkioDeviceReadBps:[] BlkioDeviceWriteBps:[] BlkioDevice
ReadIOps:[] BlkioDeviceWriteIOps:[] CPUPeriod:0 CPUQuota:0 CPURealtimePeriod:0 CPURealtimeRuntime:0 CpusetCpus: CpusetMems: Devices:[] DeviceCgroupRules:[] DiskQuota:0 Kernel
Memory:0 MemoryReservation:0 MemorySwap:0 MemorySwappiness:<nil> OomKillDisable:<nil> PidsLimit:0 Ulimits:[] CPUCount:0 CPUPercent:0 IOMaximumIOps:0 IOMaximumBandwidth:0} Mou
nts:[] Init:<nil>}} ...
I0708 09:03:34.973819   27226 docker.go:988] Attaching to container "cc6e5a59663a64532b3ba420879690cbaf09bd6062a3580cad29966a600f8364" ...
I0708 09:03:34.974188   27226 docker.go:999] Starting container "cc6e5a59663a64532b3ba420879690cbaf09bd6062a3580cad29966a600f8364" ...
I0708 09:03:35.249838   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src as src
I0708 09:03:35.250193   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/.gitignore as src/.gitignore
I0708 09:03:35.250259   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/README.md as src/README.md
I0708 09:03:35.250338   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/conf as src/conf
I0708 09:03:35.250394   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/conf/reload.py as src/conf/reload.py
I0708 09:03:35.250443   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/manage.py as src/manage.py
I0708 09:03:35.250529   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift as src/openshift
I0708 09:03:35.250589   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/scripts as src/openshift/scripts
I0708 09:03:35.250629   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/scripts/run-in-container.sh as src/openshift/scripts/run-in-container.sh
I0708 09:03:35.250699   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/templates as src/openshift/templates
I0708 09:03:35.250748   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/templates/django-postgresql-persistent.json as src/openshift/templates/django-postgresql-persistent.json
I0708 09:03:35.250801   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/templates/django-postgresql.json as src/openshift/templates/django-postgresql.json
I0708 09:03:35.250869   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/openshift/templates/django.json as src/openshift/templates/django.json
I0708 09:03:35.250944   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/project as src/project
I0708 09:03:35.250983   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/project/__init__.py as src/project/__init__.py
I0708 09:03:35.251033   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/project/database.py as src/project/database.py
I0708 09:03:35.251085   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/project/settings.py as src/project/settings.py
I0708 09:03:35.251142   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/project/urls.py as src/project/urls.py
I0708 09:03:35.251189   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/requirements.txt as src/requirements.txt
I0708 09:03:35.251244   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome as src/welcome
I0708 09:03:35.251271   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/__init__.py as src/welcome/__init__.py
I0708 09:03:35.251304   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/admin.py as src/welcome/admin.py
I0708 09:03:35.251343   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/database.py as src/welcome/database.py
I0708 09:03:35.251394   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/migrations as src/welcome/migrations
I0708 09:03:35.251430   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/migrations/0001_initial.py as src/welcome/migrations/0001_initial.py
I0708 09:03:35.251491   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/migrations/__init__.py as src/welcome/migrations/__init__.py
I0708 09:03:35.251536   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/models.py as src/welcome/models.py
I0708 09:03:35.251605   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/templates as src/welcome/templates
I0708 09:03:35.251647   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/templates/welcome as src/welcome/templates/welcome
I0708 09:03:35.251681   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/templates/welcome/index.html as src/welcome/templates/welcome/index.html
I0708 09:03:35.251734   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/tests.py as src/welcome/tests.py
I0708 09:03:35.251782   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/welcome/views.py as src/welcome/views.py
I0708 09:03:35.251836   27226 tar.go:312] Adding to tar: /tmp/s2i718143045/upload/src/wsgi.py as src/wsgi.py
I0708 09:03:35.254417   27226 sti.go:684] ---> Installing application source ...
I0708 09:03:35.256152   27226 sti.go:684] ---> Installing dependencies ...
I0708 09:03:35.565317   27226 sti.go:684] Collecting django<1.12,>=1.11 (from -r requirements.txt (line 1))
I0708 09:03:41.128106   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/bf/e0/e659df5b5b82299fffd8b3df2910c99351b9308b8f45f5702cc4cdf946e9/Django-1.11.14-py2.py3-none-any.whl (7.0MB)
I0708 09:05:44.086376   27226 sti.go:684] Collecting django-debug-toolbar==1.8 (from -r requirements.txt (line 2))
I0708 09:05:47.443054   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/b1/a2/973ab30ad33b5676a552cbc5d906074f4f360f362e9b5a71b4e4dceea70c/django_debug_toolbar-1.8-py2.py3-none-any.whl (205kB)
I0708 09:05:51.784061   27226 sti.go:684] Collecting gunicorn==19.4.5 (from -r requirements.txt (line 3))
I0708 09:05:54.408268   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/bd/4c/1c4131c6082a9cbad894b308097c9ff2e947f331c54aa2daa8e657108eb8/gunicorn-19.4.5-py2.py3-none-any.whl (112kB)
I0708 09:05:58.214975   27226 sti.go:684] Collecting psycopg2==2.7.3.1 (from -r requirements.txt (line 4))
I0708 09:06:01.082174   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/6b/fb/15c687eda2f925f0ff59373063fdb408471b4284714a7761daaa65c01f15/psycopg2-2.7.3.1.tar.gz (425kB)
I0708 09:06:12.325180   27226 sti.go:684] Collecting whitenoise==3.3.1 (from -r requirements.txt (line 5))
I0708 09:06:15.330502   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/0c/58/0f309a821b9161d0e3a73336a187d1541c2127aff7fdf3bf7293f9979d1d/whitenoise-3.3.1-py2.py3-none-any.whl
I0708 09:06:15.820993   27226 sti.go:684] Collecting pytz (from django<1.12,>=1.11->-r requirements.txt (line 1))
I0708 09:06:29.962464   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/30/4e/27c34b62430286c6d59177a0842ed90dc789ce5d1ed740887653b898779a/pytz-2018.5-py2.py3-none-any.whl (510kB)
I0708 09:06:42.452927   27226 sti.go:684] Collecting sqlparse>=0.2.0 (from django-debug-toolbar==1.8->-r requirements.txt (line 2))
I0708 09:06:45.352178   27226 sti.go:684] Downloading https://files.pythonhosted.org/packages/65/85/20bdd72f4537cf2c4d5d005368d502b2f464ede22982e724a82c86268eda/sqlparse-0.2.4-py2.py3-none-any.whl
I0708 09:06:46.173690   27226 sti.go:684] Installing collected packages: pytz, django, sqlparse, django-debug-toolbar, gunicorn, psycopg2, whitenoise
I0708 09:06:48.133256   27226 sti.go:684] Running setup.py install for psycopg2
I0708 09:06:58.111476   27226 sti.go:684] Successfully installed django-1.11.14 django-debug-toolbar-1.8 gunicorn-19.4.5 psycopg2-2.7.3.1 pytz-2018.5 sqlparse-0.2.4 whitenoise-3.3.1
I0708 09:07:01.130172   27226 sti.go:688] You are using pip version 7.1.2, however version 10.0.1 is available.
I0708 09:07:01.130188   27226 sti.go:688] You should consider upgrading via the 'pip install --upgrade pip' command.
I0708 09:07:01.208334   27226 sti.go:684] ---> Collecting Django static files ...
I0708 09:07:01.726435   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/changelists.css'
I0708 09:07:01.726712   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/rtl.css'
I0708 09:07:01.726906   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/base.css'
I0708 09:07:01.727112   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/fonts.css'
I0708 09:07:01.727315   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/forms.css'
I0708 09:07:01.727524   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/login.css'
I0708 09:07:01.727715   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/widgets.css'
I0708 09:07:01.727915   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/css/dashboard.css'
I0708 09:07:01.728283   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/actions.js'
I0708 09:07:01.728525   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/core.js'
I0708 09:07:01.728739   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/prepopulate.min.js'
I0708 09:07:01.728931   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/SelectFilter2.js'
I0708 09:07:01.729131   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/collapse.js'
I0708 09:07:01.729320   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/timeparse.js'
I0708 09:07:01.729540   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/jquery.init.js'
I0708 09:07:01.729735   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/inlines.js'
I0708 09:07:01.730043   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/prepopulate.js'
I0708 09:07:01.730263   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/inlines.min.js'
I0708 09:07:01.730549   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/calendar.js'
I0708 09:07:01.730778   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/SelectBox.js'
I0708 09:07:01.731023   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/popup_response.js'
I0708 09:07:01.731248   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/collapse.min.js'
I0708 09:07:01.731446   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/actions.min.js'
I0708 09:07:01.731689   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/cancel.js'
I0708 09:07:01.731906   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/prepopulate_init.js'
I0708 09:07:01.732091   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/urlify.js'
I0708 09:07:01.732293   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/change_form.js'
I0708 09:07:01.732588   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/xregexp/LICENSE-XREGEXP.txt'
I0708 09:07:01.732862   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/xregexp/xregexp.min.js'
I0708 09:07:01.733119   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/xregexp/xregexp.js'
I0708 09:07:01.733450   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/jquery/LICENSE-JQUERY.txt'
I0708 09:07:01.733689   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/jquery/jquery.min.js'
I0708 09:07:01.733963   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/vendor/jquery/jquery.js'
I0708 09:07:01.734381   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/admin/RelatedObjectLookups.js'
I0708 09:07:01.734694   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/js/admin/DateTimeShortcuts.js'
I0708 09:07:01.735085   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/LICENSE'
I0708 09:07:01.735341   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/calendar-icons.svg'
I0708 09:07:01.735616   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/search.svg'
I0708 09:07:01.735898   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/selector-icons.svg'
I0708 09:07:01.736141   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/inline-delete.svg'
I0708 09:07:01.736404   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-addlink.svg'
I0708 09:07:01.736679   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-yes.svg'
I0708 09:07:01.736915   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-clock.svg'
I0708 09:07:01.737158   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-changelink.svg'
I0708 09:07:01.737367   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-no.svg'
I0708 09:07:01.737564   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-unknown-alt.svg'
I0708 09:07:01.737787   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-alert.svg'
I0708 09:07:01.738022   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-calendar.svg'
I0708 09:07:01.738273   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/README.txt'
I0708 09:07:01.738508   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/tooltag-arrowright.svg'
I0708 09:07:01.738729   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-deletelink.svg'
I0708 09:07:01.738926   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/sorting-icons.svg'
I0708 09:07:01.739141   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/icon-unknown.svg'
I0708 09:07:01.739394   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/tooltag-add.svg'
I0708 09:07:01.739655   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/gis/move_vertex_off.svg'
I0708 09:07:01.739905   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/img/gis/move_vertex_on.svg'
I0708 09:07:01.740190   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/fonts/Roboto-Bold-webfont.woff'
I0708 09:07:01.740466   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/fonts/LICENSE.txt'
I0708 09:07:01.740674   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/fonts/Roboto-Light-webfont.woff'
I0708 09:07:01.740927   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/fonts/README.txt'
I0708 09:07:01.741141   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/django/contrib/admin/static/admin/fonts/Roboto-Regular-webfont.woff'
I0708 09:07:01.741511   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/css/toolbar.css'
I0708 09:07:01.741796   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/css/print.css'
I0708 09:07:01.742081   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/jquery_post.js'
I0708 09:07:01.742304   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/toolbar.profiling.js'
I0708 09:07:01.742557   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/jquery_existing.js'
I0708 09:07:01.742791   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/toolbar.template.js'
I0708 09:07:01.743035   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/toolbar.sql.js'
I0708 09:07:01.743255   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/toolbar.timer.js'
I0708 09:07:01.743460   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/toolbar.js'
I0708 09:07:01.743660   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/js/jquery_pre.js'
I0708 09:07:01.743942   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/back.png'
I0708 09:07:01.744167   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/ajax-loader.gif'
I0708 09:07:01.744370   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/close_hover.png'
I0708 09:07:01.744601   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/close.png'
I0708 09:07:01.744823   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/indicator.png'
I0708 09:07:01.745033   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/djdt_vertical.png'
I0708 09:07:01.745250   27226 sti.go:684] Copying '/opt/app-root/lib/python3.5/site-packages/debug_toolbar/static/debug_toolbar/img/back_hover.png'
I0708 09:07:01.746751   27226 sti.go:684] Post-processed 'admin/js/vendor/xregexp/LICENSE-XREGEXP.txt' as 'admin/js/vendor/xregexp/LICENSE-XREGEXP.d64cecf4f157.txt'
I0708 09:07:01.751561   27226 sti.go:684] Post-processed 'admin/js/vendor/xregexp/xregexp.min.js' as 'admin/js/vendor/xregexp/xregexp.min.c95393b8ca4d.js'
I0708 09:07:01.765910   27226 sti.go:684] Post-processed 'admin/js/vendor/xregexp/xregexp.js' as 'admin/js/vendor/xregexp/xregexp.1865b1cf5085.js'
I0708 09:07:01.766475   27226 sti.go:684] Post-processed 'admin/js/vendor/jquery/LICENSE-JQUERY.txt' as 'admin/js/vendor/jquery/LICENSE-JQUERY.a158210a2737.txt'
I0708 09:07:01.776826   27226 sti.go:684] Post-processed 'admin/js/vendor/jquery/jquery.min.js' as 'admin/js/vendor/jquery/jquery.min.33cabfa15c10.js'
I0708 09:07:01.823621   27226 sti.go:684] Post-processed 'admin/js/vendor/jquery/jquery.js' as 'admin/js/vendor/jquery/jquery.aacc43d6f308.js'
I0708 09:07:01.824446   27226 sti.go:684] Post-processed 'admin/js/admin/RelatedObjectLookups.js' as 'admin/js/admin/RelatedObjectLookups.d2bdb1018963.js'
I0708 09:07:01.826195   27226 sti.go:684] Post-processed 'admin/js/admin/DateTimeShortcuts.js' as 'admin/js/admin/DateTimeShortcuts.1536fb6bea1d.js'
I0708 09:07:01.826751   27226 sti.go:684] Post-processed 'admin/img/gis/move_vertex_off.svg' as 'admin/img/gis/move_vertex_off.7a23bf31ef8a.svg'
I0708 09:07:01.827232   27226 sti.go:684] Post-processed 'admin/img/gis/move_vertex_on.svg' as 'admin/img/gis/move_vertex_on.0047eba25b67.svg'
I0708 09:07:01.828303   27226 sti.go:684] Post-processed 'admin/css/changelists.css' as 'admin/css/changelists.f6dc691f8d62.css'
I0708 09:07:01.829140   27226 sti.go:684] Post-processed 'admin/css/rtl.css' as 'admin/css/rtl.4c867197b256.css'
I0708 09:07:01.832585   27226 sti.go:684] Post-processed 'admin/css/base.css' as 'admin/css/base.31652d31b392.css'
I0708 09:07:01.834053   27226 sti.go:684] Post-processed 'admin/css/fonts.css' as 'admin/css/fonts.494e4ec545c9.css'
I0708 09:07:01.836361   27226 sti.go:684] Post-processed 'admin/css/forms.css' as 'admin/css/forms.15ebfebbeb3d.css'
I0708 09:07:01.837001   27226 sti.go:684] Post-processed 'admin/css/login.css' as 'admin/css/login.a846c0e2ef65.css'
I0708 09:07:01.840468   27226 sti.go:684] Post-processed 'admin/css/widgets.css' as 'admin/css/widgets.5e372b41c483.css'
I0708 09:07:01.841229   27226 sti.go:684] Post-processed 'admin/css/dashboard.css' as 'admin/css/dashboard.7ac78187c567.css'
I0708 09:07:01.842206   27226 sti.go:684] Post-processed 'admin/js/actions.js' as 'admin/js/actions.32861b6cbdf9.js'
I0708 09:07:01.843111   27226 sti.go:684] Post-processed 'admin/js/core.js' as 'admin/js/core.fd861d43f0f5.js'
I0708 09:07:01.843572   27226 sti.go:684] Post-processed 'admin/js/prepopulate.min.js' as 'admin/js/prepopulate.min.f4057ebb9b62.js'
I0708 09:07:01.844844   27226 sti.go:684] Post-processed 'admin/js/SelectFilter2.js' as 'admin/js/SelectFilter2.17009b6d4428.js'
I0708 09:07:01.845456   27226 sti.go:684] Post-processed 'admin/js/collapse.js' as 'admin/js/collapse.17d715df2104.js'
I0708 09:07:01.846125   27226 sti.go:684] Post-processed 'admin/js/timeparse.js' as 'admin/js/timeparse.51258861a46a.js'
I0708 09:07:01.846651   27226 sti.go:684] Post-processed 'admin/js/jquery.init.js' as 'admin/js/jquery.init.95b62fa19378.js'
I0708 09:07:01.848075   27226 sti.go:684] Post-processed 'admin/js/inlines.js' as 'admin/js/inlines.eda404ee376d.js'
I0708 09:07:01.848681   27226 sti.go:684] Post-processed 'admin/js/prepopulate.js' as 'admin/js/prepopulate.ff9208865444.js'
I0708 09:07:01.849271   27226 sti.go:684] Post-processed 'admin/js/inlines.min.js' as 'admin/js/inlines.min.d75b9ed03975.js'
I0708 09:07:01.850459   27226 sti.go:684] Post-processed 'admin/js/calendar.js' as 'admin/js/calendar.9ac94d055fbd.js'
I0708 09:07:01.851167   27226 sti.go:684] Post-processed 'admin/js/SelectBox.js' as 'admin/js/SelectBox.b49f008d186b.js'
I0708 09:07:01.851649   27226 sti.go:684] Post-processed 'admin/js/popup_response.js' as 'admin/js/popup_response.6ce3197f8fc8.js'
I0708 09:07:01.852108   27226 sti.go:684] Post-processed 'admin/js/collapse.min.js' as 'admin/js/collapse.min.dc930adb2821.js'
I0708 09:07:01.852631   27226 sti.go:684] Post-processed 'admin/js/actions.min.js' as 'admin/js/actions.min.f51f04edab28.js'
I0708 09:07:01.853050   27226 sti.go:684] Post-processed 'admin/js/cancel.js' as 'admin/js/cancel.1d69cba4b4bf.js'
I0708 09:07:01.853505   27226 sti.go:684] Post-processed 'admin/js/prepopulate_init.js' as 'admin/js/prepopulate_init.0d3b53c37074.js'
I0708 09:07:01.855168   27226 sti.go:684] Post-processed 'admin/js/urlify.js' as 'admin/js/urlify.411bc3bb651c.js'
I0708 09:07:01.855632   27226 sti.go:684] Post-processed 'admin/js/change_form.js' as 'admin/js/change_form.9e85003a1a38.js'
I0708 09:07:01.856136   27226 sti.go:684] Post-processed 'admin/img/LICENSE' as 'admin/img/LICENSE.2c54f4e1ca1c'
I0708 09:07:01.856725   27226 sti.go:684] Post-processed 'admin/img/calendar-icons.svg' as 'admin/img/calendar-icons.39b290681a8b.svg'
I0708 09:07:01.857184   27226 sti.go:684] Post-processed 'admin/img/search.svg' as 'admin/img/search.7cf54ff789c6.svg'
I0708 09:07:01.857791   27226 sti.go:684] Post-processed 'admin/img/selector-icons.svg' as 'admin/img/selector-icons.b4555096cea2.svg'
I0708 09:07:01.858236   27226 sti.go:684] Post-processed 'admin/img/inline-delete.svg' as 'admin/img/inline-delete.fec1b761f254.svg'
I0708 09:07:01.858718   27226 sti.go:684] Post-processed 'admin/img/icon-addlink.svg' as 'admin/img/icon-addlink.d519b3bab011.svg'
I0708 09:07:01.859147   27226 sti.go:684] Post-processed 'admin/img/icon-yes.svg' as 'admin/img/icon-yes.d2f9f035226a.svg'
I0708 09:07:01.859619   27226 sti.go:684] Post-processed 'admin/img/icon-clock.svg' as 'admin/img/icon-clock.e1d4dfac3f2b.svg'
I0708 09:07:01.860054   27226 sti.go:684] Post-processed 'admin/img/icon-changelink.svg' as 'admin/img/icon-changelink.18d2fd706348.svg'
I0708 09:07:01.860515   27226 sti.go:684] Post-processed 'admin/img/icon-no.svg' as 'admin/img/icon-no.439e821418cd.svg'
I0708 09:07:01.861025   27226 sti.go:684] Post-processed 'admin/img/icon-unknown-alt.svg' as 'admin/img/icon-unknown-alt.81536e128bb6.svg'
I0708 09:07:01.861496   27226 sti.go:684] Post-processed 'admin/img/icon-alert.svg' as 'admin/img/icon-alert.034cc7d8a67f.svg'
I0708 09:07:01.861979   27226 sti.go:684] Post-processed 'admin/img/icon-calendar.svg' as 'admin/img/icon-calendar.ac7aea671bea.svg'
I0708 09:07:01.862430   27226 sti.go:684] Post-processed 'admin/img/README.txt' as 'admin/img/README.837277fa1908.txt'
I0708 09:07:01.862882   27226 sti.go:684] Post-processed 'admin/img/tooltag-arrowright.svg' as 'admin/img/tooltag-arrowright.bbfb788a849e.svg'
I0708 09:07:01.863378   27226 sti.go:684] Post-processed 'admin/img/icon-deletelink.svg' as 'admin/img/icon-deletelink.564ef9dc3854.svg'
I0708 09:07:01.863868   27226 sti.go:684] Post-processed 'admin/img/sorting-icons.svg' as 'admin/img/sorting-icons.3a097b59f104.svg'
I0708 09:07:01.864361   27226 sti.go:684] Post-processed 'admin/img/icon-unknown.svg' as 'admin/img/icon-unknown.a18cb4398978.svg'
I0708 09:07:01.864796   27226 sti.go:684] Post-processed 'admin/img/tooltag-add.svg' as 'admin/img/tooltag-add.e59d620a9742.svg'
I0708 09:07:01.865188   27226 sti.go:684] Post-processed 'admin/fonts/Roboto-Bold-webfont.woff' as 'admin/fonts/Roboto-Bold-webfont.2ad99072841e.woff'
I0708 09:07:01.866291   27226 sti.go:684] Post-processed 'admin/fonts/LICENSE.txt' as 'admin/fonts/LICENSE.d273d63619c9.txt'
I0708 09:07:01.866758   27226 sti.go:684] Post-processed 'admin/fonts/Roboto-Light-webfont.woff' as 'admin/fonts/Roboto-Light-webfont.b446c2399bb6.woff'
I0708 09:07:01.867191   27226 sti.go:684] Post-processed 'admin/fonts/README.txt' as 'admin/fonts/README.2c3d0bcdede2.txt'
I0708 09:07:01.867600   27226 sti.go:684] Post-processed 'admin/fonts/Roboto-Regular-webfont.woff' as 'admin/fonts/Roboto-Regular-webfont.ec39515ae8c6.woff'
I0708 09:07:01.869822   27226 sti.go:684] Post-processed 'debug_toolbar/css/toolbar.css' as 'debug_toolbar/css/toolbar.b35523ea26ab.css'
I0708 09:07:01.870384   27226 sti.go:684] Post-processed 'debug_toolbar/css/print.css' as 'debug_toolbar/css/print.85b39f60bfe8.css'
I0708 09:07:01.870797   27226 sti.go:684] Post-processed 'debug_toolbar/js/jquery_post.js' as 'debug_toolbar/js/jquery_post.8c9db3d1cebc.js'
I0708 09:07:01.871300   27226 sti.go:684] Post-processed 'debug_toolbar/js/toolbar.profiling.js' as 'debug_toolbar/js/toolbar.profiling.13e030bebb35.js'
I0708 09:07:01.871691   27226 sti.go:684] Post-processed 'debug_toolbar/js/jquery_existing.js' as 'debug_toolbar/js/jquery_existing.80428b75d467.js'
I0708 09:07:01.872168   27226 sti.go:684] Post-processed 'debug_toolbar/js/toolbar.template.js' as 'debug_toolbar/js/toolbar.template.ef8e759fa78a.js'
I0708 09:07:01.872672   27226 sti.go:684] Post-processed 'debug_toolbar/js/toolbar.sql.js' as 'debug_toolbar/js/toolbar.sql.e9e00e697675.js'
I0708 09:07:01.873257   27226 sti.go:684] Post-processed 'debug_toolbar/js/toolbar.timer.js' as 'debug_toolbar/js/toolbar.timer.85df3882ee48.js'
I0708 09:07:01.874889   27226 sti.go:684] Post-processed 'debug_toolbar/js/toolbar.js' as 'debug_toolbar/js/toolbar.b1acccf75314.js'
I0708 09:07:01.875323   27226 sti.go:684] Post-processed 'debug_toolbar/js/jquery_pre.js' as 'debug_toolbar/js/jquery_pre.a593235debe9.js'
I0708 09:07:01.875602   27226 sti.go:684] Post-processed 'debug_toolbar/img/back.png' as 'debug_toolbar/img/back.1a85a8afa24e.png'
I0708 09:07:01.875875   27226 sti.go:684] Post-processed 'debug_toolbar/img/ajax-loader.gif' as 'debug_toolbar/img/ajax-loader.d96a4c3765e9.gif'
I0708 09:07:01.876078   27226 sti.go:684] Post-processed 'debug_toolbar/img/close_hover.png' as 'debug_toolbar/img/close_hover.2592d7057d2c.png'
I0708 09:07:01.876321   27226 sti.go:684] Post-processed 'debug_toolbar/img/close.png' as 'debug_toolbar/img/close.c592da3c89b6.png'
I0708 09:07:01.876524   27226 sti.go:684] Post-processed 'debug_toolbar/img/indicator.png' as 'debug_toolbar/img/indicator.5eb28882cc03.png'
I0708 09:07:01.876754   27226 sti.go:684] Post-processed 'debug_toolbar/img/djdt_vertical.png' as 'debug_toolbar/img/djdt_vertical.204979d634f7.png'
I0708 09:07:01.876995   27226 sti.go:684] Post-processed 'debug_toolbar/img/back_hover.png' as 'debug_toolbar/img/back_hover.d1e655d74852.png'
I0708 09:07:01.877939   27226 sti.go:684] Post-processed 'admin/css/rtl.css' as 'admin/css/rtl.4c867197b256.css'
I0708 09:07:01.880318   27226 sti.go:684] Post-processed 'debug_toolbar/css/toolbar.css' as 'debug_toolbar/css/toolbar.b35523ea26ab.css'
I0708 09:07:01.881245   27226 sti.go:684] Post-processed 'admin/css/fonts.css' as 'admin/css/fonts.494e4ec545c9.css'
I0708 09:07:01.882631   27226 sti.go:684] Post-processed 'admin/css/forms.css' as 'admin/css/forms.2003a066ae02.css'
I0708 09:07:01.883801   27226 sti.go:684] Post-processed 'admin/css/changelists.css' as 'admin/css/changelists.f6dc691f8d62.css'
I0708 09:07:01.885814   27226 sti.go:684] Post-processed 'admin/css/widgets.css' as 'admin/css/widgets.5e372b41c483.css'
I0708 09:07:01.888306   27226 sti.go:684] Post-processed 'admin/css/base.css' as 'admin/css/base.6b517d0d5813.css'
I0708 09:07:01.889066   27226 sti.go:684] Post-processed 'admin/css/login.css' as 'admin/css/login.a846c0e2ef65.css'
I0708 09:07:01.889741   27226 sti.go:684] Post-processed 'admin/css/dashboard.css' as 'admin/css/dashboard.7ac78187c567.css'
I0708 09:07:01.890337   27226 sti.go:684] Post-processed 'debug_toolbar/css/print.css' as 'debug_toolbar/css/print.85b39f60bfe8.css'
I0708 09:07:01.891465   27226 sti.go:684] Post-processed 'admin/css/rtl.css' as 'admin/css/rtl.4c867197b256.css'
I0708 09:07:01.894459   27226 sti.go:684] Post-processed 'debug_toolbar/css/toolbar.css' as 'debug_toolbar/css/toolbar.b35523ea26ab.css'
I0708 09:07:01.895738   27226 sti.go:684] Post-processed 'admin/css/fonts.css' as 'admin/css/fonts.494e4ec545c9.css'
I0708 09:07:01.897781   27226 sti.go:684] Post-processed 'admin/css/forms.css' as 'admin/css/forms.2003a066ae02.css'
I0708 09:07:01.899183   27226 sti.go:684] Post-processed 'admin/css/changelists.css' as 'admin/css/changelists.f6dc691f8d62.css'
I0708 09:07:01.901279   27226 sti.go:684] Post-processed 'admin/css/widgets.css' as 'admin/css/widgets.5e372b41c483.css'
I0708 09:07:01.904602   27226 sti.go:684] Post-processed 'admin/css/base.css' as 'admin/css/base.6b517d0d5813.css'
I0708 09:07:01.905450   27226 sti.go:684] Post-processed 'admin/css/login.css' as 'admin/css/login.a846c0e2ef65.css'
I0708 09:07:01.906150   27226 sti.go:684] Post-processed 'admin/css/dashboard.css' as 'admin/css/dashboard.7ac78187c567.css'
I0708 09:07:01.906753   27226 sti.go:684] Post-processed 'debug_toolbar/css/print.css' as 'debug_toolbar/css/print.85b39f60bfe8.css'
I0708 09:07:01.906983   27226 sti.go:684]
I0708 09:07:01.906989   27226 sti.go:684] 78 static files copied to '/opt/app-root/src/staticfiles', 98 post-processed.
I0708 09:07:02.654169   27226 docker.go:1030] Waiting for container "cc6e5a59663a64532b3ba420879690cbaf09bd6062a3580cad29966a600f8364" to stop ...
I0708 09:07:02.969465   27226 docker.go:1055] Invoking PostExecute function
I0708 09:07:02.969479   27226 postexecutorstep.go:68] Skipping step: store previous image
I0708 09:07:02.969483   27226 postexecutorstep.go:117] Executing step: commit image
I0708 09:07:02.971001   27226 postexecutorstep.go:522] Checking for new Labels to apply...
I0708 09:07:02.971015   27226 postexecutorstep.go:530] Creating the download path '/tmp/s2i718143045/metadata'
I0708 09:07:02.971040   27226 postexecutorstep.go:464] Downloading file "/tmp/.s2i/image_metadata.json"
I0708 09:07:03.059211   27226 postexecutorstep.go:538] unable to download and extract 'image_metadata.json' ... continuing
I0708 09:07:03.061216   27226 docker.go:1089] Committing container with dockerOpts: {Reference:hello-python Comment: Author: Changes:[] Pause:false Config:0xc420336c80}, conf
ig: {Hostname: Domainname: User:1001 AttachStdin:false AttachStdout:false AttachStderr:false ExposedPorts:map[] Tty:false OpenStdin:false StdinOnce:false Env:[] Cmd:[/usr/lib
exec/s2i/run] Healthcheck:<nil> ArgsEscaped:false Image: Volumes:map[] WorkingDir: Entrypoint:[container-entrypoint] NetworkDisabled:false MacAddress: OnBuild:[] Labels:map[n
ame:centos/python-35-centos7 io.openshift.s2i.build.commit.date:Tue Apr 24 18:48:25 2018 +0200 version:3.5 io.openshift.s2i.scripts-url:image:///usr/libexec/s2i io.openshift.
expose-services:8080:http summary:Platform for building and running Python 3.5 applications io.openshift.builder-version:"577297a" org.label-schema.schema-version:= 1.0     o
rg.label-schema.name=CentOS Base Image     org.label-schema.vendor=CentOS     org.label-schema.license=GPLv2     org.label-schema.build-date=20180531 io.openshift.s2i.build.i
mage:centos/python-35-centos7 io.k8s.display-name:hello-python description:Python 3.5 available as container is a base platform for building and running various Python 3.5 ap
plications and frameworks. Python is an easy to learn, powerful programming language. It has efficient high-level data structures and a simple but effective approach to objec
t-oriented programming. Python's elegant syntax and dynamic typing, together with its interpreted nature, make it an ideal language for scripting and rapid application develo
pment in many areas on most platforms. io.k8s.description:Python 3.5 available as container is a base platform for building and running various Python 3.5 applications and fr
ameworks. Python is an easy to learn, powerful programming language. It has efficient high-level data structures and a simple but effective approach to object-oriented progra
mming. Python's elegant syntax and dynamic typing, together with its interpreted nature, make it an ideal language for scripting and rapid application development in many are
as on most platforms. io.openshift.s2i.build.commit.ref:master io.openshift.s2i.build.commit.author:Honza Horak <hhorak@redhat.com> io.openshift.s2i.build.commit.id:37f7fc414
32b9c07265c5896a4fb226caa870427 usage:s2i build https://github.com/sclorg/s2i-python-container.git --context-dir=3.5/test/setup-test-app/ centos/python-35-centos7 python-samp
le-app io.s2i.scripts-url:image:///usr/libexec/s2i maintainer:SoftwareCollections.org <sclorg@redhat.com> release:1 io.openshift.s2i.build.commit.message:Merge pull request #
115 from hhorak/python-3.6 io.openshift.s2i.build.source-location:https://github.com/openshift/django-ex io.openshift.tags:builder,python,python35,rh-python35 com.redhat.comp
onent:python35-container] StopSignal: StopTimeout:<nil> Shell:[]}
I0708 09:07:05.314432   27226 postexecutorstep.go:392] Executing step: report success
I0708 09:07:05.314452   27226 postexecutorstep.go:397] Successfully built hello-python
I0708 09:07:05.314459   27226 postexecutorstep.go:93] Skipping step: remove previous image
I0708 09:07:05.314486   27226 docker.go:966] Removing container "cc6e5a59663a64532b3ba420879690cbaf09bd6062a3580cad29966a600f8364"
I0708 09:07:05.487309   27226 docker.go:976] Removed container "cc6e5a59663a64532b3ba420879690cbaf09bd6062a3580cad29966a600f8364"
I0708 09:07:05.487373   27226 cleanup.go:33] Removing temporary directory /tmp/s2i718143045
I0708 09:07:05.487380   27226 fs.go:278] Removing directory '/tmp/s2i718143045'
I0708 09:07:05.487947   27226 build.go:177] Build completed successfully
```

</p></details></br>
