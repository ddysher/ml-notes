<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Jupyter (Notebook)](#jupyter-notebook)
  - [Overview](#overview)
  - [Kernel](#kernel)
    - [Two process model](#two-process-model)
    - [Remote Kernel](#remote-kernel)
  - [Extending Notebook](#extending-notebook)
    - [Custom Kernel](#custom-kernel)
    - [IPython Kernel Extension](#ipython-kernel-extension)
    - [Notebook Extension (nbextension)](#notebook-extension-nbextension)
    - [Notebook Server Extension](#notebook-server-extension)
- [Jupyterhub](#jupyterhub)
  - [Overview](#overview-1)
  - [Subsystems](#subsystems)
- [JupyterLab](#jupyterlab)
  - [Overview](#overview-2)
- [Extension Projects](#extension-projects)
  - [sos](#sos)
  - [nteract](#nteract)
  - [nbdime](#nbdime)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Jupyter (Notebook)

## Overview

Jupyter is an evolution of IPython, a project which provides enhanced interactive computing in python.
IPython itself now focuses on interactive experience, other parts like notebook, qt console and a
number of other pieces are now parts of `Jupyter`.

The Jupyter Notebook is an open-source web application that allows you to create and share documents
that contain live code, equations, visualizations and narrative text. Usage include: data cleaning
and transformation, numerical simulation, statistical modeling, data visualization, machine learning,
and much more.

## Kernel

### Two process model

**From IPython**

IPython has abstracted and extended the notion of a traditional `Read-Evaluate-Print Loop (REPL)`
environment by decoupling the *evaluation* into its own process. We call this process a **kernel**:
it receives execution instructions from clients and communicates the results back to them.

This decoupling allows us to have several clients connected to the same kernel, and even allows
clients and kernels to live on different machines. With the exclusion of the traditional single
process terminal-based IPython (what you start if you run ``ipython`` without any subcommands), all
other IPython machinery uses this two-process model. Most of this is now part of the `Jupyter`
project, which includes ``jupyter console``,  ``jupyter qtconsole``, and ``jupyter notebook``.

As an example, this means that when you start ``jupyter qtconsole``, you're really starting two
processes, a kernel and a Qt-based client can send commands to and receive results from that kernel.
If there is already a kernel running that you want to connect to, you can pass the  ``--existing``
flag which will skip initiating a new kernel and connect to the most recent kernel, instead. To
connect to a specific kernel once you have several kernels running, use the ``%connect_info`` magic
to get the unique connection file, which will be something like ``--existing kernel-19732.json`` but
with different numbers which correspond to the Process ID of the kernel.

**For Notebook**

Kernel runs as a backend process, launched via jupyter web application when user runs a notebook with
choosen kernel, and accepts messages from jupyter web application through ZeroMQ.

A `kernel` is a program that runs and introspects the user’s code. It is a purposely [designed feature](https://ipython.readthedocs.io/en/stable/overview.html#decoupled-two-process-model)
called `decoupled two-process model` in ipython: a client process and a kernel. The client process
is the jupyter notebook web application, note the web application actually has two parts: the frontend
part that runs in browser, and the backend part listens for request (default :8888). Frontend
communicates with backend using websocket; it is the backend part of the application that uses zeromq
to talk to kernel. The backend is a tornado based server.

<p align="center"><img src="./assets/notebook_components.png" height="240px" width="auto"></p>

The notebook server, not the kernel, is responsible for saving and loading notebooks, so you can edit
notebooks even if you don't have the kernel for that language - you just won't be able to run code.
The kernel doesn't know anything about the notebook document: it just gets sent cells of code to
execute when the user runs them.

The messge protocol between client and kernel are documented in [jupyter-client messaging section](https://jupyter-client.readthedocs.io/en/latest/messaging.html)
website. Its wire protocol uses `zeromq` and defines 5 sockets (kernel will listen on all sockets):
- Shell
- IOPub
- Stdin
- Control
- Heartbeat

For example, we can start a notebook with:

```
$ jupyter notebook
[I 19:49:41.651 NotebookApp] nteract extension loaded from /Users/deyuandeng/.pyenv/versions/3.6.7/lib/python3.6/site-packages/nteract_on_jupyter
[I 19:49:41.653 NotebookApp] Serving notebooks from local directory: /Users/deyuandeng
[I 19:49:41.653 NotebookApp] The Jupyter Notebook is running at:
[I 19:49:41.653 NotebookApp] http://localhost:8888/?token=2e9e7dfc1e8c8d4aa5b03e8e138b427d05c1b434d6629131
[I 19:49:41.653 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 19:49:41.657 NotebookApp]

    Copy/paste this URL into your browser when you connect for the first time,
    to login with a token:
        http://localhost:8888/?token=2e9e7dfc1e8c8d4aa5b03e8e138b427d05c1b434d6629131
```

At this moment, no kernel is created, only the notebook application:

```
$ ps aux | grep python
...
deyuandeng       86077   0.0  0.3  4291572  28420 s002  S+    7:49PM   0:00.99 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/jupyter-notebook
```

Now open a notebook, the application will create a ipython kernel ready to interpret python code:

```
$ ps aux | grep ipy
...
deyuandeng       86606   0.0  0.5  4306300  43920   ??  Ss    7:53PM   0:00.80 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 -m ipykernel_launcher -f /Users/deyuandeng/Library/Jupyter/runtime/kernel-230aff1e-fd99-4db5-920f-6644eda9835d.json
```

### Remote Kernel

Remote kernel means the kernel is running on a different machine than the notebook, and notebook
talks to kernels via [jupyter kernel gateway](https://github.com/jupyter/kernel_gateway), or an
advanced alternative [enterprise gateway](https://github.com/jupyter/enterprise_gateway). To use
remote kernel, we also need to enable notebook server extension [nb2kg](https://github.com/jupyter/nb2kg).
The extension overrides the `/api/kernels/*` and `/api/kernelspecs` request handlers of the Notebook
server, and proxies all requests for these resources to the Gateway. The project has a great summary
of how remote kernel works.

Internally, jupyter frontend sends a set of requests to backend proxy, e.g.
```
http://localhost:8888/api/kernels/
http://localhost:8888/api/kernels/{id}/restart
ws://localhost:8888/api/kernels/{id}/channels?session_id={id}
```

Normally, jupyter server backend handles these requests directly. Now with nb2kg extension, it
doesn't handle them directly, but in turn proxies requests to kernel gateway (e.g. list available
kernels).

Note in the context of remote kernel, client/server (the jupyter notebook web application) still
run locally, only the kernel runs on remote machine or cluster. Kernel gateway and kernels can run
on the same machine or different machines.

Pay attention to the caveats:
- When you enable the extension, all kernels run on (are managed by) the configured Gateway, instead
  of on the Notebook server host. The extension does not support local kernels.
- When you enable the extension, notebooks and other files reside on the Notebook server, which means
  that remote kernels may not have access to them.
- If your kernel gateway instance is using a self-signed certificate in your development environment,
  you can turn off certificate validation by setting `VALIDATE_KG_CERT=no` in your environment before
  starting the notebook server.

## Extending Notebook

### Custom Kernel

As mentiond above, kernel is launched when starting a notebook. Below is a quick experiment with
[gophernotes](https://github.com/gopherdata/gophernotes), a custom kernel for golang.

From the official site, we install gophernotes (linux) with:

```shell
$ go get -u github.com/gopherdata/gophernotes
$ mkdir -p ~/.local/share/jupyter/kernels/gophernotes
$ cp $GOPATH/src/github.com/gopherdata/gophernotes/kernel/* ~/.local/share/jupyter/kernels/gophernotes
```

Note that we install the golang kernel via dropping config file to `~/.local/share/jupyter/kernels`.
Once we start notebook with `jupyter notebook`, jupyter will pick up the config thus we *registered*
the new kernel to our jupyter system. The config is simple:

```json
{
  "argv": [
    "gophernotes",
    "{connection_file}"
  ],
  "display_name": "Go",
  "language": "go",
  "name": "go"
}
```

Create a new notebook and choose kernel `Go`, jupyter web application will launch a new Go kernel
using command `gophernotes /run/user/1000/jupyter/kernel-1308393d-cf35-43dc-993b-8f2c3c3ccc5a.json`.
The json file contains dynamically generated configuration for gophernotes, e.g:

```json
{
  "control_port": 50199,
  "ip": "127.0.0.1",
  "key": "b28fa4f6-09544473cebc00eeb28b5818",
  "stdin_port": 35964,
  "iopub_port": 60500,
  "hb_port": 60943,
  "transport": "tcp",
  "kernel_name": "gophernotes",
  "signature_scheme": "hmac-sha256",
  "shell_port": 33890
}
```

The gophernotes application will listen on all the ports for messages. For example, following are
three messages when we start the kernel and type `import "fmt"` in jupyter frontend. The code is
sent through the message body for evaluation.

```
...
{Header:{MsgID:0b5b1bb0cea14ddc97b6437445c33134 Username:username Session:35497103ad2a478d867345e71a562ab3 MsgType:kernel_info_request ProtocolVersion:5.2 Timestamp:2018-09-06T05:56:25.707788Z} ParentHeader:{MsgID: Username: Session: MsgType: ProtocolVersion: Timestamp:} Metadata:map[] Content:map[]}
{Header:{MsgID:dae3f7e18c0a40c890e47a94c8937f5a Username:username Session:35497103ad2a478d867345e71a562ab3 MsgType:comm_info_request ProtocolVersion:5.2 Timestamp:2018-09-06T05:56:25.847388Z} ParentHeader:{MsgID: Username: Session: MsgType: ProtocolVersion: Timestamp:} Metadata:map[] Content:map[target_name:jupyter.widget]}
{Header:{MsgID:51f7abb088414b508c62c0d2271715e9 Username:username Session:35497103ad2a478d867345e71a562ab3 MsgType:execute_request ProtocolVersion:5.2 Timestamp:2018-09-06T05:56:51.832010Z} ParentHeader:{MsgID: Username: Session: MsgType: ProtocolVersion: Timestamp:} Metadata:map[] Content:map[allow_stdin:true code:import "fmt" user_expressions:map[] silent:false stop_on_error:true store_history:true]}
...
```

### IPython Kernel Extension

IPython Kernel extensions are Python modules that can modify the interactive shell environment
within an IPython kernel. Such extensions can register magics, define variables, and generally
modify the user namespace to provide new features for use within code cells.

For example, we can implement a custom magic named `dfmagic` to convert string to dataframe, and
register it to ipython kernel. User can then use `%%dfmagic` to use the extension.

For more information:
- https://ipython-books.github.io/14-creating-an-ipython-extension-with-custom-magic-commands/
- https://ipython.readthedocs.io/en/stable/config/extensions/index.html

### Notebook Extension (nbextension)

Jupyter Notebook extensions (nbextensions) are mostly JavaScript modules that alter jupyter web
application, e.g. custom buttons, key shortcut, etc.

nbextension can be installed via `jupyter nbextension install <name> [--user]`, which will place
js script to `/usr/local/share/jupyter/nbextensions` or `~/.local/share/jupyter/nbextensions`.
After installation, nbextension can be enabled via `jupyter nbextension enable <name>`, which
updates file `~/.jupyter/nbconfig/notebook.json`.

To write a new extension, you must implement your logic in a JavaScript file conforming to the
[AMD specification](https://en.wikipedia.org/wiki/Asynchronous_module_definition) so that Jupyter
can load it using RequireJS. You should define and export a `load_ipython_extension` function
in your module so that Jupyter can invoke it after initializing its own components. Within that
function, you are free to manipulate the DOM of the page, invoke Jupyter JavaScript APIs, listen
for Jupyter events, load other modules, and so on.

An example nbextension which counts notebook cell number:

```js
define([
  'base/js/namespace'
], function(Jupyter) {
  var exports = {};

  // Show counts of cell types
  var show_stats = function() {

    // Get counts of each cell type
    var cells = Jupyter.notebook.get_cells();
    var hist = {};
    for(var i=0; i < cells.length; i++) {
      var ct = cells[i].cell_type;
      if(hist[ct] === undefined) {
        hist[ct] = 1;
      } else {
        hist[ct] += 1;
      }
    }

    // Build paragraphs of cell type and count
    var body = $('<div>');
    for(var ct in hist) {
      $('<p>').text(ct+': '+hist[ct]).appendTo(body);
    }

    // Show a modal dialog with the stats
    Jupyter.dialog.modal({
      title: "Notebook Stats",
      body: body,
      buttons : {
        "OK": {}
      }
    });
  };

  // Wait for notification that the app is ready
  exports.load_ipython_extension = function() {
    // Then register command mode hotkey "c" to show the dialog
    Jupyter.keyboard_manager.command_shortcuts.add_shortcut('c', show_stats);
  };

  return exports;
});
```

Drop it to `~/.local/share/jupyter/nbextensions/count.js` and update `~/.jupyter/nbconfig/notebook.json` with:

```
{
  "load_extensions": {
    "count": true
  }
}
```

Now start jupyter notebook and press `c`, we'll see a modal showing number of cells in our notebook.
For more extensions, see [contrib nbextensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions).

### Notebook Server Extension

Jupyter Notebook server extensions are Python modules that load when the Notebook web server
application starts. Server extension has similar interfaces to nbextension, and they are mostly
used with nbextensions to provide more powerful features to jupyter notebook. Here is an [example](https://www.civisanalytics.com/blog/jupyter-server-extensions-notebook/) server
extension.

The core to server extension is two methods, which helps jupyter load the extension. In the example,
all requests from frontend to jupyter server path `/pizza_me` will be delivered to `PizzaDeliveryHandler`,
just like a regular web application.

```
def _jupyter_nbextension_paths():
    """Required to load JS button"""
    return [dict(
        section="notebook",
        src="static",
        dest="pizzabutton",
        require="pizzabutton/index")]


def load_jupyter_server_extension(nb_server_app):
    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, [
        (url_path_join(web_app.settings['base_url'], r'/pizza_me'),
         PizzaDeliveryHandler)
    ])
```

*References*

- https://mindtrove.info/4-ways-to-extend-jupyter-notebook/

# Jupyterhub

## Overview

[JupyterHub](https://jupyterhub.readthedocs.io/en/stable/), a multi-user Hub, spawns, manages, and
proxies multiple instances of the single-user Jupyter notebook server. JupyterHub can be used to
serve notebooks to a class of students, a corporate data science group, or a scientific research group.

## Subsystems

JupyterHub consists of three subsystems:
- a multi-user Hub (tornado process)
- a configurable http proxy (node-http-proxy)
- multiple single-user Jupyter notebook servers (Python/IPython/tornado)

JupyterHub performs the following functions:
1. The Hub launches a proxy
2. The proxy forwards all requests to the Hub by default
3. The Hub handles user login and spawns single-user servers on demand
4. The Hub configures the proxy to forward URL prefixes to the single-user notebook servers

# JupyterLab

## Overview

JupyterLab is the next-generation user interface for Project Jupyter. It offers all the familiar
building blocks of the classic Jupyter Notebook (notebook, terminal, text editor, file browser,
rich outputs, etc.) in a flexible and powerful user interface. **Eventually, JupyterLab will
replace the classic Jupyter Notebook.**

JupyterLab is built on top of an extension system that enables you to customize and enhance
JupyterLab by installing additional extensions. In fact, the builtin functionality of JupyterLab
itself (notebooks, terminals, file browser, menu system, etc.) is provided by a set of core
extensions.

*References*

- https://blog.jupyter.org/jupyterlab-is-ready-for-users-5a6f039b8906

# Extension Projects

## sos

Script of Scripts (SoS) is a Jupyter-based polyglot notebook that allows the use of multiple Jupyter
kernels in one notebook, and a workflow engine for the execution of workflows in both process- and
outcome-oriented styles. It is designed for data scienticists and bioinformatics who routinely work
with scripts in different languages such as R, Python, Perl, and bash.

The SOS project contains two subprojects:
- [SOS Notebook](https://github.com/vatlab/sos-notebook)
- [SOS Workflow System](https://github.com/vatlab/SoS)

The notebook project is a kernel implementation with two nice features:
- ability to switch between different kernels, e.g. R, Python2, Javascript, etc
- a handful of magic commands to ease notebook usage

**_How switching kernel works_**

SOS uses `jupyter_client` to start new kernel. Each kernel must be installed in jupyter, i.e.

```console
~jovyan@d9e2883cd22e:~$ jupyter kernelspec list
Available kernels:
  bash          /home/jovyan/.local/share/jupyter/kernels/bash
  javascript    /home/jovyan/.local/share/jupyter/kernels/javascript
  octave        /home/jovyan/.local/share/jupyter/kernels/octave
  python2       /home/jovyan/.local/share/jupyter/kernels/python2
  sos           /home/jovyan/.local/share/jupyter/kernels/sos
  sparql        /home/jovyan/.local/share/jupyter/kernels/sparql
  ir            /opt/conda/share/jupyter/kernels/ir
  julia-0.6     /opt/conda/share/jupyter/kernels/julia-0.6
  python3       /opt/conda/share/jupyter/kernels/python3
```

Every kernel in SOS needs to implement a class with `get_vars`, `put_vars`, e.g.

```python
class sos_Ruby:
    supported_kernels = {'Ruby': ['ruby']}
    background_color = '#EA5745'
    options = {}

    def __init__(self, sos_kernel, kernel_name='ruby'):
        ...

    def get_vars(self, names):
        ...

    def put_vars(self, items, to_kernel=None):
        ...
```

SOS kernel will proxy requests from juypter frontend to corresponding kernel.

**_How magic command works_**

There is a base `SoS_Magic` class with an important method `match`. Each magic command must subclass
the base object with `apply` method.

When sos kernel receives a request, it calls `match` on every magic command to see if it matches. If
there is no match, then proceeds with normal processing; otherwise, call `apply` method on the matched
magic command.

## nteract

The [nteract](https://github.com/nteract/nteract) project is a dynamic tool to give you flexibility
when writing code, exploring data, and authoring text to share insights about the data. nteract contains:
- desktop application (built with electron)
- jupyter server extension
- service for view and share notebooks

For server extension, start by running:

```
$ pip install nteract_on_jupyter
$ jupyter serverextension enable nteract_on_jupyter

$ jupyter nteract
[I 16:46:39.959 NteractApp] JupyterLab extension loaded from /Users/deyuandeng/.pyenv/versions/3.6.7/lib/python3.6/site-packages/jupyterlab
[I 16:46:39.959 NteractApp] JupyterLab application directory is /Users/deyuandeng/.pyenv/versions/3.6.7/share/jupyter/lab
[I 16:46:39.961 NteractApp] nteract extension loaded from /Users/deyuandeng/.pyenv/versions/3.6.7/lib/python3.6/site-packages/nteract_on_jupyter
[I 16:46:39.962 NteractApp] Serving notebooks from local directory: /Users/deyuandeng

$ ps aux | grep python
...
deyuandeng       88126   0.0  0.4  4291060  29700 s004  S+    8:05PM   0:00.88 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/jupyter-nteract
```

After opening a new notebook, the application will create an ipython kernel ready to interpret python
code. Essentially, this is similar to how notebook and jupyterlab works.

```
ps aux | grep ipy
...
deyuandeng       92446   0.0  0.5  4307068  44536   ??  Ss    9:09PM   0:00.86 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 -m ipykernel_launcher -f /Users/deyuandeng/Library/Jupyter/runtime/kernel-75862be0-8d25-4a18-b906-7cceb515f915.json
```

## nbdime

Since notebook is in rich-metadata format, traditional tools like `git` cannot properly parse it, thus
can only show raw diffs. These diffs are usually not readable. [nbdime](https://nbdime.readthedocs.io/en/latest/)
is a tool to solve the problem with content-aware diffing and merging of jupyter notebooks.
