# MACP Mode Registry

Coordination Modes define semantic coordination patterns within MACP sessions.

## Identifier Format

macp.mode.<name>.v<version>

Example:

macp.mode.decision.v1

## Standard Modes

| Mode | Description | Status | Reference |
|------|-------------|--------|-----------|
| macp.mode.decision.v1 | Proposal and voting decision | permanent | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| macp.mode.quorum.v1 | N-of-M approval coordination | provisional | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| macp.mode.negotiation.v1 | Iterative negotiation | provisional | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| macp.mode.auction.v1 | Auction-style bidding coordination | provisional | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |

## Mode Requirements

Modes MUST:

- respect MACP session lifecycle
- emit a terminal message for resolution
- document participant rules
- define payload schemas

## Experimental Modes

Experimental modes should use reverse-domain naming:

com.example.mode.custom.v1
