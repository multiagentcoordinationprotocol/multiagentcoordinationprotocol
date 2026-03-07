# MACP Media Type Registry

Defines media types used in MACP transports.

## Standard Media Types

| Media Type | Description | Status |
|-----------|-------------|--------|
| application/macp-envelope+json | JSON encoded MACP envelope | permanent |
| application/macp-envelope+proto | Protobuf encoded envelope | permanent |
| application/macp-manifest+json | MACP discovery manifest | permanent |

## Usage

Transports should declare media types using standard HTTP content-type headers.
