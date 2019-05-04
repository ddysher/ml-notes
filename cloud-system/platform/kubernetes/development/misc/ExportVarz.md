As part of cluster node monitoring, we need to export various node metrics to outside world: this is critical for updating node status. There are general node metrics, like cpu/memory usage, network latency, etc; and also server specific metrics. For example, for kubelet, it can be the number of accumulated failed pod count, etc. We can also extend the concept to apiserver, e.g. successful/failed/total requests, rate limit, etc.

We already exposed various information from kubelet (via /podInfo, /stats, etc), but those are important to manage working set of pod. We also expose some machine information via /spec, but that's only static machine information - we need much more.  Also, I'd like to separate core features from metrics. Everything that's not part of core features (e.g. pod info) should go to varz metrics.

In this issue, I'm looking into a better way to implement "export varz" function that fits into kubernetes.

**Code structure**
I tempt to create a new package "pkg/varz" for the purpose, while we could also merge it with "pkg/healthz" - if we don't want to spam our pkg directory.

**Pre-defined Metrics**
The package should allow clients to install pre-defined general metrics, so clients do not need to write the same metrics multiple times. Those pre-defined metrics are the set of general metrics mentioned above.

**Metrics Cache**
For time-consuing metrics, it's preferrable to have a background process instead of loading on demand. As to which metric to cache, we probably need to delegate it metric owner.

**Metrics Format**
As to how we export metrics, there are two options off my head now:
1. A webpage with all metrics in json (or other) format: this is how "expvar" works. It is easy to implement, but client will get excessive data than necessary. Unless we have some client util to scrape the data, I'm concerned about the latency/efficiency if varz get more complicated.
2. A 'namespaced' metric list based on url. For example, all memory stats goes under "host:port/varz/mem/", kubelet pod metrics goes under "host:port/varz/kubelet/pods", etc. This might be a little harder to parse, but more efficient and easier to target desired metrics.

**Easy-to-use Interface**
Obviously, the package needs to expose an easy interface so that pkg users can add customized metrics without pain. The existing package "expvar" is easy, but not flexible: The export metric format is fixed to json, and it's only accessible from url "host:port/debug/vars". So I'd suggest we create our own expvar, for example:
```go
// VarzExporter exports all registered varz, one for each server.
type VarzExporter struct {}

// VarzProducer knows how to produce a Varz
type VarzProducer struct {
    Prefix string
    EnableCache bool
    Produce func() (string, string)
    // more fields for fine grained control
}

// NewVarzExporter creates a new VarzExporter
func NewVarzExporter() *VarzExporter {}

// InstallDefaultVarz installs common metrics
func (v *VarzExporter) InstallDefaultVarz() {}

// AddVarzExporter adds a new VarzProducer
func (v *VarzExporter) AddVarzExporter(exporter VarzProducer) {}

// more methods
```

Some random thougts while thinking about node status. Not sure if this makes much sense to us, would like to get some input.
