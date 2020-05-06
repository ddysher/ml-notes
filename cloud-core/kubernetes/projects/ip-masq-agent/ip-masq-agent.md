<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Implementation](#implementation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 05/17/2017, kubernetes v1.6*

This daemon solves the problem of configuring the CIDR ranges for non-masquerade in a cluster (via
iptables rules). Today, this is accomplished by passing a `--non-masquerade-cidr` flag to the Kubelet,
which only allows one CIDR to be configured as non-masquerade. RFC 1918, however, defines three ranges
(10/8, 172.16/12, 192.168/16) for the private IP address space. The following code snippet shows how
`--non-masquerade-cidr` flag works in kubenet:

```go
func (plugin *kubenetNetworkPlugin) Init(host network.Host, hairpinMode componentconfig.HairpinMode, nonMasqueradeCIDR string, mtu int) error {
  plugin.host = host
  plugin.hairpinMode = hairpinMode
  plugin.nonMasqueradeCIDR = nonMasqueradeCIDR

  ...

  // Need to SNAT outbound traffic from cluster
  if err = plugin.ensureMasqRule(); err != nil {
    return err
  }
  return nil
}

// TODO: move thic logic into cni bridge plugin and remove this from kubenet
func (plugin *kubenetNetworkPlugin) ensureMasqRule() error {
  if _, err := plugin.iptables.EnsureRule(utiliptables.Append, utiliptables.TableNAT, utiliptables.ChainPostrouting,
    "-m", "comment", "--comment", "kubenet: SNAT for outbound traffic from cluster",
    "-m", "addrtype", "!", "--dst-type", "LOCAL",
    "!", "-d", plugin.nonMasqueradeCIDR,
    "-j", "MASQUERADE"); err != nil {
    return fmt.Errorf("Failed to ensure that %s chain %s jumps to MASQUERADE: %v", utiliptables.TableNAT, utiliptables.ChainPostrouting, err)
  }
  return nil
}
```

Some users will want to communicate between these ranges without masquerade - for instance, if an
organization's existing network uses the 10/8 range, they may wish to run their cluster and Pods in
192.168/16 to avoid IP conflicts. They will also want these Pods to be able to communicate efficiently
(no masquerade) with each-other and with their existing network resources in 10/8.

This requires that every node in their cluster skips masquerade for both ranges. Kubernetes is trying
to eliminate networking code from the Kubelet, so rather than extend the Kubelet to accept multiple
CIDRs, the project allows you to run a DaemonSet that configures a list of CIDRs as non-masquerade.

*Update on 04/07/2018, kubernetes v1.10*

The [project](https://github.com/mtaufen/ip-masq-agent) is proposed to kubernetes incubator, which is
approved and then moved to [incubator](https://github.com/kubernetes-incubator/ip-masq-agent).

# Implementation

Basically, when start up, ip-masq-agent will add iptable rules to NOT masquerade traffic for CIDRs
passed as parameters, and for all other traffic, do masquerade. It works by adding a rule in
`POSTROUTING` chain:

```go
if _, err := m.iptables.EnsureRule(utiliptables.Append, utiliptables.TableNAT, utiliptables.ChainPostrouting,
  "-m", "comment", "--comment", postroutingJumpComment,
  // postroutingJumpComment,
  "-m", "addrtype", "!", "--dst-type", "LOCAL", "-j", string(masqChain)); err != nil {
  return fmt.Errorf("failed to ensure that %s chain %s jumps to MASQUERADE: %v", utiliptables.TableNAT, masqChain, err)
}
```

i.e. jumps to this chain for any traffic not bound for a LOCAL destination. Then for user-provided
CIDRs:

```go
// non-masquerade for user-provided CIDRs
for _, cidr := range m.config.NonMasqueradeCIDRs {
  writeNonMasqRule(lines, cidr)
}

func writeNonMasqRule(lines *bytes.Buffer, cidr string) {
  writeRule(lines, utiliptables.Append, masqChain,
    nonMasqRuleComment,
    "-m", "addrtype", "!", "--dst-type", "LOCAL", "-d", cidr, "-j", "RETURN")
}
```

This will make sure user provided CIDRs return early and thus not subject to `MASQUERADE`. The final
rule in the IP-MASQ-AGENT chain will MASQUERADE any non-LOCAL traffic.

```go
func writeMasqRule(lines *bytes.Buffer) {
  writeRule(lines, utiliptables.Append, masqChain,
    masqRuleComment,
    "-m", "addrtype", "!", "--dst-type", "LOCAL", "-j", "MASQUERADE")
}
```
