# MACP Media Type Registry

Defines media types used in MACP transports.

## Standard Media Types

| Media Type | Description | Status | Reference |
|-----------|-------------|--------|-----------|
| application/macp-envelope+json | JSON encoded MACP envelope | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| application/macp-envelope+proto | Protobuf encoded envelope | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| application/macp-manifest+json | MACP discovery manifest | permanent | [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md) |
| application/macp-receipt+json | MACP decision receipt (`macp-receipt/1`) | provisional | [RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md) |

## Usage

Transports should declare media types using standard HTTP content-type headers.
