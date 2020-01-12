<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Configurator](#configurator)
  - [Monitor](#monitor)
  - [Trireme](#trireme)
  - [PolicyResolver](#policyresolver)
  - [Supervisor](#supervisor)
  - [Enforcer](#enforcer)
- [Security](#security)
  - [PSK vs PKI](#psk-vs-pki)
  - [JWT token and TCP authentication](#jwt-token-and-tcp-authentication)
- [Kubernetes](#kubernetes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 12/24/2016*

## Configurator

configurator is not a running component; but rather a package that provides some helper functions to
help create default Trireme and Monitor configurations.

## Monitor

Monitor itself is defined as an interface and a set of constants; different implementations monitor
different PU (e.g. docker, process). Upon receiving PU events (e.g. docker event), monitor generates
a standard Trireme Processing Unit representation. The Monitor hands-over the Processing Unit runtime
to Trireme. For docker, basically, monitor acts as a bridge between docker event and Trireme defined
`event` representation; for example, it inspects docker container to extract required metadata and
send the data to Trireme. Trireme doesn't have to understand docker specific details. Monitor runs
as a set of goroutines: one goroutine listens docker events, one handles the events, etc. Monitor
hands-over the PU runtime spec to Trireme via function call in the codebase.

## Trireme

Trireme is the central package providing policy instantiation logic. It receives PU events from the
Monitor and dispatches the resulting generated policy to the other modules. At its core, Trireme
launches supervisor, enforcer and a goroutine to handle requests about PU and Policy events, i.e.

```go
if err := t.supervisor.Start(); err != nil {
}
if err := t.enforcer.Start(); err != nil {
}
go t.run()
```

## PolicyResolver

As stated in the architecture guide, Trireme calls the PolicyResolver to get a PU policy based on a
PU runtime. The PolicyResolver depends on the orchestration system used for managing identity and
policy; e.g. to use Trireme on kubernetes, a kubernetes PolicyResolver must be implemented. To be
specific, PolicyResolver is provided a context string (an ID) and a runtime reader (to read PU
runtime, e.g. PID, Tag); based on the information and known policies (predefined rules or dynamic
rules like kubernetes network policy), PolicyResolver must return a PU policy for Trireme to enforce.
On the other hand, PolicyResolver can call trireme.UpdatePolicy to explicitly require policy update,
e.g. in case of kubernetes network policy change.

## Supervisor

The Supervisor implements the policy by redirecting the TCP negotiation packets to user space. The
default implementation uses iptables with libnetfilter. In short, Supervisor uses nfqueue, and
redirect SYN,SYNACK,ACK TCP packets to user space, which is then catched by Enforcer to do the
verdict; e.g.

```
...
// Application Syn and Syn/Ack in RAW
{
  appPacketIPTableContext, r.appPacketIPTableSection,
  "-m", "set", "--match-set", set, "dst",
  "-p", "tcp", "--tcp-flags", "FIN,SYN,RST,PSH,URG", "SYN",
  "-j", "NFQUEUE", "--queue-balance", applicationQueues,
},
...
```

Supervisor is usually created via configurator, and Trireme is  to start the Supervisor. Also,
Trireme will call supervisor.Supervise to handle policies (doUpdatePolicy and do doHandleCreate).
Note that only TCP negotiation packets will be redirected, other packets won't be affected.

## Enforcer

The Enforcer enforces the policy by analyzing the redirected packets and enforcing the identity and
policy rules that are defined by the PolicyResolver in the PU policy. Like Supervisor, Enforcer is
usually created via configurator, and Trireme is responsible to start it.

Trireme will `enforcer.Enforce` to handle policies. Unlike Supervisor, Enforcer does the actual job
in background goroutines, i.e: For application queues:

```go
for i := uint16(0); i < d.filterQueue.NumberOfApplicationQueues; i++ {
  nfq[i], err = netfilter.NewNFQueue(d.filterQueue.ApplicationQueue+i, d.filterQueue.ApplicationQueueSize, netfilter.NfDefaultPacketSize)

  if err != nil {
    log.WithFields(log.Fields{
      "package": "enforcer",
      "error":   err.Error(),
    }).Fatal("Unable to initialize netfilter queue - Aborting")
  }

  go func(i uint16) {
    for true {
      select {
      case packet := <-nfq[i].Packets:
        d.processApplicationPacketsFromNFQ(packet)
      }
    }
  }(i)
}
```

For network queues:

```go
for i := uint16(0); i < d.filterQueue.NumberOfNetworkQueues; i++ {
  // Initalize all the queues
  nfq[i], err = netfilter.NewNFQueue(d.filterQueue.NetworkQueue+i, d.filterQueue.NetworkQueueSize, netfilter.NfDefaultPacketSize)
  ...
  go func(i uint16) {
    for true {
      select {
      case packet := <-nfq[i].Packets:
        d.processNetworkPacketsFromNFQ(packet)
      }
    }
  }(i)
}
```

*References*

- https://github.com/aporeto-inc/trireme/tree/b5e9662e28db6a84db591b576f5d9f636dfb49c3#trireme-architecture

# Security

## PSK vs PKI

PSK (Pre-Shared Key) is used as symmetric encryption while PKI (Public Key Infrastructure) is used
as asymmetric encryption. In Trireme, both will be converted to `tokens.Secrets` interface.

```
TriremeWithPSK([]string{"172.17.0.0/24"}, *externalMetadataFile, remoteEnforcer)
  -> configurator.NewPSKTriremeWithDockerMonitor("Server1", networks, policyEngine, nil, nil, false, []byte("THIS IS A BAD PASSWORD"), bashExtractor, remoteEnforcer)
    -> NewTriremeWithDockerMonitor(serverID, networks, resolver, processor, eventCollector, tokens.NewPSKSecrets(key), syncAtStart, dockerMetadataExtractor, remoteEnforcer)
TriremeWithPKI(*keyFile, *certFile, *caCertFile, []string{"172.17.0.0/24"}, *externalMetadataFile, remoteEnforcer)
  -> configurator.NewPKITriremeWithDockerMonitor("Server1", networks, policyEngine, nil, nil, false, keyPEM, certPEM, caCertPEM, bashExtractor, remoteEnforcer)
    -> publicKeyAdder := tokens.NewPKISecrets(keyPEM, certPEM, caCertPEM, map[string]*ecdsa.PublicKey{})
    -> NewTriremeWithDockerMonitor(serverID, networks, resolver, processor, eventCollector, publicKeyAdder, syncAtStart, dockerMetadataExtractor, remoteEnforcer)
```

## JWT token and TCP authentication

The above secret (PSK, PKI) is passed to enforcer, which then uses the secret to create a JWT token
processor, i.e:

```go
tokenEngine, err := tokens.NewJWT(validity, serverID, secrets)
``

Where `validity := time.Hour * 8760`. A token engine must implement TokenEngine interface, see below.
Along with 'ConnectionClaims' which is the JWT claim used in Trireme.

```
// TokenEngine is the interface to the different implementations of tokens
type TokenEngine interface {
  // CreteAndSign creates a token, signs it and produces the final byte string
  CreateAndSign(attachCert bool, claims *ConnectionClaims) []byte
  // Decode decodes an incoming buffer and returns the claims and the sender certificate
  Decode(decodeCert bool, buffer []byte, cert interface{}) (*ConnectionClaims, interface{})
}

// ConnectionClaims captures all the claim information
type ConnectionClaims struct {
  T   *policy.TagsMap
  LCL []byte
  RMT []byte
  EK  []byte
}
```

When a packet is received from nfqueue, enforcer (default datapath.go) will create a custom packet:

```
tcpPacket, err := packet.New(packet.PacketTypeApplication, p.Buffer)
```

Where `p` is the original packet passed from nfqueue, while `tcpPacket` has additional data added
from Trireme. If the packet is application packet, i.e. packets arriving from an application and are
destined to the network, a JWT token is created and added to tcpPacket's custom data. If the packet
is network packet, i.e. arriving from network and are destined to the application, then the JWT token
is checked; in this case, packet will be dropped if verification fails.

## Policy

Enforcer (datapath.go) encodes policy rules from PolicyResolver to its internal types `puContext.receiverRules`
and `puContext.transmitterRules`. These rules include things like "only allow traffic from docker
container with the same label as me".

In processNetworkSynPacket (process SYN packet from network to the application), we first extract
claims from Trireme custom TCP data, then check 'receiverRules' to see if the packet can be sent to
the application or not. In the docker container example, we only have 'receiverRules'.

```go
claims, err := d.parsePacketToken(connection, tcpPacket.ReadTCPData())
...
if index, action := context.receiverRules.Search(claims.T); index >= 0 {
}
```

In processNetworkSynAckPacket (process SYN/ACK packet), we also extract claims from Trireme custom
TCP data, then check 'transmitterRules' to see if reverse policy is matched, i.e. if sending from
application to network is permitted (NetworkSynAckPacket is the packet sent from application to
network to ACK the previous SYN from network).

```go
claims, cert := d.tokenEngine.Decode(false, tcpData, nil)
...
if index, action := context.transmitterRules.Search(claims.T); !d.mutualAuthorization || index >= 0 {
}
```

# Kubernetes

A few points about kubernetes integration:
- Trireme doesn't listen on kubernetes pod events, but rather still watches docker event, and only
  process kubernetes infra contaienr
- A project 'kubepox' is used to get exactly the Policies/Rules that apply to a specific Pod.
  PolicyResolver uses the information to pass policies to Trireme.
