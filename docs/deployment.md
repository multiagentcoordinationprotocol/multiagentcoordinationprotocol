# MACP Deployment Topologies

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0001 Core](../rfcs/RFC-MACP-0001-core.md)

MACP is deployment-agnostic at the protocol level, but certain deployment shapes preserve its guarantees better than others.

## 1. Single Runtime

The simplest deployment hosts a single runtime and a small set of agents.

```mermaid
flowchart LR
  Client --> Runtime[MACP Runtime]
  Runtime --> AgentA
  Runtime --> AgentB
  Runtime --> AgentC
  Runtime --> Ledger[(Session Ledger)]
```

This topology is ideal for development, proofs of concept, or tightly controlled single-tenant systems.

## 2. Sharded Runtime

For higher throughput, sessions are partitioned by `session_id`.

```mermaid
flowchart TB
  LB[Load Balancer] --> Router[Router]
  Router --> S1[Shard 1]
  Router --> S2[Shard 2]
  Router --> S3[Shard 3]
  S1 --> L1[(Partition 1)]
  S2 --> L2[(Partition 2)]
  S3 --> L3[(Partition 3)]
```

The critical invariant is that a single OPEN session has exactly one owner at a time.

## 3. Federated Coordination

Federated deployments allow different organizations or trust domains to run separate runtimes while coordinating through agreed transport and manifest surfaces.

```mermaid
flowchart LR
  A[Org A Runtime] <-->|TLS + MACP| B[Org B Runtime]
  A --> AAgents[Org A Agents]
  B --> BAgents[Org B Agents]
```

Federation works best when manifests, mode descriptors, and registries are stable and discoverable.

## 4. Operational recommendations

- keep session owners close to their ledgers,  
- propagate backpressure rather than buffering indefinitely,  
- treat registries as cacheable but versioned,  
- expose health, latency, and rejection metrics per shard.
