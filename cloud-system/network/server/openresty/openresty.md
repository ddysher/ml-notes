<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Run Openresty](#run-openresty)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

OpenResty is a web server which extends Nginx by bundling it with many useful Nginx modules and
Lua libraries.

# Run Openresty

Run openresty server (same as nginx):

```
docker run -itd -p 8999:80 openresty/openresty:jessie
```

Run openresty server with lua module: remove above container and start a new server with lua module used:

```
docker run -itd -p 8999:80 -v `pwd`/simple_lua.conf:/usr/local/openresty/nginx/conf/nginx.conf openresty/openresty:jessie
```
