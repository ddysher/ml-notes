Kubernetes’s minion interface is obscure and brittle.

Externally, we don’t have a formal document on how minion rest api works.  For example, in #1315, user is confused about ```kubecfg create minion```.  In #1995, user is unware of the assumption that to create a minion, kubelet should be started first. This is probably a bad assumption, but the worst part is the reported error, which gives user no clue of what’s happening.

Internally, I don’t know if there is a clear direction of how we want to manage minions, especially:
1. kubernetes admin interface
2. minion health check and monitoring

For 1, I think we need to give kubernetes admin a consistent view of how minion management is handled in kubernetes.  For example, we now have a minion controller that sychronizes machines from cloudprovider, but we still expose the API for admin to create a minion.  Mixing the two options are confusing and error prone.  Also, to create a minion is only to create a representation of a minion in kubernetes, we are unable to really “create” (provision) the minion for user.

For 2, we currently haven’t defined any minion state, nor do we define a strategy on how kubernetes reacts on each state.  A related issus #1923.  A better monitoring and reporting mechanism is needed to make kubernetes even better.

Instead of proposing any abstract idea, I’m thinking of some concrete stags that we can step in.

* Create a minion-controller with two functionalities: synchronization and health check.  To do this, we need to:
  * Move the health check functionality from api-server to minion-controller.
  * Define minion state.  To keep it simple, we can just use RUNNING, VANISHED for now.  In the long term, we can provide more states and health check policies.

* Make the synchronization part configurable.  If user prefers managing worker nodes themselves, Kubernetes cluster can be created without the synchronization process.  However, if synchronization is enabled, creating via user interface (command line, UI or their own plugins) is disabled, or report properly (via event if it’s ready and approprite for such use case).

* Allows user to easily see the status of his/her machines, something like
```
$ kubectl get minions
Minion Name                         Minion State             Utilization         Etc
kubernetes-1                          RUNNING                  30%
kubernetes-2                          RUNNING                  80%
kubernetes-3                          VANISHED                 0%
```

* Enable master server to provision a minion.  I don’t know how this works yet, but a rough procedure like installing salt & k8s config, deploying binaries, registering through API server, etc, might work.

* Provide better documentation.
