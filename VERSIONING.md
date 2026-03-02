
# Versioning Policy

MACP uses semantic versioning.

## MACP Core Version

Format: MAJOR.MINOR.PATCH

- MAJOR: Breaking protocol changes
- MINOR: Backward-compatible additions
- PATCH: Clarifications or documentation fixes

Major version mismatches MUST result in rejection.

## Mode Versioning

Modes MUST include explicit version identifiers.

Breaking changes require:
- New mode version
- Clear migration guidance

## Schema Versioning

- Protobuf breaking changes require new package namespace (e.g., macp.v2)
- JSON schema updates MUST remain backward compatible unless major version changes

## RFC Versioning

RFC documents include:
- Version
- Status (Draft, Accepted, Final)
- Last Updated date

Breaking changes MUST increment the major version.
