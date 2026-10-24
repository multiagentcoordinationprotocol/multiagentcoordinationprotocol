# Security Policy

## Reporting a vulnerability

Please report security problems privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Don't open a public issue for them.

This repository holds specifications and schemas, not running code. Relevant reports include:
- a protocol design flaw, such as a way to inject into another session, replay a message, or forge a commitment that the spec permits;
- a schema that accepts input the RFCs forbid;
- a gap in RFC-MACP-0004's threat model.

Bugs in an implementation belong to that implementation's repository, for example [macp-runtime](https://github.com/multiagentcoordinationprotocol/macp-runtime/security).

## Supported versions

Fixes go into the latest spec on `main` and the next tagged release. Earlier releases are not patched.
