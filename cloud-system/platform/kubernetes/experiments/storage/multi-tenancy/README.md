## Persistent volume multi-tenancy

There is currently no multi-tenancy concept in persistentvolume; however, it is
essentially implemented. If a PV is bound to a PVC, it will never be bound to
another PVC. And if PVC gets deleted, the PV gets Released. Based on
persistentVolumeReclaimPolicy of the PV, the PV is either deleted or recycled
(data on the PV are discarded in both cases) or remains Released forever and
thus nobody can bind to it. Only admin can manually access data on the PV or
forcefully bind the PV to another PVC.

The experiment runs two namespaces, but it doesn't matter if it is one or two
namespaces, since PV can only bound to one PVC at a time.
