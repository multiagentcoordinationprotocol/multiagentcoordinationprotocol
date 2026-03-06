# MACP Capability Registry

| Capability | Scope | Description | Status |
|---|---|---|---|
| `sessions.stream` | runtime | Supports bidirectional session streaming | permanent |
| `cancellation.cancelSession` | runtime | Supports explicit session cancellation | permanent |
| `progress.progress` | runtime | Supports non-binding progress updates | permanent |
| `manifest.getManifest` | runtime | Supports agent/runtime manifest retrieval | permanent |
| `modeRegistry.listModes` | runtime | Supports mode descriptor listing | permanent |
| `modeRegistry.listChanged` | runtime | Supports mode registry change notifications | provisional |
| `roots.listRoots` | runtime | Supports root/boundary disclosure | provisional |
| `roots.listChanged` | runtime | Supports root change notifications | provisional |
| `experimental.*` | both | Non-standard experimental feature namespace | experimental |
